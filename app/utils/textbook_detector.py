"""
Textbook Detection and Smart Processing System

Detects if a PDF is a textbook and handles it with special care
"""

import re
from typing import Dict, List, Tuple, Optional
import asyncio
from app.utils.pdf_extractor import extract_text_from_pdf_url, estimate_token_count
import logging

logger = logging.getLogger(__name__)

class TextbookDetector:
    """Detects if a PDF is likely a textbook based on various heuristics"""
    
    # Textbook indicators
    TEXTBOOK_KEYWORDS = [
        'chapter', 'section', 'introduction', 'conclusion', 'exercise',
        'problem set', 'learning objective', 'summary', 'review question',
        'table of contents', 'index', 'glossary', 'appendix', 'preface',
        'part i', 'part ii', 'unit', 'module', 'lesson'
    ]
    
    ACADEMIC_PUBLISHERS = [
        'pearson', 'mcgraw', 'wiley', 'springer', 'elsevier', 
        'cambridge', 'oxford', 'sage', 'taylor & francis'
    ]
    
    @classmethod
    def is_likely_textbook(cls, paper_data: Dict) -> Tuple[bool, float, Dict]:
        """
        Determine if a document is likely a textbook
        Returns: (is_textbook, confidence, metadata)
        """
        indicators = 0
        total_checks = 0
        metadata = {}
        
        # Check title
        title = paper_data.get('title', '').lower()
        total_checks += 1
        if any(keyword in title for keyword in ['textbook', 'introduction to', 'fundamentals of', 'principles of', 'handbook']):
            indicators += 1
            metadata['title_match'] = True
            
        # Check page count (textbooks are typically long)
        page_count = paper_data.get('page_count', 0)
        if page_count > 0:
            total_checks += 1
            if page_count > 100:
                indicators += 1
                metadata['long_document'] = True
                
        # Check journal/source (textbooks usually don't have journals)
        journal = paper_data.get('journal', '')
        total_checks += 1
        if not journal or journal.lower() in ['book', 'textbook', 'open textbook']:
            indicators += 0.5
            metadata['no_journal'] = True
            
        # Check for publisher
        if 'publisher' in paper_data:
            publisher = paper_data['publisher'].lower()
            total_checks += 1
            if any(pub in publisher for pub in cls.ACADEMIC_PUBLISHERS):
                indicators += 1
                metadata['academic_publisher'] = True
                
        # Sample text analysis if available
        if 'full_text' in paper_data and paper_data['full_text']:
            sample_text = paper_data['full_text'][:5000].lower()
            total_checks += 2
            
            # Check for chapter markers
            chapter_count = len(re.findall(r'chapter\s+\d+', sample_text))
            if chapter_count >= 2:
                indicators += 1
                metadata['has_chapters'] = True
                metadata['chapter_count'] = chapter_count
                
            # Check for textbook keywords
            keyword_count = sum(1 for keyword in cls.TEXTBOOK_KEYWORDS if keyword in sample_text)
            if keyword_count >= 5:
                indicators += 1
                metadata['textbook_keywords'] = keyword_count
                
        confidence = indicators / total_checks if total_checks > 0 else 0
        is_textbook = confidence >= 0.6  # 60% threshold
        
        return is_textbook, confidence, metadata


class SmartTextbookProcessor:
    """Processes textbooks intelligently with chunking and structured generation"""
    
    def __init__(self):
        self.chunk_size = 2000  # tokens per chunk for processing
        self.overlap = 200  # token overlap between chunks
        
    async def process_textbook(self, paper_data: Dict, ai_config: Dict) -> Dict:
        """
        Process a textbook with intelligent chunking and generation
        """
        is_textbook, confidence, metadata = TextbookDetector.is_likely_textbook(paper_data)
        
        if not is_textbook:
            return {
                'is_textbook': False,
                'confidence': confidence,
                'processed': False
            }
            
        logger.info(f"Detected textbook with {confidence:.2%} confidence")
        
        # Extract full text if not already done
        if not paper_data.get('full_text') and paper_data.get('full_text_url'):
            extraction = await extract_text_from_pdf_url(paper_data['full_text_url'])
            if extraction['success']:
                paper_data['full_text'] = extraction['text']
                paper_data['page_count'] = extraction['page_count']
            else:
                return {
                    'is_textbook': True,
                    'confidence': confidence,
                    'processed': False,
                    'error': 'Failed to extract text from PDF'
                }
                
        # Create structured chunks
        chunks = self._create_smart_chunks(paper_data['full_text'])
        
        # Process each chunk
        results = {
            'is_textbook': True,
            'confidence': confidence,
            'metadata': metadata,
            'chapters': [],
            'all_tags': set(),
            'all_flashcards': [],
            'structured_notes': {}
        }
        
        for i, chunk in enumerate(chunks):
            chunk_result = await self._process_chunk(chunk, i, len(chunks), paper_data, ai_config)
            
            # Aggregate results
            if chunk_result['tags']:
                results['all_tags'].update(chunk_result['tags'])
                
            if chunk_result['flashcards']:
                results['all_flashcards'].extend(chunk_result['flashcards'])
                
            if chunk_result['notes']:
                results['structured_notes'][f'chunk_{i}'] = chunk_result['notes']
                
            if chunk_result['chapter_info']:
                results['chapters'].append(chunk_result['chapter_info'])
                
        # Deduplicate and format final results
        results['final_tags'] = list(results['all_tags'])[:30]  # Limit to 30 unique tags
        results['final_flashcards'] = self._deduplicate_flashcards(results['all_flashcards'])
        results['final_notes'] = self._compile_structured_notes(results['structured_notes'])
        
        return results
        
    def _create_smart_chunks(self, text: str) -> List[Dict]:
        """Create intelligent chunks that respect chapter/section boundaries"""
        chunks = []
        
        # Try to identify chapter boundaries
        chapter_pattern = re.compile(r'(chapter\s+\d+[^\\n]*)', re.IGNORECASE)
        section_pattern = re.compile(r'(\d+\.\d+[^\\n]*|\bsection\s+\d+[^\\n]*)', re.IGNORECASE)
        
        # Split by chapters first
        chapter_splits = chapter_pattern.split(text)
        
        current_chunk = {
            'text': '',
            'chapter': None,
            'sections': [],
            'token_count': 0
        }
        
        for i, segment in enumerate(chapter_splits):
            if chapter_pattern.match(segment):
                # Start new chapter
                if current_chunk['text']:
                    chunks.append(current_chunk)
                current_chunk = {
                    'text': segment,
                    'chapter': segment.strip(),
                    'sections': [],
                    'token_count': estimate_token_count(segment)
                }
            else:
                # Add to current chunk
                segment_tokens = estimate_token_count(segment)
                
                # If adding this would exceed chunk size, split it
                if current_chunk['token_count'] + segment_tokens > self.chunk_size:
                    # Save current chunk
                    if current_chunk['text']:
                        chunks.append(current_chunk)
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk['text'][-500:] if len(current_chunk['text']) > 500 else current_chunk['text']
                    current_chunk = {
                        'text': overlap_text + segment,
                        'chapter': current_chunk['chapter'],
                        'sections': [],
                        'token_count': estimate_token_count(overlap_text + segment)
                    }
                else:
                    current_chunk['text'] += segment
                    current_chunk['token_count'] += segment_tokens
                    
        # Don't forget the last chunk
        if current_chunk['text']:
            chunks.append(current_chunk)
            
        return chunks
        
    async def _process_chunk(self, chunk: Dict, chunk_index: int, total_chunks: int, paper_data: Dict, ai_config: Dict) -> Dict:
        """Process a single chunk with AI"""
        import aiohttp
        import json
        
        # Create a focused prompt for textbook processing
        prompt = f"""You are analyzing chunk {chunk_index + 1} of {total_chunks} from a textbook.

Title: {paper_data.get('title', 'Unknown')}
Chapter: {chunk.get('chapter', 'Unknown')}

Text excerpt:
{chunk['text'][:3000]}

Generate the following:

1. TAGS (1-2 specific tags for this section):
   - Focus on key concepts, methodologies, or topics
   - Be specific to this chunk's content
   - Format: ["tag1", "tag2"]

2. FLASHCARDS (5-10 high-quality flashcards):
   - Front: Clear, specific question about a concept
   - Back: Comprehensive answer with explanation
   - Focus on understanding, not memorization
   - Include ONE application or example per flashcard
   
3. NOTES (structured summary):
   - Key concepts (bullet points)
   - Important formulas or definitions
   - Practical applications
   
Respond in JSON format:
{{
    "tags": ["tag1", "tag2"],
    "flashcards": [
        {{
            "front": "What is [specific concept] and how is it applied?",
            "back": "Comprehensive answer with explanation and example"
        }}
    ],
    "notes": {{
        "concepts": ["concept1", "concept2"],
        "definitions": {{"term": "definition"}},
        "applications": ["application1"]
    }},
    "chapter_info": {{
        "title": "Chapter title if found",
        "topics": ["main topics covered"]
    }}
}}"""

        try:
            # Make direct API call to OpenAI
            headers = {
                "Authorization": f"Bearer {ai_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": ai_config.get('model', 'gpt-3.5-turbo'),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert academic educator. Provide detailed, accurate responses in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = json.loads(data['choices'][0]['message']['content'])
                        return content
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return {
                            'tags': [],
                            'flashcards': [],
                            'notes': {},
                            'chapter_info': None
                        }
                        
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_index}: {str(e)}")
            return {
                'tags': [],
                'flashcards': [],
                'notes': {},
                'chapter_info': None
            }
            
    def _deduplicate_flashcards(self, flashcards: List[Dict]) -> List[Dict]:
        """Remove duplicate flashcards based on similarity"""
        unique_flashcards = []
        seen_fronts = set()
        
        for fc in flashcards:
            # Simple deduplication based on front text
            front_key = fc['front'].lower().strip()
            if front_key not in seen_fronts:
                seen_fronts.add(front_key)
                unique_flashcards.append(fc)
                
        return unique_flashcards
        
    def _compile_structured_notes(self, chunk_notes: Dict) -> str:
        """Compile all chunk notes into a comprehensive summary"""
        compiled = []
        
        compiled.append("# Comprehensive Textbook Notes\n")
        
        all_concepts = []
        all_definitions = {}
        all_applications = []
        
        for chunk_id, notes in chunk_notes.items():
            if isinstance(notes, dict):
                if 'concepts' in notes:
                    all_concepts.extend(notes['concepts'])
                if 'definitions' in notes:
                    all_definitions.update(notes['definitions'])
                if 'applications' in notes:
                    all_applications.extend(notes['applications'])
                    
        # Deduplicate concepts
        unique_concepts = list(dict.fromkeys(all_concepts))
        
        compiled.append("## Key Concepts")
        for concept in unique_concepts[:20]:  # Limit to top 20
            compiled.append(f"- {concept}")
            
        compiled.append("\n## Definitions")
        for term, definition in list(all_definitions.items())[:15]:  # Limit to 15
            compiled.append(f"- **{term}**: {definition}")
            
        compiled.append("\n## Applications")
        for app in list(dict.fromkeys(all_applications))[:10]:  # Limit to 10
            compiled.append(f"- {app}")
            
        return "\n".join(compiled)
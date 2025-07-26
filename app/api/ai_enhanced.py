from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import json
import asyncio
import aiohttp
from datetime import datetime
import uuid

from app.database.connection import get_db
from app.database.models import User, Collection, Paper, collection_papers
from app.api.auth import get_current_user
from app.utils.pdf_extractor import process_paper_for_ai, estimate_token_count
from app.utils.textbook_detector import TextbookDetector, SmartTextbookProcessor

router = APIRouter(prefix="/api/ai/enhanced", tags=["ai-enhanced"])


class BaseAIRequest(BaseModel):
    paper_id: str
    paper_data: Dict[str, Any]
    api_key: str
    model: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7, ge=0, le=1)
    extract_full_text: bool = Field(default=True)


class GenerateTagsRequest(BaseAIRequest):
    tag_count: int = Field(default=20, ge=10, le=30)
    tag_categories: List[str] = Field(default_factory=lambda: [
        "core_concepts", "methodology", "applications", 
        "field_of_study", "theoretical_framework", "techniques"
    ])


class GenerateNotesRequest(BaseAIRequest):
    note_sections: List[str] = Field(default_factory=lambda: [
        "summary", "key_terms", "methodology", "findings", "implications"
    ])
    max_tokens: int = Field(default=2000, ge=500, le=4000)


class GenerateFlashcardsRequest(BaseAIRequest):
    flashcard_count: int = Field(default=15, ge=5, le=30)
    difficulty_level: str = Field(default="intermediate")
    focus_areas: Optional[List[str]] = None
    include_quotes: bool = Field(default=True)


class TagsResponse(BaseModel):
    success: bool
    tags: List[Dict[str, str]]  # {tag: "...", category: "..."}
    processing_time: float
    tokens_used: int


class NotesResponse(BaseModel):
    success: bool
    notes: Dict[str, str]  # {section: content}
    processing_time: float
    tokens_used: int


class FlashcardsResponse(BaseModel):
    success: bool
    flashcards: List[Dict[str, Any]]
    processing_time: float
    tokens_used: int


async def call_openai_api(prompt: str, api_key: str, model: str, temperature: float, max_tokens: int = 2000) -> Dict:
    """Make a call to OpenAI API with the given parameters"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert academic researcher and educator. Provide detailed, accurate, and pedagogically sound responses. Always respond with valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # Add response format for compatible models
    if model in ["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-1106-preview"]:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                processing_time = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    
                    return {
                        'success': True,
                        'content': json.loads(content),
                        'processing_time': processing_time,
                        'tokens_used': usage.get('total_tokens', 0)
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f"OpenAI API error ({response.status}): {error_text}",
                        'processing_time': processing_time,
                        'tokens_used': 0
                    }
                    
    except Exception as e:
        return {
            'success': False,
            'error': f"Error calling OpenAI API: {str(e)}",
            'processing_time': 0,
            'tokens_used': 0
        }


@router.post("/generate-tags", response_model=TagsResponse)
async def generate_enhanced_tags(
    request: GenerateTagsRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive tags with categories"""
    
    # Get paper content
    paper_data = request.paper_data
    if request.extract_full_text and not paper_data.get('full_text'):
        enhanced_paper = await process_paper_for_ai(paper_data)
        paper_data = enhanced_paper
    
    content = paper_data.get('full_text', paper_data.get('abstract', ''))[:10000]
    
    prompt = f"""Analyze this academic paper and generate {request.tag_count} comprehensive tags.

Paper Title: {paper_data.get('title', 'Unknown')}
Authors: {', '.join(paper_data.get('authors', [])[:10])}
Content: {content}

Generate tags in these categories:
{json.dumps(request.tag_categories, indent=2)}

Requirements:
1. Generate {request.tag_count} diverse, specific tags
2. Cover all requested categories
3. Include both broad and specific tags
4. Tags should be useful for search and categorization
5. Include emerging trends and interdisciplinary connections

Respond with JSON:
{{
    "tags": [
        {{"tag": "machine learning", "category": "core_concepts"}},
        {{"tag": "convolutional neural networks", "category": "techniques"}},
        ...
    ]
}}"""

    result = await call_openai_api(prompt, request.api_key, request.model, request.temperature, 1500)
    
    if result['success']:
        tags_data = result['content'].get('tags', [])
        return TagsResponse(
            success=True,
            tags=tags_data,
            processing_time=result['processing_time'],
            tokens_used=result['tokens_used']
        )
    else:
        return TagsResponse(
            success=False,
            tags=[],
            processing_time=result['processing_time'],
            tokens_used=0
        )


@router.post("/generate-notes", response_model=NotesResponse)
async def generate_enhanced_notes(
    request: GenerateNotesRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate detailed notes with specific sections"""
    
    # Get paper content
    paper_data = request.paper_data
    if request.extract_full_text and not paper_data.get('full_text'):
        enhanced_paper = await process_paper_for_ai(paper_data)
        paper_data = enhanced_paper
    
    content = paper_data.get('full_text', paper_data.get('abstract', ''))[:15000]
    
    sections_detail = {
        "summary": "Comprehensive 300-400 word overview covering main arguments, methodology, and conclusions",
        "key_terms": "Important concepts, definitions, and technical terms with clear explanations",
        "methodology": "Detailed research methods, study design, data collection, and analysis approaches",
        "findings": "Main results, discoveries, statistical outcomes, and key insights",
        "implications": "Practical applications, future research directions, limitations, and broader impact"
    }
    
    sections_prompt = "\n".join([f"- {k}: {sections_detail.get(k, v)}" for k, v in enumerate(request.note_sections)])
    
    prompt = f"""Analyze this academic paper and create detailed, structured notes.

Paper Title: {paper_data.get('title', 'Unknown')}
Authors: {', '.join(paper_data.get('authors', [])[:10])}
Year: {paper_data.get('year', 'Unknown')}
Content: {content}

Generate detailed notes for these sections:
{sections_prompt}

Requirements:
1. Each section should be comprehensive and detailed
2. Use clear, academic language
3. Include specific examples and evidence from the paper
4. Highlight critical insights and contributions
5. Format with HTML tags (<h3>, <p>, <ul>, <li>, <strong>, <em>)

Respond with JSON:
{{
    "notes": {{
        "summary": "<h3>Summary</h3><p>Detailed summary here...</p>",
        "key_terms": "<h3>Key Terms</h3><ul><li><strong>Term 1</strong>: Definition...</li></ul>",
        ...
    }}
}}"""

    result = await call_openai_api(
        prompt, 
        request.api_key, 
        request.model, 
        request.temperature, 
        request.max_tokens
    )
    
    if result['success']:
        notes_data = result['content'].get('notes', {})
        return NotesResponse(
            success=True,
            notes=notes_data,
            processing_time=result['processing_time'],
            tokens_used=result['tokens_used']
        )
    else:
        return NotesResponse(
            success=False,
            notes={},
            processing_time=result['processing_time'],
            tokens_used=0
        )


@router.post("/generate-flashcards", response_model=FlashcardsResponse)
async def generate_enhanced_flashcards(
    request: GenerateFlashcardsRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate high-quality flashcards with full context"""
    
    # Get paper content
    paper_data = request.paper_data
    if request.extract_full_text and not paper_data.get('full_text'):
        enhanced_paper = await process_paper_for_ai(paper_data)
        paper_data = enhanced_paper
    
    # Check if this is a textbook
    is_textbook, confidence, metadata = TextbookDetector.is_likely_textbook(paper_data)
    
    if is_textbook and confidence > 0.7:
        # Use smart textbook processing
        processor = SmartTextbookProcessor()
        textbook_result = await processor.process_textbook(paper_data, {
            'api_key': request.api_key,
            'model': request.model
        })
        
        if textbook_result.get('processed', False):
            return FlashcardsResponse(
                success=True,
                flashcards=textbook_result['final_flashcards'][:request.flashcard_count],
                processing_time=textbook_result.get('processing_time', 0),
                tokens_used=textbook_result.get('tokens_used', 0)
            )
    
    # Regular processing for non-textbooks
    content = paper_data.get('full_text', paper_data.get('abstract', ''))[:15000]
    
    difficulty_descriptions = {
        "beginner": "fundamental concepts, basic definitions, and introductory ideas",
        "intermediate": "application of concepts, relationships, methodological understanding",
        "advanced": "critical analysis, synthesis, evaluation, and expert-level insights"
    }
    
    focus_prompt = ""
    if request.focus_areas:
        focus_prompt = f"\nFocus especially on: {', '.join(request.focus_areas)}"
    
    prompt = f"""Create {request.flashcard_count} high-quality flashcards for studying this academic paper.

Paper Title: {paper_data.get('title', 'Unknown')}
Content: {content}

Requirements:
1. Difficulty level: {request.difficulty_level} ({difficulty_descriptions[request.difficulty_level]})
2. Test deep understanding, not memorization
3. Include various types: definitions, applications, analysis, synthesis
4. Make answers comprehensive but concise
5. Include page references or quotes when relevant{focus_prompt}

Categories to cover:
- Core Concepts
- Methodology
- Key Findings
- Critical Analysis
- Applications
- Theoretical Connections

Respond with JSON:
{{
    "flashcards": [
        {{
            "id": "unique_id",
            "front": "Question that tests understanding",
            "back": "Comprehensive answer with explanation",
            "category": "Core Concepts",
            "difficulty": "{request.difficulty_level}",
            "source_quote": "Relevant quote from paper (optional)",
            "page_reference": "p. 5 (optional)"
        }},
        ...
    ]
}}"""

    result = await call_openai_api(
        prompt, 
        request.api_key, 
        request.model, 
        request.temperature, 
        3000  # More tokens for detailed flashcards
    )
    
    if result['success']:
        flashcards_data = result['content'].get('flashcards', [])
        
        # Add unique IDs if not present
        for fc in flashcards_data:
            if 'id' not in fc:
                fc['id'] = str(uuid.uuid4())
        
        return FlashcardsResponse(
            success=True,
            flashcards=flashcards_data,
            processing_time=result['processing_time'],
            tokens_used=result['tokens_used']
        )
    else:
        return FlashcardsResponse(
            success=False,
            flashcards=[],
            processing_time=result['processing_time'],
            tokens_used=0
        )


@router.post("/process-collection-enhanced")
async def process_collection_enhanced(
    collection_id: str,
    process_options: Dict[str, bool],  # {tags: true, notes: true, flashcards: true}
    ai_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process collection with separate API calls for each content type"""
    
    # Get collection and papers
    collection = db.query(Collection).filter(
        Collection.id == uuid.UUID(collection_id),
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get papers in collection
    papers = db.query(Paper).join(
        collection_papers,
        Paper.id == collection_papers.c.paper_id
    ).filter(
        collection_papers.c.collection_id == collection.id
    ).all()
    
    results = {
        "collection_id": collection_id,
        "papers_processed": [],
        "total_cost": 0,
        "errors": []
    }
    
    for paper in papers:
        paper_result = {
            "paper_id": str(paper.id),
            "title": paper.title,
            "tags": [],
            "notes": {},
            "flashcards": []
        }
        
        paper_data = {
            "title": paper.title,
            "authors": paper.authors or [],
            "year": paper.year,
            "abstract": paper.abstract,
            "journal": paper.journal,
            "doi": paper.doi,
            "url": paper.url,
            "pdf_url": paper.pdf_url,
            "full_text_url": paper.full_text_url
        }
        
        # Process tags if requested
        if process_options.get("tags"):
            tag_request = GenerateTagsRequest(
                paper_id=str(paper.id),
                paper_data=paper_data,
                api_key=ai_config["api_key"],
                model=ai_config["model"],
                tag_count=ai_config.get("tag_count", 20)
            )
            
            tag_response = await generate_enhanced_tags(tag_request, current_user)
            if tag_response.success:
                paper_result["tags"] = [t["tag"] for t in tag_response.tags]
                
                # Update database with tags
                db.execute(
                    collection_papers.update().where(
                        (collection_papers.c.collection_id == collection.id) &
                        (collection_papers.c.paper_id == paper.id)
                    ).values(
                        custom_tags=paper_result["tags"]
                    )
                )
        
        # Process notes if requested
        if process_options.get("notes"):
            notes_request = GenerateNotesRequest(
                paper_id=str(paper.id),
                paper_data=paper_data,
                api_key=ai_config["api_key"],
                model=ai_config["model"],
                note_sections=ai_config.get("note_sections", ["summary", "key_terms", "findings"])
            )
            
            notes_response = await generate_enhanced_notes(notes_request, current_user)
            if notes_response.success:
                paper_result["notes"] = notes_response.notes
                
                # Combine notes into a single string for database
                combined_notes = "\n\n".join(notes_response.notes.values())
                
                db.execute(
                    collection_papers.update().where(
                        (collection_papers.c.collection_id == collection.id) &
                        (collection_papers.c.paper_id == paper.id)
                    ).values(
                        notes=combined_notes
                    )
                )
        
        # Process flashcards if requested
        if process_options.get("flashcards"):
            flashcard_request = GenerateFlashcardsRequest(
                paper_id=str(paper.id),
                paper_data=paper_data,
                api_key=ai_config["api_key"],
                model=ai_config["model"],
                flashcard_count=ai_config.get("flashcard_count", 15),
                difficulty_level=ai_config.get("difficulty_level", "intermediate")
            )
            
            flashcard_response = await generate_enhanced_flashcards(flashcard_request, current_user)
            if flashcard_response.success:
                paper_result["flashcards"] = flashcard_response.flashcards
                
                # Store flashcards in database
                db.execute(
                    collection_papers.update().where(
                        (collection_papers.c.collection_id == collection.id) &
                        (collection_papers.c.paper_id == paper.id)
                    ).values(
                        flashcards=flashcard_response.flashcards
                    )
                )
        
        results["papers_processed"].append(paper_result)
        
        # Small delay between papers to avoid rate limiting
        await asyncio.sleep(1)
    
    db.commit()
    
    return results


@router.post("/process-textbook")
async def process_textbook_intelligent(
    paper_id: str,
    paper_data: Dict[str, Any],
    api_key: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    extract_full_text: bool = True,
    processing_options: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user)
):
    """Process a textbook with intelligent chunking and structured generation"""
    
    # Get enhanced paper data with full text
    if extract_full_text and not paper_data.get('full_text'):
        enhanced_paper = await process_paper_for_ai(paper_data)
        paper_data = enhanced_paper
    
    # Use the SmartTextbookProcessor
    processor = SmartTextbookProcessor()
    result = await processor.process_textbook(paper_data, {
        'api_key': api_key,
        'model': model,
        'temperature': temperature
    })
    
    if result.get('processed', False):
        # Format flashcards properly
        formatted_flashcards = []
        for fc in result['final_flashcards']:
            formatted_flashcards.append({
                'id': str(uuid.uuid4()),
                'front': fc.get('front', ''),
                'back': fc.get('back', ''),
                'category': 'textbook',
                'difficulty': 'intermediate',
                'source_quote': fc.get('source_quote', ''),
                'page_reference': fc.get('page_reference', '')
            })
        
        return {
            'success': True,
            'unique_tags': result['final_tags'],
            'structured_notes': result['final_notes'],
            'all_flashcards': formatted_flashcards,
            'metadata': result.get('metadata', {}),
            'chapters_processed': len(result.get('chapters', [])),
            'is_textbook': True,
            'confidence': result.get('confidence', 0)
        }
    else:
        # Not a textbook or processing failed
        return {
            'success': False,
            'is_textbook': result.get('is_textbook', False),
            'confidence': result.get('confidence', 0),
            'error': result.get('error', 'Processing failed')
        }
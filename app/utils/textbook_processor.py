"""
Advanced Textbook/Large PDF Processing Utility
Implements hierarchical chunking with context preservation for AI processing
Based on 2024 best practices for RAG and LLM applications
"""
import json
import re
from typing import Dict, List, Optional, Tuple, Any
import PyPDF2
import pdfplumber
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class TextbookChunk:
    """Represents a single chunk of textbook content with metadata"""
    chunk_id: str
    chapter_num: Optional[int]
    chapter_title: Optional[str]
    section_num: Optional[str]
    section_title: Optional[str]
    subsection_num: Optional[str]
    subsection_title: Optional[str]
    content: str
    chunk_type: str  # 'text', 'table', 'image_description', 'equation'
    page_numbers: List[int]
    token_count: int
    char_count: int
    context_before: Optional[str]  # Previous chunk summary for context
    context_after: Optional[str]   # Next chunk summary for context
    hierarchy_path: str  # e.g., "Ch1 > Sec1.2 > Subsec1.2.3"
    keywords: List[str]
    chunk_index: int  # Position within section
    total_chunks_in_section: int
    
@dataclass
class TextbookStructure:
    """Represents the complete structure of a textbook"""
    title: str
    authors: List[str]
    isbn: Optional[str]
    total_pages: int
    table_of_contents: Dict[str, Any]
    chunks: List[TextbookChunk]
    metadata: Dict[str, Any]
    processing_stats: Dict[str, Any]

class TextbookProcessor:
    """Advanced processor for converting textbooks/large PDFs into structured chunks"""
    
    # Optimal chunk sizes based on research
    DEFAULT_CHUNK_SIZE = 800  # tokens (~3200 characters)
    MAX_CHUNK_SIZE = 1000     # tokens (~4000 characters)
    MIN_CHUNK_SIZE = 250      # tokens (~1000 characters)
    OVERLAP_SIZE = 50         # tokens (~200 characters)
    
    # Regex patterns for structure detection
    CHAPTER_PATTERNS = [
        r'^Chapter\s+(\d+)[\s:.-]*(.*)$',
        r'^CHAPTER\s+(\d+)[\s:.-]*(.*)$',
        r'^Ch\.\s*(\d+)[\s:.-]*(.*)$',
        r'^(\d+)\.\s+([A-Z].*)$',  # "1. Introduction"
        r'^Unit\s+(\d+)[\s:.-]*(.*)$'
    ]
    
    SECTION_PATTERNS = [
        r'^(\d+\.\d+)[\s:.-]*(.*)$',  # "1.2 Section Title"
        r'^Section\s+(\d+\.\d+)[\s:.-]*(.*)$',
        r'^(\d+\.\d+\.\d+)[\s:.-]*(.*)$',  # Subsections
    ]
    
    def __init__(self, 
                 chunk_size: int = DEFAULT_CHUNK_SIZE,
                 overlap_size: int = OVERLAP_SIZE,
                 extract_tables: bool = True,
                 extract_images: bool = False):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        
    def process_textbook(self, pdf_path: str, max_pages: int = 500) -> TextbookStructure:
        """Main entry point for processing a textbook PDF"""
        logger.info(f"Processing textbook: {pdf_path}")
        
        # Check file size first
        file_size = Path(pdf_path).stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"Large PDF detected: {file_size / 1024 / 1024:.1f}MB")
        
        # Extract metadata first to check page count
        metadata = self._extract_metadata(pdf_path)
        if metadata.get('total_pages', 0) > max_pages:
            logger.warning(f"PDF has {metadata['total_pages']} pages, processing only first {max_pages}")
        
        # Extract raw content and structure
        raw_content = self._extract_pdf_content(pdf_path, max_pages)
        toc = self._extract_table_of_contents(raw_content)
        
        # Process content into hierarchical chunks
        chunks = self._create_hierarchical_chunks(raw_content, toc)
        
        # Add contextual information to chunks
        chunks = self._add_contextual_information(chunks)
        
        # Calculate processing statistics
        stats = self._calculate_statistics(chunks)
        
        return TextbookStructure(
            title=metadata.get('title', Path(pdf_path).stem),
            authors=metadata.get('authors', []),
            isbn=metadata.get('isbn'),
            total_pages=metadata.get('total_pages', 0),
            table_of_contents=toc,
            chunks=chunks,
            metadata=metadata,
            processing_stats=stats
        )
    
    def _extract_pdf_content(self, pdf_path: str, max_pages: int = None) -> List[Dict]:
        """Extract content from PDF with structure preservation"""
        content = []
        
        logger.info(f"Opening PDF: {pdf_path}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                logger.info(f"PDF has {total_pages} pages, processing {pages_to_process}")
                
                for page_num, page in enumerate(pdf.pages[:pages_to_process], 1):
                    if page_num % 10 == 0:
                        logger.info(f"Processing page {page_num}/{total_pages}")
                    
                    try:
                        # Extract text with position information
                        text = page.extract_text()
                        
                        # Extract tables if enabled
                        tables = []
                        if self.extract_tables:
                            tables = page.extract_tables()
                        
                        # Store page content with metadata
                        content.append({
                            'page_num': page_num,
                            'text': text,
                            'tables': tables,
                            'bbox': page.bbox,  # Bounding box for layout analysis
                        })
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                        # Continue with empty page rather than failing
                        content.append({
                            'page_num': page_num,
                            'text': '',
                            'tables': [],
                            'bbox': None
                        })
                
                logger.info(f"Successfully extracted content from {len(content)} pages")
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise
                
        return content
    
    def _extract_table_of_contents(self, content: List[Dict]) -> Dict[str, Any]:
        """Extract hierarchical table of contents from content"""
        toc = {}
        current_chapter = None
        current_section = None
        
        for page_data in content:
            lines = page_data['text'].split('\n') if page_data['text'] else []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for chapter
                for pattern in self.CHAPTER_PATTERNS:
                    match = re.match(pattern, line)
                    if match:
                        chapter_num = match.group(1)
                        chapter_title = match.group(2).strip()
                        current_chapter = f"chapter_{chapter_num}"
                        toc[current_chapter] = {
                            'title': chapter_title,
                            'number': chapter_num,
                            'sections': {},
                            'page': page_data['page_num']
                        }
                        current_section = None
                        break
                
                # Check for section (only if we have a chapter)
                if current_chapter:
                    for pattern in self.SECTION_PATTERNS:
                        match = re.match(pattern, line)
                        if match:
                            section_num = match.group(1)
                            section_title = match.group(2).strip() if match.lastindex >= 2 else ""
                            current_section = f"section_{section_num}"
                            toc[current_chapter]['sections'][current_section] = {
                                'title': section_title,
                                'number': section_num,
                                'page': page_data['page_num']
                            }
                            break
        
        return toc
    
    def _create_hierarchical_chunks(self, content: List[Dict], toc: Dict) -> List[TextbookChunk]:
        """Create chunks with hierarchical structure preservation"""
        chunks = []
        chunk_id_counter = 0
        
        # Process content based on TOC structure
        current_text_buffer = []
        current_chapter = None
        current_section = None
        current_pages = []
        
        for page_data in content:
            if not page_data['text']:
                continue
                
            lines = page_data['text'].split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Check if this line starts a new chapter/section
                is_new_structure = self._is_structure_boundary(line)
                
                if is_new_structure and current_text_buffer:
                    # Save current buffer as chunk
                    chunk = self._create_chunk(
                        content='\n'.join(current_text_buffer),
                        chunk_id=f"chunk_{chunk_id_counter}",
                        chapter_info=current_chapter,
                        section_info=current_section,
                        pages=current_pages
                    )
                    chunks.append(chunk)
                    chunk_id_counter += 1
                    
                    # Start new buffer with overlap
                    overlap_text = current_text_buffer[-self.overlap_size:] if len(current_text_buffer) > self.overlap_size else []
                    current_text_buffer = overlap_text
                    current_pages = [page_data['page_num']]
                
                # Update structure tracking
                chapter_match = self._match_chapter(line)
                if chapter_match:
                    current_chapter = chapter_match
                    current_section = None
                
                section_match = self._match_section(line)
                if section_match:
                    current_section = section_match
                
                # Add line to buffer
                current_text_buffer.append(line)
                if page_data['page_num'] not in current_pages:
                    current_pages.append(page_data['page_num'])
                
                # Check if we need to create a chunk based on size
                if self._estimate_tokens(current_text_buffer) >= self.chunk_size:
                    chunk = self._create_chunk(
                        content='\n'.join(current_text_buffer),
                        chunk_id=f"chunk_{chunk_id_counter}",
                        chapter_info=current_chapter,
                        section_info=current_section,
                        pages=current_pages
                    )
                    chunks.append(chunk)
                    chunk_id_counter += 1
                    
                    # Start new buffer with overlap
                    overlap_text = current_text_buffer[-self.overlap_size:]
                    current_text_buffer = overlap_text
                    current_pages = [page_data['page_num']]
            
            # Process tables as separate chunks
            if self.extract_tables and page_data['tables']:
                for table in page_data['tables']:
                    table_chunk = self._create_table_chunk(
                        table=table,
                        chunk_id=f"chunk_{chunk_id_counter}",
                        chapter_info=current_chapter,
                        section_info=current_section,
                        page=page_data['page_num']
                    )
                    chunks.append(table_chunk)
                    chunk_id_counter += 1
        
        # Don't forget the last buffer
        if current_text_buffer:
            chunk = self._create_chunk(
                content='\n'.join(current_text_buffer),
                chunk_id=f"chunk_{chunk_id_counter}",
                chapter_info=current_chapter,
                section_info=current_section,
                pages=current_pages
            )
            chunks.append(chunk)
        
        return chunks
    
    def _add_contextual_information(self, chunks: List[TextbookChunk]) -> List[TextbookChunk]:
        """Add contextual information to each chunk (Anthropic's 2024 approach)"""
        for i, chunk in enumerate(chunks):
            # Add context from previous chunk
            if i > 0:
                prev_chunk = chunks[i-1]
                chunk.context_before = self._summarize_chunk(prev_chunk)
            
            # Add context from next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i+1]
                chunk.context_after = self._summarize_chunk(next_chunk)
            
            # Extract keywords
            chunk.keywords = self._extract_keywords(chunk.content)
            
            # Update position information
            section_chunks = [c for c in chunks if c.section_num == chunk.section_num]
            chunk.chunk_index = section_chunks.index(chunk)
            chunk.total_chunks_in_section = len(section_chunks)
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_id: str, 
                     chapter_info: Optional[Dict], 
                     section_info: Optional[Dict],
                     pages: List[int]) -> TextbookChunk:
        """Create a chunk with full metadata"""
        # Parse chapter/section info
        chapter_num = None
        chapter_title = None
        section_num = None
        section_title = None
        
        if chapter_info:
            chapter_num = chapter_info.get('number')
            chapter_title = chapter_info.get('title')
        
        if section_info:
            section_num = section_info.get('number')
            section_title = section_info.get('title')
        
        # Build hierarchy path
        hierarchy_parts = []
        if chapter_num:
            hierarchy_parts.append(f"Ch{chapter_num}")
        if section_num:
            hierarchy_parts.append(f"Sec{section_num}")
        hierarchy_path = " > ".join(hierarchy_parts) if hierarchy_parts else "Root"
        
        return TextbookChunk(
            chunk_id=chunk_id,
            chapter_num=int(chapter_num) if chapter_num and chapter_num.isdigit() else None,
            chapter_title=chapter_title,
            section_num=section_num,
            section_title=section_title,
            subsection_num=None,  # TODO: Implement subsection detection
            subsection_title=None,
            content=content,
            chunk_type='text',
            page_numbers=pages,
            token_count=self._estimate_tokens([content]),
            char_count=len(content),
            context_before=None,  # Will be added later
            context_after=None,   # Will be added later
            hierarchy_path=hierarchy_path,
            keywords=[],  # Will be extracted later
            chunk_index=0,  # Will be updated later
            total_chunks_in_section=0  # Will be updated later
        )
    
    def _create_table_chunk(self, table: List[List], chunk_id: str,
                           chapter_info: Optional[Dict],
                           section_info: Optional[Dict],
                           page: int) -> TextbookChunk:
        """Create a chunk specifically for table content"""
        # Convert table to markdown format
        table_content = self._table_to_markdown(table)
        
        chunk = self._create_chunk(
            content=table_content,
            chunk_id=chunk_id,
            chapter_info=chapter_info,
            section_info=section_info,
            pages=[page]
        )
        chunk.chunk_type = 'table'
        
        return chunk
    
    def _table_to_markdown(self, table: List[List]) -> str:
        """Convert table data to markdown format"""
        if not table or not table[0]:
            return ""
        
        # Create header
        header = "| " + " | ".join(str(cell) for cell in table[0]) + " |"
        separator = "| " + " | ".join("---" for _ in table[0]) + " |"
        
        # Create rows
        rows = []
        for row in table[1:]:
            rows.append("| " + " | ".join(str(cell) for cell in row) + " |")
        
        return "\n".join([header, separator] + rows)
    
    def _estimate_tokens(self, text_list: List[str]) -> int:
        """Estimate token count (roughly 1 token per 4 characters)"""
        total_chars = sum(len(text) for text in text_list)
        return total_chars // 4
    
    def _is_structure_boundary(self, line: str) -> bool:
        """Check if a line represents a structural boundary"""
        for pattern in self.CHAPTER_PATTERNS + self.SECTION_PATTERNS:
            if re.match(pattern, line.strip()):
                return True
        return False
    
    def _match_chapter(self, line: str) -> Optional[Dict]:
        """Match and extract chapter information"""
        for pattern in self.CHAPTER_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                return {
                    'number': match.group(1),
                    'title': match.group(2).strip() if match.lastindex >= 2 else ""
                }
        return None
    
    def _match_section(self, line: str) -> Optional[Dict]:
        """Match and extract section information"""
        for pattern in self.SECTION_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                return {
                    'number': match.group(1),
                    'title': match.group(2).strip() if match.lastindex >= 2 else ""
                }
        return None
    
    def _summarize_chunk(self, chunk: TextbookChunk) -> str:
        """Create a brief summary of a chunk for context"""
        # Simple approach - take first 100 chars
        # In production, could use LLM for better summaries
        summary = chunk.content[:100].strip()
        if len(chunk.content) > 100:
            summary += "..."
        return f"[{chunk.hierarchy_path}] {summary}"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple approach - extract capitalized words
        # In production, use NLP libraries like spaCy or NLTK
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        # Get unique words, preserve order
        seen = set()
        keywords = []
        for word in words:
            if word not in seen and len(word) > 3:
                seen.add(word)
                keywords.append(word)
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        metadata = {
            'filename': Path(pdf_path).name,
            'file_size': Path(pdf_path).stat().st_size,
            'file_hash': self._calculate_file_hash(pdf_path)
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['total_pages'] = len(pdf_reader.pages)
                
                # Extract PDF metadata
                if pdf_reader.metadata:
                    metadata['title'] = pdf_reader.metadata.get('/Title', '')
                    metadata['authors'] = [pdf_reader.metadata.get('/Author', '')]
                    metadata['subject'] = pdf_reader.metadata.get('/Subject', '')
                    metadata['creator'] = pdf_reader.metadata.get('/Creator', '')
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _calculate_statistics(self, chunks: List[TextbookChunk]) -> Dict[str, Any]:
        """Calculate processing statistics"""
        total_tokens = sum(chunk.token_count for chunk in chunks)
        total_chars = sum(chunk.char_count for chunk in chunks)
        
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        chapters = set(chunk.chapter_num for chunk in chunks if chunk.chapter_num)
        sections = set(chunk.section_num for chunk in chunks if chunk.section_num)
        
        return {
            'total_chunks': len(chunks),
            'total_tokens': total_tokens,
            'total_characters': total_chars,
            'average_chunk_size': total_tokens / len(chunks) if chunks else 0,
            'chunk_types': chunk_types,
            'num_chapters': len(chapters),
            'num_sections': len(sections),
            'pages_processed': len(set(page for chunk in chunks for page in chunk.page_numbers))
        }
    
    def save_to_json(self, textbook_structure: TextbookStructure, output_path: str):
        """Save processed textbook structure to JSON file"""
        # Convert dataclasses to dictionaries
        data = {
            'title': textbook_structure.title,
            'authors': textbook_structure.authors,
            'isbn': textbook_structure.isbn,
            'total_pages': textbook_structure.total_pages,
            'table_of_contents': textbook_structure.table_of_contents,
            'chunks': [asdict(chunk) for chunk in textbook_structure.chunks],
            'metadata': textbook_structure.metadata,
            'processing_stats': textbook_structure.processing_stats
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved processed textbook to {output_path}")
    
    def load_from_json(self, json_path: str) -> TextbookStructure:
        """Load processed textbook structure from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct TextbookChunk objects
        chunks = [TextbookChunk(**chunk_data) for chunk_data in data['chunks']]
        
        return TextbookStructure(
            title=data['title'],
            authors=data['authors'],
            isbn=data.get('isbn'),
            total_pages=data['total_pages'],
            table_of_contents=data['table_of_contents'],
            chunks=chunks,
            metadata=data['metadata'],
            processing_stats=data['processing_stats']
        )


# Example usage
if __name__ == "__main__":
    processor = TextbookProcessor(
        chunk_size=800,  # ~3200 characters
        overlap_size=50,  # ~200 characters
        extract_tables=True
    )
    
    # Process a textbook
    textbook = processor.process_textbook("path/to/textbook.pdf")
    
    # Save to JSON
    processor.save_to_json(textbook, "textbook_processed.json")
    
    # Print statistics
    print(f"Processed textbook: {textbook.title}")
    print(f"Total chunks: {textbook.processing_stats['total_chunks']}")
    print(f"Chapters: {textbook.processing_stats['num_chapters']}")
    print(f"Sections: {textbook.processing_stats['num_sections']}")
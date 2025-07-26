"""
AI Processing endpoints for textbook/large document processing
Handles chunked processing of structured textbook data
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import json
import asyncio
from datetime import datetime
import uuid

from app.database.connection import get_db
from app.database.models import User, Collection, Paper
from app.api.auth import get_current_user
from app.utils.textbook_processor import TextbookProcessor, TextbookStructure
from app.api.ai_enhanced import call_openai_api
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/textbook", tags=["ai-textbook"])

class ProcessTextbookRequest(BaseModel):
    """Request to process a textbook/large PDF"""
    pdf_url: str
    paper_id: str
    collection_id: str
    processing_options: Dict[str, Any] = Field(default_factory=lambda: {
        "chunk_size": 800,
        "extract_tables": True,
        "extract_images": False
    })
    ai_config: Dict[str, Any] = Field(default_factory=lambda: {
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    })

class ProcessChunksRequest(BaseModel):
    """Request to process specific chunks with AI"""
    textbook_id: str
    chunk_ids: List[str]
    processing_type: str  # 'summary', 'flashcards', 'notes', 'questions'
    ai_config: Dict[str, Any]
    options: Dict[str, Any] = Field(default_factory=dict)

class ChapterSummaryRequest(BaseModel):
    """Request to generate chapter summaries"""
    textbook_id: str
    chapter_numbers: List[int]
    ai_config: Dict[str, Any]
    summary_type: str = "comprehensive"  # 'brief', 'comprehensive', 'key_points'

class TextbookProcessingResponse(BaseModel):
    """Response for textbook processing"""
    success: bool
    textbook_id: str
    title: str
    total_chunks: int
    chapters: int
    sections: int
    processing_time: float
    status_url: str

class ChunkProcessingResult(BaseModel):
    """Result of processing a single chunk"""
    chunk_id: str
    success: bool
    result_type: str
    content: Dict[str, Any]
    tokens_used: int
    error: Optional[str] = None

# In-memory storage for processed textbooks (in production, use Redis or database)
TEXTBOOK_STORAGE = {}

@router.post("/process", response_model=TextbookProcessingResponse)
async def process_textbook(
    request: ProcessTextbookRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a textbook/large PDF into structured chunks"""
    
    # Generate unique textbook ID
    textbook_id = str(uuid.uuid4())
    
    # Initialize status in storage
    TEXTBOOK_STORAGE[textbook_id] = {
        'status': 'processing',
        'started_at': datetime.now()
    }
    
    # Start processing in background using asyncio.create_task instead of BackgroundTasks
    # This ensures it runs truly asynchronously
    asyncio.create_task(
        process_textbook_background(
            textbook_id=textbook_id,
            pdf_url=request.pdf_url,
            paper_id=request.paper_id,
            collection_id=request.collection_id,
            processing_options=request.processing_options,
            user_id=current_user.id
        )
    )
    
    return TextbookProcessingResponse(
        success=True,
        textbook_id=textbook_id,
        title="Processing...",
        total_chunks=0,
        chapters=0,
        sections=0,
        processing_time=0,
        status_url=f"/api/ai/textbook/status/{textbook_id}"
    )

async def process_textbook_background(
    textbook_id: str,
    pdf_url: str,
    paper_id: str,
    collection_id: str,
    processing_options: Dict,
    user_id: int
):
    """Background task to process textbook"""
    start_time = datetime.now()
    logger.info(f"Starting textbook processing for {textbook_id} from URL: {pdf_url}")
    
    try:
        # Download PDF to temporary file
        import aiohttp
        import tempfile
        import os
        import concurrent.futures
        
        logger.info(f"Processing PDF from: {pdf_url}")
        
        # Check if it's a local file path or URL
        if pdf_url.startswith('/') or pdf_url.startswith('file://'):
            # It's already a local file
            if pdf_url.startswith('file://'):
                tmp_path = pdf_url.replace('file://', '')
            else:
                tmp_path = pdf_url
            logger.info(f"Using local file: {tmp_path}")
        else:
            # Download from URL
            logger.info(f"Downloading PDF from URL: {pdf_url}")
            
            # Set timeout for download
            timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(pdf_url) as response:
                    logger.info(f"Download response status: {response.status}")
                    if response.status != 200:
                        raise Exception(f"Failed to download PDF: {response.status}")
                    
                    # Read content with size limit
                    content = await response.read()
                    logger.info(f"Downloaded {len(content) / 1024 / 1024:.1f}MB")
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(content)
                        tmp_path = tmp_file.name
                        logger.info(f"Saved PDF to temporary file: {tmp_path}")
        
        # Process the textbook in a thread pool to avoid blocking
        processor = TextbookProcessor(
            chunk_size=processing_options.get('chunk_size', 800),
            extract_tables=processing_options.get('extract_tables', True),
            extract_images=processing_options.get('extract_images', False)
        )
        
        # Run the blocking operation in a thread pool with timeout
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            try:
                # Add timeout of 5 minutes for PDF processing
                textbook_structure = await asyncio.wait_for(
                    loop.run_in_executor(
                        pool, 
                        processor.process_textbook, 
                        tmp_path
                    ),
                    timeout=300.0  # 5 minutes
                )
            except asyncio.TimeoutError:
                logger.error(f"Textbook processing timed out for {textbook_id}")
                raise Exception("PDF processing timed out after 5 minutes")
        
        # Clean up temporary file only if we downloaded it
        if not (pdf_url.startswith('/') or pdf_url.startswith('file://')):
            os.unlink(tmp_path)
            logger.info(f"Cleaned up temporary file: {tmp_path}")
        
        # Store processed textbook
        TEXTBOOK_STORAGE[textbook_id] = {
            'structure': textbook_structure,
            'paper_id': paper_id,
            'collection_id': collection_id,
            'user_id': user_id,
            'processed_at': datetime.now(),
            'processing_time': (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"Successfully processed textbook {textbook_id}: {textbook_structure.title}")
        
    except Exception as e:
        logger.error(f"Error processing textbook {textbook_id}: {str(e)}")
        TEXTBOOK_STORAGE[textbook_id] = {
            'error': str(e),
            'processed_at': datetime.now()
        }

@router.get("/status/{textbook_id}")
async def get_textbook_status(
    textbook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of textbook processing"""
    
    if textbook_id not in TEXTBOOK_STORAGE:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    stored_data = TEXTBOOK_STORAGE[textbook_id]
    
    if 'error' in stored_data:
        return {
            'status': 'error',
            'error': stored_data['error']
        }
    
    if 'structure' in stored_data:
        structure = stored_data['structure']
        return {
            'status': 'completed',
            'textbook_id': textbook_id,
            'title': structure.title,
            'total_chunks': structure.processing_stats['total_chunks'],
            'chapters': structure.processing_stats['num_chapters'],
            'sections': structure.processing_stats['num_sections'],
            'processing_time': stored_data['processing_time']
        }
    
    return {'status': 'processing'}

@router.post("/process-chunks", response_model=List[ChunkProcessingResult])
async def process_chunks(
    request: ProcessChunksRequest,
    current_user: User = Depends(get_current_user)
):
    """Process specific chunks with AI"""
    
    if request.textbook_id not in TEXTBOOK_STORAGE:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    stored_data = TEXTBOOK_STORAGE[request.textbook_id]
    if 'error' in stored_data:
        raise HTTPException(status_code=400, detail="Textbook processing failed")
    
    structure: TextbookStructure = stored_data['structure']
    
    # Get requested chunks
    chunks_to_process = [
        chunk for chunk in structure.chunks 
        if chunk.chunk_id in request.chunk_ids
    ]
    
    if not chunks_to_process:
        raise HTTPException(status_code=404, detail="No valid chunks found")
    
    # Process chunks based on type
    results = []
    for chunk in chunks_to_process:
        result = await process_single_chunk(
            chunk=chunk,
            processing_type=request.processing_type,
            ai_config=request.ai_config,
            options=request.options,
            context_structure=structure
        )
        results.append(result)
    
    return results

async def process_single_chunk(
    chunk,
    processing_type: str,
    ai_config: Dict,
    options: Dict,
    context_structure: TextbookStructure
) -> ChunkProcessingResult:
    """Process a single chunk with AI"""
    
    try:
        # Build context-aware prompt
        context = f"""
You are processing a chunk from the textbook "{context_structure.title}".
Location: {chunk.hierarchy_path}
Chapter: {chunk.chapter_num}. {chunk.chapter_title or 'Unknown'}
Section: {chunk.section_num}. {chunk.section_title or 'Unknown'}
This is chunk {chunk.chunk_index + 1} of {chunk.total_chunks_in_section} in this section.
"""
        
        if chunk.context_before:
            context += f"\nPrevious context: {chunk.context_before}"
        
        if chunk.context_after:
            context += f"\nNext context: {chunk.context_after}"
        
        # Generate prompt based on processing type
        if processing_type == "summary":
            prompt = f"""{context}

Generate a comprehensive summary of the following textbook chunk. 
Focus on key concepts, definitions, and important relationships.
Maintain the educational context and hierarchy.

Chunk content:
{chunk.content}

Provide the summary in a structured format with:
1. Main concepts
2. Key definitions
3. Important relationships
4. Examples mentioned
"""
        
        elif processing_type == "flashcards":
            num_cards = options.get('num_flashcards', 5)
            difficulty = options.get('difficulty', 'intermediate')
            
            prompt = f"""{context}

Create {num_cards} educational flashcards from this textbook chunk.
Difficulty level: {difficulty}
Include a mix of:
- Definition cards
- Concept application cards
- Problem-solving cards
- Relationship/comparison cards

Chunk content:
{chunk.content}

Return as JSON array with format:
[
  {{
    "front": "Question or prompt",
    "back": "Answer with explanation",
    "type": "definition|concept|application|comparison",
    "difficulty": "{difficulty}",
    "tags": ["tag1", "tag2"]
  }}
]
"""
        
        elif processing_type == "notes":
            note_style = options.get('style', 'cornell')
            
            prompt = f"""{context}

Generate structured study notes from this textbook chunk.
Note style: {note_style}

Chunk content:
{chunk.content}

Organize notes with:
1. Main Ideas
2. Supporting Details
3. Key Terms & Definitions
4. Examples
5. Questions for Review
6. Summary

Use markdown formatting for clarity.
"""
        
        elif processing_type == "questions":
            question_types = options.get('question_types', ['comprehension', 'application', 'analysis'])
            
            prompt = f"""{context}

Generate study questions from this textbook chunk.
Include these question types: {', '.join(question_types)}

Chunk content:
{chunk.content}

Create questions that:
1. Test comprehension of key concepts
2. Require application of knowledge
3. Encourage critical thinking
4. Connect to previous/next sections

Format as JSON with answers and explanations.
"""
        
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
        
        # Call AI API
        result = await call_openai_api(
            prompt=prompt,
            api_key=ai_config['api_key'],
            model=ai_config.get('model', 'gpt-3.5-turbo'),
            temperature=ai_config.get('temperature', 0.7),
            max_tokens=ai_config.get('max_tokens', 1500)
        )
        
        if result['success']:
            return ChunkProcessingResult(
                chunk_id=chunk.chunk_id,
                success=True,
                result_type=processing_type,
                content=result['content'],
                tokens_used=result['tokens_used']
            )
        else:
            return ChunkProcessingResult(
                chunk_id=chunk.chunk_id,
                success=False,
                result_type=processing_type,
                content={},
                tokens_used=0,
                error=result.get('error', 'Unknown error')
            )
    
    except Exception as e:
        logger.error(f"Error processing chunk {chunk.chunk_id}: {str(e)}")
        return ChunkProcessingResult(
            chunk_id=chunk.chunk_id,
            success=False,
            result_type=processing_type,
            content={},
            tokens_used=0,
            error=str(e)
        )

@router.post("/summarize-chapters")
async def summarize_chapters(
    request: ChapterSummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate summaries for entire chapters"""
    
    if request.textbook_id not in TEXTBOOK_STORAGE:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    stored_data = TEXTBOOK_STORAGE[request.textbook_id]
    if 'error' in stored_data:
        raise HTTPException(status_code=400, detail="Textbook processing failed")
    
    structure: TextbookStructure = stored_data['structure']
    
    summaries = []
    
    for chapter_num in request.chapter_numbers:
        # Get all chunks for this chapter
        chapter_chunks = [
            chunk for chunk in structure.chunks 
            if chunk.chapter_num == chapter_num
        ]
        
        if not chapter_chunks:
            continue
        
        # Process in batches to avoid token limits
        batch_size = 5  # Process 5 chunks at a time
        chapter_summaries = []
        
        for i in range(0, len(chapter_chunks), batch_size):
            batch = chapter_chunks[i:i + batch_size]
            
            # Combine chunk contents
            combined_content = "\n\n---\n\n".join([
                f"[{chunk.hierarchy_path}]\n{chunk.content}" 
                for chunk in batch
            ])
            
            prompt = f"""Summarize this section of Chapter {chapter_num} from "{structure.title}".
Focus on main concepts, key relationships, and important examples.

Content:
{combined_content}

Provide a {request.summary_type} summary.
"""
            
            result = await call_openai_api(
                prompt=prompt,
                api_key=request.ai_config['api_key'],
                model=request.ai_config.get('model', 'gpt-3.5-turbo'),
                temperature=0.5,
                max_tokens=2000
            )
            
            if result['success']:
                chapter_summaries.append(result['content'])
        
        # Combine all chapter summaries
        if chapter_summaries:
            if len(chapter_summaries) > 1:
                # Synthesize multiple summaries
                synthesis_prompt = f"""Combine these summaries of Chapter {chapter_num} into a cohesive {request.summary_type} summary:

{chr(10).join(chapter_summaries)}

Create a unified summary that captures all key points without repetition.
"""
                
                final_result = await call_openai_api(
                    prompt=synthesis_prompt,
                    api_key=request.ai_config['api_key'],
                    model=request.ai_config.get('model', 'gpt-3.5-turbo'),
                    temperature=0.5,
                    max_tokens=2000
                )
                
                if final_result['success']:
                    summaries.append({
                        'chapter_num': chapter_num,
                        'chapter_title': chapter_chunks[0].chapter_title,
                        'summary': final_result['content'],
                        'chunks_processed': len(chapter_chunks)
                    })
            else:
                summaries.append({
                    'chapter_num': chapter_num,
                    'chapter_title': chapter_chunks[0].chapter_title,
                    'summary': chapter_summaries[0],
                    'chunks_processed': len(chapter_chunks)
                })
    
    return {
        'textbook_title': structure.title,
        'chapters_summarized': len(summaries),
        'summaries': summaries
    }

@router.get("/structure/{textbook_id}")
async def get_textbook_structure(
    textbook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the hierarchical structure of a processed textbook"""
    
    if textbook_id not in TEXTBOOK_STORAGE:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    stored_data = TEXTBOOK_STORAGE[textbook_id]
    if 'error' in stored_data:
        raise HTTPException(status_code=400, detail="Textbook processing failed")
    
    structure: TextbookStructure = stored_data['structure']
    
    # Build hierarchical view
    chapters = {}
    for chunk in structure.chunks:
        if chunk.chapter_num not in chapters:
            chapters[chunk.chapter_num] = {
                'title': chunk.chapter_title,
                'sections': {},
                'chunk_count': 0
            }
        
        chapters[chunk.chapter_num]['chunk_count'] += 1
        
        if chunk.section_num:
            if chunk.section_num not in chapters[chunk.chapter_num]['sections']:
                chapters[chunk.chapter_num]['sections'][chunk.section_num] = {
                    'title': chunk.section_title,
                    'chunks': []
                }
            
            chapters[chunk.chapter_num]['sections'][chunk.section_num]['chunks'].append({
                'chunk_id': chunk.chunk_id,
                'type': chunk.chunk_type,
                'pages': chunk.page_numbers,
                'token_count': chunk.token_count
            })
    
    return {
        'textbook_id': textbook_id,
        'title': structure.title,
        'authors': structure.authors,
        'total_pages': structure.total_pages,
        'total_chunks': structure.processing_stats['total_chunks'],
        'chapters': chapters,
        'table_of_contents': structure.table_of_contents
    }
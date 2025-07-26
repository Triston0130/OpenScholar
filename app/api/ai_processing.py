from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import os
import json
import asyncio
import aiohttp
from datetime import datetime
from sqlalchemy import or_ as db_or
import uuid

from app.database.connection import get_db
from app.database.models import User, Collection, Paper, collection_papers
from app.api.auth import get_current_user
from app.security.validation import sanitize_paper_data
from app.utils.pdf_extractor import process_paper_for_ai, estimate_token_count, chunk_text_for_processing

router = APIRouter(prefix="/api/ai", tags=["ai"])


class NoteTypes(BaseModel):
    summary: bool = True
    keyTerms: bool = True  
    topics: bool = True
    methodology: bool = True
    findings: bool = True
    implications: bool = False
    flashcards: bool = False
    flashcard_count: int = Field(default=10, ge=1, le=30)
    flashcard_difficulty: str = Field(default="intermediate")

class AIConfig(BaseModel):
    api_key: str
    model: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: int = Field(default=1500, ge=100, le=16000)
    note_types: Optional[NoteTypes] = Field(default_factory=NoteTypes)
    extract_full_text: bool = Field(default=True)


class ProcessCollectionRequest(BaseModel):
    collection_id: str
    folder_id: Optional[str] = None
    ai_config: AIConfig
    process_empty_only: bool = True

class ProcessPapersRequest(BaseModel):
    papers: List[Dict]  # List of paper objects with their notes/tags
    ai_config: AIConfig


class ProcessedPaper(BaseModel):
    paper_id: str
    title: str
    tags: List[str]
    notes: str
    flashcards: Optional[List[Dict]] = None
    success: bool
    error_message: Optional[str] = None


class ProcessCollectionResponse(BaseModel):
    collection_id: str
    processed_papers: List[ProcessedPaper]
    total_processed: int
    total_failed: int
    total_cost_estimate: float


async def generate_notes_and_tags(paper: dict, ai_config: AIConfig, retry_count: int = 0) -> Dict[str, any]:
    """
    Use OpenAI API to generate notes and tags for a paper with retry logic
    """
    # Validate model name
    valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-0125-preview"]
    print(f"DEBUG: Attempting to use model: {ai_config.model}")
    if ai_config.model not in valid_models:
        return {
            'success': False,
            'error': f"Invalid model: {ai_config.model}. Valid models are: {', '.join(valid_models)}"
        }
    
    # Try to get full text if not already present and extraction is enabled
    if ai_config.extract_full_text and not paper.get('has_full_text') and not paper.get('_skip_pdf_extraction'):
        print(f"DEBUG: Attempting to extract full text for: {paper.get('title', 'Unknown')[:50]}...")
        enhanced_paper = await process_paper_for_ai(paper)
        paper = enhanced_paper
        if paper.get('has_full_text'):
            print(f"DEBUG: Successfully extracted {paper.get('page_count', 0)} pages, {paper.get('text_token_count', 0)} tokens")
        else:
            print(f"DEBUG: Failed to extract text: {paper.get('text_extraction_error', 'Unknown error')}")
    
    # Get selected note types
    note_types = ai_config.note_types or NoteTypes()
    
    # Build sections based on selected note types
    sections = []
    if note_types.summary:
        sections.append("<h3>Summary</h3>\\nA comprehensive overview of the paper (200-300 words)")
    if note_types.keyTerms:
        sections.append("<h3>Key Terms & Definitions</h3>\\nImportant terms with clear explanations")
    if note_types.topics:
        sections.append("<h3>Main Topics</h3>\\nPrimary topics and themes covered")
    if note_types.methodology:
        sections.append("<h3>Methodology</h3>\\nResearch methods, study design, and approaches used")
    if note_types.findings:
        sections.append("<h3>Key Findings</h3>\\nMain results, discoveries, and conclusions")
    if note_types.implications:
        sections.append("<h3>Implications & Applications</h3>\\nPractical applications, future research directions, and impact")
    
    sections_text = "\\n\\n".join(sections)
    
    # Add flashcard generation instruction if requested
    flashcard_instruction = ""
    flashcard_json_format = ""
    if note_types.flashcards:
        difficulty_descriptions = {
            "beginner": "basic concepts, definitions, and fundamental principles",
            "intermediate": "application of concepts, relationships between ideas, and moderate complexity",
            "advanced": "complex analysis, synthesis of ideas, critical thinking, and expert-level understanding"
        }
        flashcard_instruction = f"""
3. {note_types.flashcard_count} flashcards for studying at {note_types.flashcard_difficulty} level ({difficulty_descriptions[note_types.flashcard_difficulty]})
   - Each flashcard should test understanding, not just memorization
   - Include a mix of concept definitions, applications, and analytical questions
   - Make the backs comprehensive but concise
   - Format as: {{"front": "question", "back": "answer", "category": "category"}}"""
        flashcard_json_format = ',\n    "flashcards": [{"front": "...", "back": "...", "category": "..."}, ...]'
    
    # Check if this is a book (usually has many authors or specific keywords in title)
    is_book = (
        'book' in paper.get('title', '').lower() or 
        'textbook' in paper.get('title', '').lower() or
        'introduction to' in paper.get('title', '').lower() or
        len(paper.get('authors', [])) > 10
    )
    
    # Construct the prompt based on available content
    paper_type = "book" if is_book else "academic paper"
    has_full_text = paper.get('has_full_text', False)
    
    if has_full_text:
        full_text = paper.get('full_text', '')
        token_count = paper.get('text_token_count', estimate_token_count(full_text))
        
        # Determine max context based on model
        model_context_limits = {
            "gpt-3.5-turbo": 4000,
            "gpt-4": 8000,
            "gpt-4-turbo-preview": 120000,
            "gpt-4-1106-preview": 120000,
            "gpt-4-0125-preview": 120000
        }
        max_context = model_context_limits.get(ai_config.model, 4000)
        
        # Leave room for prompt and response
        max_text_tokens = max_context - 2000  # Reserve 2k for prompt structure and response
        
        # Truncate or use full text based on token count
        if token_count > max_text_tokens:
            # For long documents, focus on beginning and end
            chars_to_use = max_text_tokens * 4  # Rough conversion
            text_portion = full_text[:chars_to_use//2] + "\n\n[... middle section omitted due to length ...]\n\n" + full_text[-chars_to_use//2:]
            analysis_instruction = f"Analyze this {paper_type} based on the provided excerpts (beginning and end sections)"
        else:
            text_portion = full_text
            analysis_instruction = f"Analyze this complete {paper_type}"
        
        content_section = f"""
Full Text (Page count: {paper.get('page_count', 'Unknown')}):
{text_portion}

Note: Analysis is based on the {'complete' if token_count <= max_text_tokens else 'partial'} full text of the paper."""
    else:
        analysis_instruction = f"Analyze this {paper_type} based on the abstract"
        content_section = f"""
Abstract: {paper.get('abstract', 'No abstract available')[:3000] + ('...' if len(paper.get('abstract', '')) > 3000 else '')}

Note: Analysis is based on the abstract and metadata only. {paper.get('text_extraction_error', 'Full paper text is not available')}."""
    
    prompt = f"""{analysis_instruction} and provide:
1. 10 relevant tags (keywords/topics)
2. Detailed structured notes with the following sections:
{sections_text}{flashcard_instruction}

Paper Information:
Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', []))[:200] + ('...' if len(', '.join(paper.get('authors', []))) > 200 else '')}
Year: {paper.get('year', 'Unknown')}
Journal/Publisher: {paper.get('journal', 'Unknown')}
DOI: {paper.get('doi', 'None')}
Type: {paper_type}
{content_section}

Please respond in JSON format:
{{
    "tags": ["tag1", "tag2", ...],
    "notes": "Structured notes with proper formatting. Use <h3> tags for section headers and double line breaks between sections for clarity."{flashcard_json_format}
}}

Format the notes as follows:
- Use <h3>Section Name</h3> for headers
- Add double line breaks (\\n\\n) between sections
- Use numbered or bulleted lists where appropriate
- Keep paragraphs concise and well-separated

Make the notes detailed, informative, and useful for research purposes."""

    headers = {
        "Authorization": f"Bearer {ai_config.api_key}",
        "Content-Type": "application/json"
    }
    
    # Build payload - only include response_format for compatible models
    payload = {
        "model": ai_config.model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert academic researcher skilled at analyzing papers and extracting key information. When full text is provided, analyze the complete paper thoroughly. When only abstract is available, provide the best analysis possible from the limited information. For books and textbooks, focus on major themes and key concepts. Be comprehensive but concise. Always respond with valid JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": ai_config.temperature,
        "max_tokens": ai_config.max_tokens
    }
    
    # Only add response_format for models that support it
    if ai_config.model in ["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-1106-preview"]:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    result = json.loads(content)
                    
                    # Ensure we have the expected structure
                    tags = result.get('tags', [])[:10]  # Limit to 10 tags
                    notes = result.get('notes', '')
                    flashcards = result.get('flashcards', [])
                    
                    # Clean and validate tags
                    tags = [tag.strip()[:100] for tag in tags if tag.strip()]  # Limit tag length
                    # Don't limit notes length - let the full response come through
                    notes = notes if notes else ''
                    
                    # Process flashcards if they exist
                    processed_flashcards = []
                    if flashcards and isinstance(flashcards, list):
                        for fc in flashcards:
                            if isinstance(fc, dict) and fc.get('front') and fc.get('back'):
                                processed_flashcards.append({
                                    'front': fc.get('front', '').strip(),
                                    'back': fc.get('back', '').strip(),
                                    'category': fc.get('category', 'General'),
                                    'difficulty': ai_config.note_types.flashcard_difficulty if hasattr(ai_config, 'note_types') else 'intermediate'
                                })
                    
                    return {
                        'success': True,
                        'tags': tags,
                        'notes': notes,
                        'flashcards': processed_flashcards
                    }
                else:
                    error_text = await response.text()
                    # Handle rate limiting specifically
                    if response.status == 429 and retry_count < 2:
                        wait_time = 5 * (retry_count + 1)  # Exponential backoff
                        print(f"Rate limited, waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        return await generate_notes_and_tags(paper, ai_config, retry_count + 1)
                    
                    # Handle model access errors
                    print(f"DEBUG: API Error - Status: {response.status}, Error: {error_text}")
                    if response.status == 404 and "model" in error_text.lower():
                        return {
                            'success': False,
                            'error': f"Model '{ai_config.model}' not available for your API key. Please use gpt-3.5-turbo or ensure you have access to GPT-4."
                        }
                    
                    # Parse error for more details
                    try:
                        error_json = json.loads(error_text)
                        error_message = error_json.get('error', {}).get('message', error_text)
                    except:
                        error_message = error_text
                    
                    return {
                        'success': False,
                        'error': f"OpenAI API error ({response.status}): {error_message}"
                    }
    except asyncio.TimeoutError:
        if retry_count < 1:  # One retry for timeout
            print(f"Timeout processing paper '{paper.get('title', 'Unknown')[:50]}...', retrying...")
            return await generate_notes_and_tags(paper, ai_config, retry_count + 1)
        return {
            'success': False,
            'error': "Request timed out after 60 seconds"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error calling OpenAI API: {str(e)}"
        }


def estimate_cost(paper_count: int, model: str) -> float:
    """Estimate the cost of processing papers"""
    # Rough cost estimates per paper (in USD)
    model_costs = {
        "gpt-3.5-turbo": 0.001,
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-4-turbo-preview": 0.01,
        "gpt-4-1106-preview": 0.01,
        "gpt-4-0125-preview": 0.01
    }
    return paper_count * model_costs.get(model, 0.001)


@router.post("/process-collection", response_model=ProcessCollectionResponse)
async def process_collection(
    request: ProcessCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process all papers in a collection with AI to generate notes and tags"""
    
    print(f"DEBUG: AI Processing request received")
    print(f"DEBUG: Collection ID: {request.collection_id}")
    print(f"DEBUG: User ID: {current_user.id}")
    print(f"DEBUG: Process empty only: {request.process_empty_only}")
    print(f"DEBUG: AI Model: {request.ai_config.model}")
    
    # Convert collection_id to UUID if it's a string
    try:
        collection_uuid = uuid.UUID(request.collection_id) if isinstance(request.collection_id, str) else request.collection_id
    except ValueError:
        print(f"DEBUG: Invalid collection ID format: {request.collection_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid collection ID format"
        )
    
    # Verify collection exists and belongs to user
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        print(f"DEBUG: Collection not found!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    print(f"DEBUG: Collection found: {collection.name}")
    
    # Get papers in the collection with their association data
    query = db.query(
        Paper,
        collection_papers.c.notes,
        collection_papers.c.custom_tags
    ).join(
        collection_papers,
        Paper.id == collection_papers.c.paper_id
    ).filter(
        collection_papers.c.collection_id == collection_uuid
    )
    
    print(f"DEBUG: Built query for papers")
    
    # TODO: Add folder filtering if needed
    # if request.folder_id:
    #     query = query.filter(collection_papers.c.folder_id == request.folder_id)
    
    # Filter to only papers without notes/tags if requested
    if request.process_empty_only:
        query = query.filter(
            db_or(
                collection_papers.c.notes == None,
                collection_papers.c.notes == '',
                collection_papers.c.custom_tags == None,
            )
        )
    
    papers_data = query.all()
    
    print(f"DEBUG: Query executed, found {len(papers_data)} papers")
    
    if not papers_data:
        print(f"DEBUG: No papers found to process")
        return ProcessCollectionResponse(
            collection_id=request.collection_id,
            processed_papers=[],
            total_processed=0,
            total_failed=0,
            total_cost_estimate=0
        )
    
    # Estimate cost
    estimated_cost = estimate_cost(len(papers_data), request.ai_config.model)
    
    # Process papers in batches to avoid overwhelming the API
    processed_papers = []
    batch_size = 3  # Process 3 papers concurrently for more stability
    
    for i in range(0, len(papers_data), batch_size):
        batch = papers_data[i:i+batch_size]
        
        # Process batch concurrently
        tasks = []
        for paper, existing_notes, existing_tags in batch:
            # Create paper dict from SQLAlchemy model
            paper_dict = {
                'title': paper.title,
                'authors': paper.authors or [],
                'year': paper.year,
                'abstract': paper.abstract,
                'journal': paper.journal,
                'doi': paper.doi,
                'url': paper.url,
                'pdf_url': paper.pdf_url,
                'full_text_url': paper.full_text_url
            }
            task = generate_notes_and_tags(paper_dict, request.ai_config)
            tasks.append((task, paper, existing_notes, existing_tags))
        
        # Execute tasks and process results
        for task_data in tasks:
            task, paper, existing_notes, existing_tags = task_data
            result = await task
            
            if result['success']:
                # Append to existing notes instead of replacing
                new_notes = result['notes']
                
                # Combine notes with a separator if there are existing notes
                if existing_notes and existing_notes.strip():
                    combined_notes = f"{existing_notes}\n\n--- AI Generated Notes ---\n\n{new_notes}"
                else:
                    combined_notes = new_notes
                
                # Merge tags (combine existing and new, remove duplicates)
                existing_tag_list = existing_tags or []
                new_tags = result['tags']
                all_tags = list(set(existing_tag_list + new_tags))[:20]  # Limit to 20 tags
                
                # Update the association table
                db.execute(
                    collection_papers.update().where(
                        (collection_papers.c.collection_id == collection_uuid) &
                        (collection_papers.c.paper_id == paper.id)
                    ).values(
                        notes=combined_notes,
                        custom_tags=all_tags
                    )
                )
                
                processed_papers.append(ProcessedPaper(
                    paper_id=str(paper.id),
                    title=paper.title,
                    tags=all_tags,
                    notes=combined_notes,
                    flashcards=result.get('flashcards', []),
                    success=True
                ))
            else:
                processed_papers.append(ProcessedPaper(
                    paper_id=str(paper.id),
                    title=paper.title,
                    tags=[],
                    notes='',
                    flashcards=None,
                    success=False,
                    error_message=result.get('error', 'Unknown error')
                ))
        
        # Add a small delay between batches to avoid rate limiting
        if i + batch_size < len(papers_data):
            await asyncio.sleep(2)  # Increased delay between batches
            print(f"DEBUG: Processed batch {i//batch_size + 1}, moving to next batch...")
    
    # Commit all changes
    db.commit()
    
    # Calculate stats
    total_processed = len([p for p in processed_papers if p.success])
    total_failed = len([p for p in processed_papers if not p.success])
    
    return ProcessCollectionResponse(
        collection_id=request.collection_id,
        processed_papers=processed_papers,
        total_processed=total_processed,
        total_failed=total_failed,
        total_cost_estimate=estimated_cost
    )


@router.get("/models")
async def get_available_models():
    """Get available AI models and their information"""
    return {
        "models": [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and cost-effective for most tasks",
                "cost_per_paper": 0.001
            },
            {
                "id": "gpt-4-0125-preview",
                "name": "GPT-4 Turbo (Latest)",
                "description": "Latest GPT-4 Turbo with improved performance",
                "cost_per_paper": 0.01
            },
            {
                "id": "gpt-4-1106-preview",
                "name": "GPT-4 Turbo",
                "description": "GPT-4 Turbo with 128K context window",
                "cost_per_paper": 0.01
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "description": "Original GPT-4, most capable",
                "cost_per_paper": 0.03
            }
        ]
    }


@router.post("/process-papers", response_model=ProcessCollectionResponse)
async def process_papers_directly(
    request: ProcessPapersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process papers directly without needing a collection"""
    
    print(f"DEBUG: Processing {len(request.papers)} papers directly")
    print(f"DEBUG: AI Config - Model: {request.ai_config.model}, Max Tokens: {request.ai_config.max_tokens}")
    
    if not request.papers:
        return ProcessCollectionResponse(
            collection_id="direct",
            processed_papers=[],
            total_processed=0,
            total_failed=0,
            total_cost_estimate=0
        )
    
    # Filter papers that need processing
    papers_to_process = []
    for paper in request.papers:
        # Check if paper already has AI-generated content
        existing_notes = paper.get('notes', '')
        existing_tags = paper.get('tags', [])
        
        # Only process if no AI notes exist
        if not existing_notes or '--- AI Generated Notes ---' not in existing_notes:
            papers_to_process.append(paper)
    
    if not papers_to_process:
        print(f"DEBUG: All papers already have AI-generated content")
        return ProcessCollectionResponse(
            collection_id="direct",
            processed_papers=[],
            total_processed=0,
            total_failed=0,
            total_cost_estimate=0
        )
    
    print(f"DEBUG: {len(papers_to_process)} papers need processing")
    
    # Estimate cost
    estimated_cost = estimate_cost(len(papers_to_process), request.ai_config.model)
    
    # Process papers
    processed_papers = []
    batch_size = 3
    
    for i in range(0, len(papers_to_process), batch_size):
        batch = papers_to_process[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(papers_to_process) + batch_size - 1) // batch_size
        
        print(f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        # Process batch concurrently
        tasks = []
        for idx, paper_data in enumerate(batch):
            print(f"  - Paper {i+idx+1}/{len(papers_to_process)}: {paper_data.get('title', 'Unknown')[:60]}...")
            task = generate_notes_and_tags(paper_data, request.ai_config)
            tasks.append((task, paper_data))
        
        # Execute tasks and process results
        for task_data in tasks:
            task, paper_data = task_data
            result = await task
            
            if result['success']:
                # Get existing notes and tags
                existing_notes = paper_data.get('notes', '')
                existing_tags = paper_data.get('tags', [])
                
                # Append to existing notes
                new_notes = result['notes']
                if existing_notes and existing_notes.strip():
                    combined_notes = f"{existing_notes}\n\n--- AI Generated Notes ---\n\n{new_notes}"
                else:
                    combined_notes = new_notes
                
                # Merge tags
                new_tags = result['tags']
                all_tags = list(set(existing_tags + new_tags))[:20]
                
                # Create a unique ID for the paper (using title + first author)
                paper_id = paper_data.get('doi') or f"{paper_data.get('title', 'unknown')}_{paper_data.get('authors', [''])[0]}"
                paper_id = paper_id[:50]  # Limit length
                
                processed_papers.append(ProcessedPaper(
                    paper_id=paper_id,
                    title=paper_data.get('title', 'Unknown'),
                    tags=all_tags,
                    notes=combined_notes,
                    flashcards=result.get('flashcards', []),
                    success=True
                ))
            else:
                paper_id = paper_data.get('doi') or f"{paper_data.get('title', 'unknown')}_{paper_data.get('authors', [''])[0]}"
                paper_id = paper_id[:50]
                
                processed_papers.append(ProcessedPaper(
                    paper_id=paper_id,
                    title=paper_data.get('title', 'Unknown'),
                    tags=[],
                    notes='',
                    flashcards=None,
                    success=False,
                    error_message=result.get('error', 'Unknown error')
                ))
        
        # Add delay between batches
        if i + batch_size < len(papers_to_process):
            await asyncio.sleep(2)  # Increased delay between batches
            print(f"DEBUG: Processed batch {i//batch_size + 1}, moving to next batch...")
    
    # Calculate stats
    total_processed = len([p for p in processed_papers if p.success])
    total_failed = len([p for p in processed_papers if not p.success])
    
    return ProcessCollectionResponse(
        collection_id="direct",
        processed_papers=processed_papers,
        total_processed=total_processed,
        total_failed=total_failed,
        total_cost_estimate=estimated_cost
    )


@router.post("/test-api-key")
async def test_api_key(api_key: str = Query(..., min_length=1), model: str = Query(default="gpt-3.5-turbo")):
    """Test if an OpenAI API key is valid with a specific model"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"DEBUG: Testing API key with model: {model}")
    
    # Simple test request to check if key is valid
    test_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return {"valid": True, "message": f"API key is valid for {model}"}
                elif response.status == 401:
                    return {"valid": False, "message": "Invalid API key"}
                elif response.status == 429:
                    return {"valid": True, "message": f"API key is valid for {model} (rate limited)"}
                elif response.status == 404:
                    error_text = await response.text()
                    return {"valid": False, "message": f"Model {model} not found or not available for your API key"}
                else:
                    error_text = await response.text()
                    return {"valid": False, "message": f"API error {response.status}: {error_text[:200]}"}
    except Exception as e:
        return {"valid": False, "message": f"Connection error: {str(e)}"}
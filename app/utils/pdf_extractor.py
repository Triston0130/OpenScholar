"""
PDF text extraction utility for processing academic papers
"""
import asyncio
import aiohttp
import aiofiles
import PyPDF2
import tempfile
import os
from typing import Optional, Dict
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


async def extract_text_from_pdf_url(pdf_url: str, max_pages: Optional[int] = None) -> Dict[str, any]:
    """
    Extract text from a PDF URL asynchronously
    
    Args:
        pdf_url: URL of the PDF to extract text from
        max_pages: Maximum number of pages to extract (None = all pages)
        
    Returns:
        Dict with 'success', 'text', 'page_count', and 'error' keys
    """
    try:
        # Download PDF content
        async with aiohttp.ClientSession() as session:
            async with session.get(
                pdf_url,
                timeout=aiohttp.ClientTimeout(total=60),
                headers={'User-Agent': 'OpenScholar Academic Research Tool'}
            ) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'text': '',
                        'page_count': 0,
                        'error': f'Failed to download PDF: HTTP {response.status}'
                    }
                
                pdf_content = await response.read()
                
        # Extract text from PDF
        return await extract_text_from_pdf_bytes(pdf_content, max_pages)
        
    except asyncio.TimeoutError:
        return {
            'success': False,
            'text': '',
            'page_count': 0,
            'error': 'PDF download timed out'
        }
    except Exception as e:
        logger.error(f"Error extracting PDF from URL {pdf_url}: {str(e)}")
        return {
            'success': False,
            'text': '',
            'page_count': 0,
            'error': f'Error processing PDF: {str(e)}'
        }


async def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: Optional[int] = None) -> Dict[str, any]:
    """
    Extract text from PDF bytes
    
    Args:
        pdf_bytes: PDF file content as bytes
        max_pages: Maximum number of pages to extract (None = all pages)
        
    Returns:
        Dict with 'success', 'text', 'page_count', and 'error' keys
    """
    try:
        # Use BytesIO to read PDF from memory
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        total_pages = len(pdf_reader.pages)
        pages_to_extract = min(max_pages, total_pages) if max_pages else total_pages
        
        # Extract text from pages
        extracted_text = []
        for page_num in range(pages_to_extract):
            try:
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    extracted_text.append(f"[Page {page_num + 1}]\n{text}")
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
                continue
        
        full_text = "\n\n".join(extracted_text)
        
        # Check if we got meaningful text
        if not full_text.strip() or len(full_text) < 100:
            return {
                'success': False,
                'text': full_text,
                'page_count': total_pages,
                'error': 'PDF appears to be empty or contains only images'
            }
        
        return {
            'success': True,
            'text': full_text,
            'page_count': total_pages,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        return {
            'success': False,
            'text': '',
            'page_count': 0,
            'error': f'Error reading PDF: {str(e)}'
        }


def estimate_token_count(text: str) -> int:
    """
    Estimate the number of tokens in a text string
    Rough approximation: 1 token ≈ 4 characters or 0.75 words
    """
    # Use character count divided by 4 as a rough estimate
    return len(text) // 4


def chunk_text_for_processing(text: str, max_tokens: int = 100000) -> list[str]:
    """
    Split text into chunks that fit within token limits
    
    Args:
        text: Full text to chunk
        max_tokens: Maximum tokens per chunk (leaving room for prompt)
        
    Returns:
        List of text chunks
    """
    estimated_tokens = estimate_token_count(text)
    
    if estimated_tokens <= max_tokens:
        return [text]
    
    # Split by pages first (if formatted with [Page X] markers)
    pages = text.split('[Page ')
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for page in pages:
        if not page.strip():
            continue
            
        page_text = '[Page ' + page if page != pages[0] else page
        page_tokens = estimate_token_count(page_text)
        
        if current_tokens + page_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = page_text
            current_tokens = page_tokens
        else:
            current_chunk += "\n\n" + page_text if current_chunk else page_text
            current_tokens += page_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


async def process_paper_for_ai(paper_data: dict) -> Dict[str, any]:
    """
    Prepare paper data for AI processing, fetching full text if available
    
    Args:
        paper_data: Dictionary containing paper metadata
        
    Returns:
        Dict with paper data enhanced with full_text if available
    """
    # Check for PDF URL
    pdf_url = paper_data.get('pdf_url') or paper_data.get('full_text_url')
    
    if not pdf_url:
        # If no PDF URL, try to use abstract
        abstract = paper_data.get('abstract', '')
        if abstract:
            return {
                **paper_data,
                'full_text': abstract,
                'has_full_text': False,
                'is_abstract_only': True,
                'text_token_count': estimate_token_count(abstract),
                'text_extraction_error': None,
                'extraction_note': 'Using abstract only - no PDF URL available'
            }
        else:
            return {
                **paper_data,
                'full_text': None,
                'has_full_text': False,
                'text_extraction_error': 'No PDF URL or abstract available'
            }
    
    # Check if URL is likely HTML instead of PDF
    if any(ext in pdf_url.lower() for ext in ['.html', '.htm', '.php', '.jsp', '.asp']):
        # For HTML sources, we'll use the abstract only
        abstract = paper_data.get('abstract', '')
        if abstract:
            return {
                **paper_data,
                'full_text': abstract,
                'has_full_text': False,
                'is_html_source': True,
                'text_token_count': estimate_token_count(abstract),
                'text_extraction_error': None,
                'extraction_note': 'Using abstract only for HTML source'
            }
        else:
            return {
                **paper_data,
                'full_text': None,
                'has_full_text': False,
                'is_html_source': True,
                'text_extraction_error': 'HTML source with no abstract available'
            }
    
    # Skip if URL doesn't look like a PDF
    if not any(pdf_url.lower().endswith(ext) for ext in ['.pdf', '/pdf', 'format=pdf']):
        # Some URLs might still serve PDFs without .pdf extension
        # but for now, we'll be conservative
        if 'arxiv.org' not in pdf_url.lower() and 'pdf' not in pdf_url.lower():
            # Try to use abstract for non-PDF sources
            abstract = paper_data.get('abstract', '')
            if abstract:
                return {
                    **paper_data,
                    'full_text': abstract,
                    'has_full_text': False,
                    'is_non_pdf_source': True,
                    'text_token_count': estimate_token_count(abstract),
                    'text_extraction_error': None,
                    'extraction_note': 'Using abstract only for non-PDF source'
                }
            else:
                return {
                    **paper_data,
                    'full_text': None,
                    'has_full_text': False,
                    'text_extraction_error': 'URL does not appear to be a PDF'
                }
    
    # Extract text from PDF
    logger.info(f"Attempting to extract text from: {pdf_url}")
    extraction_result = await extract_text_from_pdf_url(pdf_url, max_pages=50)  # Limit to 50 pages
    
    if extraction_result['success']:
        # Estimate tokens and potentially chunk
        full_text = extraction_result['text']
        token_count = estimate_token_count(full_text)
        
        return {
            **paper_data,
            'full_text': full_text,
            'has_full_text': True,
            'text_token_count': token_count,
            'page_count': extraction_result['page_count'],
            'text_extraction_error': None
        }
    else:
        return {
            **paper_data,
            'full_text': None,
            'has_full_text': False,
            'text_extraction_error': extraction_result['error']
        }
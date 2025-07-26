"""
External paper/book lookup API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import aiohttp
import asyncio
import re
from app.api.auth import get_current_user_optional
from app.database.models import User

router = APIRouter(prefix="/api/external", tags=["external"])

async def fetch_from_google_books(isbn: str) -> Dict[str, Any]:
    """Fetch book data from Google Books API"""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Google Books API error")
                
                data = await response.json()
                
                if data.get('totalItems', 0) == 0:
                    raise HTTPException(status_code=404, detail="Book not found")
                
                # Get the first result
                book = data['items'][0]['volumeInfo']
                
                # Extract relevant information
                return {
                    'title': book.get('title', 'Unknown Title'),
                    'authors': book.get('authors', ['Unknown Author']),
                    'publisher': book.get('publisher', 'Unknown Publisher'),
                    'publishedDate': book.get('publishedDate', ''),
                    'description': book.get('description', 'No description available'),
                    'pageCount': book.get('pageCount', 0),
                    'categories': book.get('categories', []),
                    'thumbnail': book.get('imageLinks', {}).get('thumbnail', ''),
                    'previewLink': book.get('previewLink', ''),
                    'language': book.get('language', 'en'),
                    'isbn': isbn
                }
                
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching book data: {str(e)}")

async def fetch_from_open_library(isbn: str) -> Optional[Dict[str, Any]]:
    """Fetch book data from Open Library API as fallback"""
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if not data or f"ISBN:{isbn}" not in data:
                    return None
                
                book = data[f"ISBN:{isbn}"]
                
                # Extract authors
                authors = []
                if 'authors' in book:
                    authors = [author['name'] for author in book['authors']]
                
                return {
                    'title': book.get('title', 'Unknown Title'),
                    'authors': authors or ['Unknown Author'],
                    'publisher': ', '.join(book.get('publishers', [{'name': 'Unknown Publisher'}])[0].get('name', 'Unknown Publisher') 
                                         if isinstance(book.get('publishers', [{}])[0], dict) 
                                         else book.get('publishers', ['Unknown Publisher'])),
                    'publishedDate': book.get('publish_date', ''),
                    'description': book.get('notes', 'No description available'),
                    'pageCount': book.get('number_of_pages', 0),
                    'categories': book.get('subjects', [])[:5] if 'subjects' in book else [],
                    'thumbnail': book.get('cover', {}).get('medium', ''),
                    'previewLink': book.get('url', ''),
                    'language': 'en',
                    'isbn': isbn
                }
                
    except Exception:
        return None

@router.get("/isbn/{isbn}")
async def lookup_book_by_isbn(
    isbn: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Look up book information by ISBN
    Supports both ISBN-10 and ISBN-13
    """
    # Clean ISBN
    clean_isbn = re.sub(r'[-\s]', '', isbn)
    
    # Validate ISBN format
    if not re.match(r'^(\d{10}|\d{13})$', clean_isbn):
        raise HTTPException(status_code=400, detail="Invalid ISBN format")
    
    # Try Google Books first
    try:
        book_data = await fetch_from_google_books(clean_isbn)
        return book_data
    except HTTPException as e:
        if e.status_code == 404:
            # Try Open Library as fallback
            open_lib_data = await fetch_from_open_library(clean_isbn)
            if open_lib_data:
                return open_lib_data
        raise e

@router.get("/doi/{doi:path}")
async def lookup_paper_by_doi(
    doi: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Look up paper information by DOI
    This wraps the existing DOI lookup functionality
    """
    from app.api_clients.crossref import CrossRefClient
    
    try:
        client = CrossRefClient()
        paper_data = await client.search_by_doi(doi)
        
        if not paper_data:
            raise HTTPException(status_code=404, detail="Paper not found")
            
        return paper_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching paper data: {str(e)}")
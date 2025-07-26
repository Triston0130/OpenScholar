from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
import json
import os
import tempfile
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectGutenbergClient(BaseAPIClient):
    """Project Gutenberg client using RDF catalog download"""
    
    def __init__(self):
        super().__init__(base_url="https://gutenberg.org")
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "*/*"
        })
        
        # Cache setup
        self.cache_dir = Path(tempfile.gettempdir()) / "openscholar_gutenberg"
        self.cache_dir.mkdir(exist_ok=True)
        self.catalog_file = self.cache_dir / "gutenberg_catalog.json"
        self.catalog = []
        self.catalog_loaded = False
        self.cache_age_days = 7
    
    async def _wait_for_rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _ensure_catalog_loaded(self) -> bool:
        """Ensure the catalog is loaded from cache or downloaded"""
        if self.catalog_loaded and self.catalog:
            return True
        
        # Check if cached catalog exists and is fresh
        if self.catalog_file.exists():
            cache_age = time.time() - self.catalog_file.stat().st_mtime
            if cache_age < self.cache_age_days * 24 * 3600:
                logger.info("Loading Project Gutenberg catalog from cache...")
                try:
                    with open(self.catalog_file, 'r', encoding='utf-8') as f:
                        self.catalog = json.load(f)
                    logger.info(f"Loaded {len(self.catalog)} books from cache")
                    self.catalog_loaded = True
                    return True
                except Exception as e:
                    logger.error(f"Error loading catalog cache: {e}")
        
        # Download and parse RDF catalog
        logger.info("Downloading Project Gutenberg RDF catalog...")
        success = await self._download_and_parse_catalog()
        if success:
            self.catalog_loaded = True
            return True
        
        return False
    
    async def _download_and_parse_catalog(self) -> bool:
        """Download and parse the RDF catalog"""
        try:
            catalog_url = "https://gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
            
            await self._wait_for_rate_limit()
            
            logger.info("Downloading RDF catalog (this may take a few minutes)...")
            response = await self.client.get(catalog_url, timeout=600.0)  # 10 minute timeout
            response.raise_for_status()
            
            logger.info(f"Downloaded {len(response.content)} bytes, extracting...")
            
            # Process tar.bz2 content
            books = []
            with tempfile.TemporaryFile() as tmp_file:
                tmp_file.write(response.content)
                tmp_file.seek(0)
                
                with tarfile.open(fileobj=tmp_file, mode='r:bz2') as tar:
                    members = tar.getmembers()
                    logger.info(f"Processing {len(members)} RDF files...")
                    
                    # Process first 5000 files to limit memory usage
                    for i, member in enumerate(members[:5000]):
                        if member.isfile() and member.name.endswith('.rdf'):
                            try:
                                rdf_file = tar.extractfile(member)
                                if rdf_file:
                                    content = rdf_file.read().decode('utf-8', errors='ignore')
                                    book_data = self._parse_rdf_file(content)
                                    if book_data:
                                        books.append(book_data)
                                
                                # Progress logging
                                if i % 500 == 0:
                                    logger.info(f"Processed {i} files, found {len(books)} books")
                                    
                            except Exception as e:
                                logger.debug(f"Error processing {member.name}: {e}")
                                continue
            
            logger.info(f"Successfully parsed {len(books)} books")
            
            # Save to cache
            if books:
                with open(self.catalog_file, 'w', encoding='utf-8') as f:
                    json.dump(books, f, indent=2, ensure_ascii=False)
                
                self.catalog = books
                logger.info(f"Cached {len(books)} books to {self.catalog_file}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error downloading/parsing RDF catalog: {e}")
            return False
    
    def _parse_rdf_file(self, rdf_content: str) -> Optional[Dict[str, Any]]:
        """Parse a single RDF file to extract book metadata"""
        try:
            root = ET.fromstring(rdf_content)
            
            # Define RDF namespaces
            ns = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'dcterms': 'http://purl.org/dc/terms/',
                'pgterms': 'http://www.gutenberg.org/2009/pgterms/',
                'dcam': 'http://purl.org/dc/dcam/'
            }
            
            # Find ebook element
            ebook = root.find('.//pgterms:ebook', ns)
            if ebook is None:
                return None
            
            # Extract book ID
            about = ebook.get(f'{{{ns["rdf"]}}}about')
            if not about:
                return None
                
            book_id_match = re.search(r'ebooks/(\d+)', about)
            if not book_id_match:
                return None
            book_id = book_id_match.group(1)
            
            # Extract title
            title_elem = ebook.find('.//dcterms:title', ns)
            title = title_elem.text if title_elem is not None else None
            if not title:
                return None
            
            # Extract authors
            authors = []
            for creator in ebook.findall('.//dcterms:creator', ns):
                agent = creator.find('.//pgterms:agent', ns)
                if agent is not None:
                    name_elem = agent.find('.//pgterms:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
            
            # Extract subjects
            subjects = []
            for subject in ebook.findall('.//dcterms:subject', ns):
                value_elem = subject.find('.//rdf:value', ns)
                if value_elem is not None and value_elem.text:
                    subjects.append(value_elem.text)
            
            # Extract languages
            languages = []
            for lang in ebook.findall('.//dcterms:language', ns):
                value_elem = lang.find('.//rdf:value', ns)
                if value_elem is not None and value_elem.text:
                    languages.append(value_elem.text)
            
            # Extract download count
            downloads_elem = ebook.find('.//pgterms:downloads', ns)
            download_count = 0
            if downloads_elem is not None and downloads_elem.text:
                try:
                    download_count = int(downloads_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Extract year from date fields
            year = None
            for date_tag in ['.//dcterms:issued', './/dcterms:created', './/dcterms:date']:
                date_elem = ebook.find(date_tag, ns)
                if date_elem is not None and date_elem.text:
                    year_match = re.search(r'(18|19|20)\d{2}', date_elem.text)
                    if year_match:
                        year = int(year_match.group(0))
                        break
            
            return {
                'id': book_id,
                'title': title,
                'authors': authors,
                'subjects': subjects,
                'languages': languages or ['en'],
                'year': year,
                'download_count': download_count
            }
            
        except Exception as e:
            logger.debug(f"Error parsing RDF: {e}")
            return None
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search Project Gutenberg catalog"""
        
        # Ensure catalog is loaded
        if not await self._ensure_catalog_loaded():
            logger.error("Failed to load Project Gutenberg catalog")
            return []
        
        await self._wait_for_rate_limit()
        
        try:
            # Normalize query
            query_lower = query.lower()
            query_terms = query_lower.split()
            
            # Add discipline keywords
            if discipline:
                discipline_keywords = {
                    "psychology": ["psychology", "mind", "behavior", "mental"],
                    "philosophy": ["philosophy", "ethics", "logic"], 
                    "history": ["history", "historical"],
                    "literature": ["literature", "fiction", "novel"],
                    "science": ["science", "scientific"],
                    "mathematics": ["mathematics", "math"]
                }
                if discipline.lower() in discipline_keywords:
                    query_terms.extend(discipline_keywords[discipline.lower()])
            
            # Search through catalog
            matches = []
            for book in self.catalog:
                if self._matches_query(book, query_terms, year_start, year_end):
                    matches.append(book)
                    if len(matches) >= limit:
                        break
            
            # Convert to Paper objects
            papers = []
            for book in matches:
                paper = self._book_to_paper(book)
                if paper:
                    papers.append(paper)
            
            logger.info(f"Project Gutenberg returned {len(papers)} books for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Project Gutenberg: {e}")
            return []
    
    def _matches_query(self, book: Dict[str, Any], query_terms: List[str], 
                      year_start: int, year_end: int) -> bool:
        """Check if book matches search criteria"""
        try:
            # Build searchable text
            searchable_parts = [
                book.get('title', ''),
                ' '.join(book.get('authors', [])),
                ' '.join(book.get('subjects', []))
            ]
            searchable_text = ' '.join(searchable_parts).lower()
            
            # Check if any query term matches
            if not any(term in searchable_text for term in query_terms):
                return False
            
            # Check year constraints
            book_year = book.get('year')
            if book_year:
                if year_start and book_year < year_start:
                    return False
                if year_end and book_year > year_end:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _book_to_paper(self, book: Dict[str, Any]) -> Optional[Paper]:
        """Convert book data to Paper object"""
        try:
            book_id = book.get('id', '')
            title = book.get('title', '').strip()
            authors = book.get('authors', [])
            subjects = book.get('subjects', [])
            year = book.get('year')
            
            # Clean author names
            clean_authors = []
            for author in authors:
                # Remove birth/death years and reverse "Last, First" format
                clean = re.sub(r'\s*\(\d{4}-?\d{0,4}\)', '', author).strip()
                if ',' in clean:
                    parts = clean.split(',', 1)
                    if len(parts) == 2:
                        clean = f"{parts[1].strip()} {parts[0].strip()}"
                if clean:
                    clean_authors.append(clean)
            
            # Build abstract from subjects
            if subjects:
                abstract = f"Subjects: {', '.join(subjects[:5])}"
            else:
                abstract = "Project Gutenberg public domain book"
            
            # Build URLs
            full_text_url = f"https://gutenberg.org/files/{book_id}/{book_id}-0.txt"
            
            return Paper(
                title=title,
                authors=clean_authors or ["Unknown"],
                abstract=abstract,
                year=str(year) if year else "Unknown",
                source="Project Gutenberg",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=book.get('download_count'),
                influential_citation_count=None,
                content_type="book",
                isbn=None,
                publisher="Project Gutenberg",
                page_count=None,
                language=book.get('languages', ['en'])[0],
                subjects=subjects or None,
                download_formats=["TXT", "HTML", "EPUB"]
            )
            
        except Exception as e:
            logger.error(f"Error converting book to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return None
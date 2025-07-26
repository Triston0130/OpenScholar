"""
MIT OpenCourseWare Client

This client attempts to use Google Custom Search Engine if configured,
otherwise falls back to web scraping to find relevant courses and materials.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class MITOpenCourseWareClient:
    """Client for searching MIT OpenCourseWare materials"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://ocw.mit.edu"
        self.timeout = httpx.Timeout(30.0)
        self.api_key = api_key
        # CSE ID can come from environment or be configured separately
        self.cse_id = os.getenv('MIT_OCW_CSE_ID') or os.getenv('GOOGLE_CSE_ID')
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for open course materials using Google CSE if available,
        otherwise by scraping MIT OCW website
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing course materials
        """
        # Check if we have valid API key for Google CSE
        if not self.api_key or self.api_key == "00000000000000000000000000000000":
            logger.info(f"MIT OCW enhanced search skipped - requires valid Google API key (current: {self.api_key[:8] if self.api_key else 'None'}...)")
        elif not self.cse_id:
            logger.info("MIT OCW enhanced search skipped - Google CSE ID not configured")
        else:
            # Try to use Google CSE if we have valid credentials
            try:
                from .mit_ocw_cse import MITOpenCourseWareCSEClient
                cse_client = MITOpenCourseWareCSEClient(api_key=self.api_key, cse_id=self.cse_id)
                results = await cse_client.search(query, max_results)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Failed to use Google CSE, falling back to web scraping: {e}")
        
        # Fall back to web scraping
        papers = []
        
        try:
            # MIT OCW doesn't have a search API, but we can use their course listing
            # Let's try to get courses from their course finder
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try to search using their course finder page
                # They organize courses by department, so let's get some popular departments
                departments = [
                    '/courses/mathematics/',
                    '/courses/physics/',
                    '/courses/electrical-engineering-and-computer-science/',
                    '/courses/biology/',
                    '/courses/chemistry/',
                    '/courses/economics/'
                ]
                
                for dept_url in departments:
                    if len(papers) >= max_results:
                        break
                        
                    try:
                        full_url = urljoin(self.base_url, dept_url)
                        response = await client.get(full_url)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Find course cards/links
                            course_cards = soup.find_all('h3', class_='course-title')
                            if not course_cards:
                                # Try alternative structure
                                course_cards = soup.find_all('a', class_='course-link')
                            
                            for card in course_cards[:10]:  # Limit per department
                                if len(papers) >= max_results:
                                    break
                                    
                                # Extract course info
                                course_title = card.get_text(strip=True)
                                
                                # Check if query matches course title
                                if query.lower() in course_title.lower():
                                    # Get course link
                                    course_link = None
                                    if card.name == 'a':
                                        course_link = card.get('href')
                                    else:
                                        parent_a = card.find_parent('a')
                                        if parent_a:
                                            course_link = parent_a.get('href')
                                    
                                    if course_link:
                                        course_url = urljoin(self.base_url, course_link)
                                        
                                        # Create paper object
                                        paper = Paper(
                                            title=course_title,
                                            authors=['MIT Faculty'],
                                            abstract=f"MIT OpenCourseWare course: {course_title}. Free course materials including lecture notes, assignments, and exams.",
                                            year='2024',  # OCW courses are continuously updated
                                            source="MIT OpenCourseWare",
                                            full_text_url=course_url,
                                            journal="MIT OpenCourseWare",
                                            content_type='book',
                                            subjects=[dept_url.split('/')[-2].replace('-', ' ').title()],
                                            download_formats=['HTML', 'PDF']
                                        )
                                        papers.append(paper)
                                        
                    except Exception as e:
                        logger.error(f"Error scraping department {dept_url}: {str(e)}")
                        continue
                
                # If we didn't find enough results, try a more general approach
                if len(papers) < 5:
                    # Get some featured courses
                    logger.info("Trying to get featured MIT courses")
                    
                    # Common MIT courses that might match various queries
                    featured_courses = [
                        {
                            'title': '18.01 Single Variable Calculus',
                            'url': '/courses/18-01-single-variable-calculus-fall-2005/',
                            'subject': 'Mathematics'
                        },
                        {
                            'title': '6.001 Structure and Interpretation of Computer Programs',
                            'url': '/courses/6-001-structure-and-interpretation-of-computer-programs-spring-2005/',
                            'subject': 'Computer Science'
                        },
                        {
                            'title': '8.01 Physics I: Classical Mechanics',
                            'url': '/courses/8-01-physics-i-classical-mechanics-fall-2003/',
                            'subject': 'Physics'
                        },
                        {
                            'title': '7.012 Introduction to Biology',
                            'url': '/courses/7-012-introduction-to-biology-fall-2004/',
                            'subject': 'Biology'
                        },
                        {
                            'title': '14.01 Principles of Microeconomics',
                            'url': '/courses/14-01-principles-of-microeconomics-fall-2018/',
                            'subject': 'Economics'
                        }
                    ]
                    
                    for course in featured_courses:
                        if query.lower() in course['title'].lower() or query.lower() in course['subject'].lower():
                            paper = Paper(
                                title=course['title'],
                                authors=['MIT Faculty'],
                                abstract=f"MIT OpenCourseWare course: {course['title']}. This course provides free access to lecture notes, assignments, exams, and other educational materials.",
                                year='2024',
                                source="MIT OpenCourseWare",
                                full_text_url=urljoin(self.base_url, course['url']),
                                journal="MIT OpenCourseWare",
                                content_type='book',
                                subjects=[course['subject']],
                                download_formats=['HTML', 'PDF']
                            )
                            papers.append(paper)
                            
                            if len(papers) >= max_results:
                                break
                
                logger.info(f"Found {len(papers)} MIT OCW courses matching '{query}'")
                
        except Exception as e:
            logger.error(f"Error searching MIT OpenCourseWare: {str(e)}")
            
        return papers
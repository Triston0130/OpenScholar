"""
MIT OpenCourseWare Google Custom Search Engine Client

This client uses Google CSE to search MIT OCW for comprehensive results.
Requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID environment variables.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
from urllib.parse import quote
import re

logger = logging.getLogger(__name__)

class MITOpenCourseWareCSEClient:
    """Client for searching MIT OpenCourseWare using Google Custom Search Engine"""
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.timeout = httpx.Timeout(30.0)
    
    def _extract_course_info(self, title: str, snippet: str) -> Dict[str, Any]:
        """Extract course number, title, and other info from search results"""
        info = {
            'course_number': None,
            'clean_title': title,
            'department': 'MIT',
            'level': 'Undergraduate'
        }
        
        # Try to extract course number (e.g., "18.01", "6.001")
        course_match = re.search(r'(\d+\.\d+[A-Z]?)', title)
        if course_match:
            info['course_number'] = course_match.group(1)
            
        # Department mapping based on course number
        if info['course_number']:
            dept_num = info['course_number'].split('.')[0]
            dept_map = {
                '1': 'Civil and Environmental Engineering',
                '2': 'Mechanical Engineering',
                '3': 'Materials Science and Engineering',
                '4': 'Architecture',
                '5': 'Chemistry',
                '6': 'Electrical Engineering and Computer Science',
                '7': 'Biology',
                '8': 'Physics',
                '9': 'Brain and Cognitive Sciences',
                '10': 'Chemical Engineering',
                '11': 'Urban Studies and Planning',
                '12': 'Earth, Atmospheric, and Planetary Sciences',
                '14': 'Economics',
                '15': 'Management',
                '16': 'Aeronautics and Astronautics',
                '17': 'Political Science',
                '18': 'Mathematics',
                '20': 'Biological Engineering',
                '21': 'Humanities',
                '22': 'Nuclear Science and Engineering',
                '24': 'Linguistics and Philosophy'
            }
            info['department'] = dept_map.get(dept_num, 'MIT')
            
        # Check for graduate level indicators
        if 'graduate' in title.lower() or 'advanced' in title.lower():
            info['level'] = 'Graduate'
            
        return info
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for MIT OCW courses using Google Custom Search Engine
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing course materials
        """
        if not self.api_key or not self.cse_id:
            logger.error("Google CSE API key or CSE ID not configured.")
            return []
        
        papers = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Google CSE returns max 10 results per request
                # Make multiple requests if needed
                num_requests = min((max_results + 9) // 10, 10)  # Max 100 results total
                
                for page in range(num_requests):
                    start_index = page * 10 + 1
                    
                    params = {
                        'key': self.api_key,
                        'cx': self.cse_id,
                        'q': f'site:ocw.mit.edu {query}',
                        'start': start_index,
                        'num': min(10, max_results - len(papers))
                    }
                    
                    response = await client.get(self.base_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract results
                        items = data.get('items', [])
                        
                        for item in items:
                            if len(papers) >= max_results:
                                break
                                
                            title = item.get('title', '')
                            link = item.get('link', '')
                            snippet = item.get('snippet', '')
                            
                            # Skip non-course pages
                            if not '/courses/' in link:
                                continue
                                
                            # Extract course information
                            course_info = self._extract_course_info(title, snippet)
                            
                            # Clean up title - remove " | MIT OpenCourseWare" suffix
                            clean_title = title.replace(' | MIT OpenCourseWare', '')
                            clean_title = clean_title.replace(' | Free Online Course Materials', '')
                            
                            # Extract year from URL if possible
                            year_match = re.search(r'-(19|20)\d{2}[/-]', link)
                            year = year_match.group(0)[1:5] if year_match else '2024'
                            
                            paper = Paper(
                                title=clean_title,
                                authors=['MIT Faculty'],
                                abstract=snippet or f"MIT OpenCourseWare course: {clean_title}. Free course materials including lecture notes, assignments, and exams.",
                                year=year,
                                source="MIT OpenCourseWare",
                                full_text_url=link,
                                journal=f"MIT {course_info['department']}",
                                content_type='course',
                                subjects=[course_info['department'], course_info['level'], 'Open Education'],
                                download_formats=['HTML', 'PDF', 'Video'],
                                license='CC BY-NC-SA 4.0'
                            )
                            
                            # Add course number as additional metadata
                            if course_info['course_number']:
                                paper.doi = f"MIT-{course_info['course_number']}"
                                
                            papers.append(paper)
                    
                    elif response.status_code == 403:
                        logger.error("Google CSE API quota exceeded or invalid credentials")
                        break
                    else:
                        logger.error(f"Google CSE API error: {response.status_code}")
                        break
                        
                logger.info(f"MIT OCW CSE: Found {len(papers)} results for '{query}'")
                
        except Exception as e:
            logger.error(f"Error searching MIT OCW via Google CSE: {str(e)}")
            
        # CSE client doesn't fall back - that's handled by the main MIT OCW client
            
        return papers
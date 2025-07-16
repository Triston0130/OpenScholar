from typing import List, Optional, Dict, Any
import httpx
from app.models import Paper, SearchRequest
from .base import BaseAPIClient
import xml.etree.ElementTree as ET
import re

class PubMedClient(BaseAPIClient):
    """Client for PubMed/MEDLINE API - NIH's premier database"""
    
    def __init__(self):
        super().__init__(base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/")
        self.search_url = f"{self.base_url}esearch.fcgi"
        self.fetch_url = f"{self.base_url}efetch.fcgi"
    
    async def search(self, query: str, year_start: Optional[int] = None, 
                    year_end: Optional[int] = None, discipline: Optional[str] = None,
                    education_level: Optional[str] = None) -> List[Paper]:
        """Search PubMed for papers"""
        
        # Build query with filters
        search_query = self._build_query(query, discipline, education_level)
        
        # Add date range
        date_filter = ""
        if year_start and year_end:
            date_filter = f"{year_start}:{year_end}[pdat]"
        
        params = {
            "db": "pubmed",
            "term": f"{search_query} {date_filter}".strip(),
            "retmax": 100,
            "retmode": "json"
        }
        
        try:
            # First, search for IDs
            search_response = await self.client.get(self.search_url, params=params)
            search_data = search_response.json()
            
            if "esearchresult" not in search_data or not search_data["esearchresult"]["idlist"]:
                return []
            
            # Fetch details for the IDs
            ids = search_data["esearchresult"]["idlist"]
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml"
            }
            
            fetch_response = await self.client.get(self.fetch_url, params=fetch_params)
            return self._parse_response(fetch_response.text)
            
        except Exception as e:
            self.logger.error(f"PubMed search error: {str(e)}")
            return []
    
    def _build_query(self, query: str, discipline: Optional[str], education_level: Optional[str]) -> str:
        """Build PubMed query with education/child development focus"""
        
        # Start with base query
        terms = [query]
        
        # Add education/child development filters
        if discipline:
            if "education" in discipline.lower():
                terms.append("(education[MeSH] OR educational[Title/Abstract])")
            elif "child" in discipline.lower() or "development" in discipline.lower():
                terms.append("(child development[MeSH] OR child psychology[MeSH])")
        
        if education_level:
            if "early" in education_level.lower():
                terms.append("(early childhood[Title/Abstract] OR preschool[Title/Abstract])")
            elif "k-12" in education_level.lower():
                terms.append("(K-12[Title/Abstract] OR elementary[Title/Abstract] OR secondary education[Title/Abstract])")
            elif "higher" in education_level.lower():
                terms.append("(higher education[Title/Abstract] OR university[Title/Abstract])")
        
        return " AND ".join(terms)
    
    def _parse_response(self, xml_text: str) -> List[Paper]:
        """Parse PubMed XML response"""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract article details
                    medline = article.find(".//MedlineCitation")
                    if not medline:
                        continue
                    
                    # Title
                    title_elem = medline.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else ""
                    
                    # Authors
                    authors = []
                    for author in medline.findall(".//Author"):
                        last_name = author.find("LastName")
                        first_name = author.find("ForeName")
                        if last_name is not None:
                            name = last_name.text
                            if first_name is not None:
                                name = f"{name}, {first_name.text}"
                            authors.append(name)
                    
                    # Abstract
                    abstract_parts = []
                    for abstract in medline.findall(".//AbstractText"):
                        if abstract.text:
                            abstract_parts.append(abstract.text)
                    abstract = " ".join(abstract_parts)
                    
                    # Year
                    year = "2000"
                    pub_date = medline.find(".//PubDate")
                    if pub_date:
                        year_elem = pub_date.find("Year")
                        if year_elem is not None and year_elem.text:
                            year = year_elem.text
                    
                    # Journal
                    journal = ""
                    journal_elem = medline.find(".//Journal/Title")
                    if journal_elem is not None:
                        journal = journal_elem.text
                    
                    # PMID and DOI
                    pmid = medline.find(".//PMID").text
                    doi = None
                    for article_id in medline.findall(".//ArticleId"):
                        if article_id.get("IdType") == "doi":
                            doi = article_id.text
                    
                    # PMC URL if available
                    pmc_id = None
                    for article_id in article.findall(".//ArticleId"):
                        if article_id.get("IdType") == "pmc":
                            pmc_id = article_id.text
                    
                    full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    
                    paper = Paper(
                        title=title,
                        authors=authors if authors else ["Unknown"],
                        abstract=abstract if abstract else "No abstract available",
                        year=year,
                        source="PubMed",
                        full_text_url=full_text_url,
                        doi=doi,
                        journal=journal
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing PubMed article: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing PubMed XML: {str(e)}")
        
        return papers
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize PubMed XML response to Paper model - not used since we parse XML directly"""
        # This method is required by BaseAPIClient but not used in PubMed
        # since we parse the XML response directly in _parse_response
        return None
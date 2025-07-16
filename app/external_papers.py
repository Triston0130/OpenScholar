import requests
from typing import Dict, Any, Optional

class ExternalPaperFetcher:
    """Fetches paper metadata from external sources like Crossref and Unpaywall."""
    
    def __init__(self):
        self.crossref_base_url = "https://api.crossref.org/works"
        self.unpaywall_base_url = "https://api.unpaywall.org/v2"
        self.email = "contact@openscholar.org"  # Required for Unpaywall
        
    def fetch_paper_from_doi(self, doi: str) -> Dict[str, Any]:
        """
        Fetch paper metadata from DOI using Crossref and Unpaywall APIs.
        
        Args:
            doi: The DOI to fetch metadata for
            
        Returns:
            Dict containing paper metadata in OpenScholar format
        """
        # Clean up DOI
        clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()
        
        # Fetch from Crossref
        paper_data = self._fetch_from_crossref(clean_doi)
        
        # Try to get open access link from Unpaywall
        try:
            full_text_url = self._fetch_from_unpaywall(clean_doi)
            if full_text_url:
                paper_data["full_text_url"] = full_text_url
        except Exception as e:
            # If Unpaywall fails, continue without full text URL
            print(f"Unpaywall lookup failed for {clean_doi}: {e}")
            
        return paper_data
    
    def _fetch_from_crossref(self, doi: str) -> Dict[str, Any]:
        """Fetch metadata from Crossref API."""
        try:
            response = requests.get(f"{self.crossref_base_url}/{doi}")
            response.raise_for_status()
            
            data = response.json()
            work = data["message"]
            
            # Extract authors
            authors = []
            if "author" in work:
                for author in work["author"]:
                    given = author.get("given", "")
                    family = author.get("family", "")
                    full_name = f"{given} {family}".strip()
                    if full_name:
                        authors.append(full_name)
            
            if not authors:
                authors = ["Unknown Author"]
            
            # Extract publication date
            year = "Unknown"
            if "published" in work and "date-parts" in work["published"]:
                date_parts = work["published"]["date-parts"][0]
                if date_parts:
                    year = str(date_parts[0])
            elif "published-online" in work and "date-parts" in work["published-online"]:
                date_parts = work["published-online"]["date-parts"][0]
                if date_parts:
                    year = str(date_parts[0])
            
            # Format paper data
            paper = {
                "title": work.get("title", ["Unknown Title"])[0],
                "authors": authors,
                "abstract": work.get("abstract", "No abstract available"),
                "year": year,
                "journal": work.get("container-title", ["Unknown Journal"])[0] if work.get("container-title") else "Unknown Journal",
                "doi": doi,
                "full_text_url": None,  # Will be filled by Unpaywall if available
                "source": "External (Crossref)",
                "citation_count": work.get("is-referenced-by-count", 0),
                "influential_citation_count": None
            }
            
            return paper
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch from Crossref: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from Crossref: {e}")
    
    def _fetch_from_unpaywall(self, doi: str) -> Optional[str]:
        """Fetch open access URL from Unpaywall API."""
        try:
            response = requests.get(f"{self.unpaywall_base_url}/{doi}?email={self.email}")
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("is_oa") and data.get("best_oa_location"):
                location = data["best_oa_location"]
                # Prefer PDF URL, fallback to host URL
                return location.get("url_for_pdf") or location.get("host_url")
            
            return None
            
        except requests.exceptions.RequestException:
            # If Unpaywall fails, just return None
            return None
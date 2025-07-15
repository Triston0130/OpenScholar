import json
from typing import List, Tuple, Dict, Any
from app.models import Paper
from app.export.base import BaseExporter

class JSONExporter(BaseExporter):
    """JSON export functionality"""
    
    def export(self, papers: List[Paper]) -> Tuple[str, str]:
        """Export papers to JSON format"""
        
        # Convert papers to dictionary format
        papers_data = []
        for paper in papers:
            paper_dict = {
                "title": self.clean_text(paper.title),
                "authors": paper.authors,
                "abstract": self.clean_text(paper.abstract),
                "year": paper.year,
                "doi": paper.doi,
                "full_text_url": paper.full_text_url,
                "source": paper.source,
                "journal": self.clean_text(paper.journal or "")
            }
            papers_data.append(paper_dict)
        
        # Create export metadata
        export_data = {
            "export_metadata": {
                "exported_at": self.timestamp,
                "total_papers": len(papers),
                "format": "json",
                "source": "OpenScholar"
            },
            "papers": papers_data
        }
        
        # Convert to JSON with proper formatting
        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Generate filename
        filename = self.generate_filename("json")
        
        return json_content, filename
    
    def get_mime_type(self) -> str:
        """Return JSON MIME type"""
        return "application/json"
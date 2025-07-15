import csv
import io
from typing import List, Tuple
from app.models import Paper
from app.export.base import BaseExporter

class CSVExporter(BaseExporter):
    """CSV export functionality"""
    
    def export(self, papers: List[Paper]) -> Tuple[str, str]:
        """Export papers to CSV format"""
        
        # Create string buffer for CSV content
        output = io.StringIO()
        
        # Define CSV headers
        headers = [
            'title',
            'authors', 
            'abstract',
            'year',
            'doi',
            'full_text_url',
            'source',
            'journal'
        ]
        
        # Create CSV writer
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write headers
        writer.writerow(headers)
        
        # Write paper data
        for paper in papers:
            row = [
                self.clean_text(paper.title),
                self.format_authors(paper.authors),
                self.clean_text(paper.abstract),
                paper.year,
                paper.doi or "",
                paper.full_text_url or "",
                paper.source,
                self.clean_text(paper.journal or "")
            ]
            writer.writerow(row)
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        filename = self.generate_filename("csv")
        
        return csv_content, filename
    
    def get_mime_type(self) -> str:
        """Return CSV MIME type"""
        return "text/csv"
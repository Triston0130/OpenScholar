from typing import List, Tuple
from app.models import Paper, ExportRequest
from app.export.csv_export import CSVExporter
from app.export.json_export import JSONExporter
from app.export.bibtex_export import BibTeXExporter
import logging

logger = logging.getLogger(__name__)

class ExportService:
    """Service to handle paper exports in different formats"""
    
    def __init__(self):
        self.exporters = {
            "csv": CSVExporter(),
            "json": JSONExporter(),
            "bib": BibTeXExporter()
        }
    
    def export_papers(self, request: ExportRequest) -> Tuple[str, str, str]:
        """
        Export papers in the specified format
        Returns: (content, filename, mime_type)
        """
        
        if request.format not in self.exporters:
            raise ValueError(f"Unsupported export format: {request.format}")
        
        if not request.papers:
            raise ValueError("No papers provided for export")
        
        logger.info(f"Exporting {len(request.papers)} papers in {request.format} format")
        
        exporter = self.exporters[request.format]
        content, filename = exporter.export(request.papers)
        mime_type = exporter.get_mime_type()
        
        logger.info(f"Export completed: {filename}")
        
        return content, filename, mime_type
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return list(self.exporters.keys())
from abc import ABC, abstractmethod
from typing import List, Tuple
from app.models import Paper
from datetime import datetime

class BaseExporter(ABC):
    """Base class for all exporters"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
    
    @abstractmethod
    def export(self, papers: List[Paper]) -> Tuple[str, str]:
        """
        Export papers to the specified format
        Returns: (content, filename)
        """
        pass
    
    @abstractmethod
    def get_mime_type(self) -> str:
        """Return the MIME type for this export format"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean text for export (remove newlines, excess spaces, etc.)"""
        if not text:
            return ""
        # Replace newlines and multiple spaces with single spaces
        cleaned = " ".join(text.strip().split())
        return cleaned
    
    def format_authors(self, authors: List[str]) -> str:
        """Format authors list as a string"""
        if not authors:
            return ""
        return "; ".join(authors)
    
    def generate_filename(self, extension: str) -> str:
        """Generate filename with timestamp"""
        return f"openscholar_export_{self.timestamp}.{extension}"
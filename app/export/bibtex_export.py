import re
from typing import List, Tuple
from app.models import Paper
from app.export.base import BaseExporter

class BibTeXExporter(BaseExporter):
    """BibTeX export functionality"""
    
    def export(self, papers: List[Paper]) -> Tuple[str, str]:
        """Export papers to BibTeX format"""
        
        bib_entries = []
        
        for i, paper in enumerate(papers):
            # Generate citation key
            citation_key = self.generate_citation_key(paper, i)
            
            # Determine entry type (default to article)
            entry_type = self.determine_entry_type(paper)
            
            # Build BibTeX entry
            bib_entry = f"@{entry_type}{{{citation_key},\n"
            
            # Add required and optional fields
            if paper.title:
                bib_entry += f"  title={{{self.escape_bibtex(paper.title)}}},\n"
            
            if paper.authors:
                author_string = self.format_authors_bibtex(paper.authors)
                bib_entry += f"  author={{{author_string}}},\n"
            
            if paper.year:
                bib_entry += f"  year={{{paper.year}}},\n"
            
            if paper.journal:
                bib_entry += f"  journal={{{self.escape_bibtex(paper.journal)}}},\n"
            
            if paper.abstract:
                # Limit abstract length for BibTeX
                abstract = self.clean_text(paper.abstract)
                if len(abstract) > 500:
                    abstract = abstract[:497] + "..."
                bib_entry += f"  abstract={{{self.escape_bibtex(abstract)}}},\n"
            
            if paper.doi:
                bib_entry += f"  doi={{{paper.doi}}},\n"
            
            if paper.full_text_url:
                bib_entry += f"  url={{{paper.full_text_url}}},\n"
            
            # Add source as note
            bib_entry += f"  note={{Retrieved from {paper.source}}},\n"
            
            # Remove trailing comma and close entry
            bib_entry = bib_entry.rstrip(",\n") + "\n}\n"
            bib_entries.append(bib_entry)
        
        # Combine all entries
        bib_content = "\n".join(bib_entries)
        
        # Add header comment
        header = f"% BibTeX export from OpenScholar\n% Generated on {self.timestamp}\n% Total entries: {len(papers)}\n\n"
        bib_content = header + bib_content
        
        # Generate filename
        filename = self.generate_filename("bib")
        
        return bib_content, filename
    
    def generate_citation_key(self, paper: Paper, index: int) -> str:
        """Generate a citation key for the paper"""
        # Extract first author's last name
        first_author = ""
        if paper.authors and len(paper.authors) > 0:
            # Try to extract last name (assume format "Last, First" or "First Last")
            author = paper.authors[0]
            if "," in author:
                first_author = author.split(",")[0].strip()
            else:
                parts = author.split()
                if len(parts) > 1:
                    first_author = parts[-1]  # Last word as surname
                else:
                    first_author = parts[0] if parts else ""
        
        # Clean the author name (remove non-alphanumeric)
        first_author = re.sub(r'[^a-zA-Z]', '', first_author).lower()
        
        # If no author, use source
        if not first_author:
            first_author = paper.source.lower().replace(" ", "")
        
        # Combine with year and index for uniqueness
        year = paper.year if paper.year else "unknown"
        citation_key = f"{first_author}{year}_{index + 1}"
        
        return citation_key
    
    def determine_entry_type(self, paper: Paper) -> str:
        """Determine BibTeX entry type based on paper metadata"""
        # Default to article for most academic papers
        return "article"
    
    def format_authors_bibtex(self, authors: List[str]) -> str:
        """Format authors for BibTeX (using 'and' separator)"""
        if not authors:
            return ""
        return " and ".join(authors)
    
    def escape_bibtex(self, text: str) -> str:
        """Escape special characters for BibTeX"""
        if not text:
            return ""
        
        # Replace special characters
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        text = text.replace("&", "\\&")
        text = text.replace("%", "\\%")
        text = text.replace("$", "\\$")
        text = text.replace("#", "\\#")
        text = text.replace("_", "\\_")
        text = text.replace("^", "\\^{}")
        text = text.replace("~", "\\~{}")
        
        return text
    
    def get_mime_type(self) -> str:
        """Return BibTeX MIME type"""
        return "application/x-bibtex"
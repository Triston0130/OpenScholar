"""
Unified query translator for consistent search across diverse APIs
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class QueryComponents:
    """Parsed components of a search query"""
    keywords: List[str]
    phrases: List[str]  # Exact phrases in quotes
    must_include: List[str]  # Terms with +
    must_exclude: List[str]  # Terms with -
    field_searches: Dict[str, str]  # field:value pairs
    boolean_query: Optional[str] = None  # Original query with boolean operators


class QueryTranslator:
    """Translate user queries to API-specific formats"""
    
    # Discipline keyword expansions
    DISCIPLINE_EXPANSIONS = {
        "education": ["education", "educational", "teaching", "learning", "pedagogy", "instruction", "curriculum"],
        "psychology": ["psychology", "psychological", "cognitive", "behavioral", "mental"],
        "child development": ["child development", "childhood", "developmental", "pediatric", "youth"],
        "early childhood": ["early childhood", "preschool", "kindergarten", "toddler", "infant"],
        "computer science": ["computer science", "computing", "software", "algorithm", "programming"],
        "mathematics": ["mathematics", "mathematical", "math", "algebra", "calculus", "geometry"],
        "physics": ["physics", "physical", "quantum", "mechanics", "thermodynamics"],
        "biology": ["biology", "biological", "life sciences", "genetics", "molecular"],
        "statistics": ["statistics", "statistical", "data analysis", "probability", "regression"]
    }
    
    # Education level expansions
    EDUCATION_LEVEL_EXPANSIONS = {
        "early childhood": ["early childhood", "preschool", "pre-k", "kindergarten", "toddler"],
        "k-12": ["k-12", "elementary", "middle school", "high school", "secondary", "primary"],
        "higher ed": ["higher education", "university", "college", "undergraduate", "graduate", "postsecondary"]
    }
    
    # Publication type expansions
    PUBLICATION_TYPE_EXPANSIONS = {
        "journal article": ["journal", "article", "peer-reviewed", "publication"],
        "conference paper": ["conference", "proceedings", "symposium", "workshop"],
        "book": ["book", "textbook", "monograph", "chapter"],
        "thesis": ["thesis", "dissertation", "doctoral", "masters"],
        "report": ["report", "technical report", "white paper", "working paper"],
        "preprint": ["preprint", "arxiv", "biorxiv", "medrxiv", "ssrn"]
    }
    
    # Study type expansions
    STUDY_TYPE_EXPANSIONS = {
        "experimental": ["experimental", "experiment", "randomized", "controlled trial", "RCT"],
        "survey": ["survey", "questionnaire", "cross-sectional", "poll"],
        "review": ["review", "systematic review", "literature review", "synthesis"],
        "meta-analysis": ["meta-analysis", "meta analysis", "meta-analytic", "pooled analysis"],
        "case study": ["case study", "case report", "case series", "clinical case"],
        "longitudinal": ["longitudinal", "cohort", "prospective", "follow-up"],
        "qualitative": ["qualitative", "interview", "ethnographic", "phenomenological"]
    }
    
    def __init__(self):
        self.components = None
    
    def parse_query(self, query: str) -> QueryComponents:
        """Parse a query into its components"""
        components = QueryComponents(
            keywords=[],
            phrases=[],
            must_include=[],
            must_exclude=[],
            field_searches={}
        )
        
        # Extract quoted phrases first
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        components.phrases = phrases
        query_without_phrases = re.sub(phrase_pattern, '', query)
        
        # Extract field searches (e.g., author:smith)
        field_pattern = r'(\w+):(\S+)'
        for match in re.finditer(field_pattern, query_without_phrases):
            field, value = match.groups()
            components.field_searches[field] = value
        query_without_fields = re.sub(field_pattern, '', query_without_phrases)
        
        # Extract must include/exclude terms
        must_include_pattern = r'\+(\S+)'
        must_exclude_pattern = r'-(\S+)'
        
        for match in re.finditer(must_include_pattern, query_without_fields):
            components.must_include.append(match.group(1))
        
        for match in re.finditer(must_exclude_pattern, query_without_fields):
            components.must_exclude.append(match.group(1))
        
        # Remove special operators
        query_clean = re.sub(r'[+\-](\S+)', '', query_without_fields)
        
        # Check for boolean operators
        if any(op in query.upper() for op in [' AND ', ' OR ', ' NOT ']):
            components.boolean_query = query
        
        # Extract remaining keywords
        keywords = query_clean.split()
        components.keywords = [kw for kw in keywords if kw.lower() not in ['and', 'or', 'not']]
        
        self.components = components
        return components
    
    def expand_keywords(self, keywords: List[str], discipline: Optional[str] = None, 
                       education_level: Optional[str] = None,
                       publication_type: Optional[str] = None,
                       study_type: Optional[str] = None) -> List[str]:
        """Expand keywords with synonyms based on filters"""
        expanded = list(keywords)
        
        # Add discipline expansions
        if discipline and discipline.lower() in self.DISCIPLINE_EXPANSIONS:
            expanded.extend(self.DISCIPLINE_EXPANSIONS[discipline.lower()])
        
        # Add education level expansions
        if education_level and education_level.lower() in self.EDUCATION_LEVEL_EXPANSIONS:
            expanded.extend(self.EDUCATION_LEVEL_EXPANSIONS[education_level.lower()])
        
        # Add publication type expansions
        if publication_type and publication_type.lower() in self.PUBLICATION_TYPE_EXPANSIONS:
            expanded.extend(self.PUBLICATION_TYPE_EXPANSIONS[publication_type.lower()])
        
        # Add study type expansions
        if study_type and study_type.lower() in self.STUDY_TYPE_EXPANSIONS:
            expanded.extend(self.STUDY_TYPE_EXPANSIONS[study_type.lower()])
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for term in expanded:
            if term.lower() not in seen:
                seen.add(term.lower())
                result.append(term)
        
        return result
    
    def to_boolean_query(self, components: QueryComponents, operator: str = "AND") -> str:
        """Convert components to boolean query string"""
        parts = []
        
        # Add phrases
        for phrase in components.phrases:
            parts.append(f'"{phrase}"')
        
        # Add keywords
        parts.extend(components.keywords)
        
        # Add must include with AND
        for term in components.must_include:
            parts.append(term)
        
        # Join with specified operator
        query = f" {operator} ".join(parts)
        
        # Add exclusions
        for term in components.must_exclude:
            query += f" NOT {term}"
        
        return query.strip()
    
    def to_pubmed_query(self, query: str, discipline: Optional[str] = None,
                       education_level: Optional[str] = None, 
                       year_start: Optional[int] = None, year_end: Optional[int] = None) -> str:
        """Convert to PubMed query format with MeSH terms"""
        components = self.parse_query(query)
        query_parts = []
        
        # Main query with field specifiers
        if components.phrases:
            for phrase in components.phrases:
                query_parts.append(f'"{phrase}"[Title/Abstract]')
        
        if components.keywords:
            keyword_str = " ".join(components.keywords)
            query_parts.append(f'({keyword_str})[Title/Abstract]')
        
        # Add discipline with MeSH
        if discipline:
            discipline_map = {
                "education": "education[MeSH] OR educational[Title/Abstract]",
                "psychology": "psychology[MeSH] OR psychological[Title/Abstract]",
                "child development": "child development[MeSH] OR childhood[Title/Abstract]",
                "biology": "biology[MeSH] OR biological[Title/Abstract]"
            }
            if discipline.lower() in discipline_map:
                query_parts.append(f"({discipline_map[discipline.lower()]})")
        
        # Add education level
        if education_level:
            level_map = {
                "early childhood": "(early childhood[Title/Abstract] OR preschool[Title/Abstract])",
                "k-12": "(K-12[Title/Abstract] OR elementary[Title/Abstract] OR secondary[Title/Abstract])",
                "higher ed": "(higher education[Title/Abstract] OR university[Title/Abstract])"
            }
            if education_level.lower() in level_map:
                query_parts.append(level_map[education_level.lower()])
        
        # Add date range
        if year_start and year_end:
            query_parts.append(f"{year_start}:{year_end}[pdat]")
        
        # Add exclusions
        for term in components.must_exclude:
            query_parts.append(f"NOT {term}[Title/Abstract]")
        
        return " AND ".join(query_parts)
    
    def to_arxiv_query(self, query: str, discipline: Optional[str] = None) -> str:
        """Convert to arXiv query format with categories"""
        components = self.parse_query(query)
        
        # Map disciplines to arXiv categories
        category_map = {
            "computer science": ["cs.*"],
            "mathematics": ["math.*"],
            "physics": ["physics.*", "quant-ph", "hep-*"],
            "statistics": ["stat.*"],
            "biology": ["q-bio.*"]
        }
        
        query_str = self.to_boolean_query(components)
        
        if discipline and discipline.lower() in category_map:
            categories = category_map[discipline.lower()]
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            return f"{query_str} AND ({cat_query})"
        
        return query_str
    
    def to_semantic_scholar_query(self, query: str, discipline: Optional[str] = None,
                                 education_level: Optional[str] = None,
                                 publication_type: Optional[str] = None,
                                 study_type: Optional[str] = None) -> str:
        """Convert to Semantic Scholar format with keyword expansion"""
        components = self.parse_query(query)
        
        # Expand keywords based on all filters
        all_keywords = components.keywords + [phrase for phrase in components.phrases]
        expanded = self.expand_keywords(all_keywords, discipline, education_level, publication_type, study_type)
        
        return " ".join(expanded)
    
    def to_plos_query(self, query: str, discipline: Optional[str] = None,
                     year_start: Optional[int] = None, year_end: Optional[int] = None) -> str:
        """Convert to PLOS query format"""
        components = self.parse_query(query)
        query_parts = []
        
        # Main search
        main_query = self.to_boolean_query(components)
        query_parts.append(f'everything:"{main_query}"')
        
        # Add date range
        if year_start and year_end:
            query_parts.append(
                f'publication_date:[{year_start}-01-01T00:00:00Z TO {year_end}-12-31T23:59:59Z]'
            )
        
        # Add discipline
        if discipline:
            # Map to PLOS subject categories
            subject_map = {
                "biology": "Biology and life sciences",
                "medicine": "Medicine and health sciences",
                "computer science": "Computer and information sciences",
                "physics": "Physical sciences",
                "mathematics": "Mathematics"
            }
            if discipline.lower() in subject_map:
                query_parts.append(f'subject:"{subject_map[discipline.lower()]}"')
        
        return " AND ".join(query_parts)
    
    def to_base_query(self, query: str, discipline: Optional[str] = None,
                     year_start: Optional[int] = None, year_end: Optional[int] = None) -> str:
        """Convert to BASE query format (Lucene syntax)"""
        components = self.parse_query(query)
        query_parts = []
        
        # Main query
        main_query = self.to_boolean_query(components)
        query_parts.append(main_query)
        
        # Add year filter
        if year_start and year_end:
            query_parts.append(f"dcyear:[{year_start} TO {year_end}]")
        
        # Add discipline
        if discipline:
            query_parts.append(f'dcsubject:"{discipline}"')
        
        return " AND ".join(query_parts)
    
    def to_crossref_query(self, query: str, discipline: Optional[str] = None) -> str:
        """Convert to Crossref format with discipline expansion"""
        components = self.parse_query(query)
        
        # Get base query
        base_query = self.to_boolean_query(components)
        
        # Add discipline expansion
        if discipline and discipline.lower() in self.DISCIPLINE_EXPANSIONS:
            expansions = self.DISCIPLINE_EXPANSIONS[discipline.lower()]
            discipline_query = " OR ".join(expansions)
            return f"{base_query} AND ({discipline_query})"
        
        return base_query
    
    def to_simple_query(self, query: str, discipline: Optional[str] = None,
                       education_level: Optional[str] = None,
                       publication_type: Optional[str] = None,
                       study_type: Optional[str] = None) -> str:
        """Convert to simple concatenated query for APIs with basic search"""
        # For simple APIs, use keyword expansion
        components = self.parse_query(query)
        all_keywords = components.keywords + [phrase for phrase in components.phrases]
        expanded = self.expand_keywords(all_keywords, discipline, education_level, publication_type, study_type)
        
        return " ".join(expanded)
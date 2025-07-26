"""
BM25 relevance scoring for search results
"""
import math
from typing import List, Dict, Any
from collections import Counter
import re
from app.models import Paper


class BM25Scorer:
    """BM25 algorithm for relevance scoring"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 scorer
        k1: controls term frequency saturation (typically 1.2-2.0)
        b: controls length normalization (0-1)
        """
        self.k1 = k1
        self.b = b
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = {}
        self.total_docs = 0
    
    def fit(self, papers: List[Paper]):
        """Fit the BM25 model on the corpus of papers"""
        if not papers:
            return
            
        self.total_docs = len(papers)
        self.doc_lengths = []
        term_doc_counts = Counter()
        
        for paper in papers:
            # Combine title, abstract, and journal for scoring
            doc_text = f"{paper.title} {paper.abstract} {paper.journal or ''}"
            terms = self._tokenize(doc_text)
            self.doc_lengths.append(len(terms))
            
            # Count unique terms per document
            unique_terms = set(terms)
            for term in unique_terms:
                term_doc_counts[term] += 1
        
        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1
        
        # Calculate IDF for each term
        self.doc_freqs = {
            term: math.log((self.total_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in term_doc_counts.items()
        }
    
    def score(self, query: str, paper: Paper, index: int) -> float:
        """Calculate BM25 score for a paper given a query"""
        if not query or not paper:
            return 0.0
            
        query_terms = self._tokenize(query.lower())
        if not query_terms:
            return 0.0
        
        # Combine paper fields with weight for title
        doc_text = f"{paper.title} {paper.title} {paper.abstract} {paper.journal or ''}"
        doc_terms = self._tokenize(doc_text.lower())
        doc_length = self.doc_lengths[index] if index < len(self.doc_lengths) else len(doc_terms)
        
        score = 0.0
        term_freqs = Counter(doc_terms)
        
        for term in query_terms:
            if term in self.doc_freqs:
                tf = term_freqs.get(term, 0)
                idf = self.doc_freqs[term]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                score += idf * (numerator / denominator)
        
        # Boost score for exact phrase matches in title
        if query.lower() in paper.title.lower():
            score *= 2.0
        
        # Additional boost if ALL query terms appear in title+abstract
        query_words = set(query.lower().split())
        title_words = set(paper.title.lower().split()) if paper.title else set()
        abstract_words = set(paper.abstract.lower().split()) if paper.abstract else set()
        paper_words = title_words | abstract_words
        
        # Check if all query words appear
        if query_words and query_words.issubset(paper_words):
            score *= 1.5  # Boost for containing all terms
        
        # Boost for recent papers (slight recency bias)
        try:
            year = int(paper.year)
            if year >= 2020:
                score *= 1.1
            elif year >= 2015:
                score *= 1.05
        except:
            pass
        
        # Citation boost for highly cited papers (helps older papers with high impact)
        if paper.citation_count and paper.citation_count > 0:
            # Logarithmic boost to prevent overwhelming dominance of highly cited papers
            citation_boost = 1 + (math.log(paper.citation_count + 1) / 10)
            score *= citation_boost
        
        # Additional boost for influential citations
        if paper.influential_citation_count and paper.influential_citation_count > 0:
            influential_boost = 1 + (paper.influential_citation_count / 20)  # Smaller boost
            score *= influential_boost
        
        return score
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - splits on non-word characters and filters short words"""
        text = text.lower()
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        # Split on non-word characters
        tokens = re.findall(r'\b\w+\b', text)
        # Filter out very short words (but keep important 2-letter words) and numbers
        # Keep words like: to, in, on, of, is, it, etc. as they might be important
        return [token for token in tokens if (len(token) > 1 or token in ['a', 'i']) and not token.isdigit()]


def calculate_relevance_scores(papers: List[Paper], query: str) -> List[Dict[str, Any]]:
    """
    Calculate relevance scores for papers and return them with scores
    """
    if not papers:
        return []
    
    # Initialize and fit BM25 model
    scorer = BM25Scorer()
    scorer.fit(papers)
    
    # Calculate scores for each paper
    scored_papers = []
    for i, paper in enumerate(papers):
        score = scorer.score(query, paper, i)
        scored_papers.append({
            'paper': paper,
            'relevance_score': round(score, 2),
            'original_index': i
        })
    
    return scored_papers


def sort_papers(papers: List[Paper], query: str, sort_by: str = 'relevance') -> List[Paper]:
    """
    Sort papers by different criteria
    
    Args:
        papers: List of papers to sort
        query: Search query for relevance scoring
        sort_by: One of 'relevance', 'newest', 'oldest', 'citations'
    
    Returns:
        Sorted list of papers
    """
    if sort_by == 'relevance':
        # Calculate relevance scores and sort by them
        scored_papers = calculate_relevance_scores(papers, query)
        scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        return [sp['paper'] for sp in scored_papers]
    
    elif sort_by == 'newest':
        # Sort by year, newest first
        def get_year(paper):
            try:
                return int(paper.year)
            except:
                return 0
        return sorted(papers, key=get_year, reverse=True)
    
    elif sort_by == 'oldest':
        # Sort by year, oldest first
        def get_year(paper):
            try:
                return int(paper.year)
            except:
                return 9999
        return sorted(papers, key=get_year)
    
    elif sort_by == 'citations':
        # Sort by citation count, then influential citations, highest first
        def get_citations(paper):
            citation_count = paper.citation_count if paper.citation_count is not None else 0
            influential_count = paper.influential_citation_count if paper.influential_citation_count is not None else 0
            return (citation_count, influential_count)
        return sorted(papers, key=get_citations, reverse=True)
    
    else:
        # Default: return as-is
        return papers
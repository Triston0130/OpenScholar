"""
Smart search optimization with adaptive result limiting and quality scoring
"""
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import math
import logging
from app.models import Paper
from app.utils.relevance import BM25Scorer, calculate_relevance_scores

logger = logging.getLogger(__name__)


class SearchOptimizer:
    """Optimizes search results across multiple sources"""
    
    # Source quality weights based on academic reputation and data quality
    SOURCE_WEIGHTS = {
        "PubMed": 1.0,          # Gold standard for medical/life sciences
        "Semantic Scholar": 0.95,  # AI-enhanced with citation analysis
        "arXiv": 0.9,           # High-quality preprints
        "PubMed Central": 0.9,   # Open access medical literature
        "PLOS": 0.85,           # Peer-reviewed open access
        "Crossref": 0.85,       # Comprehensive metadata
        "CORE": 0.8,            # Large aggregator
        "Europe PMC": 0.8,      # European medical literature
        "DOAJ": 0.75,           # Directory of OA journals
        "BioMed Central": 0.75,  # Biomedical open access
        "ERIC": 0.75,           # Education-specific
        "BASE": 0.7,            # Academic search engine
        "Unpaywall": 0.7,       # Free versions finder
        "DOAB": 0.65,           # Open access books
        "Google Books": 0.6,     # Mix of academic and popular
        "Internet Archive": 0.55, # Varied quality
        "Project Gutenberg": 0.5, # Public domain (older)
        "Open Library": 0.5,     # Book metadata
        "OpenStax": 0.6,        # Textbooks
        "OAPEN": 0.65,          # Academic books
        "BHL": 0.6,             # Biodiversity heritage
        "NLM Bookshelf": 0.7,   # Medical textbooks
        "Google Search": 0.7,   # PDF search across web
    }
    
    # Minimum quality thresholds for including papers
    MIN_RELEVANCE_SCORE = 0.5  # Increased for better quality
    MIN_ABSTRACT_LENGTH = 50  # Require decent abstracts
    
    def __init__(self):
        self.scorer = BM25Scorer()
    
    def optimize_search_results(self, results_by_source: Dict[str, List[Paper]], 
                              query: str, 
                              target_per_source: int = 50,
                              max_total: int = 1000) -> Tuple[List[Paper], Dict[str, int]]:
        """
        Optimize search results with smart limiting and quality filtering
        
        Args:
            results_by_source: Dictionary mapping source names to paper lists
            query: Original search query
            target_per_source: Target number of papers per source (adaptive)
            max_total: Maximum total papers to process
            
        Returns:
            Tuple of (optimized_papers, source_counts)
        """
        # Stage 1: Quality filtering and per-source relevance scoring
        scored_by_source = {}
        source_counts = {}
        
        # Handle empty results gracefully
        if not results_by_source or all(not papers for papers in results_by_source.values()):
            return [], {}
        
        for source, papers in results_by_source.items():
            if not papers:
                source_counts[source] = 0
                continue
                
            # Filter low-quality papers (more lenient for Google Search)
            quality_papers = self._filter_quality_papers(papers, source)
            
            # Score papers within this source
            if quality_papers:
                try:
                    self.scorer.fit(quality_papers)
                    scored_papers = []
                    
                    for i, paper in enumerate(quality_papers):
                        score = self.scorer.score(query, paper, i)
                        
                        # Apply source weight
                        source_weight = self.SOURCE_WEIGHTS.get(source, 0.5)
                        weighted_score = score * source_weight
                        
                        scored_papers.append({
                            'paper': paper,
                            'relevance_score': score,
                            'weighted_score': weighted_score,
                            'source': source,
                            'source_weight': source_weight
                        })
                    
                    # Sort by relevance within source
                    scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                    # Adaptive limiting based on result quality
                    limit = self._adaptive_limit(scored_papers, target_per_source, source)
                    scored_by_source[source] = scored_papers[:limit]
                    source_counts[source] = len(scored_papers[:limit])
                except Exception as e:
                    # If scoring fails, just take the papers as-is
                    logger.error(f"Scoring failed for {source}: {e}")
                    simple_papers = [{'paper': p, 'relevance_score': 1.0, 'weighted_score': 1.0, 
                                    'source': source, 'source_weight': self.SOURCE_WEIGHTS.get(source, 0.5)} 
                                   for p in quality_papers[:target_per_source]]
                    scored_by_source[source] = simple_papers
                    source_counts[source] = len(simple_papers)
            else:
                source_counts[source] = 0
        
        # Stage 2: Global relevance ranking
        all_scored_papers = []
        for source_papers in scored_by_source.values():
            all_scored_papers.extend(source_papers)
        
        # Re-score globally for better cross-source comparison
        if all_scored_papers:
            # Fit BM25 on combined corpus
            all_papers = [sp['paper'] for sp in all_scored_papers]
            self.scorer.fit(all_papers)
            
            # Re-score with global context
            for i, scored_paper in enumerate(all_scored_papers):
                paper = scored_paper['paper']
                global_score = self.scorer.score(query, paper, i)
                
                # Combine local and global scores with source weight
                source_weight = scored_paper['source_weight']
                local_score = scored_paper['relevance_score']
                
                # Weighted combination: 60% global, 40% local
                combined_score = (0.6 * global_score + 0.4 * local_score) * source_weight
                
                scored_paper['final_score'] = combined_score
                scored_paper['global_score'] = global_score
        
        # Sort by final score
        all_scored_papers.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Extract papers up to max_total
        final_papers = [sp['paper'] for sp in all_scored_papers[:max_total]]
        
        return final_papers, source_counts
    
    def _filter_quality_papers(self, papers: List[Paper], source: str = None) -> List[Paper]:
        """Filter out low-quality papers (more lenient for Google Search)"""
        quality_papers = []
        is_google_search = source == "Google Search"
        
        for paper in papers:
            # Must have title
            if not paper.title or len(paper.title.strip()) < 5:  # Reduced from 10
                continue
                
            # Don't filter by abstract - some papers don't have abstracts but are still valid
            # Only exclude if it's completely missing essential information
            # Abstract is optional - many valid papers don't have abstracts
                
            # Must have authors (unless it's a book or Google Search)
            if not is_google_search and paper.content_type == "paper" and (not paper.authors or 
                len(paper.authors) == 0 or 
                (len(paper.authors) == 1 and paper.authors[0].lower() in ['anonymous', 'unknown', ''])):
                continue
                
            # Must have year (more lenient for Google Search)
            if not is_google_search and (not paper.year or paper.year == "Unknown"):
                continue
                
            # Filter out obviously non-academic content (be more careful)
            title_lower = paper.title.lower()
            # Only filter if title is EXACTLY these terms, not if they're part of a longer title
            if title_lower in ['test', 'untitled', 'document', 'page', 'sample']:
                continue
                
            quality_papers.append(paper)
        
        return quality_papers
    
    def _adaptive_limit(self, scored_papers: List[Dict], target: int, source: str) -> int:
        """
        Adaptively determine how many papers to keep from a source
        based on result quality distribution
        """
        if not scored_papers:
            return 0
            
        # Calculate quality metrics
        scores = [sp['relevance_score'] for sp in scored_papers]
        
        if not scores:
            return 0
            
        # Find quality cutoff points
        avg_score = sum(scores) / len(scores)
        
        # Count high-quality papers (score > average)
        high_quality_count = sum(1 for s in scores if s > avg_score)
        
        # For high-reputation sources, be more generous
        source_weight = self.SOURCE_WEIGHTS.get(source, 0.5)
        
        if source_weight >= 0.9:
            # Premium sources: be generous
            if high_quality_count > target:
                return min(int(target * 2.0), len(scored_papers))  # Increased from 1.5x
            else:
                return min(int(target * 1.5), len(scored_papers))  # At least 1.5x
        elif source_weight >= 0.7:
            # Good sources: take most results
            return min(int(target * 1.2), max(high_quality_count, 50))  # Increased from 20
        else:
            # Lower quality sources: still take a good amount
            return min(target, max(high_quality_count, 30))  # Increased from 10
    
    def get_result_metrics(self, papers: List[Paper], scored_papers: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics about the search results"""
        if not papers:
            return {}
            
        # Source distribution
        source_counts = defaultdict(int)
        for sp in scored_papers:
            source_counts[sp['source']] += 1
            
        # Score distribution
        scores = [sp.get('final_score', 0) for sp in scored_papers]
        
        # Year distribution
        year_counts = defaultdict(int)
        for paper in papers:
            try:
                year = int(paper.year)
                year_counts[year] += 1
            except:
                pass
                
        # Citation statistics
        citations = [p.citation_count for p in papers if p.citation_count is not None]
        
        metrics = {
            'total_results': len(papers),
            'sources_used': len(source_counts),
            'source_distribution': dict(source_counts),
            'avg_relevance_score': sum(scores) / len(scores) if scores else 0,
            'max_relevance_score': max(scores) if scores else 0,
            'min_relevance_score': min(scores) if scores else 0,
            'year_range': [min(year_counts.keys()), max(year_counts.keys())] if year_counts else None,
            'avg_citations': sum(citations) / len(citations) if citations else None,
            'highly_cited_count': sum(1 for c in citations if c > 100)
        }
        
        return metrics
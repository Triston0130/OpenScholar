"""
Advanced Learning-to-Rank System for Academic Search
Implements state-of-the-art IR techniques for scholarly literature ranking
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import math
import re
from datetime import datetime
import logging
from dataclasses import dataclass
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os

from app.models import Paper

logger = logging.getLogger(__name__)


@dataclass
class RankingFeatures:
    """Features extracted for ranking"""
    # Text relevance features
    bm25_title: float
    bm25_abstract: float
    bm25_combined: float
    tfidf_cosine_title: float
    tfidf_cosine_abstract: float
    
    # Exact and phrase matching
    exact_title_match: bool
    exact_abstract_match: bool
    phrase_match_count: int
    query_coverage_title: float
    query_coverage_abstract: float
    
    # Field-specific features
    title_length: int
    abstract_length: int
    title_query_overlap: float
    abstract_query_overlap: float
    
    # Academic impact features
    citation_count: int
    citation_velocity: float  # Citations per year
    influential_citation_count: int
    citation_percentile: float
    h_index_estimate: float
    
    # Temporal features
    years_since_publication: float
    is_recent_2_years: bool
    is_recent_5_years: bool
    publication_year: int
    temporal_relevance_score: float
    
    # Source quality features
    source_reputation_score: float
    is_peer_reviewed: bool
    journal_impact_factor: float
    source_type: str  # journal, conference, preprint, book
    
    # Author features
    author_count: int
    has_known_authors: bool
    author_reputation_score: float
    
    # Query-document features
    query_length: int
    query_specificity: float
    document_length: int
    language_model_score: float
    
    # Semantic features
    embedding_similarity: float
    topic_relevance: float
    discipline_match: bool
    
    # User interaction features (if available)
    click_probability: float
    dwell_time_estimate: float
    
    # Diversity features
    novelty_score: float
    topical_diversity: float


class AdvancedRanker:
    """
    State-of-the-art ranking system using machine learning and IR best practices
    """
    
    # Enhanced source reputation scores based on academic impact
    SOURCE_REPUTATION = {
        "PubMed": 1.0,
        "Nature": 0.98,
        "Science": 0.98,
        "Cell": 0.96,
        "PNAS": 0.95,
        "Semantic Scholar": 0.93,
        "IEEE": 0.92,
        "ACM": 0.92,
        "arXiv": 0.90,
        "PLOS": 0.88,
        "PubMed Central": 0.88,
        "Elsevier": 0.85,
        "Springer": 0.85,
        "Wiley": 0.85,
        "Crossref": 0.83,
        "CORE": 0.80,
        "Europe PMC": 0.80,
        "DOAJ": 0.75,
        "BioMed Central": 0.75,
        "ERIC": 0.73,
        "BASE": 0.70,
        "Unpaywall": 0.68,
        "DOAB": 0.65,
        "Google Books": 0.60,
        "Internet Archive": 0.55,
        "Project Gutenberg": 0.50,
    }
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_path = model_path or "ranking_model.pkl"
        
        # BM25 parameters optimized for academic text
        self.k1 = 1.2
        self.b = 0.75
        self.k3 = 500  # For query term weighting
        
        # Initialize components
        self._initialize_components()
        
        # Load pre-trained model if available
        if os.path.exists(self.model_path):
            self._load_model()
        else:
            # Initialize with a basic model
            self._initialize_default_model()
    
    def _initialize_components(self):
        """Initialize ranking components"""
        self.stop_words = set([
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'the', 'this',
            'these', 'those', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'may', 'might', 'must', 'can', 'using', 'used', 'use'
        ])
        
        # Academic term weights for domain-specific boosting
        self.academic_terms = {
            'study': 1.2, 'research': 1.2, 'analysis': 1.1, 'method': 1.1,
            'results': 1.1, 'conclusion': 1.0, 'hypothesis': 1.2, 'theory': 1.2,
            'experiment': 1.1, 'data': 1.0, 'evidence': 1.1, 'findings': 1.1,
            'review': 1.0, 'meta-analysis': 1.3, 'systematic': 1.2, 'clinical': 1.1,
            'trial': 1.1, 'randomized': 1.2, 'controlled': 1.1, 'cohort': 1.1,
            'survey': 1.0, 'qualitative': 1.0, 'quantitative': 1.0, 'statistical': 1.1
        }
        
    def _initialize_default_model(self):
        """Initialize a default ranking model with hand-tuned weights"""
        # This serves as a fallback when no trained model is available
        self.model = None  # Will use weighted linear combination instead
        
        # Hand-tuned feature weights based on IR research
        self.feature_weights = {
            'bm25_combined': 0.25,
            'bm25_title': 0.15,
            'exact_title_match': 0.20,
            'phrase_match_count': 0.10,
            'citation_percentile': 0.08,
            'temporal_relevance_score': 0.05,
            'source_reputation_score': 0.05,
            'query_coverage_title': 0.07,
            'embedding_similarity': 0.05
        }
    
    def rank_papers(self, papers: List[Paper], query: str, 
                   context: Optional[Dict[str, Any]] = None) -> List[Tuple[Paper, float, Dict[str, Any]]]:
        """
        Rank papers using advanced ML-based ranking
        
        Returns:
            List of (paper, score, explanation) tuples
        """
        if not papers:
            return []
        
        # Extract features for all papers
        features_list = []
        papers_with_features = []
        
        # Pre-compute corpus statistics
        corpus_stats = self._compute_corpus_statistics(papers)
        query_features = self._analyze_query(query)
        
        for i, paper in enumerate(papers):
            try:
                features = self._extract_features(
                    paper, query, i, corpus_stats, query_features, context
                )
                features_list.append(features)
                papers_with_features.append((paper, features))
            except Exception as e:
                logger.error(f"Feature extraction failed for paper {i}: {e}")
                # Create minimal features
                features = self._get_minimal_features()
                features_list.append(features)
                papers_with_features.append((paper, features))
        
        # Score papers
        scores = self._score_papers(features_list)
        
        # Create explanations
        results = []
        for i, ((paper, features), score) in enumerate(zip(papers_with_features, scores)):
            explanation = self._generate_explanation(features, score, query)
            results.append((paper, score, explanation))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply diversity re-ranking if needed
        if context and context.get('enable_diversity', True):
            results = self._diversify_results(results, query)
        
        return results
    
    def _extract_features(self, paper: Paper, query: str, index: int,
                         corpus_stats: Dict, query_features: Dict,
                         context: Optional[Dict] = None) -> RankingFeatures:
        """Extract all ranking features for a paper"""
        
        # Text processing with null safety
        query_terms = self._tokenize(query.lower())
        title_terms = self._tokenize(paper.title.lower() if paper.title else "")
        abstract_terms = self._tokenize(paper.abstract.lower() if paper.abstract else "")
        
        # BM25 scores
        bm25_title = self._compute_bm25(
            query_terms, title_terms, 
            corpus_stats['avg_title_length'],
            corpus_stats['title_term_df']
        )
        
        bm25_abstract = self._compute_bm25(
            query_terms, abstract_terms,
            corpus_stats['avg_abstract_length'],
            corpus_stats['abstract_term_df']
        )
        
        bm25_combined = 0.7 * bm25_title + 0.3 * bm25_abstract
        
        # Exact and phrase matching with null safety
        exact_title_match = paper.title and query.lower() in paper.title.lower()
        exact_abstract_match = paper.abstract and query.lower() in paper.abstract.lower()
        phrase_matches = self._count_phrase_matches(query, paper)
        
        # Query coverage
        query_coverage_title = self._compute_query_coverage(query_terms, title_terms)
        query_coverage_abstract = self._compute_query_coverage(query_terms, abstract_terms)
        
        # Citation features
        citation_count = paper.citation_count or 0
        influential_count = paper.influential_citation_count or 0
        
        # Compute citation velocity
        try:
            paper_year = int(paper.year)
            years_old = max(1, datetime.now().year - paper_year)
            citation_velocity = citation_count / years_old
        except:
            years_old = 5  # Default
            citation_velocity = citation_count / 5
        
        # Citation percentile (simplified - in production, use actual distribution)
        citation_percentile = self._estimate_citation_percentile(
            citation_count, paper_year if 'paper_year' in locals() else None
        )
        
        # Temporal features
        current_year = datetime.now().year
        try:
            pub_year = int(paper.year)
            years_since_pub = current_year - pub_year
            is_recent_2 = years_since_pub <= 2
            is_recent_5 = years_since_pub <= 5
        except:
            pub_year = current_year - 5
            years_since_pub = 5
            is_recent_2 = False
            is_recent_5 = True
        
        # Temporal relevance (newer papers get slight boost, but not overwhelming)
        temporal_relevance = self._compute_temporal_relevance(years_since_pub, citation_count)
        
        # Source features
        source_reputation = self._get_source_reputation(paper)
        is_peer_reviewed = self._is_peer_reviewed(paper)
        
        # Author features
        author_count = len(paper.authors) if paper.authors else 0
        has_known_authors = author_count > 0 and not self._has_anonymous_authors(paper)
        
        # Document features
        title_length = len(title_terms)
        abstract_length = len(abstract_terms)
        doc_length = title_length + abstract_length
        
        # Handle papers without abstracts gracefully
        if abstract_length == 0 and paper.content_type != "book":
            # For papers without abstracts, use title more heavily
            abstract_length = title_length  # Prevent division by zero in calculations
        
        # Semantic similarity (simplified - in production, use embeddings)
        embedding_similarity = self._compute_semantic_similarity(query, paper)
        
        # Topic relevance
        topic_relevance = self._compute_topic_relevance(query_features, paper)
        
        # Create features object
        return RankingFeatures(
            bm25_title=bm25_title,
            bm25_abstract=bm25_abstract,
            bm25_combined=bm25_combined,
            tfidf_cosine_title=0.0,  # Placeholder
            tfidf_cosine_abstract=0.0,  # Placeholder
            exact_title_match=exact_title_match,
            exact_abstract_match=exact_abstract_match,
            phrase_match_count=phrase_matches,
            query_coverage_title=query_coverage_title,
            query_coverage_abstract=query_coverage_abstract,
            title_length=title_length,
            abstract_length=abstract_length,
            title_query_overlap=len(set(query_terms) & set(title_terms)) / max(len(query_terms), 1),
            abstract_query_overlap=len(set(query_terms) & set(abstract_terms)) / max(len(query_terms), 1),
            citation_count=citation_count,
            citation_velocity=citation_velocity,
            influential_citation_count=influential_count,
            citation_percentile=citation_percentile,
            h_index_estimate=math.sqrt(citation_count),  # Simplified
            years_since_publication=years_since_pub,
            is_recent_2_years=is_recent_2,
            is_recent_5_years=is_recent_5,
            publication_year=pub_year,
            temporal_relevance_score=temporal_relevance,
            source_reputation_score=source_reputation,
            is_peer_reviewed=is_peer_reviewed,
            journal_impact_factor=self._estimate_impact_factor(paper),
            source_type=paper.content_type or "paper",
            author_count=author_count,
            has_known_authors=has_known_authors,
            author_reputation_score=0.5,  # Placeholder
            query_length=len(query_terms),
            query_specificity=self._compute_query_specificity(query_terms, corpus_stats),
            document_length=doc_length,
            language_model_score=0.0,  # Placeholder
            embedding_similarity=embedding_similarity,
            topic_relevance=topic_relevance,
            discipline_match=self._check_discipline_match(paper, context),
            click_probability=0.5,  # Default
            dwell_time_estimate=30.0,  # Default seconds
            novelty_score=0.5,  # Placeholder
            topical_diversity=0.5  # Placeholder
        )
    
    def _compute_bm25(self, query_terms: List[str], doc_terms: List[str],
                     avg_doc_length: float, term_df: Dict[str, int]) -> float:
        """Compute BM25 score with improvements"""
        if not query_terms or not doc_terms:
            return 0.0
        
        score = 0.0
        doc_length = len(doc_terms)
        term_freqs = Counter(doc_terms)
        
        # Length normalization factor
        K = self.k1 * ((1 - self.b) + self.b * (doc_length / avg_doc_length))
        
        for term in query_terms:
            if term in term_df:
                # IDF calculation with smoothing
                df = term_df.get(term, 0)
                N = term_df.get('__total_docs__', 1000)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                
                # Term frequency component
                tf = term_freqs.get(term, 0)
                tf_component = (tf * (self.k1 + 1)) / (tf + K)
                
                # Query term weight (useful for long queries)
                qtf = query_terms.count(term)
                query_weight = (qtf * (self.k3 + 1)) / (qtf + self.k3)
                
                # Academic term boost
                term_boost = self.academic_terms.get(term, 1.0)
                
                score += idf * tf_component * query_weight * term_boost
        
        return score
    
    def _compute_corpus_statistics(self, papers: List[Paper]) -> Dict:
        """Pre-compute corpus-level statistics for efficiency"""
        stats = {
            'total_docs': len(papers),
            'title_term_df': defaultdict(int),
            'abstract_term_df': defaultdict(int),
            'avg_title_length': 0,
            'avg_abstract_length': 0,
            'citation_distribution': [],
            '__total_docs__': len(papers)
        }
        
        title_lengths = []
        abstract_lengths = []
        
        for paper in papers:
            # Title statistics
            if paper.title:
                title_terms = self._tokenize(paper.title.lower())
                title_lengths.append(len(title_terms))
                for term in set(title_terms):
                    stats['title_term_df'][term] += 1
            else:
                title_lengths.append(0)
            
            # Abstract statistics
            if paper.abstract:
                abstract_terms = self._tokenize(paper.abstract.lower())
                abstract_lengths.append(len(abstract_terms))
                for term in set(abstract_terms):
                    stats['abstract_term_df'][term] += 1
            else:
                abstract_lengths.append(0)
            
            # Citation statistics
            if paper.citation_count is not None:
                stats['citation_distribution'].append(paper.citation_count)
        
        stats['avg_title_length'] = sum(title_lengths) / len(title_lengths) if title_lengths else 10
        stats['avg_abstract_length'] = sum(abstract_lengths) / len(abstract_lengths) if abstract_lengths else 100
        stats['title_term_df']['__total_docs__'] = len(papers)
        stats['abstract_term_df']['__total_docs__'] = len(papers)
        
        return stats
    
    def _tokenize(self, text: str) -> List[str]:
        """Advanced tokenization with academic text handling"""
        if not text:
            return []
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Handle academic notation (e.g., COVID-19, SARS-CoV-2)
        text = re.sub(r'([A-Z]+)-(\d+)', r'\1\2', text)
        
        # Split on non-word characters but preserve hyphens in compounds
        tokens = re.findall(r'\b[\w-]+\b', text.lower())
        
        # Filter tokens
        filtered = []
        for token in tokens:
            # Remove pure numbers unless they're years
            if token.isdigit() and (len(token) != 4 or int(token) < 1900 or int(token) > 2100):
                continue
            # Remove single characters unless they're meaningful (e.g., 'r' for R language)
            if len(token) == 1 and token not in ['r', 'c', 'p']:
                continue
            # Remove stop words unless they're part of academic phrases
            if token in self.stop_words and token not in self.academic_terms:
                continue
            filtered.append(token)
        
        return filtered
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to extract features and intent"""
        features = {
            'terms': self._tokenize(query.lower()),
            'has_quotes': '"' in query,
            'has_boolean': any(op in query.upper() for op in ['AND', 'OR', 'NOT']),
            'has_field_search': ':' in query,
            'query_type': 'general'  # vs 'author', 'title', 'doi'
        }
        
        # Detect query intent
        if query.startswith('10.') or 'doi:' in query.lower():
            features['query_type'] = 'doi'
        elif 'author:' in query.lower() or re.search(r'\b[A-Z][a-z]+,?\s+[A-Z]\.?\b', query):
            features['query_type'] = 'author'
        elif len(features['terms']) <= 3:
            features['query_type'] = 'navigational'
        else:
            features['query_type'] = 'informational'
        
        return features
    
    def _count_phrase_matches(self, query: str, paper: Paper) -> int:
        """Count phrase matches in paper fields"""
        count = 0
        
        # Extract phrases from query (2-3 word combinations)
        query_terms = self._tokenize(query.lower())
        for i in range(len(query_terms) - 1):
            bigram = f"{query_terms[i]} {query_terms[i+1]}"
            if paper.title and bigram in paper.title.lower():
                count += 2
            if paper.abstract and bigram in paper.abstract.lower():
                count += 1
            
            if i < len(query_terms) - 2:
                trigram = f"{query_terms[i]} {query_terms[i+1]} {query_terms[i+2]}"
                if paper.title and trigram in paper.title.lower():
                    count += 3
                if paper.abstract and trigram in paper.abstract.lower():
                    count += 1.5
        
        return count
    
    def _compute_query_coverage(self, query_terms: List[str], doc_terms: List[str]) -> float:
        """Compute what fraction of query terms appear in document"""
        if not query_terms:
            return 0.0
        
        query_set = set(query_terms)
        doc_set = set(doc_terms)
        
        # Count how many unique query terms appear in document
        matching_terms = query_set & doc_set
        
        return len(matching_terms) / len(query_set)
    
    def _estimate_citation_percentile(self, citations: int, year: Optional[int]) -> float:
        """Estimate citation percentile (simplified)"""
        # In production, this would use actual citation distributions by year and field
        if citations == 0:
            return 0.0
        elif citations < 5:
            return 0.3
        elif citations < 20:
            return 0.5
        elif citations < 50:
            return 0.7
        elif citations < 100:
            return 0.85
        elif citations < 500:
            return 0.95
        else:
            return 0.99
    
    def _compute_temporal_relevance(self, years_old: float, citations: int) -> float:
        """Compute temporal relevance score balancing recency and impact"""
        # Base recency score (exponential decay)
        recency_score = math.exp(-years_old / 10)  # 10-year half-life
        
        # Impact adjustment (older papers need more citations to maintain relevance)
        if years_old > 5:
            expected_citations = years_old * 3  # Rough heuristic
            impact_multiplier = min(2.0, 1.0 + citations / expected_citations)
        else:
            impact_multiplier = 1.0
        
        return recency_score * impact_multiplier
    
    def _get_source_reputation(self, paper: Paper) -> float:
        """Get source reputation score"""
        # Check paper source
        if hasattr(paper, 'source') and paper.source in self.SOURCE_REPUTATION:
            return self.SOURCE_REPUTATION[paper.source]
        
        # Check journal
        if paper.journal:
            journal_lower = paper.journal.lower()
            for source, score in self.SOURCE_REPUTATION.items():
                if source.lower() in journal_lower:
                    return score
        
        # Default by content type
        if paper.content_type == "preprint":
            return 0.7
        elif paper.content_type == "book":
            return 0.6
        else:
            return 0.5
    
    def _is_peer_reviewed(self, paper: Paper) -> bool:
        """Determine if paper is peer-reviewed"""
        # Simple heuristic - in production, use journal metadata
        if paper.content_type == "preprint":
            return False
        if paper.doi and paper.journal:
            return True
        if hasattr(paper, 'source') and paper.source in ["DOAJ", "PubMed", "PLOS"]:
            return True
        return False
    
    def _has_anonymous_authors(self, paper: Paper) -> bool:
        """Check if paper has anonymous or unknown authors"""
        if not paper.authors:
            return True
        
        anonymous_indicators = ['anonymous', 'unknown', 'no author', 'n/a', '']
        for author in paper.authors:
            if author.lower() in anonymous_indicators:
                return True
        
        return False
    
    def _estimate_impact_factor(self, paper: Paper) -> float:
        """Estimate journal impact factor (simplified)"""
        # In production, use actual journal metrics
        if not paper.journal:
            return 0.0
        
        journal_lower = paper.journal.lower()
        
        # Top-tier journals
        if any(j in journal_lower for j in ['nature', 'science', 'cell', 'lancet', 'nejm']):
            return 30.0
        elif any(j in journal_lower for j in ['pnas', 'bmj', 'jama']):
            return 15.0
        elif 'ieee' in journal_lower or 'acm' in journal_lower:
            return 5.0
        elif 'plos' in journal_lower:
            return 3.0
        else:
            return 1.0
    
    def _compute_semantic_similarity(self, query: str, paper: Paper) -> float:
        """Compute semantic similarity (placeholder for embedding-based similarity)"""
        # In production, use actual embeddings (BERT, SciBERT, etc.)
        # For now, use enhanced keyword overlap
        
        query_terms = set(self._tokenize(query.lower()))
        # Safe concatenation with null checks
        paper_text = ""
        if paper.title:
            paper_text += paper.title + " "
        if paper.abstract:
            paper_text += paper.abstract
        paper_terms = set(self._tokenize(paper_text.lower()))
        
        if not query_terms or not paper_terms:
            return 0.0
        
        # Jaccard similarity with IDF weighting would go here
        intersection = query_terms & paper_terms
        union = query_terms | paper_terms
        
        return len(intersection) / len(union)
    
    def _compute_topic_relevance(self, query_features: Dict, paper: Paper) -> float:
        """Compute topical relevance"""
        # Simplified topic modeling - in production, use LDA or similar
        score = 0.5  # Default
        
        # Boost for matching academic terminology
        paper_text = ""
        if paper.title:
            paper_text += paper.title + " "
        if paper.abstract:
            paper_text += paper.abstract
        
        if paper_text:  # Only process if we have text
            paper_text_lower = paper_text.lower()
            for term, weight in self.academic_terms.items():
                if term in paper_text_lower:
                    score *= weight
        
        return min(1.0, score)
    
    def _compute_query_specificity(self, query_terms: List[str], corpus_stats: Dict) -> float:
        """Compute how specific/rare the query terms are"""
        if not query_terms:
            return 0.0
        
        # Average IDF of query terms
        total_idf = 0
        term_dfs = corpus_stats.get('title_term_df', {})
        N = corpus_stats.get('total_docs', 1000)
        
        for term in query_terms:
            df = term_dfs.get(term, 1)
            idf = math.log(N / df)
            total_idf += idf
        
        return total_idf / len(query_terms)
    
    def _check_discipline_match(self, paper: Paper, context: Optional[Dict]) -> bool:
        """Check if paper matches requested discipline"""
        if not context or 'discipline' not in context:
            return True
        
        requested_discipline = context['discipline'].lower()
        
        # Check paper metadata
        if hasattr(paper, 'discipline') and paper.discipline:
            return requested_discipline in paper.discipline.lower()
        
        # Infer from journal/source
        paper_text = f"{paper.title} {paper.abstract or ''} {paper.journal or ''}"
        
        discipline_keywords = {
            'computer science': ['algorithm', 'software', 'computing', 'ai', 'machine learning'],
            'medicine': ['clinical', 'patient', 'treatment', 'disease', 'therapy'],
            'biology': ['cell', 'gene', 'protein', 'organism', 'molecular'],
            'physics': ['quantum', 'particle', 'energy', 'force', 'relativity'],
            'chemistry': ['chemical', 'molecule', 'reaction', 'compound', 'synthesis'],
            'mathematics': ['theorem', 'proof', 'equation', 'mathematical', 'topology'],
        }
        
        if requested_discipline in discipline_keywords:
            keywords = discipline_keywords[requested_discipline]
            matches = sum(1 for kw in keywords if kw in paper_text.lower())
            return matches >= 2
        
        return True
    
    def _get_minimal_features(self) -> RankingFeatures:
        """Get minimal features for error cases"""
        return RankingFeatures(
            bm25_title=0.0,
            bm25_abstract=0.0,
            bm25_combined=0.0,
            tfidf_cosine_title=0.0,
            tfidf_cosine_abstract=0.0,
            exact_title_match=False,
            exact_abstract_match=False,
            phrase_match_count=0,
            query_coverage_title=0.0,
            query_coverage_abstract=0.0,
            title_length=10,
            abstract_length=100,
            title_query_overlap=0.0,
            abstract_query_overlap=0.0,
            citation_count=0,
            citation_velocity=0.0,
            influential_citation_count=0,
            citation_percentile=0.0,
            h_index_estimate=0.0,
            years_since_publication=5.0,
            is_recent_2_years=False,
            is_recent_5_years=True,
            publication_year=2020,
            temporal_relevance_score=0.5,
            source_reputation_score=0.5,
            is_peer_reviewed=False,
            journal_impact_factor=1.0,
            source_type="paper",
            author_count=1,
            has_known_authors=True,
            author_reputation_score=0.5,
            query_length=3,
            query_specificity=0.5,
            document_length=110,
            language_model_score=0.0,
            embedding_similarity=0.0,
            topic_relevance=0.5,
            discipline_match=True,
            click_probability=0.5,
            dwell_time_estimate=30.0,
            novelty_score=0.5,
            topical_diversity=0.5
        )
    
    def _score_papers(self, features_list: List[RankingFeatures]) -> List[float]:
        """Score papers using model or hand-tuned weights"""
        if self.model is not None:
            # Use trained model
            feature_matrix = self._features_to_matrix(features_list)
            scores = self.model.predict(feature_matrix)
            return scores.tolist()
        else:
            # Use hand-tuned weights
            scores = []
            for features in features_list:
                score = 0.0
                
                # Core relevance features (40% weight)
                score += features.bm25_combined * 0.20
                score += features.bm25_title * 0.10
                score += (1.0 if features.exact_title_match else 0.0) * 0.10
                
                # Query match features (20% weight)
                score += min(features.phrase_match_count / 5, 1.0) * 0.10
                score += features.query_coverage_title * 0.10
                
                # Academic impact (20% weight)
                score += features.citation_percentile * 0.10
                score += min(features.citation_velocity / 50, 1.0) * 0.05
                score += features.source_reputation_score * 0.05
                
                # Temporal relevance (10% weight)
                score += features.temporal_relevance_score * 0.10
                
                # Semantic features (10% weight)
                score += features.embedding_similarity * 0.05
                score += features.topic_relevance * 0.05
                
                scores.append(score)
            
            return scores
    
    def _features_to_matrix(self, features_list: List[RankingFeatures]) -> np.ndarray:
        """Convert features to numpy matrix"""
        # In production, this would handle feature engineering pipeline
        matrix = []
        for features in features_list:
            row = [
                features.bm25_title,
                features.bm25_abstract,
                features.bm25_combined,
                float(features.exact_title_match),
                features.phrase_match_count,
                features.query_coverage_title,
                features.query_coverage_abstract,
                features.citation_percentile,
                features.citation_velocity,
                features.temporal_relevance_score,
                features.source_reputation_score,
                features.embedding_similarity
            ]
            matrix.append(row)
        
        return np.array(matrix)
    
    def _generate_explanation(self, features: RankingFeatures, score: float, query: str) -> Dict[str, Any]:
        """Generate human-readable explanation for ranking"""
        explanation = {
            'score': round(score, 3),
            'primary_factors': [],
            'key_features': {}
        }
        
        # Identify primary ranking factors
        if features.exact_title_match:
            explanation['primary_factors'].append("Exact query match in title")
        
        if features.bm25_title > 10:
            explanation['primary_factors'].append("High keyword relevance in title")
        elif features.bm25_combined > 5:
            explanation['primary_factors'].append("Strong keyword relevance")
        
        if features.citation_percentile > 0.9:
            explanation['primary_factors'].append("Highly cited paper (top 10%)")
        elif features.citation_percentile > 0.7:
            explanation['primary_factors'].append("Well-cited paper")
        
        if features.is_recent_2_years:
            explanation['primary_factors'].append("Recent publication (< 2 years)")
        
        if features.source_reputation_score > 0.9:
            explanation['primary_factors'].append("Published in top-tier venue")
        
        # Key feature values
        explanation['key_features'] = {
            'relevance_score': round(features.bm25_combined, 2),
            'citation_impact': round(features.citation_percentile, 2),
            'source_quality': round(features.source_reputation_score, 2),
            'query_match': round(features.query_coverage_title, 2),
            'recency': 'Recent' if features.is_recent_5_years else 'Older'
        }
        
        return explanation
    
    def _diversify_results(self, results: List[Tuple[Paper, float, Dict]], 
                          query: str, lambda_param: float = 0.5) -> List[Tuple[Paper, float, Dict]]:
        """Apply MMR (Maximal Marginal Relevance) for result diversification"""
        if len(results) <= 1:
            return results
        
        diversified = [results[0]]  # Start with top result
        remaining = results[1:]
        
        while remaining and len(diversified) < len(results):
            best_score = -1
            best_idx = -1
            
            for i, (paper, score, exp) in enumerate(remaining):
                # Compute similarity to already selected papers
                max_sim = 0
                for selected_paper, _, _ in diversified:
                    sim = self._compute_paper_similarity(paper, selected_paper)
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr_score = lambda_param * score - (1 - lambda_param) * max_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            if best_idx >= 0:
                diversified.append(remaining[best_idx])
                remaining.pop(best_idx)
            else:
                break
        
        return diversified
    
    def _compute_paper_similarity(self, paper1: Paper, paper2: Paper) -> float:
        """Compute similarity between two papers"""
        # Simple Jaccard similarity on terms with null safety
        text1 = f"{paper1.title or ''} {paper1.abstract or ''}"
        text2 = f"{paper2.title or ''} {paper2.abstract or ''}"
        terms1 = set(self._tokenize(text1))
        terms2 = set(self._tokenize(text2))
        
        if not terms1 or not terms2:
            return 0.0
        
        intersection = terms1 & terms2
        union = terms1 | terms2
        
        return len(intersection) / len(union)
    
    def _load_model(self):
        """Load pre-trained ranking model"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_names = model_data['feature_names']
            logger.info("Loaded pre-trained ranking model")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._initialize_default_model()
    
    def save_model(self):
        """Save trained model"""
        if self.model is not None:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info("Saved ranking model")
    
    def train_model(self, training_data: List[Tuple[RankingFeatures, float]]):
        """Train ranking model on labeled data"""
        if not training_data:
            logger.error("No training data provided")
            return
        
        # Prepare training data
        X = self._features_to_matrix([f for f, _ in training_data])
        y = np.array([score for _, score in training_data])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train gradient boosting model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=20,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42
        )
        
        self.model.fit(X_scaled, y)
        logger.info("Trained new ranking model")
        
        # Save model
        self.save_model()
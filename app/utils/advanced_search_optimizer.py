"""
Advanced Search Optimization with Multi-Stage Ranking Pipeline
Implements sophisticated IR techniques for result optimization
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict, Counter
import math
import logging
import numpy as np
from datetime import datetime
import asyncio

from app.models import Paper
from app.ranking.advanced_ranker import AdvancedRanker, RankingFeatures

logger = logging.getLogger(__name__)


class AdvancedSearchOptimizer:
    """
    Sophisticated search result optimization with multi-stage ranking
    """
    
    # Source-specific retrieval configurations
    SOURCE_CONFIGS = {
        "PubMed": {
            "weight": 1.0,
            "min_quality_score": 0.3,
            "max_results": 100,
            "specialization": ["medicine", "biology", "health"],
            "boost_fields": ["mesh_terms", "clinical_trial"],
            "reliability": 0.98
        },
        "Semantic Scholar": {
            "weight": 0.95,
            "min_quality_score": 0.35,
            "max_results": 100,
            "specialization": ["computer_science", "ai", "general"],
            "boost_fields": ["influential_citations", "tldr"],
            "reliability": 0.95
        },
        "arXiv": {
            "weight": 0.9,
            "min_quality_score": 0.4,
            "max_results": 100,
            "specialization": ["physics", "mathematics", "computer_science", "statistics"],
            "boost_fields": ["categories", "comments"],
            "reliability": 0.93
        },
        "IEEE": {
            "weight": 0.92,
            "min_quality_score": 0.35,
            "max_results": 75,
            "specialization": ["engineering", "computer_science", "electronics"],
            "boost_fields": ["conference", "standards"],
            "reliability": 0.94
        },
        "ACM": {
            "weight": 0.92,
            "min_quality_score": 0.35,
            "max_results": 75,
            "specialization": ["computer_science", "information_systems"],
            "boost_fields": ["acm_categories", "conference"],
            "reliability": 0.94
        },
        "PLOS": {
            "weight": 0.85,
            "min_quality_score": 0.35,
            "max_results": 75,
            "specialization": ["biology", "medicine", "general_science"],
            "boost_fields": ["peer_review", "data_availability"],
            "reliability": 0.90
        },
        "Crossref": {
            "weight": 0.85,
            "min_quality_score": 0.3,
            "max_results": 100,
            "specialization": ["general"],
            "boost_fields": ["publisher", "license"],
            "reliability": 0.88
        },
        "DOAJ": {
            "weight": 0.75,
            "min_quality_score": 0.4,
            "max_results": 75,
            "specialization": ["general"],
            "boost_fields": ["open_access", "peer_review"],
            "reliability": 0.85
        },
        "Google Books": {
            "weight": 0.6,
            "min_quality_score": 0.5,
            "max_results": 50,
            "specialization": ["books", "general"],
            "boost_fields": ["preview", "ratings"],
            "reliability": 0.75
        }
    }
    
    def __init__(self):
        self.ranker = AdvancedRanker()
        self.query_cache = {}
        self.performance_stats = defaultdict(lambda: {
            'queries': 0,
            'avg_precision': 0.0,
            'avg_recall': 0.0,
            'avg_response_time': 0.0
        })
    
    async def optimize_search_results(
        self,
        results_by_source: Dict[str, List[Paper]],
        query: str,
        search_context: Optional[Dict[str, Any]] = None,
        target_results: int = 100
    ) -> Tuple[List[Paper], Dict[str, Any]]:
        """
        Advanced multi-stage search result optimization
        
        Returns:
            Tuple of (optimized_papers, search_metrics)
        """
        start_time = datetime.now()
        
        # Initialize search context
        context = self._prepare_search_context(query, search_context)
        
        # Stage 1: Source-specific quality filtering and enhancement
        enhanced_results = await self._enhance_source_results(results_by_source, context)
        
        # Stage 2: Initial relevance scoring with source-specific strategies
        scored_results = self._apply_source_strategies(enhanced_results, query, context)
        
        # Stage 3: Cross-source normalization and calibration
        normalized_results = self._normalize_scores(scored_results)
        
        # Stage 4: Apply advanced ranking with ML model
        ranked_results = self.ranker.rank_papers(
            [item['paper'] for item in normalized_results],
            query,
            context
        )
        
        # Stage 5: Post-processing and result curation
        curated_results = self._curate_results(ranked_results, context, target_results)
        
        # Stage 6: Generate search analytics
        search_metrics = self._generate_search_metrics(
            results_by_source,
            curated_results,
            query,
            context,
            start_time
        )
        
        # Extract just the papers for return
        final_papers = [paper for paper, _, _ in curated_results]
        
        return final_papers, search_metrics
    
    def _prepare_search_context(self, query: str, user_context: Optional[Dict]) -> Dict[str, Any]:
        """Prepare comprehensive search context"""
        context = {
            'query': query,
            'timestamp': datetime.now(),
            'session_id': user_context.get('session_id') if user_context else None,
            'user_preferences': user_context.get('preferences', {}) if user_context else {},
            'search_intent': self._infer_search_intent(query),
            'query_expansion': self._expand_query(query),
            'enable_diversity': user_context.get('enable_diversity', True) if user_context else True,
            'personalization': user_context.get('personalization', False) if user_context else False
        }
        
        # Merge with user context
        if user_context:
            context.update(user_context)
        
        return context
    
    async def _enhance_source_results(
        self,
        results_by_source: Dict[str, List[Paper]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance results with source-specific processing"""
        enhanced_results = []
        
        # Process each source in parallel
        enhancement_tasks = []
        for source, papers in results_by_source.items():
            if papers:
                task = self._enhance_source_papers(source, papers, context)
                enhancement_tasks.append(task)
        
        # Wait for all enhancements
        if enhancement_tasks:
            enhanced_groups = await asyncio.gather(*enhancement_tasks, return_exceptions=True)
            
            for result in enhanced_groups:
                if isinstance(result, Exception):
                    logger.error(f"Enhancement failed: {result}")
                else:
                    enhanced_results.extend(result)
        
        return enhanced_results
    
    async def _enhance_source_papers(
        self,
        source: str,
        papers: List[Paper],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance papers from a specific source"""
        enhanced = []
        source_config = self.SOURCE_CONFIGS.get(source, {})
        
        for paper in papers:
            # Apply source-specific enhancements
            enhanced_paper = {
                'paper': paper,
                'source': source,
                'source_weight': source_config.get('weight', 0.5),
                'source_reliability': source_config.get('reliability', 0.7),
                'enhancements': {}
            }
            
            # Add source-specific metadata
            if source == "Semantic Scholar" and hasattr(paper, 'tldr'):
                enhanced_paper['enhancements']['tldr'] = paper.tldr
            elif source == "arXiv" and hasattr(paper, 'categories'):
                enhanced_paper['enhancements']['categories'] = paper.categories
            elif source == "PubMed" and hasattr(paper, 'mesh_terms'):
                enhanced_paper['enhancements']['mesh_terms'] = paper.mesh_terms
            
            # Quality check
            if self._passes_quality_check(paper, source_config):
                enhanced.append(enhanced_paper)
        
        return enhanced
    
    def _passes_quality_check(self, paper: Paper, source_config: Dict) -> bool:
        """Check if paper meets quality standards"""
        # Title check
        if not paper.title or len(paper.title.strip()) < 5:
            return False
        
        # Don't filter by abstract - many valid papers don't have abstracts
        # Abstract is optional
        
        # Author check for papers
        if paper.content_type == "paper" and (not paper.authors or 
            all(author.lower() in ['anonymous', 'unknown', ''] for author in paper.authors)):
            return False
        
        # Year check
        try:
            year = int(paper.year)
            if year < 1800 or year > datetime.now().year + 1:
                return False
        except:
            return False
        
        return True
    
    def _apply_source_strategies(
        self,
        enhanced_results: List[Dict[str, Any]],
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply source-specific retrieval strategies"""
        scored_results = []
        
        # Group by source for strategy application
        by_source = defaultdict(list)
        for result in enhanced_results:
            by_source[result['source']].append(result)
        
        for source, source_results in by_source.items():
            source_config = self.SOURCE_CONFIGS.get(source, {})
            
            # Apply source-specific scoring adjustments
            for result in source_results:
                paper = result['paper']
                base_score = self._compute_base_relevance(paper, query)
                
                # Source-specific boosts
                source_score = base_score * result['source_weight']
                
                # Specialization boost
                if context.get('discipline') in source_config.get('specialization', []):
                    source_score *= 1.2
                
                # Reliability adjustment
                source_score *= result['source_reliability']
                
                result['initial_score'] = source_score
                result['scoring_details'] = {
                    'base_relevance': base_score,
                    'source_multiplier': result['source_weight'],
                    'specialization_boost': 1.2 if context.get('discipline') in source_config.get('specialization', []) else 1.0,
                    'reliability_factor': result['source_reliability']
                }
                
                scored_results.append(result)
        
        return scored_results
    
    def _compute_base_relevance(self, paper: Paper, query: str) -> float:
        """Compute base relevance score"""
        # Simple relevance for initial scoring (full scoring happens in ranker)
        score = 0.0
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Title relevance
        title_lower = paper.title.lower()
        if query_lower in title_lower:
            score += 2.0
        else:
            for term in query_terms:
                if term in title_lower:
                    score += 0.5
        
        # Abstract relevance
        if paper.abstract:
            abstract_lower = paper.abstract.lower()
            if query_lower in abstract_lower:
                score += 1.0
            else:
                for term in query_terms:
                    if term in abstract_lower:
                        score += 0.2
        
        # Citation boost
        if paper.citation_count:
            score += math.log(paper.citation_count + 1) / 10
        
        return score
    
    def _normalize_scores(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize scores across sources"""
        if not scored_results:
            return []
        
        # Group by source
        by_source = defaultdict(list)
        for result in scored_results:
            by_source[result['source']].append(result)
        
        # Normalize within each source
        normalized_results = []
        for source, source_results in by_source.items():
            if not source_results:
                continue
            
            # Get score statistics
            scores = [r['initial_score'] for r in source_results]
            max_score = max(scores)
            min_score = min(scores)
            mean_score = sum(scores) / len(scores)
            
            # Z-score normalization with clipping
            if max_score > min_score:
                std_dev = np.std(scores) if len(scores) > 1 else 1.0
                for result in source_results:
                    if std_dev > 0:
                        z_score = (result['initial_score'] - mean_score) / std_dev
                        # Clip to [-3, 3] and transform to [0, 1]
                        normalized_score = (min(max(z_score, -3), 3) + 3) / 6
                    else:
                        normalized_score = 0.5
                    
                    result['normalized_score'] = normalized_score
                    normalized_results.append(result)
            else:
                # All scores are the same
                for result in source_results:
                    result['normalized_score'] = 0.5
                    normalized_results.append(result)
        
        return normalized_results
    
    def _curate_results(
        self,
        ranked_results: List[Tuple[Paper, float, Dict[str, Any]]],
        context: Dict[str, Any],
        target_results: int
    ) -> List[Tuple[Paper, float, Dict[str, Any]]]:
        """Curate final result set with quality and diversity considerations"""
        if not ranked_results:
            return []
        
        curated = []
        seen_titles = set()
        seen_authors = defaultdict(int)
        source_counts = defaultdict(int)
        
        for paper, score, explanation in ranked_results:
            # Duplicate check (fuzzy)
            title_key = self._get_title_key(paper.title)
            if title_key in seen_titles:
                continue
            
            # Diversity constraints
            if context.get('enable_diversity', True):
                # Limit papers per author
                main_author = paper.authors[0] if paper.authors else "Unknown"
                if seen_authors[main_author] >= 3:
                    continue
                
                # Limit papers per source (after minimum threshold)
                if len(curated) > 20:  # After first 20, apply diversity
                    paper_source = getattr(paper, 'source', 'Unknown')
                    if source_counts[paper_source] >= max(5, target_results // 10):
                        continue
            
            # Add to curated set
            curated.append((paper, score, explanation))
            seen_titles.add(title_key)
            if paper.authors:
                seen_authors[paper.authors[0]] += 1
            source_counts[getattr(paper, 'source', 'Unknown')] += 1
            
            if len(curated) >= target_results:
                break
        
        return curated
    
    def _get_title_key(self, title: str) -> str:
        """Generate normalized title key for deduplication"""
        # Remove common words and normalize
        stop_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but'}
        words = title.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        return ' '.join(sorted(key_words[:5]))  # Use first 5 key words
    
    def _infer_search_intent(self, query: str) -> Dict[str, Any]:
        """Infer the intent behind the search query"""
        intent = {
            'type': 'general',
            'specificity': 'medium',
            'domain_indicators': [],
            'temporal_intent': None
        }
        
        query_lower = query.lower()
        
        # Check for specific intent patterns
        if 'review' in query_lower or 'survey' in query_lower:
            intent['type'] = 'literature_review'
        elif 'how to' in query_lower or 'tutorial' in query_lower:
            intent['type'] = 'tutorial'
        elif 'comparison' in query_lower or 'versus' in query_lower or ' vs ' in query_lower:
            intent['type'] = 'comparison'
        elif any(year in query for year in ['2024', '2023', '2022', '2021', '2020']):
            intent['type'] = 'recent_research'
            intent['temporal_intent'] = 'recent'
        
        # Domain indicators
        cs_terms = ['algorithm', 'software', 'neural', 'machine learning', 'ai', 'database']
        med_terms = ['clinical', 'patient', 'treatment', 'diagnosis', 'therapy', 'disease']
        
        for term in cs_terms:
            if term in query_lower:
                intent['domain_indicators'].append('computer_science')
                break
        
        for term in med_terms:
            if term in query_lower:
                intent['domain_indicators'].append('medicine')
                break
        
        # Query specificity
        word_count = len(query.split())
        if word_count <= 2:
            intent['specificity'] = 'low'
        elif word_count >= 6:
            intent['specificity'] = 'high'
        
        return intent
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expansions = [query]  # Always include original
        
        # Simple expansion rules (in production, use WordNet or domain thesaurus)
        expansion_map = {
            'ml': ['machine learning', 'ML'],
            'ai': ['artificial intelligence', 'AI'],
            'nn': ['neural network', 'neural networks'],
            'nlp': ['natural language processing', 'NLP'],
            'cv': ['computer vision', 'CV'],
            'rl': ['reinforcement learning', 'RL'],
            'dl': ['deep learning', 'DL'],
            'hci': ['human computer interaction', 'HCI'],
            'ux': ['user experience', 'UX'],
            'ui': ['user interface', 'UI']
        }
        
        query_lower = query.lower()
        for abbrev, expanded in expansion_map.items():
            if abbrev in query_lower.split():
                for exp in expanded:
                    expansions.append(query_lower.replace(abbrev, exp))
        
        return list(set(expansions))[:3]  # Limit to 3 expansions
    
    def _generate_search_metrics(
        self,
        original_results: Dict[str, List[Paper]],
        curated_results: List[Tuple[Paper, float, Dict[str, Any]]],
        query: str,
        context: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive search analytics"""
        # Calculate timing
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Source statistics
        source_stats = {}
        for source, papers in original_results.items():
            source_stats[source] = {
                'retrieved': len(papers),
                'in_final': sum(1 for p, _, _ in curated_results if hasattr(p, 'source') and p.source == source),
                'precision': 0.0  # Would need relevance judgments
            }
        
        # Result statistics
        scores = [score for _, score, _ in curated_results]
        
        # Year distribution
        year_dist = defaultdict(int)
        for paper, _, _ in curated_results:
            try:
                year = int(paper.year)
                year_dist[year] += 1
            except:
                pass
        
        # Citation statistics
        citations = [p.citation_count for p, _, _ in curated_results if p.citation_count is not None]
        
        metrics = {
            'query': query,
            'query_intent': context.get('search_intent', {}),
            'timing': {
                'total_seconds': round(total_time, 2),
                'per_result_ms': round(total_time * 1000 / len(curated_results), 2) if curated_results else 0
            },
            'result_stats': {
                'total_retrieved': sum(len(papers) for papers in original_results.values()),
                'total_curated': len(curated_results),
                'avg_score': round(sum(scores) / len(scores), 3) if scores else 0,
                'score_range': [round(min(scores), 3), round(max(scores), 3)] if scores else [0, 0]
            },
            'source_distribution': source_stats,
            'temporal_distribution': dict(year_dist),
            'citation_stats': {
                'mean': round(sum(citations) / len(citations), 1) if citations else 0,
                'median': sorted(citations)[len(citations)//2] if citations else 0,
                'highly_cited': sum(1 for c in citations if c > 100),
                'uncited': sum(1 for c in citations if c == 0)
            },
            'diversity_metrics': {
                'unique_sources': len(set(getattr(p, 'source', 'Unknown') for p, _, _ in curated_results)),
                'unique_authors': len(set(author for p, _, _ in curated_results for author in (p.authors or []))),
                'year_span': max(year_dist.keys()) - min(year_dist.keys()) if year_dist else 0
            },
            'quality_indicators': {
                'peer_reviewed': sum(1 for p, _, _ in curated_results if self._is_likely_peer_reviewed(p)),
                'recent_5_years': sum(1 for year, count in year_dist.items() if year >= datetime.now().year - 5 for _ in range(count)),
                'has_citations': len(citations)
            }
        }
        
        # Update performance statistics
        self._update_performance_stats(source_stats, total_time)
        
        return metrics
    
    def _is_likely_peer_reviewed(self, paper: Paper) -> bool:
        """Estimate if paper is peer-reviewed"""
        if paper.content_type == "preprint":
            return False
        if paper.doi and paper.journal:
            return True
        if hasattr(paper, 'source') and paper.source in ["PubMed", "PLOS", "DOAJ", "IEEE", "ACM"]:
            return True
        return False
    
    def _update_performance_stats(self, source_stats: Dict, response_time: float):
        """Update running performance statistics"""
        for source, stats in source_stats.items():
            self.performance_stats[source]['queries'] += 1
            self.performance_stats[source]['avg_response_time'] = (
                (self.performance_stats[source]['avg_response_time'] * 
                 (self.performance_stats[source]['queries'] - 1) + response_time) /
                self.performance_stats[source]['queries']
            )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all sources"""
        return dict(self.performance_stats)
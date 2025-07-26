from typing import List, Set, Tuple, Dict
import asyncio
import logging
from app.models import Paper, SearchRequest
from app.api_clients import (
    ERICClient, COREClient, DOAJClient, EuropePMCClient, PMCClient, PubMedClient, 
    SemanticScholarClient, OpenAlexClient, ArxivClient, CrossrefClient,
    DOABClient, ProjectGutenbergClient, InternetArchiveClient, OpenLibraryClient, OpenStaxClient,
    OAPENClient, BiodiversityClient, NLMBookshelfClient,
    PLOSClient, BioMedCentralClient, UnpaywallClient, GoogleBooksClient, GoogleSearchClient, BASEClient,
    OpenTextbookLibraryClient, PressbooksClient, LibreTextsClient,
    MERLOTClient, OERCommonsClient, MITOpenCourseWareClient
)
# Import enhanced implementations
try:
    from app.api_clients.open_textbook_library_scraper import OpenTextbookLibraryScraper
    from app.api_clients.libretexts_enhanced import LibreTextsEnhanced
    USE_ENHANCED_CLIENTS = True
except ImportError:
    USE_ENHANCED_CLIENTS = False
from app.utils import sort_papers
from app.utils.query_translator import QueryTranslator
from app.utils.search_optimizer import SearchOptimizer
# from app.utils.advanced_search_optimizer import AdvancedSearchOptimizer
# from app.ranking.advanced_ranker import AdvancedRanker
import hashlib
import re

logger = logging.getLogger(__name__)

class SearchService:
    """Service to handle multi-source search and deduplication"""
    
    def __init__(self, core_api_key: str = None, use_advanced_ranking: bool = False):
        self.query_translator = QueryTranslator()
        self.search_optimizer = SearchOptimizer()
        self.use_advanced_ranking = use_advanced_ranking
        if self.use_advanced_ranking:
            pass
            # self.advanced_optimizer = AdvancedSearchOptimizer()
            # self.advanced_ranker = AdvancedRanker()
        self.eric_client = ERICClient()
        self.core_client = COREClient(api_key=core_api_key)
        self.doaj_client = DOAJClient()
        self.europe_pmc_client = EuropePMCClient()
        self.pmc_client = PMCClient()
        self.pubmed_client = PubMedClient()
        self.semantic_scholar_client = SemanticScholarClient()
        # New high-impact APIs
        self.openalex_client = OpenAlexClient()
        self.arxiv_client = ArxivClient()
        self.crossref_client = CrossrefClient()
        # Book sources
        self.doab_client = DOABClient()
        self.project_gutenberg_client = ProjectGutenbergClient()
        self.internet_archive_client = InternetArchiveClient()
        self.open_library_client = OpenLibraryClient()
        self.openstax_client = OpenStaxClient()
        self.oapen_client = OAPENClient()
        # self.hathitrust_client = HathiTrustClient()  # Removed - not working
        self.biodiversity_client = BiodiversityClient()
        self.nlm_bookshelf_client = NLMBookshelfClient()
        # Article sources
        self.plos_client = PLOSClient()
        self.biomed_central_client = BioMedCentralClient()
        self.unpaywall_client = UnpaywallClient()
        # self.mdpi_client = MDPIClient()  # Removed - not working
        self.google_books_client = GoogleBooksClient()
        self.google_search_client = GoogleSearchClient()
        self.base_client = BASEClient()
        # OER sources - use enhanced versions if available
        if USE_ENHANCED_CLIENTS:
            self.open_textbook_library_client = OpenTextbookLibraryScraper()
            # Use basic LibreTexts client which properly filters out category pages
            self.libretexts_client = LibreTextsClient()
        else:
            self.open_textbook_library_client = OpenTextbookLibraryClient()
            self.libretexts_client = LibreTextsClient()
        self.pressbooks_client = PressbooksClient()
        self.merlot_client = MERLOTClient()
        self.oer_commons_client = OERCommonsClient()
        self.mit_ocw_client = MITOpenCourseWareClient()
        
    def update_api_keys(self, api_keys: dict):
        """Update API keys for clients that need them"""
        if api_keys:
            # Update BHL API key
            if 'BHL' in api_keys:
                self.biodiversity_client.api_key = api_keys['BHL']
            # Update BioMed Central API key  
            if 'BioMed Central' in api_keys:
                self.biomed_central_client.api_key = api_keys['BioMed Central']
            # Update MIT OpenCourseWare Google API key
            if 'MIT OpenCourseWare' in api_keys:
                self.mit_ocw_client.api_key = api_keys['MIT OpenCourseWare']
            # Update MERLOT API key
            if 'MERLOT' in api_keys:
                self.merlot_client.api_key = api_keys['MERLOT']
            # Update OER Commons API key
            if 'OER Commons' in api_keys:
                self.oer_commons_client.api_key = api_keys['OER Commons']
            # Update Google Search API key and Search Engine ID
            if 'Google Search' in api_keys:
                self.google_search_client.api_key = api_keys['Google Search']
                # Also check for Search Engine ID
                if 'Google Search_ENGINE_ID' in api_keys:
                    self.google_search_client.search_engine_id = api_keys['Google Search_ENGINE_ID']
            # BASE uses IP whitelisting, not API keys
    
    def _get_translated_query(self, api_name: str, request: SearchRequest) -> str:
        """Get API-specific translated query"""
        # For some APIs, use translated queries only if they'll help
        # For broad searches, sometimes the original query works better
        
        if api_name == "PubMed":
            # PubMed benefits from field-specific search
            return self.query_translator.to_pubmed_query(
                request.query, request.discipline, request.education_level,
                request.year_start, request.year_end
            )
        elif api_name == "arXiv":
            # Only use category search if discipline matches arXiv categories
            if request.discipline and request.discipline.lower() in ["computer science", "mathematics", "physics", "statistics"]:
                return self.query_translator.to_arxiv_query(request.query, request.discipline)
            else:
                return request.query  # Use original query for better coverage
        elif api_name == "Semantic Scholar":
            # Semantic Scholar handles expansion well
            return self.query_translator.to_semantic_scholar_query(
                request.query, request.discipline, request.education_level,
                request.publication_type, request.study_type
            )
        elif api_name in ["PLOS", "BASE", "Crossref"]:
            # These benefit from structured queries
            if api_name == "PLOS":
                return self.query_translator.to_plos_query(
                    request.query, request.discipline, request.year_start, request.year_end
                )
            elif api_name == "BASE":
                return self.query_translator.to_base_query(
                    request.query, request.discipline, request.year_start, request.year_end
                )
            else:  # Crossref
                return self.query_translator.to_crossref_query(request.query, request.discipline)
        else:
            # For most APIs, use the original query for maximum coverage
            return request.query
        
    async def search(self, request: SearchRequest) -> Tuple[List[Paper], List[str], int]:
        """
        Search multiple sources and return deduplicated, sorted, and paginated results
        Returns: (paginated_papers, sources_queried, total_results)
        """
        # Update API keys if provided
        if request.api_keys:
            self.update_api_keys(request.api_keys)
            
        # Enhance query with publication_type and study_type keywords if provided
        enhanced_query = request.query
        if request.publication_type or request.study_type:
            enhanced_query = self.query_translator.to_simple_query(
                request.query, 
                request.discipline,
                request.education_level,
                request.publication_type,
                request.study_type
            )
            
        sources_queried = []
        
        # Create search tasks for selected APIs only
        tasks = []
        
        # Get list of sources to search (default to all if none specified)
        sources_to_search = request.sources if request.sources else [
            "ERIC", "CORE", "DOAJ", "Europe PMC", "PubMed Central", "PubMed", "Semantic Scholar",
            "OpenAlex", "arXiv", "Crossref", "DOAB", "Project Gutenberg", "Internet Archive", "Open Library", "OpenStax",
            "OAPEN", "BHL", "NLM Bookshelf", "PLOS", "BioMed Central", "Unpaywall",
            "Google Books", "Google Search",  # Removed BASE - requires IP whitelisting
            "Open Textbook Library", "Pressbooks", "LibreTexts", "MERLOT", "OER Commons", "MIT OpenCourseWare"
        ]
        
        # ERIC search
        if "ERIC" in sources_to_search:
            tasks.append(self.eric_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("ERIC")
        
        # CORE search
        if "CORE" in sources_to_search:
            tasks.append(self.core_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("CORE")
        
        # DOAJ search
        if "DOAJ" in sources_to_search:
            tasks.append(self.doaj_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("DOAJ")
        
        # Europe PMC search
        if "Europe PMC" in sources_to_search:
            tasks.append(self.europe_pmc_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("Europe PMC")
        
        # PubMed Central search
        if "PubMed Central" in sources_to_search:
            tasks.append(self.pmc_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("PubMed Central")
        
        # PubMed search
        if "PubMed" in sources_to_search:
            tasks.append(self.pubmed_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level
            ))
            sources_queried.append("PubMed")
        
        # Semantic Scholar search
        if "Semantic Scholar" in sources_to_search:
            tasks.append(self.semantic_scholar_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level
            ))
            sources_queried.append("Semantic Scholar")
        
        # OpenAlex search (MASSIVE database - 200M+ papers) - using existing one
        if "OpenAlex" in sources_to_search:
            tasks.append(self.openalex_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("OpenAlex")
        
        # arXiv search (preprints and STEM papers)
        if "arXiv" in sources_to_search:
            tasks.append(self.arxiv_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("arXiv")
        
        # Crossref search (scholarly metadata)
        if "Crossref" in sources_to_search:
            tasks.append(self.crossref_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("Crossref")
        
        # DOAB search (open access books)
        if "DOAB" in sources_to_search:
            tasks.append(self.doab_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("DOAB")
        
        # Project Gutenberg search (public domain books)
        if "Project Gutenberg" in sources_to_search:
            tasks.append(self.project_gutenberg_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("Project Gutenberg")
        
        # Internet Archive search (digital library)
        if "Internet Archive" in sources_to_search:
            tasks.append(self.internet_archive_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("Internet Archive")
        
        # Open Library search (book metadata)
        if "Open Library" in sources_to_search:
            tasks.append(self.open_library_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("Open Library")
        
        # OpenStax search (free textbooks)
        if "OpenStax" in sources_to_search:
            tasks.append(self.openstax_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("OpenStax")
        
        # OAPEN search (academic books)
        if "OAPEN" in sources_to_search:
            tasks.append(self.oapen_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("OAPEN")
        
        # HathiTrust search (digital library) - commented out as client not working
        # if "HathiTrust" in sources_to_search:
        #     tasks.append(self.hathitrust_client.search(
        #         query=enhanced_query,
        #         year_start=request.year_start,
        #         year_end=request.year_end,
        #         discipline=request.discipline,
        #         education_level=request.education_level,
        #         limit=50
        #     ))
        #     sources_queried.append("HathiTrust")
        
        # Biodiversity Heritage Library search
        if "BHL" in sources_to_search:
            tasks.append(self.biodiversity_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=30
            ))
            sources_queried.append("BHL")
        
        # NLM Bookshelf search (medical textbooks)
        if "NLM Bookshelf" in sources_to_search:
            tasks.append(self.nlm_bookshelf_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=30
            ))
            sources_queried.append("NLM Bookshelf")
        
        # PLOS search (open access science)
        if "PLOS" in sources_to_search:
            tasks.append(self.plos_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("PLOS")
        
        # BioMed Central search (biomedical research)
        if "BioMed Central" in sources_to_search:
            tasks.append(self.biomed_central_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("BioMed Central")
        
        # Unpaywall search (free versions of papers)
        if "Unpaywall" in sources_to_search:
            tasks.append(self.unpaywall_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("Unpaywall")
        
        # MDPI search (multidisciplinary open access) - commented out as client not working
        # if "MDPI" in sources_to_search:
        #     tasks.append(self.mdpi_client.search(
        #         query=enhanced_query,
        #         year_start=request.year_start,
        #         year_end=request.year_end,
        #         discipline=request.discipline,
        #         education_level=request.education_level,
        #         limit=75
        #     ))
        #     sources_queried.append("MDPI")
        
        # Google Books search (academic books and texts)
        if "Google Books" in sources_to_search:
            tasks.append(self.google_books_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50
            ))
            sources_queried.append("Google Books")
        
        # Google Search (PDF-only search across the web)
        if "Google Search" in sources_to_search:
            tasks.append(self.google_search_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=50  # Increased limit for more PDF results
            ))
            sources_queried.append("Google Search")
        
        # OER Sources
        # Open Textbook Library
        if "Open Textbook Library" in sources_to_search:
            tasks.append(self.open_textbook_library_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("Open Textbook Library")
        
        # Pressbooks
        if "Pressbooks" in sources_to_search:
            tasks.append(self.pressbooks_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("Pressbooks")
        
        # LibreTexts
        if "LibreTexts" in sources_to_search:
            tasks.append(self.libretexts_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("LibreTexts")
        
        # MERLOT
        if "MERLOT" in sources_to_search:
            tasks.append(self.merlot_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("MERLOT")
        
        # OER Commons
        if "OER Commons" in sources_to_search:
            tasks.append(self.oer_commons_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("OER Commons")
        
        # MIT OpenCourseWare
        if "MIT OpenCourseWare" in sources_to_search:
            tasks.append(self.mit_ocw_client.search(
                query=enhanced_query,
                max_results=50
            ))
            sources_queried.append("MIT OpenCourseWare")
        
        # BASE search (Bielefeld Academic Search Engine)
        if "BASE" in sources_to_search:
            tasks.append(self.base_client.search(
                query=enhanced_query,
                year_start=request.year_start,
                year_end=request.year_end,
                discipline=request.discipline,
                education_level=request.education_level,
                limit=75
            ))
            sources_queried.append("BASE")
        
        # Execute all searches concurrently with improved timeout handling
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60.0  # Reasonable timeout
            )
        except asyncio.TimeoutError:
            logger.error("Overall search timeout - some APIs may be slow")
            results = [[] for _ in tasks]  # Return empty lists instead of None
        
        # Organize results by source
        results_by_source = {}
        total_before_filter = 0
        
        for i, result in enumerate(results):
            source_name = sources_queried[i]
            if isinstance(result, Exception):
                logger.error(f"Error from {source_name}: {result}")
                results_by_source[source_name] = []
            elif result:
                total_before_filter += len(result)
                logger.info(f"Got {len(result)} open access results from {source_name}")
                results_by_source[source_name] = result
            else:
                logger.info(f"No results from {source_name}")
                results_by_source[source_name] = []
        
        # Use advanced or basic optimizer based on configuration
        source_counts = {}  # Initialize source_counts
        search_metrics = {}  # Initialize search metrics
        
        if self.use_advanced_ranking:
            # Use advanced multi-stage ranking system
            try:
                # Prepare search context
                search_context = {
                    'discipline': request.discipline,
                    'education_level': request.education_level,
                    'year_start': request.year_start,
                    'year_end': request.year_end,
                    'enable_diversity': True,
                    'min_citations': request.min_citations,
                    'sort_by': getattr(request, 'sort_by', 'relevance')
                }
                
                # Run advanced optimization
                optimized_papers, search_metrics = await self.advanced_optimizer.optimize_search_results(
                    results_by_source=results_by_source,
                    query=enhanced_query,
                    search_context=search_context,
                    target_results=1000  # Process up to 1000 papers
                )
                
                # Extract source counts from metrics
                if 'source_distribution' in search_metrics:
                    source_counts = {source: stats['in_final'] 
                                   for source, stats in search_metrics['source_distribution'].items()}
                
            except Exception as e:
                logger.error(f"Advanced optimization failed, falling back to basic: {e}")
                # Fallback to basic optimizer
                optimized_papers, source_counts = self.search_optimizer.optimize_search_results(
                    results_by_source=results_by_source,
                    query=enhanced_query,
                    target_per_source=50,
                    max_total=1000
                )
        else:
            # Special handling for Google Search - return raw results without filtering
            if len(results_by_source) == 1 and "Google Search" in results_by_source:
                google_papers = results_by_source["Google Search"]
                optimized_papers = google_papers  # Raw results, no filtering
                source_counts = {"Google Search": len(google_papers)}
                logger.info(f"Google Search returning {len(google_papers)} raw PDF results")
            else:
                # Use basic search optimizer for other sources
                try:
                    optimized_papers, source_counts = self.search_optimizer.optimize_search_results(
                        results_by_source=results_by_source,
                        query=enhanced_query,
                        target_per_source=50,  # Adaptive, will vary by source quality
                        max_total=1000  # Process up to 1000 papers for ranking
                    )
                except Exception as e:
                    logger.error(f"Search optimization failed: {e}")
                    # Fallback: combine all results without optimization
                    optimized_papers = []
                    for source, papers in results_by_source.items():
                        papers_to_take = papers[:75]
                        optimized_papers.extend(papers_to_take)
                        source_counts[source] = len(papers_to_take)
        
        # Deduplicate the optimized papers (skip for Google Search raw results)
        if len(results_by_source) == 1 and "Google Search" in results_by_source:
            deduplicated_papers = optimized_papers  # Skip deduplication for Google Search
        else:
            deduplicated_papers = self._deduplicate_papers(optimized_papers)
        
        # Apply additional filters (skip for Google Search raw results)
        if len(results_by_source) == 1 and "Google Search" in results_by_source:
            filtered_papers = deduplicated_papers  # Skip additional filters for Google Search
        else:
            filtered_papers = deduplicated_papers
        
        # Apply citation count filter if specified
        if request.min_citations is not None:
            filtered_papers = [
                paper for paper in filtered_papers 
                if paper.citation_count is not None and paper.citation_count >= request.min_citations
            ]
        
        # Apply author filter if specified
        if hasattr(request, 'require_authors') and request.require_authors:
            filtered_papers = [
                paper for paper in filtered_papers 
                if paper.authors and len(paper.authors) > 0 and 
                not (len(paper.authors) == 1 and paper.authors[0].lower() in ['no authors listed', 'anonymous', ''])
            ]
        
        # Papers are already sorted by relevance from optimizer
        # Apply different sorting if requested
        if hasattr(request, 'sort_by') and request.sort_by != 'relevance':
            sorted_papers = sort_papers(filtered_papers, request.query, request.sort_by)
        else:
            sorted_papers = filtered_papers  # Already sorted by relevance
        
        # Apply pagination AFTER all filtering and sorting
        total_results = len(sorted_papers)
        start_idx = (request.page - 1) * request.per_page
        end_idx = start_idx + request.per_page
        paginated_papers = sorted_papers[start_idx:end_idx]
        
        # Log comprehensive statistics
        logger.info(f"Search summary: {total_before_filter} initial → "
                   f"{len(optimized_papers)} after optimization → "
                   f"{len(deduplicated_papers)} after dedup → "
                   f"{len(filtered_papers)} after filters → "
                   f"{total_results} final results → "
                   f"{len(paginated_papers)} on page {request.page}")
        
        # Log source distribution
        if source_counts:
            logger.info(f"Papers per source: {source_counts}")
        
        # Return with search metrics if available
        if self.use_advanced_ranking and search_metrics:
            return paginated_papers, sources_queried, total_results, source_counts, search_metrics
        else:
            return paginated_papers, sources_queried, total_results, source_counts
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Deduplicate papers based on DOI and title similarity"""
        seen_dois: Set[str] = set()
        seen_titles: Set[str] = set()
        deduplicated = []
        
        for paper in papers:
            # Check DOI first
            if paper.doi and paper.doi in seen_dois:
                continue
            
            # Check title similarity
            normalized_title = self._normalize_title(paper.title)
            if normalized_title in seen_titles:
                continue
            
            # Add to deduplicated list
            deduplicated.append(paper)
            
            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(normalized_title)
        
        return deduplicated
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Convert to lowercase
        title = title.lower()
        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        # Create a hash for efficient comparison
        return hashlib.md5(title.encode()).hexdigest()
    
    async def close(self):
        """Close all API clients"""
        await self.eric_client.close()
        await self.core_client.close()
        await self.doaj_client.close()
        await self.europe_pmc_client.close()
        await self.pmc_client.close()
        await self.pubmed_client.close()
        await self.semantic_scholar_client.close()
        # Close new API clients
        # await self.openalex_client.close()  # Commented out - not initialized
        await self.arxiv_client.close()
        await self.crossref_client.close()
        # Close book API clients
        await self.doab_client.close()
        await self.project_gutenberg_client.close()
        await self.internet_archive_client.close()
        await self.open_library_client.close()
        await self.openstax_client.close()
        await self.oapen_client.close()
        # await self.hathitrust_client.close()  # Not initialized
        await self.biodiversity_client.close()
        await self.nlm_bookshelf_client.close()
        # Close article API clients
        await self.plos_client.close()
        await self.biomed_central_client.close()
        await self.unpaywall_client.close()
        # await self.mdpi_client.close()  # Not initialized
        await self.google_books_client.close()
        await self.google_search_client.close()
        await self.base_client.close()
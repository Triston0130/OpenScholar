from .eric import ERICClient
from .core import COREClient
from .doaj import DOAJClient
from .europe_pmc import EuropePMCClient
from .pmc import PMCClient
from .pubmed import PubMedClient
from .semantic_scholar import SemanticScholarClient
from .openalex import OpenAlexClient
from .arxiv import ArxivClient
from .crossref import CrossrefClient
# Book sources
from .doab import DOABClient
from .project_gutenberg import ProjectGutenbergClient
from .internet_archive import InternetArchiveClient
from .open_library import OpenLibraryClient
from .openstax import OpenStaxClient
from .oapen import OAPENClient
# from .hathitrust import HathiTrustClient  # Removed - not working
from .biodiversity import BiodiversityClient
from .nlm_bookshelf import NLMBookshelfClient
# Article sources
from .plos import PLOSClient
from .biomed_central import BioMedCentralClient
from .unpaywall import UnpaywallClient
# from .mdpi import MDPIClient  # Removed - not working
from .google_books import GoogleBooksClient
from .base_search import BASEClient
from .base import BaseAPIClient
# OER sources
from .open_textbook_library import OpenTextbookLibraryClient
from .pressbooks import PressbooksClient
from .libretexts import LibreTextsClient
from .merlot import MERLOTClient
from .oer_commons import OERCommonsClient
from .mit_ocw import MITOpenCourseWareClient
from .google_search import GoogleSearchClient

__all__ = [
    "ERICClient", "COREClient", "DOAJClient", "EuropePMCClient", "PMCClient", 
    "PubMedClient", "SemanticScholarClient", "OpenAlexClient", "ArxivClient", 
    "CrossrefClient", "DOABClient", "ProjectGutenbergClient", "InternetArchiveClient", 
    "OpenLibraryClient", "OpenStaxClient", "OAPENClient",
    "BiodiversityClient", "NLMBookshelfClient", "PLOSClient", "BioMedCentralClient",
    "UnpaywallClient", "GoogleBooksClient", "GoogleSearchClient", "BASEClient", "BaseAPIClient",
    "OpenTextbookLibraryClient", "PressbooksClient", "LibreTextsClient",
    "MERLOTClient", "OERCommonsClient", "MITOpenCourseWareClient"
]
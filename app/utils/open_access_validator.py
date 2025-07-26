"""
Centralized Open Access Validation System

This module provides comprehensive validation to ensure that only
genuinely open access papers are returned to users.
"""
import re
import logging
from typing import Optional, Set, List
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

class OpenAccessValidator:
    """Comprehensive open access validation"""
    
    # Known paywall domains that should never be considered open access
    PAYWALL_DOMAINS = {
        'link.springer.com', 'springerlink.com', 'springer.com',
        'tandfonline.com', 'www.tandfonline.com',
        'wiley.com', 'onlinelibrary.wiley.com',
        'sciencedirect.com', 'www.sciencedirect.com',
        'elsevier.com', 'www.elsevier.com',
        'journals.sagepub.com', 'sagepub.com',
        'psycnet.apa.org', 'content.apa.org',
        'academic.oup.com', 'oup.com',
        'cambridge.org', 'www.cambridge.org',
        'jstor.org', 'www.jstor.org',
        'muse.jhu.edu', 'projectmuse.org',
        'erudit.org', 'www.erudit.org',  # Returns HTML pages instead of PDFs
        'projecteuclid.org', 'www.projecteuclid.org'  # Returns HTML pages instead of PDFs
    }
    
    # Known open access domains that are generally trustworthy
    OPEN_ACCESS_DOMAINS = {
        'europepmc.org', 'www.ncbi.nlm.nih.gov/pmc',
        'arxiv.org', 'www.arxiv.org',
        'biorxiv.org', 'www.biorxiv.org',
        'medrxiv.org', 'www.medrxiv.org',
        'files.eric.ed.gov', 'eric.ed.gov',
        'doaj.org', 'www.doaj.org',
        'core.ac.uk', 'www.core.ac.uk',
        'pubmed.ncbi.nlm.nih.gov/pmc',
        'plos.org', 'www.plos.org',
        'frontiersin.org', 'www.frontiersin.org',
        'mdpi.com', 'www.mdpi.com',
        'hindawi.com', 'www.hindawi.com',
        'nature.com/articles/s41',  # Nature Communications and other open access
        'bmj.com', 'www.bmj.com',  # BMJ Open and other open access BMJ journals
        # Educational and research domains commonly used in ERIC
        'ojs.jstem.org',  # Journal of Science Technology Engineering and Mathematics
        'repositorio.',  # Common pattern for institutional repositories
        'repository.',   # Common pattern for institutional repositories
        'digitalcommons.',  # Common institutional repository platform
        'scholarworks.',  # Common institutional repository platform
        'eprints.',  # Common institutional repository platform
        'researchgate.net',  # Research sharing platform
        'semanticscholar.org',  # Semantic Scholar provides open access papers
        # New API domains
        'openalex.org',  # OpenAlex database
        'arxiv.org',  # arXiv preprint server
        'export.arxiv.org',  # arXiv API domain
        'crossref.org'  # Crossref metadata (DOI links often lead to OA)
    }
    
    # Creative Commons license patterns
    CC_LICENSE_PATTERNS = [
        r'cc[-\s]by',
        r'creative\s*commons',
        r'cc[-\s]0',
        r'cc[-\s]by[-\s]sa',
        r'cc[-\s]by[-\s]nc',
        r'cc[-\s]by[-\s]nd'
    ]
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            follow_redirects=True,
            headers={'User-Agent': 'OpenScholar OpenAccess Validator 1.0'}
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def is_paywall_domain(self, url: str) -> bool:
        """Check if URL points to a known paywall domain"""
        if not url:
            return True
            
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. for comparison
            domain = domain.replace('www.', '')
            
            # Check against known paywall domains
            for paywall_domain in self.PAYWALL_DOMAINS:
                if domain == paywall_domain or domain.endswith('.' + paywall_domain):
                    logger.debug(f"Paywall domain detected: {domain}")
                    return True
                    
            return False
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return True  # Err on the side of caution
    
    def is_open_access_domain(self, url: str) -> bool:
        """Check if URL points to a known open access domain"""
        if not url:
            return False
            
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. for comparison
            domain = domain.replace('www.', '')
            
            # Check against known open access domains
            for oa_domain in self.OPEN_ACCESS_DOMAINS:
                if domain == oa_domain or domain.endswith('.' + oa_domain) or oa_domain in url.lower():
                    logger.debug(f"Open access domain detected: {domain}")
                    return True
                    
            return False
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return False
    
    def has_creative_commons_license(self, license_text: Optional[str], abstract_text: Optional[str] = None) -> bool:
        """Check if text contains Creative Commons license indicators"""
        if not license_text and not abstract_text:
            return False
            
        text_to_check = []
        if license_text:
            text_to_check.append(license_text.lower())
        if abstract_text:
            text_to_check.append(abstract_text.lower())
            
        combined_text = ' '.join(text_to_check)
        
        for pattern in self.CC_LICENSE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                logger.debug(f"Creative Commons license pattern found: {pattern}")
                return True
                
        return False
    
    def is_doi_likely_open_access(self, doi: str) -> bool:
        """
        Check if DOI pattern suggests open access
        This is a heuristic and should be used with other validation
        """
        if not doi:
            return False
            
        # Some DOI prefixes are more likely to be open access
        open_access_prefixes = [
            '10.1371',  # PLOS
            '10.3389',  # Frontiers
            '10.3390',  # MDPI
            '10.1155',  # Hindawi
            '10.1038/s41467',  # Nature Communications
            '10.1038/s41598',  # Scientific Reports
            '10.1186',  # BioMed Central
            '10.1371/journal.pone',  # PLOS ONE specifically
        ]
        
        # DOI prefixes that are typically paywalled
        paywall_prefixes = [
            '10.1111',  # Wiley
            '10.1007',  # Springer
            '10.1016',  # Elsevier
            '10.1080',  # Taylor & Francis
            '10.1177',  # SAGE
            '10.1093',  # Oxford Academic (some OA, but mostly paywall)
            '10.1017',  # Cambridge
            '10.2307',  # JSTOR
        ]
        
        # Check paywall prefixes first
        for prefix in paywall_prefixes:
            if doi.startswith(prefix):
                logger.debug(f"Paywall DOI prefix detected: {prefix}")
                return False
        
        # Then check open access prefixes
        for prefix in open_access_prefixes:
            if doi.startswith(prefix):
                logger.debug(f"Open access DOI prefix detected: {prefix}")
                return True
                
        return False
    
    async def validate_url_accessibility(self, url: str) -> bool:
        """
        Check if URL is actually accessible without authentication
        This makes a HEAD request to check accessibility
        """
        if not url:
            return False
            
        try:
            # First check domain
            if self.is_paywall_domain(url):
                logger.debug(f"URL rejected due to paywall domain: {url}")
                return False
                
            if self.is_open_access_domain(url):
                logger.debug(f"URL accepted due to open access domain: {url}")
                return True
                
            # For unknown domains, try to access
            response = await self.client.head(url)
            
            # Check if we get redirected to a paywall
            if response.url and self.is_paywall_domain(str(response.url)):
                logger.debug(f"URL redirects to paywall: {url} -> {response.url}")
                return False
                
            # Check status code
            if response.status_code not in [200, 202, 204]:
                logger.debug(f"URL returned non-success status: {url} -> {response.status_code}")
                return False
                
            logger.debug(f"URL appears accessible: {url}")
            return True
            
        except httpx.TimeoutException:
            logger.debug(f"URL validation timeout: {url}")
            return False
        except Exception as e:
            logger.debug(f"URL validation error for {url}: {e}")
            return False
    
    def validate_paper_metadata(self, 
                              title: str,
                              journal: Optional[str] = None,
                              doi: Optional[str] = None,
                              license_info: Optional[str] = None,
                              abstract: Optional[str] = None,
                              full_text_url: Optional[str] = None) -> tuple[bool, str]:
        """
        Comprehensive validation of paper metadata for open access status
        Returns (is_open_access, reason)
        """
        
        # Check DOI first - if it's a known paywall DOI pattern, reject immediately
        if doi:
            if not self.is_doi_likely_open_access(doi):
                # Check if it's explicitly a paywall DOI
                paywall_prefixes = ['10.1111', '10.1007', '10.1016', '10.1080', '10.1177', '10.1017', '10.2307']
                for prefix in paywall_prefixes:
                    if doi.startswith(prefix):
                        return False, f"DOI from paywall publisher: {doi}"
        
        # Check for paywall URL
        if full_text_url and self.is_paywall_domain(full_text_url):
            return False, f"URL points to paywall domain: {full_text_url}"
            
        # Check for open access URL
        if full_text_url and self.is_open_access_domain(full_text_url):
            return True, f"URL points to open access domain: {full_text_url}"
            
        # Special case: Educational URLs from academic institutions and educational journals
        # These are often open access even if not in our main list
        if full_text_url:
            url_lower = full_text_url.lower()
            educational_patterns = [
                '.edu/', '.ac.', '.org/', 'ojs.', 'journal',
                'repository', 'digital', 'scholar', 'research'
            ]
            if any(pattern in url_lower for pattern in educational_patterns):
                # Additional check: make sure it's not a known paywall
                if not self.is_paywall_domain(full_text_url):
                    return True, f"Educational/research URL (likely open access): {full_text_url}"
            
        # Check for Creative Commons license
        if self.has_creative_commons_license(license_info, abstract):
            return True, "Creative Commons license detected"
            
        # Check DOI pattern
        if doi and self.is_doi_likely_open_access(doi):
            return True, f"Open access DOI pattern: {doi}"
            
        # Check journal name for known open access publishers
        if journal:
            journal_lower = journal.lower()
            open_access_journals = [
                'plos', 'frontiers', 'mdpi', 'hindawi', 'bmc',
                'biomedcentral', 'nature communications', 'scientific reports',
                'bmj open', 'open access',
                # Educational and research journals commonly open access
                'journal of science technology engineering', 'jstem',
                'international journal of', 'european journal of',
                'educational', 'education research', 'teaching',
                'learning', 'pedagogical', 'curriculum'
            ]
            
            for oa_journal in open_access_journals:
                if oa_journal in journal_lower:
                    return True, f"Open access journal detected: {journal}"
        
        # If no clear indicators and URL is not from trusted domain, reject
        if full_text_url:
            return False, f"Cannot verify open access status for URL: {full_text_url}"
        else:
            return False, "No full text URL provided"
    
    async def validate_paper(self, 
                           title: str,
                           journal: Optional[str] = None,
                           doi: Optional[str] = None,
                           license_info: Optional[str] = None,
                           abstract: Optional[str] = None,
                           full_text_url: Optional[str] = None,
                           check_url_accessibility: bool = False) -> tuple[bool, str]:
        """
        Complete validation of a paper for open access status
        Returns (is_open_access, reason)
        """
        
        # First check metadata
        is_oa, reason = self.validate_paper_metadata(
            title, journal, doi, license_info, abstract, full_text_url
        )
        
        if not is_oa:
            return is_oa, reason
            
        # If metadata suggests open access, optionally verify URL accessibility
        if check_url_accessibility and full_text_url:
            is_accessible = await self.validate_url_accessibility(full_text_url)
            if not is_accessible:
                return False, f"URL not accessible or redirects to paywall: {full_text_url}"
                
        return True, reason


# Global instance for use across the application
open_access_validator = OpenAccessValidator()
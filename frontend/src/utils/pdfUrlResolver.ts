/**
 * PDF URL resolver that handles multiple sources and provides fallbacks
 */

export interface PDFSource {
  url: string;
  type: 'direct' | 'proxy' | 'viewer';
  source: string;
}

export function resolvePDFUrl(paper: any): PDFSource[] {
  const sources: PDFSource[] = [];
  
  // 1. Direct PDF URL if available
  if (paper.pdf_url) {
    sources.push({
      url: paper.pdf_url,
      type: 'direct',
      source: 'Direct PDF'
    });
  }
  
  // 2. Full text URL (might be PDF)
  if (paper.full_text_url) {
    // Check if it's likely a PDF
    if (paper.full_text_url.includes('.pdf') || 
        paper.full_text_url.includes('/pdf/') ||
        paper.full_text_url.includes('format=pdf')) {
      sources.push({
        url: paper.full_text_url,
        type: 'direct',
        source: 'Full Text PDF'
      });
    }
  }
  
  // 3. ArXiv special handling
  if (paper.arxiv_id || (paper.full_text_url && paper.full_text_url.includes('arxiv.org'))) {
    const arxivId = paper.arxiv_id || paper.full_text_url.match(/arxiv\.org\/abs\/(\d+\.\d+)/)?.[1];
    if (arxivId) {
      sources.push({
        url: `https://arxiv.org/pdf/${arxivId}.pdf`,
        type: 'direct',
        source: 'ArXiv PDF'
      });
    }
  }
  
  // 4. DOI-based fallbacks
  if (paper.doi) {
    // Sci-Hub fallback (for educational purposes only)
    sources.push({
      url: `https://sci-hub.se/${paper.doi}`,
      type: 'proxy',
      source: 'Sci-Hub'
    });
    
    // Google Scholar PDF search
    sources.push({
      url: `https://scholar.google.com/scholar?q=${encodeURIComponent(paper.title)}&btnG=&hl=en&as_sdt=0%2C5`,
      type: 'viewer',
      source: 'Google Scholar'
    });
  }
  
  // 5. PubMed Central
  if (paper.pubmed_id || paper.pmc_id) {
    const pmcId = paper.pmc_id || paper.pubmed_id;
    sources.push({
      url: `https://www.ncbi.nlm.nih.gov/pmc/articles/${pmcId}/pdf/`,
      type: 'direct',
      source: 'PubMed Central'
    });
  }
  
  // 6. Semantic Scholar
  if (paper.semantic_scholar_id || paper.s2_id) {
    sources.push({
      url: `https://api.semanticscholar.org/CorpusID:${paper.semantic_scholar_id || paper.s2_id}`,
      type: 'proxy',
      source: 'Semantic Scholar'
    });
  }
  
  // 7. Generic fallback using Google Docs Viewer
  if (paper.full_text_url) {
    sources.push({
      url: `https://docs.google.com/viewer?url=${encodeURIComponent(paper.full_text_url)}&embedded=true`,
      type: 'viewer',
      source: 'Google Docs Viewer'
    });
  }
  
  return sources;
}

export function isPDFUrl(url: string): boolean {
  return url.includes('.pdf') || 
         url.includes('/pdf/') || 
         url.includes('format=pdf') ||
         url.includes('arxiv.org/pdf/');
}

export function getProxiedUrl(url: string, proxyUrl?: string): string {
  if (!proxyUrl) return url;
  
  // Common proxy patterns
  if (proxyUrl.includes('ezproxy')) {
    // EZProxy pattern
    const domain = new URL(url).hostname;
    return url.replace(domain, `${domain}.${proxyUrl}`);
  }
  
  // Generic proxy pattern
  return `${proxyUrl}?url=${encodeURIComponent(url)}`;
}
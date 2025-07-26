import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Paper } from '../types';
import { getPaperCollections, addPaperToCollection, removePaperFromCollection } from '../utils/collections';
import { formatCitation } from '../utils/citationFormatter';
import { generateAccessLinks, AccessLink } from '../utils/proxy';
import CollectionSelector from './CollectionSelector';
import PDFViewerSmart from './PDFViewerSmart';

interface ResultCardProps {
  paper: Paper;
  searchQuery?: string;
  showCheckbox?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (paper: Paper, selected: boolean) => void;
}

const ResultCard: React.FC<ResultCardProps> = ({ 
  paper, 
  searchQuery, 
  showCheckbox = false, 
  isSelected = false, 
  onToggleSelect 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCitationMenu, setShowCitationMenu] = useState(false);
  const [showCollectionSelector, setShowCollectionSelector] = useState(false);
  const [paperCollections, setPaperCollections] = useState<any[]>([]);
  const [accessLinks, setAccessLinks] = useState<AccessLink[]>([]);
  const [showPDFViewer, setShowPDFViewer] = useState(false);
  const [extractedPdfUrl, setExtractedPdfUrl] = useState<string | null>(null);
  const [isExtractingPdf, setIsExtractingPdf] = useState(false);
  const citationMenuRef = useRef<HTMLDivElement>(null);

  const updatePaperCollections = useCallback(() => {
    setPaperCollections(getPaperCollections(paper));
  }, [paper]);

  const updateAccessLinks = useCallback(() => {
    setAccessLinks(generateAccessLinks(paper));
  }, [paper]);

  useEffect(() => {
    updatePaperCollections();
    updateAccessLinks();
  }, [paper, updatePaperCollections, updateAccessLinks]);

  useEffect(() => {
    const handleCollectionsChange = () => {
      updatePaperCollections();
    };

    const handleProxySettingsChange = () => {
      updateAccessLinks();
    };

    window.addEventListener('collectionsChanged', handleCollectionsChange);
    window.addEventListener('proxySettingsChanged', handleProxySettingsChange);
    return () => {
      window.removeEventListener('collectionsChanged', handleCollectionsChange);
      window.removeEventListener('proxySettingsChanged', handleProxySettingsChange);
    };
  }, [updatePaperCollections, updateAccessLinks]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (citationMenuRef.current && !citationMenuRef.current.contains(event.target as Node)) {
        setShowCitationMenu(false);
      }
    };

    if (showCitationMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showCitationMenu]);

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const formatAuthors = (authors: string[]) => {
    if (!authors || authors.length === 0) return 'No authors listed';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', ')} et al.`;
  };

  const getSourceColor = (source: string) => {
    const colors: { [key: string]: string } = {
      'ERIC': 'bg-blue-100 text-blue-800 hover:bg-blue-200',
      'CORE': 'bg-green-100 text-green-800 hover:bg-green-200', 
      'DOAJ': 'bg-purple-100 text-purple-800 hover:bg-purple-200',
      'Europe PMC': 'bg-red-100 text-red-800 hover:bg-red-200',
      'PubMed Central': 'bg-orange-100 text-orange-800 hover:bg-orange-200',
      'PubMed': 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200',
      'Semantic Scholar': 'bg-teal-100 text-teal-800 hover:bg-teal-200',
      // Book sources
      'DOAB': 'bg-amber-100 text-amber-800 hover:bg-amber-200',
      'Project Gutenberg': 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200',
      'Internet Archive': 'bg-cyan-100 text-cyan-800 hover:bg-cyan-200',
      'Open Library': 'bg-rose-100 text-rose-800 hover:bg-rose-200',
      // OER sources
      'Open Textbook Library': 'bg-lime-100 text-lime-800 hover:bg-lime-200',
      'Pressbooks': 'bg-violet-100 text-violet-800 hover:bg-violet-200',
      'LibreTexts': 'bg-fuchsia-100 text-fuchsia-800 hover:bg-fuchsia-200',
      'MERLOT': 'bg-sky-100 text-sky-800 hover:bg-sky-200',
      'OER Commons': 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
      'MIT OpenCourseWare': 'bg-slate-100 text-slate-800 hover:bg-slate-200',
    };
    return colors[source] || 'bg-gray-100 text-gray-800 hover:bg-gray-200';
  };

  const getSourceUrl = (source: string) => {
    const urls: { [key: string]: string } = {
      'ERIC': 'https://eric.ed.gov/',
      'CORE': 'https://core.ac.uk/',
      'DOAJ': 'https://doaj.org/',
      'Europe PMC': 'https://europepmc.org/',
      'PubMed Central': 'https://www.ncbi.nlm.nih.gov/pmc/',
      'PubMed': 'https://pubmed.ncbi.nlm.nih.gov/',
      'Semantic Scholar': 'https://www.semanticscholar.org/',
      // Book sources
      'DOAB': 'https://www.doabooks.org/',
      'Project Gutenberg': 'https://www.gutenberg.org/',
      'Internet Archive': 'https://archive.org/',
      'Open Library': 'https://openlibrary.org/',
      // OER sources
      'Open Textbook Library': 'https://open.umn.edu/opentextbooks/',
      'Pressbooks': 'https://pressbooks.com/',
      'LibreTexts': 'https://libretexts.org/',
      'MERLOT': 'https://www.merlot.org/',
      'OER Commons': 'https://www.oercommons.org/',
      'MIT OpenCourseWare': 'https://ocw.mit.edu/',
    };
    return urls[source] || '#';
  };

  const highlightKeywords = (text: string, query?: string) => {
    if (!query || !text) return text;
    
    const keywords = query.toLowerCase().split(/\s+/).filter(word => word.length > 2);
    let highlightedText = text;
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
    });
    
    return highlightedText;
  };

  const generateCitation = (format: 'apa' | 'mla' | 'chicago') => {
    return formatCitation(paper, format);
  };

  const copyCitation = (format: 'apa' | 'mla' | 'chicago') => {
    const citation = generateCitation(format);
    navigator.clipboard.writeText(citation).then(() => {
      // You could add a toast notification here
      setShowCitationMenu(false);
    });
  };

  const handleSaveToCollection = (collectionId: string, tags?: string[], notes?: string, folderId?: string) => {
    addPaperToCollection(paper, collectionId, tags, notes, folderId);
    updatePaperCollections();
  };

  const handleRemoveFromCollection = (collectionId: string) => {
    removePaperFromCollection(paper, collectionId);
    updatePaperCollections();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Title with Action Buttons */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-start flex-1">
          {showCheckbox && (
            <div className="mr-3 mt-1">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => onToggleSelect?.(paper, e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
          )}
          <h3 className="text-lg font-semibold text-gray-900 leading-tight flex-1 mr-3">
          {paper.full_text_url ? (
            <a
              href={paper.full_text_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 hover:underline"
              dangerouslySetInnerHTML={{ __html: highlightKeywords(paper.title, searchQuery) }}
            />
          ) : (
            <span dangerouslySetInnerHTML={{ __html: highlightKeywords(paper.title, searchQuery) }} />
          )}
          </h3>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Save to Collection Button */}
          <button
            onClick={() => setShowCollectionSelector(true)}
            className={`flex items-center px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              paperCollections.length > 0
                ? 'text-blue-700 bg-blue-100 hover:bg-blue-200'
                : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
            }`}
            title={paperCollections.length > 0 ? `Saved in ${paperCollections.length} collection(s)` : 'Save to collection'}
          >
            <svg className="w-4 h-4 mr-1" fill={paperCollections.length > 0 ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            {paperCollections.length > 0 ? `Saved (${paperCollections.length})` : 'Save'}
          </button>

          {/* View PDF Button */}
          {paper.full_text_url && (
            <button
              onClick={async (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('[ResultCard] PDF button clicked, checking if extraction needed for:', paper.full_text_url);
                
                // Check if this is from Open Textbook Library or LibreTexts and needs PDF extraction
                const needsExtraction = paper.source === 'Open Textbook Library' || paper.source === 'LibreTexts';
                
                if (needsExtraction && !extractedPdfUrl) {
                  setIsExtractingPdf(true);
                  try {
                    const response = await fetch('/extract-pdf-url', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ url: paper.full_text_url })
                    });
                    
                    if (response.ok) {
                      const data = await response.json();
                      console.log('[ResultCard] PDF extraction result:', data);
                      setExtractedPdfUrl(data.pdf_url);
                    } else {
                      console.error('[ResultCard] PDF extraction failed, using original URL');
                      setExtractedPdfUrl(paper.full_text_url || null);
                    }
                  } catch (error) {
                    console.error('[ResultCard] PDF extraction error:', error);
                    setExtractedPdfUrl(paper.full_text_url || null);
                  } finally {
                    setIsExtractingPdf(false);
                  }
                }
                
                setShowPDFViewer(true);
              }}
              className="flex items-center px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors"
              title="View PDF with annotations"
              disabled={isExtractingPdf}
            >
              {isExtractingPdf ? (
                <>
                  <svg className="animate-spin w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  View PDF
                </>
              )}
            </button>
          )}

          {/* Copy Citation Dropdown */}
          <div className="relative" ref={citationMenuRef}>
          <button
            onClick={() => setShowCitationMenu(!showCitationMenu)}
            className="flex items-center px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            title="Copy Citation"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            Cite
          </button>
          
          {showCitationMenu && (
            <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg border border-gray-200 z-10">
              <div className="py-1">
                <button
                  onClick={() => copyCitation('apa')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  APA Style
                </button>
                <button
                  onClick={() => copyCitation('mla')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  MLA Style
                </button>
                <button
                  onClick={() => copyCitation('chicago')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Chicago Style
                </button>
              </div>
            </div>
          )}
          </div>
        </div>
      </div>

      {/* Authors and Year */}
      <div className="flex flex-wrap items-center gap-2 mb-3 text-sm text-gray-600">
        <span>{formatAuthors(paper.authors)}</span>
        {paper.year && (
          <>
            <span>•</span>
            <span>{paper.year}</span>
          </>
        )}
      </div>

      {/* Source and Journal Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        <a
          href={getSourceUrl(paper.source)}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium cursor-pointer transition-colors ${getSourceColor(paper.source)}`}
          title={`View ${paper.source} database`}
        >
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-1M10 6V4a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2h-2M10 6l8 8m0 0V10m0 4.5h-4.5" />
          </svg>
          {paper.source}
        </a>
        {paper.journal && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            📄 {paper.journal}
          </span>
        )}
        {paper.publisher && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            🏢 {paper.publisher}
          </span>
        )}
        {paper.content_type === 'book' && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            📚 Book
          </span>
        )}
        {paper.page_count && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            📄 {paper.page_count} pages
          </span>
        )}
        {paper.language && paper.language !== 'en' && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            🌐 {paper.language.toUpperCase()}
          </span>
        )}
      </div>

      {/* Abstract with Keyword Highlighting */}
      <div className="mb-4">
        <p 
          className="text-gray-700 leading-relaxed"
          dangerouslySetInnerHTML={{ 
            __html: highlightKeywords(
              isExpanded ? paper.abstract : truncateText(paper.abstract, 300), 
              searchQuery
            ) 
          }}
        />
        {paper.abstract.length > 300 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium mt-2 focus:outline-none"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Access Links */}
      <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
        {accessLinks.map((link, index) => (
          <a
            key={index}
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
              link.type === 'free' 
                ? 'text-green-700 bg-green-50 hover:bg-green-100 border border-green-200' 
                : link.type === 'university'
                ? 'text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200'
                : 'text-gray-700 bg-gray-50 hover:bg-gray-100 border border-gray-200'
            }`}
            title={link.type === 'free' ? 'Open access - free to read' : 
                   link.type === 'university' ? 'This link will open through your campus library proxy' : 
                   'Publisher access (may require subscription)'}
          >
            <span className="mr-1.5">{link.icon}</span>
            {link.label}
            <svg className="w-3 h-3 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ))}

        {/* Citation Count or Download Formats */}
        {paper.content_type === 'book' && paper.download_formats ? (
          <div className="inline-flex items-center text-sm px-3 py-1.5">
            <svg className="w-4 h-4 mr-1.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-green-600 font-medium">Available: </span>
            <div className="flex gap-1 ml-1">
              {paper.download_formats.map((format, index) => (
                <span key={index} className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                  {format.toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="inline-flex items-center text-sm text-gray-600 px-3 py-1.5">
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            {paper.citation_count !== null && paper.citation_count !== undefined ? (
              <>
                {paper.citation_count.toLocaleString()} citation{paper.citation_count !== 1 ? 's' : ''}
                {paper.influential_citation_count !== null && paper.influential_citation_count !== undefined && paper.influential_citation_count > 0 && (
                  <span className="ml-2 px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full font-medium" title="Influential citations">
                    {paper.influential_citation_count} influential
                  </span>
                )}
              </>
            ) : (
              <span className="text-gray-400">{paper.content_type === 'book' ? 'Book resource' : 'Citations loading...'}</span>
            )}
          </div>
        )}

        {/* Relevance Score Indicator */}
        {paper.relevance_score && (
          <div className="inline-flex items-center text-sm px-3 py-1.5" title="Search relevance score">
            <svg className="w-4 h-4 mr-1.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <span className="text-blue-600 font-medium">
              {Math.round(paper.relevance_score * 100)}% relevance
            </span>
            {paper.relevance_factors?.exact_phrase_match && (
              <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium" title="Contains exact phrase match">
                ✓ Exact match
              </span>
            )}
          </div>
        )}

        {/* Quality Indicators */}
        <div className="flex items-center gap-2">
          {parseInt(paper.year) >= 2020 && (
            <span className="inline-flex items-center px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium" title="Recent publication">
              🕐 Recent
            </span>
          )}
          {paper.citation_count && paper.citation_count >= 50 && (
            <span className="inline-flex items-center px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full font-medium" title="Highly cited">
              ⭐ Popular
            </span>
          )}
          {paper.journal && (paper.journal.toLowerCase().includes('nature') || paper.journal?.toLowerCase().includes('science') || paper.journal?.toLowerCase().includes('cell')) && (
            <span className="inline-flex items-center px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium" title="High-impact journal">
              🏆 Top journal
            </span>
          )}
        </div>
      </div>

      {/* Collection Selector Modal */}
      <CollectionSelector
        isOpen={showCollectionSelector}
        onClose={() => setShowCollectionSelector(false)}
        paper={paper}
        onSaveToCollection={handleSaveToCollection}
        onRemoveFromCollection={handleRemoveFromCollection}
      />

      {/* PDF Viewer Modal */}
      {showPDFViewer && paper.full_text_url && (
        <PDFViewerSmart
          paper={paper}
          pdfUrl={extractedPdfUrl || paper.full_text_url}
          collectionId={paperCollections.length > 0 ? paperCollections[0].id : undefined}
          onClose={() => {
            setShowPDFViewer(false);
            // Don't reset extractedPdfUrl to avoid re-extraction next time
          }}
        />
      )}
    </div>
  );
};

export default ResultCard;
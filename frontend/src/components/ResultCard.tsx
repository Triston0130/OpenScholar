import React, { useState, useRef, useEffect } from 'react';
import { Paper } from '../types';
import { getPaperCollections, addPaperToCollection, removePaperFromCollection } from '../utils/collections';
import CollectionSelector from './CollectionSelector';

interface ResultCardProps {
  paper: Paper;
  searchQuery?: string;
}

const ResultCard: React.FC<ResultCardProps> = ({ paper, searchQuery }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCitationMenu, setShowCitationMenu] = useState(false);
  const [showCollectionSelector, setShowCollectionSelector] = useState(false);
  const [paperCollections, setPaperCollections] = useState<any[]>([]);
  const citationMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    updatePaperCollections();
  }, [paper]);

  useEffect(() => {
    const handleCollectionsChange = () => {
      updatePaperCollections();
    };

    window.addEventListener('collectionsChanged', handleCollectionsChange);
    return () => window.removeEventListener('collectionsChanged', handleCollectionsChange);
  }, [paper]);

  const updatePaperCollections = () => {
    setPaperCollections(getPaperCollections(paper));
  };

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
    const authors = paper.authors.join(', ');
    const year = paper.year;
    const title = paper.title;
    const journal = paper.journal || paper.source;
    
    switch (format) {
      case 'apa':
        return `${authors} (${year}). ${title}. ${journal}.`;
      case 'mla':
        return `${authors}. "${title}." ${journal}, ${year}.`;
      case 'chicago':
        return `${authors}. "${title}." ${journal} (${year}).`;
      default:
        return `${authors} (${year}). ${title}. ${journal}.`;
    }
  };

  const copyCitation = (format: 'apa' | 'mla' | 'chicago') => {
    const citation = generateCitation(format);
    navigator.clipboard.writeText(citation).then(() => {
      // You could add a toast notification here
      setShowCitationMenu(false);
    });
  };

  const handleSaveToCollection = (collectionId: string) => {
    addPaperToCollection(paper, collectionId);
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

      {/* Links */}
      <div className="flex flex-wrap gap-4 pt-4 border-t border-gray-200">
        {paper.full_text_url && (
          <a
            href={paper.full_text_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            {paper.full_text_url.includes('pmc') || paper.full_text_url.includes('doi.org') || paper.full_text_url.includes('doaj') || paper.full_text_url.includes('core') ? 
              'Full Text' : 
              'View Details'
            }
            {(paper.full_text_url.includes('pmc') || paper.full_text_url.includes('doi.org')) && (
              <span className="ml-1 px-1 py-0.5 bg-green-100 text-green-700 text-xs rounded">PDF</span>
            )}
          </a>
        )}
        
        {paper.doi && (
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            DOI: {paper.doi}
          </a>
        )}
      </div>

      {/* Collection Selector Modal */}
      <CollectionSelector
        isOpen={showCollectionSelector}
        onClose={() => setShowCollectionSelector(false)}
        paper={paper}
        onSaveToCollection={handleSaveToCollection}
        onRemoveFromCollection={handleRemoveFromCollection}
      />
    </div>
  );
};

export default ResultCard;
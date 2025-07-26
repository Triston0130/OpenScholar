import React, { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import SearchForm from '../components/SearchForm';
import ResultCard from '../components/ResultCard';
import ExportBar from '../components/ExportBar';
import Pagination from '../components/Pagination';
import CollectionsOverview from '../components/CollectionsOverview';
import SettingsModal from '../components/SettingsModal';
import UserProfile from '../components/UserProfile';
import AuthModal from '../components/AuthModal';
import ProfileSettingsModal from '../components/ProfileSettingsModal';
import EmailSettings from '../components/EmailSettings';
import { Paper, SearchRequest } from '../types';
import { searchPapers, exportPapers, downloadFile } from '../utils/api';
import { getAllCollectionsWithPapers, addPaperToCollection } from '../utils/collections';
import { getProxySettings } from '../utils/proxy';
import CollectionSelector from '../components/CollectionSelector';
import SearchRelevanceInfo from '../components/SearchRelevanceInfo';
import { getAllAnnotations } from '../utils/annotations';

interface PaginationCache {
  [key: string]: {
    papers: Paper[];
    sourcesQueried: string[];
    sourceCounts?: Record<string, number>;
    totalResults: number;
  };
}

interface SearchPageProps {
  onNavigate: (page: 'search' | 'flashcards' | 'landing') => void;
}

const SearchPage: React.FC<SearchPageProps> = ({ onNavigate }) => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [sourcesQueried, setSourcesQueried] = useState<string[]>([]);
  const [sourceCounts, setSourceCounts] = useState<Record<string, number>>({});
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [sortBy, setSortBy] = useState<'relevance' | 'newest' | 'oldest' | 'citations'>('relevance');
  const [currentSearchRequest, setCurrentSearchRequest] = useState<SearchRequest | null>(null);
  const [showCollections, setShowCollections] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [showProfileSettings, setShowProfileSettings] = useState(false);
  const [showEmailSettings, setShowEmailSettings] = useState(false);
  const [totalSavedCount, setTotalSavedCount] = useState(0);
  const [proxySettings, setProxySettings] = useState(getProxySettings());
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);
  const [showBulkMode, setShowBulkMode] = useState(false);
  const [showBulkCollectionSelector, setShowBulkCollectionSelector] = useState(false);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [paginationCache, setPaginationCache] = useState<PaginationCache>({});
  const [currentSearchId, setCurrentSearchId] = useState<string>('');

  useEffect(() => {
    updateSavedCount();
    // Listen for collections changes
    const handleCollectionsChange = () => updateSavedCount();
    const handleProxySettingsChange = () => setProxySettings(getProxySettings());
    
    window.addEventListener('collectionsChanged', handleCollectionsChange);
    window.addEventListener('proxySettingsChanged', handleProxySettingsChange);
    return () => {
      window.removeEventListener('collectionsChanged', handleCollectionsChange);
      window.removeEventListener('proxySettingsChanged', handleProxySettingsChange);
    };
  }, []);

  // Close export dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showExportDropdown) {
        setShowExportDropdown(false);
      }
    };

    if (showExportDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportDropdown]);

  const updateSavedCount = () => {
    const collections = getAllCollectionsWithPapers();
    const totalCount = collections.reduce((sum, collection) => sum + collection.papers.length, 0);
    setTotalSavedCount(totalCount);
  };

  const handleToggleSelect = (paper: Paper, selected: boolean) => {
    setSelectedPapers(prev => {
      if (selected) {
        return [...prev, paper];
      } else {
        return prev.filter(p => p.title !== paper.title);
      }
    });
  };

  const handleBulkAddToCollection = (collectionId: string, tags?: string[], notes?: string, folderId?: string) => {
    selectedPapers.forEach(paper => {
      addPaperToCollection(paper, collectionId, tags, notes, folderId);
    });
    setSelectedPapers([]);
    setShowBulkCollectionSelector(false);
    updateSavedCount();
    toast.success(`Added ${selectedPapers.length} papers to collection`);
  };

  const handleBulkExport = async (format: 'csv' | 'json' | 'bib') => {
    if (selectedPapers.length === 0) {
      toast.error('No papers selected for export');
      return;
    }

    setIsExporting(true);
    
    try {
      const blob = await exportPapers({ papers: selectedPapers, format });
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `openscholar_selected_${timestamp}.${format}`;
      
      downloadFile(blob, filename);
      toast.success(`Successfully exported ${selectedPapers.length} selected papers as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to export papers');
    } finally {
      setIsExporting(false);
    }
  };

  // Generate cache key for pagination consistency
  const generateCacheKey = (searchRequest: SearchRequest, searchId: string) => {
    return `${searchId}-page-${searchRequest.page}-perpage-${searchRequest.per_page}-sort-${searchRequest.sort_by}`;
  };

  // Generate unique search ID to ensure cache isolation between searches
  // IMPORTANT: Don't include page, per_page, or sort_by in the search ID
  // as these are handled separately in the cache key
  const generateSearchId = (searchRequest: SearchRequest) => {
    const searchParams = {
      query: searchRequest.query,
      year_start: searchRequest.year_start,
      year_end: searchRequest.year_end,
      discipline: searchRequest.discipline,
      education_level: searchRequest.education_level,
      publication_type: searchRequest.publication_type,
      study_type: searchRequest.study_type,
      min_citations: searchRequest.min_citations,
      sources: searchRequest.sources?.sort().join(',') || '',
      require_authors: searchRequest.require_authors
    };
    return btoa(JSON.stringify(searchParams)).replace(/[/+=]/g, '');
  };

  const performSearchRequest = async (searchRequest: SearchRequest, isNewSearch = false) => {
    const searchId = currentSearchId || generateSearchId(searchRequest);
    const cacheKey = generateCacheKey(searchRequest, searchId);
    
    // Check cache first for pagination requests
    if (!isNewSearch && paginationCache[cacheKey]) {
      const cached = paginationCache[cacheKey];
      setPapers(cached.papers);
      setSourcesQueried(cached.sourcesQueried);
      setSourceCounts(cached.sourceCounts || {});
      setTotalResults(cached.totalResults);
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await searchPapers(searchRequest);
      setPapers(response.papers);
      setSourcesQueried(response.sources_queried);
      setSourceCounts(response.source_counts || {});
      setTotalResults(response.total_results);
      
      // Cache the result
      setPaginationCache(prev => ({
        ...prev,
        [cacheKey]: {
          papers: response.papers,
          sourcesQueried: response.sources_queried,
          sourceCounts: response.source_counts || {},
          totalResults: response.total_results
        }
      }));
      
      if (isNewSearch) {
        setSearchPerformed(true);
        if (response.papers.length === 0) {
          toast.error('No papers found. Try different keywords or filters.');
        } else {
          toast.success(`Found ${response.total_results || response.papers.length} papers`);
        }
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to search papers');
      setPapers([]);
      setSourceCounts({});  // Reset source counts on error
      setTotalResults(0);
      if (isNewSearch) {
        setSearchPerformed(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (searchRequest: SearchRequest, resetPage = true) => {
    setSearchPerformed(false);
    setCurrentSearchRequest(searchRequest);
    
    // Generate new search ID and clear cache for new searches
    const newSearchId = generateSearchId(searchRequest);
    setCurrentSearchId(newSearchId);
    setPaginationCache({});
    
    // Clear selections on new search
    setSelectedPapers([]);
    setShowBulkMode(false);
    
    // Reset to page 1 if new search
    if (resetPage) {
      setCurrentPage(1);
    }
    
    const requestWithPagination = {
      ...searchRequest,
      page: resetPage ? 1 : currentPage,
      per_page: perPage,
      sort_by: sortBy
    };
    
    await performSearchRequest(requestWithPagination, true);
  };
  
  const handlePageChange = async (page: number) => {
    setCurrentPage(page);
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page, per_page: perPage, sort_by: sortBy };
      await performSearchRequest(request, false);
    }
  };
  
  const handlePerPageChange = async (newPerPage: number) => {
    setPerPage(newPerPage);
    setCurrentPage(1);
    setPaginationCache({}); // Clear cache when pagination size changes
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page: 1, per_page: newPerPage, sort_by: sortBy };
      await performSearchRequest(request, false);
    }
  };

  const handleSortChange = async (newSortBy: 'relevance' | 'newest' | 'oldest' | 'citations') => {
    setSortBy(newSortBy);
    setCurrentPage(1);
    setPaginationCache({}); // Clear cache when sort order changes
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page: 1, per_page: perPage, sort_by: newSortBy };
      await performSearchRequest(request, false);
    }
  };

  const handleExport = async (format: 'csv' | 'json' | 'bib') => {
    if (papers.length === 0) {
      toast.error('No papers to export');
      return;
    }

    setIsExporting(true);
    
    try {
      const blob = await exportPapers({ papers, format });
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `openscholar_export_${timestamp}.${format}`;
      
      downloadFile(blob, filename);
      toast.success(`Successfully exported ${papers.length} papers as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to export papers');
    } finally {
      setIsExporting(false);
    }
  };

  if (showCollections) {
    return <CollectionsOverview onBackToSearch={() => setShowCollections(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold text-gray-900 mb-3">
                🎓 OpenScholar
              </h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                Your gateway to open-access academic research — no paywalls, no limits
              </p>
            </div>
            
            {/* Navigation */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowCollections(true)}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                📚 Collections
                {totalSavedCount > 0 && (
                  <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                    {totalSavedCount}
                  </span>
                )}
              </button>
              
              <button
                onClick={() => onNavigate('flashcards')}
                className="flex items-center px-3 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 rounded-md hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-md"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Flashcards
                {(() => {
                  const flashcardCount = getAllAnnotations().filter(a => a.type === 'flashcard').length;
                  return flashcardCount > 0 ? (
                    <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-white/20 text-white rounded-full">
                      {flashcardCount}
                    </span>
                  ) : null;
                })()}
              </button>
              
              {/* User Profile / Login */}
              <UserProfile 
                onOpenAuth={() => setShowAuth(true)} 
                onOpenSettings={() => setShowProfileSettings(true)}
                onOpenEmailSettings={() => setShowEmailSettings(true)}
                onOpenProxySettings={() => setShowSettings(true)}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section - only show when no search has been performed */}
        {!searchPerformed && (
          <div className="text-center mb-12">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Discover Research That Matters
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Search through millions of peer-reviewed papers from leading academic databases. 
                Find evidence-based research in education, psychology, child development, and more.
              </p>
              
              {/* Feature highlights */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-lg p-6 shadow-sm border">
                  <div className="text-3xl font-bold text-blue-600 mb-2">23</div>
                  <div className="text-sm text-gray-600">Total Sources</div>
                  <div className="text-xs text-gray-500 mt-1">Academic papers + books</div>
                </div>
                <div className="bg-white rounded-lg p-6 shadow-sm border">
                  <div className="text-3xl font-bold text-green-600 mb-2">100%</div>
                  <div className="text-sm text-gray-600">Open Access</div>
                  <div className="text-xs text-gray-500 mt-1">No paywalls ever</div>
                </div>
                <div className="bg-white rounded-lg p-6 shadow-sm border">
                  <div className="text-3xl font-bold text-purple-600 mb-2">⚡</div>
                  <div className="text-sm text-gray-600">Fast Search</div>
                  <div className="text-xs text-gray-500 mt-1">30-60 second results</div>
                </div>
                <div className="bg-white rounded-lg p-6 shadow-sm border">
                  <div className="text-3xl font-bold text-orange-600 mb-2">🎯</div>
                  <div className="text-sm text-gray-600">Quality Content</div>
                  <div className="text-xs text-gray-500 mt-1">Academic sources</div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Search Form */}
        <SearchForm onSearch={handleSearch} isLoading={isLoading} />

        {/* Export Bar */}
        {papers.length > 0 && (
          <ExportBar
            papers={papers}
            onExport={handleExport}
            isExporting={isExporting}
          />
        )}

        {/* Search Results */}
        {searchPerformed && (
          <div className="mb-8">
            {papers.length > 0 ? (
              <>
                {/* Proxy Status Indicator */}
                {proxySettings.enabled && proxySettings.proxyUrl && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-blue-800">
                          🔐 University access enabled
                        </p>
                        <p className="text-xs text-blue-600">
                          {proxySettings.institutionName ? 
                            `Accessing through ${proxySettings.institutionName} proxy` : 
                            'Accessing through your institution\'s proxy'
                          }
                        </p>
                      </div>
                      <div className="ml-auto">
                        <button
                          onClick={() => setShowSettings(true)}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Configure
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Search Relevance Info */}
                <SearchRelevanceInfo 
                  totalResults={totalResults}
                  sortBy={sortBy}
                  searchQuery={currentSearchRequest?.query || ''}
                />

                {/* Results Summary */}
                <div className="mb-6">
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-semibold text-gray-900">
                      Search Results ({totalResults} papers found)
                    </h2>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => setShowBulkMode(!showBulkMode)}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                          showBulkMode
                            ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {showBulkMode ? 'Exit Bulk' : 'Bulk Select'}
                      </button>
                      <div className="flex items-center gap-2">
                      <label htmlFor="sort" className="text-sm font-medium text-gray-700">
                        Sort by:
                      </label>
                      <select
                        id="sort"
                        value={sortBy}
                        onChange={(e) => handleSortChange(e.target.value as 'relevance' | 'newest' | 'oldest' | 'citations')}
                        className="rounded-md border-gray-300 shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500"
                      >
                        <option value="relevance">Relevance</option>
                        <option value="newest">Newest</option>
                        <option value="oldest">Oldest</option>
                        <option value="citations">Most Cited</option>
                      </select>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-sm text-gray-600">Results from sources:</span>
                    {sourceCounts && Object.entries(sourceCounts)
                      .filter(([_, count]) => count > 0)
                      .sort((a, b) => b[1] - a[1])  // Sort by count descending
                      .map(([source, count]) => (
                        <span
                          key={source}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          title={`${count} results from ${source}`}
                        >
                          {source} ({count})
                        </span>
                      ))}
                    {(!sourceCounts || Object.keys(sourceCounts).length === 0) && sourcesQueried.length > 0 && (
                      <span className="text-xs text-gray-500 italic">
                        Searching {sourcesQueried.length} sources...
                      </span>
                    )}
                  </div>
                </div>

                {/* Professional Bulk Action Bar */}
                {showBulkMode && selectedPapers.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-gray-900 font-medium">
                            {selectedPapers.length} paper{selectedPapers.length !== 1 ? 's' : ''} selected
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <button
                            onClick={() => setSelectedPapers(papers)}
                            className="text-blue-600 hover:text-blue-700 font-medium"
                          >
                            Select All ({papers.length})
                          </button>
                          <span className="text-gray-300">•</span>
                          <button
                            onClick={() => setSelectedPapers([])}
                            className="text-gray-600 hover:text-gray-700 font-medium"
                          >
                            Clear All
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        {/* Add to Collection Button */}
                        <button
                          onClick={() => setShowBulkCollectionSelector(true)}
                          className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          Add to Collection
                        </button>
                        
                        {/* Export Dropdown */}
                        <div className="relative">
                          <button
                            onClick={() => setShowExportDropdown(!showExportDropdown)}
                            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Export
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                          
                          {showExportDropdown && (
                            <div className="absolute right-0 mt-1 w-40 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                              <div className="py-1">
                                <button
                                  onClick={() => {
                                    handleBulkExport('csv');
                                    setShowExportDropdown(false);
                                  }}
                                  disabled={isExporting}
                                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Export as CSV
                                </button>
                                <button
                                  onClick={() => {
                                    handleBulkExport('json');
                                    setShowExportDropdown(false);
                                  }}
                                  disabled={isExporting}
                                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Export as JSON
                                </button>
                                <button
                                  onClick={() => {
                                    handleBulkExport('bib');
                                    setShowExportDropdown(false);
                                  }}
                                  disabled={isExporting}
                                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  Export as BibTeX
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Results Grid */}
                <div className="grid gap-6">
                  {papers.map((paper, index) => (
                    <ResultCard 
                      key={index} 
                      paper={paper} 
                      searchQuery={currentSearchRequest?.query}
                      showCheckbox={showBulkMode}
                      isSelected={selectedPapers.some(p => p.title === paper.title)}
                      onToggleSelect={handleToggleSelect}
                    />
                  ))}
                </div>
                
                {/* Pagination */}
                {totalResults > perPage && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={Math.ceil(totalResults / perPage)}
                    totalResults={totalResults}
                    perPage={perPage}
                    onPageChange={handlePageChange}
                    onPerPageChange={handlePerPageChange}
                  />
                )}
              </>
            ) : (
              /* No Results */
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No papers found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Try different keywords or adjust your filters
                </p>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <svg className="animate-spin mx-auto h-12 w-12 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Searching papers...</h3>
            <p className="mt-1 text-sm text-gray-500">
              Querying {isLoading ? 'multiple databases' : 'ERIC, CORE, DOAJ, Europe PMC, PubMed Central'}
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Academic Sources</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• ERIC - Education research</li>
                <li>• CORE - Open access papers*</li>
                <li>• DOAJ - Open access journals</li>
                <li>• Europe PMC - Life sciences</li>
                <li>• PubMed Central - Open access</li>
                <li>• PubMed - Biomedical literature</li>
                <li>• Semantic Scholar - AI-powered</li>
                <li>• arXiv - Physics & CS preprints</li>
                <li>• Crossref - DOI database</li>
                <li>• PLOS - Open science</li>
                <li>• BioMed Central - Biomedical*</li>
                <li>• BASE - Academic search*</li>
                <li>• Unpaywall - Free versions</li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Book & OER Sources</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• DOAB - Open access books</li>
                <li>• Open Textbook Library - CC textbooks</li>
                <li>• Pressbooks - Open textbook networks</li>
                <li>• LibreTexts - OER textbooks</li>
                <li>• MERLOT - Peer-reviewed OER</li>
                <li>• OER Commons - Educational resources</li>
                <li>• MIT OpenCourseWare - Course materials</li>
                <li>• Project Gutenberg - Public domain</li>
                <li>• Internet Archive - Digital library</li>
                <li>• Open Library - Book metadata</li>
                <li>• OpenStax - Free textbooks</li>
                <li>• OAPEN - Academic books</li>
                <li>• Google Books - Full access</li>
                <li>• BHL - Biodiversity heritage*</li>
                <li>• NLM Bookshelf - Medical texts</li>
              </ul>
              <p className="text-xs text-gray-500 mt-2">* Requires API key</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Features</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 100% open access - no paywalls</li>
                <li>• Fast search across 29+ databases</li>
                <li>• Advanced filtering options</li>
                <li>• Export to multiple formats</li>
                <li>• Save papers to collections</li>
                <li>• Quality author filtering</li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">About OpenScholar</h3>
              <p className="text-sm text-gray-600 mb-3">
                Your gateway to open academic research. Search millions of academic papers and books
                without barriers or paywalls.
              </p>
              <p className="text-xs text-gray-500">
                Built with ❤️ for researchers, educators, and students worldwide.
              </p>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-gray-200 text-center">
            <p className="text-xs text-gray-500">
              OpenScholar aggregates content from multiple academic databases. All papers remain property of their respective publishers.
            </p>
          </div>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        initialMode="login"
      />

      {/* Profile Settings Modal */}
      <ProfileSettingsModal
        isOpen={showProfileSettings}
        onClose={() => setShowProfileSettings(false)}
      />
      {/* Email Settings Modal */}
      {showEmailSettings && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={() => setShowEmailSettings(false)}></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <EmailSettings />
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowEmailSettings(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Collection Selector Modal */}
      {showBulkCollectionSelector && selectedPapers.length > 0 && (
        <CollectionSelector
          isOpen={showBulkCollectionSelector}
          onClose={() => setShowBulkCollectionSelector(false)}
          paper={selectedPapers[0]} // Use first paper as reference
          onSaveToCollection={handleBulkAddToCollection}
          onRemoveFromCollection={() => {}} // Not applicable for bulk
          bulkMode={true}
          bulkCount={selectedPapers.length}
        />
      )}
    </div>
  );
};

export default SearchPage;
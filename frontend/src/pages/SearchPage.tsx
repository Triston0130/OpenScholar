import React, { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import SearchForm from '../components/SearchForm';
import ResultCard from '../components/ResultCard';
import ExportBar from '../components/ExportBar';
import Pagination from '../components/Pagination';
import CollectionsOverview from '../components/CollectionsOverview';
import SettingsModal from '../components/SettingsModal';
import { Paper, SearchRequest } from '../types';
import { searchPapers, exportPapers, downloadFile } from '../utils/api';
import { getAllCollectionsWithPapers, addPaperToCollection } from '../utils/collections';
import { getProxySettings } from '../utils/proxy';
import CollectionSelector from '../components/CollectionSelector';

const SearchPage: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [sourcesQueried, setSourcesQueried] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [sortBy, setSortBy] = useState<'relevance' | 'newest' | 'oldest' | 'citations'>('relevance');
  const [currentSearchRequest, setCurrentSearchRequest] = useState<SearchRequest | null>(null);
  const [showCollections, setShowCollections] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [totalSavedCount, setTotalSavedCount] = useState(0);
  const [proxySettings, setProxySettings] = useState(getProxySettings());
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);
  const [showBulkMode, setShowBulkMode] = useState(false);
  const [showBulkCollectionSelector, setShowBulkCollectionSelector] = useState(false);
  const [showExportDropdown, setShowExportDropdown] = useState(false);

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

  const handleSearch = async (searchRequest: SearchRequest, resetPage = true) => {
    setIsLoading(true);
    setSearchPerformed(false);
    setCurrentSearchRequest(searchRequest);
    
    // Clear selections on new search
    setSelectedPapers([]);
    setShowBulkMode(false);
    
    // Reset to page 1 if new search
    if (resetPage) {
      setCurrentPage(1);
    }
    
    try {
      const requestWithPagination = {
        ...searchRequest,
        page: resetPage ? 1 : currentPage,
        per_page: perPage,
        sort_by: sortBy
      };
      
      const response = await searchPapers(requestWithPagination);
      setPapers(response.papers);
      setSourcesQueried(response.sources_queried);
      setTotalResults(response.total_results);
      setSearchPerformed(true);
      
      if (response.papers.length === 0) {
        toast.error('No papers found. Try different keywords or filters.');
      } else {
        toast.success(`Found ${response.total_results || response.papers.length} papers`);
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to search papers');
      setPapers([]);
      setSearchPerformed(true);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handlePageChange = async (page: number) => {
    setCurrentPage(page);
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page, per_page: perPage };
      await handleSearch(request, false);
    }
  };
  
  const handlePerPageChange = async (newPerPage: number) => {
    setPerPage(newPerPage);
    setCurrentPage(1);
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page: 1, per_page: newPerPage };
      await handleSearch(request, false);
    }
  };

  const handleSortChange = async (newSortBy: 'relevance' | 'newest' | 'oldest' | 'citations') => {
    setSortBy(newSortBy);
    setCurrentPage(1);
    if (currentSearchRequest) {
      const request = { ...currentSearchRequest, page: 1, sort_by: newSortBy };
      await handleSearch(request, false);
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                OpenScholar
              </h1>
              <p className="text-lg text-gray-600">
                Search peer-reviewed, open-access research papers in education and child development
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
                onClick={() => setShowSettings(true)}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                title="University Access Settings"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                    <span className="text-sm text-gray-600">Sources queried:</span>
                    {sourcesQueried.map((source, index) => (
                      <span
                        key={source}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {source}
                      </span>
                    ))}
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
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>
              OpenScholar searches peer-reviewed, open-access papers from ERIC, CORE, DOAJ, Europe PMC, and PubMed Central
            </p>
          </div>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />

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
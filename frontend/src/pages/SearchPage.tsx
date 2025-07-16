import React, { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import SearchForm from '../components/SearchForm';
import ResultCard from '../components/ResultCard';
import ExportBar from '../components/ExportBar';
import Pagination from '../components/Pagination';
import CollectionsOverview from '../components/CollectionsOverview';
import { Paper, SearchRequest } from '../types';
import { searchPapers, exportPapers, downloadFile } from '../utils/api';
import { getAllCollectionsWithPapers } from '../utils/collections';

const SearchPage: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [sourcesQueried, setSourcesQueried] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [sortBy, setSortBy] = useState<'relevance' | 'newest' | 'oldest'>('relevance');
  const [currentSearchRequest, setCurrentSearchRequest] = useState<SearchRequest | null>(null);
  const [showCollections, setShowCollections] = useState(false);
  const [totalSavedCount, setTotalSavedCount] = useState(0);

  useEffect(() => {
    updateSavedCount();
    // Listen for collections changes
    const handleCollectionsChange = () => updateSavedCount();
    window.addEventListener('collectionsChanged', handleCollectionsChange);
    return () => {
      window.removeEventListener('collectionsChanged', handleCollectionsChange);
    };
  }, []);

  const updateSavedCount = () => {
    const collections = getAllCollectionsWithPapers();
    const totalCount = collections.reduce((sum, collection) => sum + collection.papers.length, 0);
    setTotalSavedCount(totalCount);
  };

  const handleSearch = async (searchRequest: SearchRequest, resetPage = true) => {
    setIsLoading(true);
    setSearchPerformed(false);
    setCurrentSearchRequest(searchRequest);
    
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

  const handleSortChange = async (newSortBy: 'relevance' | 'newest' | 'oldest') => {
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
                {/* Results Summary */}
                <div className="mb-6">
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-semibold text-gray-900">
                      Search Results ({totalResults} papers found)
                    </h2>
                    <div className="flex items-center gap-2">
                      <label htmlFor="sort" className="text-sm font-medium text-gray-700">
                        Sort by:
                      </label>
                      <select
                        id="sort"
                        value={sortBy}
                        onChange={(e) => handleSortChange(e.target.value as 'relevance' | 'newest' | 'oldest')}
                        className="rounded-md border-gray-300 shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500"
                      >
                        <option value="relevance">Relevance</option>
                        <option value="newest">Newest</option>
                        <option value="oldest">Oldest</option>
                      </select>
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

                {/* Results Grid */}
                <div className="grid gap-6">
                  {papers.map((paper, index) => (
                    <ResultCard 
                      key={index} 
                      paper={paper} 
                      searchQuery={currentSearchRequest?.query}
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
    </div>
  );
};

export default SearchPage;
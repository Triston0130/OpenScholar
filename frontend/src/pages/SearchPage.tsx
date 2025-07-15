import React, { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import SearchForm from '../components/SearchForm';
import ResultCard from '../components/ResultCard';
import ExportBar from '../components/ExportBar';
import { Paper, SearchRequest } from '../types';
import { searchPapers, exportPapers, downloadFile } from '../utils/api';

const SearchPage: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [sourcesQueried, setSourcesQueried] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);

  const handleSearch = async (searchRequest: SearchRequest) => {
    setIsLoading(true);
    setSearchPerformed(false);
    
    try {
      const response = await searchPapers(searchRequest);
      setPapers(response.papers);
      setSourcesQueried(response.sources_queried);
      setTotalResults(response.total_results);
      setSearchPerformed(true);
      
      if (response.papers.length === 0) {
        toast.error('No papers found. Try different keywords or filters.');
      } else {
        toast.success(`Found ${response.papers.length} papers`);
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              OpenScholar
            </h1>
            <p className="text-lg text-gray-600">
              Search peer-reviewed, open-access research papers in education and child development
            </p>
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
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Search Results ({totalResults} papers found)
                  </h2>
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
                    <ResultCard key={index} paper={paper} />
                  ))}
                </div>
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
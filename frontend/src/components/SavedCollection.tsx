import React, { useState, useEffect } from 'react';
import { getSavedPapers, exportSavedPapers, unsavePaper } from '../utils/savedPapers';
import { SavedPaper } from '../utils/collections';
import ResultCard from './ResultCard';

interface SavedCollectionProps {
  onBackToSearch?: () => void;
}

const SavedCollection: React.FC<SavedCollectionProps> = ({ onBackToSearch }) => {
  const [savedPapers, setSavedPapers] = useState<SavedPaper[]>([]);
  const [showExportMenu, setShowExportMenu] = useState(false);

  useEffect(() => {
    loadSavedPapers();
  }, []);

  const loadSavedPapers = () => {
    setSavedPapers(getSavedPapers());
  };

  const handleExport = (format: 'bibtex' | 'pdf-list' | 'summary') => {
    const content = exportSavedPapers(format);
    const filename = `openscholar_saved_${format}_${new Date().toISOString().split('T')[0]}`;
    const fileExtension = format === 'bibtex' ? 'bib' : format === 'pdf-list' ? 'md' : 'md';
    
    // Create and download file
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.${fileExtension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setShowExportMenu(false);
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to remove all saved papers? This cannot be undone.')) {
      localStorage.removeItem('openscholar_saved_papers');
      setSavedPapers([]);
    }
  };

  // Refresh saved papers when a paper is unsaved
  useEffect(() => {
    const handleStorageChange = () => {
      loadSavedPapers();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  if (savedPapers.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              {onBackToSearch && (
                <button
                  onClick={onBackToSearch}
                  className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Search
                </button>
              )}
              <div className="text-center flex-1">
                <h1 className="text-2xl font-bold text-gray-900">
                  📁 Saved Collection
                </h1>
                <p className="text-gray-600 mt-1">
                  Your saved research papers
                </p>
              </div>
              <div className="w-32"></div> {/* Spacer for centering */}
            </div>
          </div>
        </header>

        {/* Empty State */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No saved papers</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start saving papers by clicking the ⭐ button on any search result
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            {onBackToSearch && (
              <button
                onClick={onBackToSearch}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Search
              </button>
            )}
            <div className="text-center flex-1">
              <h1 className="text-2xl font-bold text-gray-900">
                📁 Saved Collection
              </h1>
              <p className="text-gray-600 mt-1">
                {savedPapers.length} saved paper{savedPapers.length !== 1 ? 's' : ''}
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Export Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export
                </button>
                
                {showExportMenu && (
                  <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                    <div className="py-1">
                      <button
                        onClick={() => handleExport('bibtex')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        📚 BibTeX File (.bib)
                      </button>
                      <button
                        onClick={() => handleExport('pdf-list')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        📄 PDF Links (.md)
                      </button>
                      <button
                        onClick={() => handleExport('summary')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        📊 Collection Summary (.md)
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Clear All Button */}
              <button
                onClick={handleClearAll}
                className="flex items-center px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear All
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Saved Papers */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {savedPapers.map((paper, index) => (
            <div key={`${paper.doi || paper.title}-${index}`} className="relative">
              <ResultCard paper={paper} />
              
              {/* Tags and Notes Overlay */}
              <div className="absolute top-4 right-4 bg-white bg-opacity-95 rounded-lg p-3 shadow-sm border border-gray-200 max-w-xs">
                <div className="text-xs text-gray-500 mb-2">
                  Saved {new Date(paper.savedAt).toLocaleDateString()}
                </div>
                
                {/* Tags */}
                {paper.tags && paper.tags.length > 0 && (
                  <div className="mb-2">
                    <div className="flex flex-wrap gap-1">
                      {paper.tags.map((tag, tagIndex) => (
                        <span
                          key={tagIndex}
                          className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Notes */}
                {paper.notes && paper.notes.trim() && (
                  <div className="text-xs text-gray-700 bg-yellow-50 p-2 rounded border border-yellow-200">
                    <div className="font-medium text-yellow-800 mb-1 flex items-center">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                      </svg>
                      Note:
                    </div>
                    <div className="text-gray-600 line-clamp-3">{paper.notes}</div>
                  </div>
                )}
                
                {/* Edit button */}
                <button
                  onClick={() => {/* TODO: Add edit functionality */}}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit tags & notes
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default SavedCollection;
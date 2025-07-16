import React, { useState, useEffect } from 'react';
import { SavedPaper, updatePaperTagsAndNotes, getAllTags, getCollectionPapers, getCollections } from '../utils/collections';
import ResultCard from './ResultCard';

interface SavedCollectionProps {
  onBackToSearch?: () => void;
}

const SavedCollection: React.FC<SavedCollectionProps> = ({ onBackToSearch }) => {
  const [savedPapers, setSavedPapers] = useState<SavedPaper[]>([]);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [editingPaper, setEditingPaper] = useState<SavedPaper | null>(null);
  const [editTags, setEditTags] = useState<string[]>([]);
  const [editNotes, setEditNotes] = useState('');
  const [newTag, setNewTag] = useState('');
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  useEffect(() => {
    loadSavedPapers();
  }, []);

  const loadSavedPapers = () => {
    // Get papers from the default collection
    const collections = getCollections();
    const defaultCollection = collections.find(c => c.id === 'default');
    if (defaultCollection) {
      setSavedPapers(getCollectionPapers('default'));
    } else {
      setSavedPapers([]);
    }
    setAvailableTags(getAllTags());
  };

  const handleEditPaper = (paper: SavedPaper) => {
    setEditingPaper(paper);
    setEditTags(paper.tags || []);
    setEditNotes(paper.notes || '');
    setNewTag('');
  };

  const handleSaveEdit = () => {
    if (editingPaper) {
      updatePaperTagsAndNotes(editingPaper, 'default', editTags, editNotes);
      setEditingPaper(null);
      loadSavedPapers();
    }
  };

  const handleAddTag = (tag: string) => {
    if (tag && !editTags.includes(tag)) {
      setEditTags([...editTags, tag]);
    }
    setNewTag('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setEditTags(editTags.filter(tag => tag !== tagToRemove));
  };

  const handleExport = (format: 'bibtex' | 'pdf-list' | 'summary') => {
    // For now, just show an alert - can implement export later
    alert(`Export as ${format} coming soon!`);
    setShowExportMenu(false);
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to remove all saved papers? This cannot be undone.')) {
      // Clear the default collection
      const data = { collections: getCollections(), papers: { default: [] } };
      localStorage.setItem('openscholar_collections', JSON.stringify(data));
      loadSavedPapers();
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
            <div key={`${paper.doi || paper.title}-${index}`} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
              <ResultCard paper={paper} />
              
              {/* Integrated Tags and Notes Section */}
              <div className="px-6 pb-6 border-t border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs text-gray-500">
                    Saved {new Date(paper.savedAt).toLocaleDateString()}
                  </div>
                  <button
                    onClick={() => handleEditPaper(paper)}
                    className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                  >
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit tags & notes
                  </button>
                </div>
                
                {/* Tags */}
                {paper.tags && paper.tags.length > 0 && (
                  <div className="mb-3">
                    <div className="flex items-center mb-2">
                      <svg className="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      <span className="text-sm font-medium text-gray-700">Tags:</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {paper.tags.map((tag, tagIndex) => (
                        <span
                          key={tagIndex}
                          className="inline-block px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Notes */}
                {paper.notes && paper.notes.trim() && (
                  <div>
                    <div className="flex items-center mb-2">
                      <svg className="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      <span className="text-sm font-medium text-gray-700">Notes:</span>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{paper.notes}</p>
                    </div>
                  </div>
                )}
                
                {/* Show message if no tags or notes */}
                {(!paper.tags || paper.tags.length === 0) && (!paper.notes || !paper.notes.trim()) && (
                  <div className="text-center py-2">
                    <p className="text-xs text-gray-400 italic">No tags or notes added yet</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Edit Tags and Notes Modal */}
      {editingPaper && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                Edit Tags & Notes
              </h3>
              <button
                onClick={() => setEditingPaper(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Paper Title */}
              <div className="bg-gray-50 p-3 rounded-md">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Paper:</h4>
                <p className="text-sm text-gray-600 line-clamp-2">{editingPaper.title}</p>
              </div>

              {/* Tags Section */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                
                {/* Tag Input */}
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    placeholder="Add a tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag(newTag);
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    onClick={() => handleAddTag(newTag)}
                    disabled={!newTag || editTags.includes(newTag)}
                    className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    Add
                  </button>
                </div>

                {/* Suggested Tags */}
                {availableTags.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-500 mb-2">Suggested tags:</p>
                    <div className="flex flex-wrap gap-1">
                      {availableTags.slice(0, 10).map((tag) => (
                        <button
                          key={tag}
                          onClick={() => handleAddTag(tag)}
                          disabled={editTags.includes(tag)}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selected Tags */}
                {editTags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {editTags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 text-sm bg-blue-100 text-blue-800 rounded-full"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Notes Section */}
              <div>
                <label htmlFor="editNotes" className="block text-sm font-medium text-gray-700 mb-2">
                  Notes
                </label>
                <textarea
                  id="editNotes"
                  placeholder="Add notes about this paper... (e.g., 'Use for lit review intro', 'Refutes 2020 Smith study')"
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 resize-none"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
              <button
                onClick={() => setEditingPaper(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SavedCollection;
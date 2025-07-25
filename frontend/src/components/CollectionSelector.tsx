import React, { useState, useEffect } from 'react';
import { Collection, getCollections, createCollection, isPaperInCollection, getAllTags, getFolders, getAllCollectionsWithPapers } from '../utils/collections';
import { Paper } from '../types';
import CreateCollectionModal from './CreateCollectionModal';

interface CollectionSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  paper: Paper;
  onSaveToCollection: (collectionId: string, tags?: string[], notes?: string, folderId?: string) => void;
  onRemoveFromCollection: (collectionId: string) => void;
  bulkMode?: boolean;
  bulkCount?: number;
}

const CollectionSelector: React.FC<CollectionSelectorProps> = ({
  isOpen,
  onClose,
  paper,
  onSaveToCollection,
  onRemoveFromCollection,
  bulkMode = false,
  bulkCount = 0
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showTagsNotesDialog, setShowTagsNotesDialog] = useState(false);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [newTag, setNewTag] = useState('');
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (isOpen) {
      loadCollections();
      setAvailableTags(getAllTags());
    }
  }, [isOpen]);

  useEffect(() => {
    const handleCollectionsChange = () => {
      loadCollections();
    };

    window.addEventListener('collectionsChanged', handleCollectionsChange);
    return () => window.removeEventListener('collectionsChanged', handleCollectionsChange);
  }, []);

  const loadCollections = () => {
    setCollections(getCollections());
  };

  // Helper function to find existing tags and notes for a paper across all collections
  const findExistingMetadata = () => {
    const allCollections = getAllCollectionsWithPapers();
    let existingTags: string[] = [];
    let existingNotes: string = '';
    
    allCollections.forEach(collection => {
      const existingPaper = collection.papers.find(p => 
        (paper.doi && p.doi === paper.doi) || p.title === paper.title
      );
      
      if (existingPaper) {
        // Merge tags (avoiding duplicates)
        if (existingPaper.tags && existingPaper.tags.length > 0) {
          existingTags = Array.from(new Set([...existingTags, ...existingPaper.tags]));
        }
        
        // Use the longest/most detailed notes
        if (existingPaper.notes && existingPaper.notes.length > existingNotes.length) {
          existingNotes = existingPaper.notes;
        }
      }
    });
    return { tags: existingTags, notes: existingNotes };
  };

  const handleCreateCollection = async (name: string, description?: string, color?: string) => {
    const newCollection = await createCollection(name, description, color);
    loadCollections();
    
    // Automatically add paper to new collection with existing tags and notes if available
    const existing = findExistingMetadata();
    onSaveToCollection(newCollection.id, existing.tags, existing.notes, undefined);
  };

  const handleToggleCollection = (collectionId: string) => {
    if (bulkMode || !isPaperInCollection(paper, collectionId)) {
      // Show tags and notes dialog for new saves (always for bulk mode)
      setSelectedCollectionId(collectionId);
      
      // Load existing tags and notes from other collections
      const existing = findExistingMetadata();
      setTags(existing.tags);
      setNotes(existing.notes);
      
      setSelectedFolderId(undefined);
      setShowTagsNotesDialog(true);
    } else {
      onRemoveFromCollection(collectionId);
    }
    loadCollections(); // Refresh to show updated state
  };

  const handleSaveWithTagsAndNotes = () => {
    onSaveToCollection(selectedCollectionId, tags, notes, selectedFolderId);
    setShowTagsNotesDialog(false);
    setSelectedCollectionId('');
    setTags([]);
    setNotes('');
    setSelectedFolderId(undefined);
  };

  const handleAddTag = (tag: string) => {
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
    }
    setNewTag('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const filteredCollections = collections.filter(collection =>
    collection.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (collection.description && collection.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
        <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {bulkMode ? `Add ${bulkCount} Papers to Collection` : 'Save to Collection'}
              </h3>
              <p className="text-sm text-gray-600 mt-1 truncate">
                {bulkMode ? `${bulkCount} papers selected` : paper.title}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Search and Create */}
          <div className="p-4 border-b">
            <div className="flex gap-2 mb-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Search collections..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 pr-8 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                />
                <svg className="absolute right-2 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
              >
                + New
              </button>
            </div>
          </div>

          {/* Collections List */}
          <div className="flex-1 overflow-y-auto p-4">
            {filteredCollections.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-8 w-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                {searchTerm ? 'No collections match your search' : 'No collections yet'}
              </div>
            ) : (
              <div className="space-y-2">
                {filteredCollections.map((collection) => {
                  const isInCollection = !bulkMode && isPaperInCollection(paper, collection.id);
                  
                  return (
                    <button
                      key={collection.id}
                      onClick={() => handleToggleCollection(collection.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        isInCollection
                          ? 'border-blue-200 bg-blue-50 ring-1 ring-blue-500'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div
                            className="w-4 h-4 rounded-full border-2"
                            style={{ 
                              backgroundColor: collection.color,
                              borderColor: collection.color
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900 truncate">
                                {collection.name}
                              </span>
                              {isInCollection && (
                                <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                            {collection.description && (
                              <p className="text-sm text-gray-500 truncate mt-1">
                                {collection.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t bg-gray-50">
            <div className="flex justify-between items-center text-sm text-gray-600">
              <span>
                {bulkMode 
                  ? `Ready to add ${bulkCount} papers to selected collection`
                  : `Paper saved in ${filteredCollections.filter(c => isPaperInCollection(paper, c.id)).length} collection(s)`
                }
              </span>
              <button
                onClick={onClose}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                {bulkMode ? 'Cancel' : 'Done'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Create Collection Modal */}
      <CreateCollectionModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreateCollection={handleCreateCollection}
      />

      {/* Tags and Notes Dialog */}
      {showTagsNotesDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                Add Tags & Notes
              </h3>
              <button
                onClick={() => setShowTagsNotesDialog(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
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
                    disabled={!newTag || tags.includes(newTag)}
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
                          disabled={tags.includes(tag)}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selected Tags */}
                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
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

              {/* Folder Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Folder (Optional)
                </label>
                <select
                  value={selectedFolderId || ''}
                  onChange={(e) => setSelectedFolderId(e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">No folder</option>
                  {selectedCollectionId && getFolders(selectedCollectionId).map((folder) => (
                    <option key={folder.id} value={folder.id}>
                      📁 {folder.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Notes Section */}
              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                  Notes
                </label>
                <textarea
                  id="notes"
                  placeholder="Add notes about this paper... (e.g., 'Use for lit review intro', 'Refutes 2020 Smith study')"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 resize-none"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
              <button
                onClick={() => setShowTagsNotesDialog(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveWithTagsAndNotes}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                {bulkMode ? `Add ${bulkCount} Papers` : 'Save to Collection'}
              </button>
            </div>
          </div>
        </div>
      )}

    </>
  );
};

export default CollectionSelector;
import React, { useState, useEffect } from 'react';
import { Collection, getCollections, createCollection, isPaperInCollection } from '../utils/collections';
import { Paper } from '../types';
import CreateCollectionModal from './CreateCollectionModal';

interface CollectionSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  paper: Paper;
  onSaveToCollection: (collectionId: string) => void;
  onRemoveFromCollection: (collectionId: string) => void;
}

const CollectionSelector: React.FC<CollectionSelectorProps> = ({
  isOpen,
  onClose,
  paper,
  onSaveToCollection,
  onRemoveFromCollection
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadCollections();
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

  const handleCreateCollection = (name: string, description?: string, color?: string) => {
    const newCollection = createCollection(name, description, color);
    loadCollections();
    // Automatically add paper to new collection
    onSaveToCollection(newCollection.id);
  };

  const handleToggleCollection = (collectionId: string) => {
    if (isPaperInCollection(paper, collectionId)) {
      onRemoveFromCollection(collectionId);
    } else {
      onSaveToCollection(collectionId);
    }
    loadCollections(); // Refresh to show updated state
  };

  const filteredCollections = collections.filter(collection =>
    collection.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (collection.description && collection.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Save to Collection
              </h3>
              <p className="text-sm text-gray-600 mt-1 truncate">
                {paper.title}
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
                  const isInCollection = isPaperInCollection(paper, collection.id);
                  
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
                Paper saved in {filteredCollections.filter(c => isPaperInCollection(paper, c.id)).length} collection(s)
              </span>
              <button
                onClick={onClose}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Done
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
    </>
  );
};

export default CollectionSelector;
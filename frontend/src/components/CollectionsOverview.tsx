import React, { useState, useEffect } from 'react';
import { getAllCollectionsWithPapers, deleteCollection, updateCollection, exportCollection, getCollectionStats, Collection, updatePaperTagsAndNotes, getAllTags, SavedPaper, addPaperToCollection, Folder, createFolder, updateFolder, deleteFolder, getFolderPapers, movePaperToFolder } from '../utils/collections';
import CreateCollectionModal from './CreateCollectionModal';
import AddExternalPaperModal from './AddExternalPaperModal';
import ResultCard from './ResultCard';
import { Paper } from '../types';

interface CollectionsOverviewProps {
  onBackToSearch?: () => void;
}

const CollectionsOverview: React.FC<CollectionsOverviewProps> = ({ onBackToSearch }) => {
  const [collections, setCollections] = useState<any[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState<string | null>(null);
  const [editingCollection, setEditingCollection] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editingPaper, setEditingPaper] = useState<SavedPaper | null>(null);
  const [editTags, setEditTags] = useState<string[]>([]);
  const [editNotes, setEditNotes] = useState('');
  const [newTag, setNewTag] = useState('');
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());
  const [showAddExternalModal, setShowAddExternalModal] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [showCreateFolderInput, setShowCreateFolderInput] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [editingFolder, setEditingFolder] = useState<string | null>(null);
  const [editFolderName, setEditFolderName] = useState('');

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    const handleCollectionsChange = () => {
      loadCollections();
    };

    window.addEventListener('collectionsChanged', handleCollectionsChange);
    return () => window.removeEventListener('collectionsChanged', handleCollectionsChange);
  }, []);

  const loadCollections = () => {
    const allCollections = getAllCollectionsWithPapers();
    setCollections(allCollections);
    setAvailableTags(getAllTags());
  };

  const handleCreateCollection = (name: string, description?: string, color?: string) => {
    // Collection creation is handled in the modal
    loadCollections();
  };

  const handleEditCollection = (collection: Collection) => {
    setEditingCollection(collection.id);
    setEditName(collection.name);
    setEditDescription(collection.description || '');
  };

  const handleSaveEdit = () => {
    if (editingCollection && editName.trim()) {
      updateCollection(editingCollection, {
        name: editName.trim(),
        description: editDescription.trim() || undefined
      });
      setEditingCollection(null);
      setEditName('');
      setEditDescription('');
      loadCollections();
    }
  };

  const handleCancelEdit = () => {
    setEditingCollection(null);
    setEditName('');
    setEditDescription('');
  };

  const handleEditPaper = (paper: SavedPaper, collectionId: string) => {
    setEditingPaper(paper);
    setEditTags(paper.tags || []);
    setEditNotes(paper.notes || '');
    setNewTag('');
    // Store the collection ID in the paper for reference
    setEditingPaper({ ...paper, collectionId } as any);
  };

  const handleSavePaperEdit = () => {
    if (editingPaper && (editingPaper as any).collectionId) {
      updatePaperTagsAndNotes(editingPaper, (editingPaper as any).collectionId, editTags, editNotes);
      setEditingPaper(null);
      loadCollections();
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

  const handleAddExternalPaper = (paper: Paper) => {
    if (selectedCollection) {
      addPaperToCollection(paper, selectedCollection, [], '', selectedFolder || undefined);
      loadCollections();
    }
  };

  const handleCreateFolder = () => {
    if (selectedCollection && newFolderName.trim()) {
      createFolder(selectedCollection, newFolderName.trim());
      setNewFolderName('');
      setShowCreateFolderInput(false);
      loadCollections();
    }
  };

  const handleEditFolder = (folder: Folder) => {
    setEditingFolder(folder.id);
    setEditFolderName(folder.name);
  };

  const handleSaveFolderEdit = () => {
    if (editingFolder && selectedCollection && editFolderName.trim()) {
      updateFolder(editingFolder, selectedCollection, { name: editFolderName.trim() });
      setEditingFolder(null);
      setEditFolderName('');
      loadCollections();
    }
  };

  const handleDeleteFolder = (folderId: string) => {
    if (selectedCollection && window.confirm('Are you sure you want to delete this folder? Papers in this folder will be moved to the collection root.')) {
      deleteFolder(folderId, selectedCollection);
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
      }
      loadCollections();
    }
  };

  const handleMovePaperToFolder = (paper: SavedPaper, folderId?: string) => {
    if (selectedCollection) {
      movePaperToFolder(paper, selectedCollection, folderId);
      loadCollections();
    }
  };

  const handleDeleteCollection = (collectionId: string) => {
    const collection = collections.find(c => c.id === collectionId);
    if (collection && window.confirm(`Are you sure you want to delete "${collection.name}"? This will remove all papers from this collection.`)) {
      deleteCollection(collectionId);
      if (selectedCollection === collectionId) {
        setSelectedCollection(null);
      }
      loadCollections();
    }
  };

  const handleExport = (collectionId: string, format: 'bibtex' | 'pdf-list' | 'summary' | 'apa' | 'mla' | 'chicago') => {
    const collection = collections.find(c => c.id === collectionId);
    if (!collection) return;

    const content = exportCollection(collectionId, format);
    const filename = `${collection.name.replace(/[^a-zA-Z0-9]/g, '_')}_${format}_${new Date().toISOString().split('T')[0]}`;
    const fileExtension = format === 'bibtex' ? 'bib' : 'txt';
    
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
    
    setShowExportMenu(null);
  };

  const totalPapers = collections.reduce((sum, collection) => sum + collection.papers.length, 0);
  const selectedCollectionData = selectedCollection ? collections.find(c => c.id === selectedCollection) : null;

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
                📚 My Collections
              </h1>
              <p className="text-gray-600 mt-1">
                {collections.length} collection{collections.length !== 1 ? 's' : ''} • {totalPapers} total papers
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Collection
              </button>
              
              {selectedCollection && (
                <button
                  onClick={() => setShowAddExternalModal(true)}
                  className="flex items-center px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add External Paper
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Collections Sidebar */}
          <div className="w-80 flex-shrink-0">
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h3 className="font-medium text-gray-900">Collections</h3>
              </div>
              <div className="divide-y">
                {collections.map((collection) => {
                  const stats = getCollectionStats(collection.id);
                  const isSelected = selectedCollection === collection.id;
                  const isEditing = editingCollection === collection.id;
                  
                  return (
                    <div
                      key={collection.id}
                      className={`p-4 cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-50 border-r-2 border-blue-500' : 'hover:bg-gray-50'
                      }`}
                      onClick={() => !isEditing && setSelectedCollection(collection.id)}
                    >
                      {isEditing ? (
                        <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="Collection name"
                            maxLength={50}
                          />
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded resize-none"
                            placeholder="Description (optional)"
                            rows={2}
                            maxLength={200}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={handleSaveEdit}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Save
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              className="px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3 flex-1 min-w-0">
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: collection.color }}
                              />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-gray-900 truncate">
                                  {collection.name}
                                </p>
                                {collection.description && (
                                  <p className="text-sm text-gray-500 truncate">
                                    {collection.description}
                                  </p>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-1">
                              <span className="text-sm font-medium text-gray-900">
                                {stats.totalPapers}
                              </span>
                              
                              {/* Collection Actions Menu */}
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setShowExportMenu(showExportMenu === collection.id ? null : collection.id);
                                  }}
                                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                                  </svg>
                                </button>
                                
                                {showExportMenu === collection.id && (
                                  <div className="absolute right-0 top-6 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                                    <div className="py-1">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'bibtex');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📚 Export BibTeX
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'pdf-list');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📄 Export PDF List
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'summary');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📊 Export Summary
                                      </button>
                                      <div className="border-t my-1"></div>
                                      <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                                        Citation Formats
                                      </div>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'apa');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📝 APA Citations
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'mla');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📝 MLA Citations
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleExport(collection.id, 'chicago');
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        📝 Chicago Citations
                                      </button>
                                      <div className="border-t my-1"></div>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleEditCollection(collection);
                                          setShowExportMenu(null);
                                        }}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        ✏️ Edit Collection
                                      </button>
                                      {collection.id !== 'default' && (
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteCollection(collection.id);
                                            setShowExportMenu(null);
                                          }}
                                          className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                        >
                                          🗑️ Delete Collection
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          <div className="mt-2 text-xs text-gray-500">
                            Updated {new Date(collection.updatedAt).toLocaleDateString()}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Collection Content */}
          <div className="flex-1">
            {selectedCollectionData ? (
              <div>
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div
                      className="w-6 h-6 rounded-full"
                      style={{ backgroundColor: selectedCollectionData.color }}
                    />
                    <h2 className="text-xl font-bold text-gray-900">
                      {selectedCollectionData.name}
                    </h2>
                  </div>
                  
                  {selectedCollectionData.description && (
                    <p className="text-gray-600 mb-4">
                      {selectedCollectionData.description}
                    </p>
                  )}

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedCollectionData.papers.length}
                      </div>
                      <div className="text-sm text-gray-500">Papers</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        {selectedCollectionData.papers.filter((p: any) => p.full_text_url).length}
                      </div>
                      <div className="text-sm text-gray-500">With PDFs</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-purple-600">
                        {new Set(selectedCollectionData.papers.map((p: any) => p.source)).size}
                      </div>
                      <div className="text-sm text-gray-500">Sources</div>
                    </div>
                  </div>
                </div>

                {/* Folders and Papers */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Folders</h3>
                    <button
                      onClick={() => setShowCreateFolderInput(true)}
                      className="flex items-center px-3 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      New Folder
                    </button>
                  </div>

                  {/* Create Folder Input */}
                  {showCreateFolderInput && (
                    <div className="flex gap-2 mb-4">
                      <input
                        type="text"
                        placeholder="Folder name..."
                        value={newFolderName}
                        onChange={(e) => setNewFolderName(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleCreateFolder();
                          }
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                        autoFocus
                      />
                      <button
                        onClick={handleCreateFolder}
                        disabled={!newFolderName.trim()}
                        className="px-3 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        Create
                      </button>
                      <button
                        onClick={() => {
                          setShowCreateFolderInput(false);
                          setNewFolderName('');
                        }}
                        className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  )}

                  {/* Folder Navigation */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <button
                      onClick={() => setSelectedFolder(null)}
                      className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        selectedFolder === null
                          ? 'text-blue-700 bg-blue-100'
                          : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      📄 All Papers
                    </button>
                    
                    {selectedCollectionData.folders.map((folder: Folder) => (
                      <div key={folder.id} className="relative">
                        {editingFolder === folder.id ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={editFolderName}
                              onChange={(e) => setEditFolderName(e.target.value)}
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                  handleSaveFolderEdit();
                                }
                              }}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                              autoFocus
                            />
                            <button
                              onClick={handleSaveFolderEdit}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => {
                                setEditingFolder(null);
                                setEditFolderName('');
                              }}
                              className="px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center">
                            <button
                              onClick={() => setSelectedFolder(folder.id)}
                              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                                selectedFolder === folder.id
                                  ? 'text-blue-700 bg-blue-100'
                                  : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
                              }`}
                            >
                              📁 {folder.name}
                            </button>
                            <div className="ml-1 relative">
                              <button
                                onClick={() => {/* Toggle folder menu */}}
                                className="p-1 text-gray-400 hover:text-gray-600 rounded"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                                </svg>
                              </button>
                              <div className="absolute right-0 top-6 w-32 bg-white rounded-md shadow-lg border border-gray-200 z-10 hidden">
                                <div className="py-1">
                                  <button
                                    onClick={() => handleEditFolder(folder)}
                                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => handleDeleteFolder(folder.id)}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                  >
                                    Delete
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Papers */}
                {(() => {
                  const papersToShow = selectedFolder 
                    ? getFolderPapers(selectedCollectionData.id, selectedFolder)
                    : getFolderPapers(selectedCollectionData.id, undefined);
                  
                  return papersToShow.length > 0 ? (
                    <div className="space-y-6">
                      {papersToShow.map((paper: any, index: number) => (
                      <div key={`${paper.doi || paper.title}-${index}`}>
                        <ResultCard paper={paper} />
                        
                        {/* Tags and Notes Section */}
                        <div className="bg-white rounded-lg shadow-md p-6 -mt-6 pt-4 border-t border-gray-200">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-4">
                              <span className="text-xs text-gray-500">
                                Added {new Date(paper.savedAt).toLocaleDateString()}
                              </span>
                              {paper.folderId && (
                                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                  📁 {selectedCollectionData.folders.find((f: Folder) => f.id === paper.folderId)?.name || 'Unknown Folder'}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <select
                                value={paper.folderId || ''}
                                onChange={(e) => handleMovePaperToFolder(paper, e.target.value || undefined)}
                                className="text-xs border border-gray-300 rounded px-2 py-1 text-gray-600"
                              >
                                <option value="">No Folder</option>
                                {selectedCollectionData.folders.map((folder: Folder) => (
                                  <option key={folder.id} value={folder.id}>
                                    📁 {folder.name}
                                  </option>
                                ))}
                              </select>
                              <button
                                onClick={() => handleEditPaper(paper, selectedCollectionData.id)}
                                className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                              >
                                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                Edit tags & notes
                              </button>
                            </div>
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
                                {paper.tags.map((tag: string, tagIndex: number) => (
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
                            <div className="mb-3">
                              <div className="flex items-center mb-2">
                                <svg className="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span className="text-sm font-medium text-gray-700">Notes:</span>
                              </div>
                              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                {(() => {
                                  const noteId = paper.doi || paper.title;
                                  const isExpanded = expandedNotes.has(noteId);
                                  const displayText = isExpanded ? paper.notes : paper.notes.substring(0, 300);
                                  
                                  return (
                                    <div>
                                      <p className="text-gray-700 leading-relaxed">{displayText}</p>
                                      {paper.notes.length > 300 && (
                                        <button
                                          onClick={() => {
                                            const newExpandedNotes = new Set(expandedNotes);
                                            if (isExpanded) {
                                              newExpandedNotes.delete(noteId);
                                            } else {
                                              newExpandedNotes.add(noteId);
                                            }
                                            setExpandedNotes(newExpandedNotes);
                                          }}
                                          className="text-blue-600 hover:text-blue-700 text-sm font-medium mt-2 focus:outline-none"
                                        >
                                          {isExpanded ? 'Show less' : 'Show more'}
                                        </button>
                                      )}
                                    </div>
                                  );
                                })()}
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
                  ) : (
                    <div className="text-center py-12 bg-white rounded-lg shadow">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">
                        {selectedFolder ? 'Folder is empty' : 'Collection is empty'}
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {selectedFolder 
                          ? 'This folder has no papers yet. Move papers here using the dropdown above each paper.'
                          : 'Start adding papers by clicking the "Save" button on search results'
                        }
                      </p>
                    </div>
                  );
                })()}
              </div>
            ) : (
              <div className="text-center py-20 bg-white rounded-lg shadow">
                <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <h3 className="mt-2 text-lg font-medium text-gray-900">Select a collection</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose a collection from the sidebar to view its papers
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Collection Modal */}
      <CreateCollectionModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreateCollection={handleCreateCollection}
      />
      
      {/* Add External Paper Modal */}
      <AddExternalPaperModal
        isOpen={showAddExternalModal}
        onClose={() => setShowAddExternalModal(false)}
        onAddPaper={handleAddExternalPaper}
      />

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
                onClick={handleSavePaperEdit}
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

export default CollectionsOverview;
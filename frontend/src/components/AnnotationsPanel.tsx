import React, { useState, useEffect } from 'react';
import { Annotation, getAnnotationsByPdfUrl, deleteAnnotation, updateAnnotation } from '../utils/annotations';

interface AnnotationsPanelProps {
  pdfUrl: string;
  isOpen: boolean;
  onClose: () => void;
  onAnnotationClick?: (annotation: Annotation) => void;
}

const AnnotationsPanel: React.FC<AnnotationsPanelProps> = ({ pdfUrl, isOpen, onClose, onAnnotationClick }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [filter, setFilter] = useState<'all' | 'highlight' | 'note' | 'flashcard'>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAnnotations();
    
    const handleAnnotationsChanged = () => {
      loadAnnotations();
    };
    
    window.addEventListener('annotationsChanged', handleAnnotationsChanged);
    return () => {
      window.removeEventListener('annotationsChanged', handleAnnotationsChanged);
    };
  }, [pdfUrl]);

  const loadAnnotations = () => {
    const loaded = getAnnotationsByPdfUrl(pdfUrl);
    setAnnotations(loaded);
  };

  const filteredAnnotations = annotations.filter(ann => {
    // Filter by type
    if (filter !== 'all' && ann.type !== filter) return false;
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const searchableText = `
        ${ann.text.toLowerCase()}
        ${ann.note?.toLowerCase() || ''}
        ${ann.colorName?.toLowerCase() || ''}
        ${(ann as any).front?.toLowerCase() || ''}
        ${(ann as any).back?.toLowerCase() || ''}
      `;
      return searchableText.includes(query);
    }
    
    return true;
  });

  const handleDelete = (id: string) => {
    if (window.confirm('Delete this annotation?')) {
      deleteAnnotation(id);
    }
  };

  const handleEdit = (annotation: Annotation) => {
    setEditingId(annotation.id);
    setEditText(annotation.note || annotation.text);
  };

  const handleSaveEdit = (annotation: Annotation) => {
    updateAnnotation(annotation.id, { 
      note: annotation.type === 'note' ? editText : annotation.note,
      text: annotation.type !== 'note' ? editText : annotation.text
    });
    setEditingId(null);
    setEditText('');
  };

  const getAnnotationIcon = (type: string) => {
    switch (type) {
      case 'highlight':
        return '🖍️';
      case 'note':
        return '📝';
      case 'flashcard':
        return '🎴';
      default:
        return '📌';
    }
  };

  const getAnnotationColor = (type: string) => {
    switch (type) {
      case 'highlight':
        return 'bg-yellow-100 border-yellow-300';
      case 'note':
        return 'bg-blue-100 border-blue-300';
      case 'flashcard':
        return 'bg-purple-100 border-purple-300';
      default:
        return 'bg-gray-100 border-gray-300';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold">Annotations ({annotations.length})</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-full"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Search bar */}
      <div className="p-3 border-b">
        <div className="relative">
          <input
            type="text"
            placeholder="Search annotations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex border-b">
        {(['all', 'highlight', 'note', 'flashcard'] as const).map(type => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`flex-1 px-4 py-2 text-sm font-medium capitalize ${
              filter === type 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Annotations list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 annotations-panel">
        {filteredAnnotations.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            {searchQuery ? 'No annotations match your search' : 'No annotations yet'}
          </p>
        ) : (
          filteredAnnotations.map(annotation => (
            <div
              key={annotation.id}
              className={`p-3 rounded-lg border ${getAnnotationColor(annotation.type)} cursor-pointer hover:shadow-md transition-shadow`}
              onClick={() => onAnnotationClick?.(annotation)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{getAnnotationIcon(annotation.type)}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(annotation.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                  
                  {editingId === annotation.id ? (
                    <div className="space-y-2">
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="w-full p-2 border rounded text-sm"
                        rows={3}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSaveEdit(annotation);
                          }}
                          className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                        >
                          Save
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingId(null);
                          }}
                          className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm hover:bg-gray-400"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-gray-800 line-clamp-2">
                        {annotation.text}
                      </p>
                      
                      {annotation.colorName && (
                        <div className="flex items-center gap-1 mt-1">
                          <div 
                            className="w-3 h-3 rounded-full border border-gray-300"
                            style={{ backgroundColor: annotation.color }}
                          />
                          <span className="text-xs text-gray-500">{annotation.colorName}</span>
                        </div>
                      )}
                      
                      {annotation.type === 'note' && annotation.note && (
                        <p className="text-sm text-gray-600 mt-1 italic">
                          Note: {annotation.note}
                        </p>
                      )}
                      
                      {annotation.type === 'flashcard' && (
                        <div className="mt-2 text-sm">
                          <p className="font-medium">Front: {(annotation as any).front}</p>
                          <p className="text-gray-600">Back: {(annotation as any).back}</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
                
                {editingId !== annotation.id && (
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(annotation);
                      }}
                      className="p-1 hover:bg-white rounded"
                      title="Edit"
                    >
                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(annotation.id);
                      }}
                      className="p-1 hover:bg-white rounded"
                      title="Delete"
                    >
                      <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Export button */}
      <div className="p-4 border-t">
        <button
          onClick={() => {
            const json = JSON.stringify(filteredAnnotations, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'annotations.json';
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Export Annotations
        </button>
      </div>
    </div>
  );
};

export default AnnotationsPanel;
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import { Paper } from '../types';

interface PDFViewerProps {
  paper: Paper;
  pdfUrl: string;
  collectionId?: string;
  onClose: () => void;
}

interface Annotation {
  id?: string;
  annotation_type: 'highlight' | 'comment' | 'note';
  selected_text: string;
  comment?: string;
  color: string;
  page_number: number;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  created_at?: string;
  user_id?: string;
}

const PDFViewerWithSelection: React.FC<PDFViewerProps> = ({ paper, pdfUrl, collectionId, onClose }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [showPopup, setShowPopup] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [selectedText, setSelectedText] = useState('');
  const [showNoteDialog, setShowNoteDialog] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  // Generate a unique identifier for the paper
  const paperId = paper.doi || encodeURIComponent(paper.title);

  // Create instance of default layout plugin
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    sidebarTabs: () => [],
    toolbarPlugin: {
      fullScreenPlugin: {
        onEnterFullScreen: () => {},
        onExitFullScreen: () => {},
      },
    },
  });

  // Load existing annotations when component mounts
  useEffect(() => {
    loadAnnotations();
  }, [paperId]);

  const loadAnnotations = async () => {
    try {
      const response = await fetch(`/api/papers/${paperId}/annotations?collection_id=${collectionId || ''}`);
      if (response.ok) {
        const data = await response.json();
        setAnnotations(data);
      }
    } catch (error) {
      console.error('Error loading annotations:', error);
    }
  };

  // Handle text selection
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    
    const handleTextSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      
      if (text && text.length > 0) {
        const range = selection?.getRangeAt(0);
        const rect = range?.getBoundingClientRect();
        
        if (rect && containerRef.current) {
          const containerRect = containerRef.current.getBoundingClientRect();
          
          setSelectedText(text);
          setPopupPosition({
            x: rect.left + rect.width / 2 - containerRect.left,
            y: rect.top - containerRect.top - 10
          });
          setShowPopup(true);
        }
      }
    };

    const handleMouseUp = () => {
      // Small delay to ensure selection is complete
      timeoutId = setTimeout(handleTextSelection, 10);
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        setShowPopup(false);
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      clearTimeout(timeoutId);
      if (container) {
        container.removeEventListener('mouseup', handleMouseUp);
      }
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleHighlight = async () => {
    try {
      const annotation: Omit<Annotation, 'id'> = {
        annotation_type: 'highlight',
        selected_text: selectedText,
        color: '#FFFF00',
        page_number: currentPage,
        position_x: popupPosition.x,
        position_y: popupPosition.y,
        width: 100,
        height: 20,
        comment: ''
      };

      const response = await fetch(`/api/papers/${paperId}/annotations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...annotation,
          paper_id: paperId,
          collection_id: collectionId,
          is_private: false,
          shared_in_collection: !!collectionId
        })
      });

      if (response.ok) {
        const savedAnnotation = await response.json();
        setAnnotations([...annotations, savedAnnotation]);
      }
    } catch (error) {
      console.error('Error saving highlight:', error);
    }
    setShowPopup(false);
    window.getSelection()?.removeAllRanges();
  };

  const handleAddNote = () => {
    setShowNoteDialog(true);
    setShowPopup(false);
  };

  const handleSaveNote = async () => {
    try {
      const annotation: Omit<Annotation, 'id'> = {
        annotation_type: 'comment',
        selected_text: selectedText,
        color: '#FFE4B5',
        page_number: currentPage,
        position_x: popupPosition.x,
        position_y: popupPosition.y,
        width: 100,
        height: 20,
        comment: noteText
      };

      const response = await fetch(`/api/papers/${paperId}/annotations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...annotation,
          paper_id: paperId,
          collection_id: collectionId,
          is_private: false,
          shared_in_collection: !!collectionId
        })
      });

      if (response.ok) {
        const savedAnnotation = await response.json();
        setAnnotations([...annotations, savedAnnotation]);
      }
    } catch (error) {
      console.error('Error saving note:', error);
    }
    setShowNoteDialog(false);
    setNoteText('');
    window.getSelection()?.removeAllRanges();
  };

  const handleFlashcard = async () => {
    // TODO: Implement flashcard creation
    alert('Flashcard feature coming soon!');
    setShowPopup(false);
    window.getSelection()?.removeAllRanges();
  };

  const handleDeleteAnnotation = async (annotationId: string) => {
    try {
      const response = await fetch(`/api/annotations/${annotationId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setAnnotations(annotations.filter(a => a.id !== annotationId));
      }
    } catch (error) {
      console.error('Error deleting annotation:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-md z-10 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h2 className="text-lg font-semibold truncate max-w-2xl">{paper.title}</h2>
        </div>

        <div className="flex items-center space-x-4">
          {/* Toggle annotations */}
          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-md transition-colors ${
              showAnnotations ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
            </svg>
            <span>{annotations.filter(a => a.annotation_type === 'highlight').length} highlights</span>
          </button>
          
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-gray-100 relative overflow-auto" ref={containerRef}>
        <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
          <div style={{ height: '100%' }}>
            <Viewer 
              fileUrl={pdfUrl} 
              plugins={[defaultLayoutPluginInstance]}
              onPageChange={(e) => setCurrentPage(e.currentPage + 1)}
            />
          </div>
        </Worker>

        {/* Selection Popup */}
        {showPopup && (
          <div 
            ref={popupRef}
            className="absolute bg-gray-800 text-white rounded-lg shadow-lg p-1 flex space-x-1 z-20"
            style={{ 
              left: `${popupPosition.x}px`, 
              top: `${popupPosition.y - 40}px`,
              transform: 'translateX(-50%)'
            }}
          >
            <button
              onClick={handleHighlight}
              className="px-3 py-2 hover:bg-gray-700 rounded flex items-center space-x-2"
              title="Highlight"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">Highlight</span>
            </button>
            
            <button
              onClick={handleAddNote}
              className="px-3 py-2 hover:bg-gray-700 rounded flex items-center space-x-2"
              title="Add Note"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span className="text-sm">Note</span>
            </button>
            
            <button
              onClick={handleFlashcard}
              className="px-3 py-2 hover:bg-gray-700 rounded flex items-center space-x-2"
              title="Create Flashcard"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span className="text-sm">Flashcard</span>
            </button>
          </div>
        )}

        {/* Note Dialog */}
        {showNoteDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-30">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Add Note</h3>
              <p className="text-sm text-gray-600 mb-4 line-clamp-3">"{selectedText}"</p>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add your note..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                rows={4}
                autoFocus
              />
              <div className="flex justify-end space-x-3 mt-4">
                <button
                  onClick={() => {
                    setShowNoteDialog(false);
                    setNoteText('');
                  }}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveNote}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Save Note
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Annotations Display */}
        {showAnnotations && annotations.length > 0 && (
          <div className="absolute bottom-4 right-4 max-w-sm max-h-96 overflow-y-auto">
            <div className="bg-white rounded-lg shadow-lg p-4 space-y-3">
              <h4 className="font-semibold text-sm text-gray-700">Your Annotations</h4>
              {annotations.filter(a => a.page_number === currentPage).map((annotation) => (
                <div
                  key={annotation.id}
                  className={`p-3 rounded-md text-sm ${
                    annotation.annotation_type === 'highlight' 
                      ? 'bg-yellow-50 border border-yellow-200' 
                      : 'bg-blue-50 border border-blue-200'
                  }`}
                >
                  <p className="text-gray-700 line-clamp-2">{annotation.selected_text}</p>
                  {annotation.comment && (
                    <p className="text-xs text-gray-600 mt-1 italic">{annotation.comment}</p>
                  )}
                  <button
                    onClick={() => annotation.id && handleDeleteAnnotation(annotation.id)}
                    className="text-xs text-red-600 hover:text-red-700 mt-1"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFViewerWithSelection;
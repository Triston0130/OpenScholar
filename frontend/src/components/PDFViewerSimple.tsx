import React, { useState, useEffect, useRef } from 'react';
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

const PDFViewer: React.FC<PDFViewerProps> = ({ paper, pdfUrl, collectionId, onClose }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [showPopup, setShowPopup] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [selectedText, setSelectedText] = useState('');
  const [showNoteDialog, setShowNoteDialog] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [showQuickAnnotate, setShowQuickAnnotate] = useState(false);
  const [quickAnnotateText, setQuickAnnotateText] = useState('');

  // Generate a unique identifier for the paper
  const paperId = paper.doi || encodeURIComponent(paper.title);

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
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      
      if (text && text.length > 0) {
        const range = selection?.getRangeAt(0);
        const rect = range?.getBoundingClientRect();
        
        if (rect) {
          setSelectedText(text);
          setPopupPosition({
            x: rect.left + rect.width / 2,
            y: rect.top - 10
          });
          setShowPopup(true);
        }
      } else {
        setShowPopup(false);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('touchend', handleSelection);

    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('touchend', handleSelection);
    };
  }, []);

  const handleHighlight = async () => {
    try {
      const annotation: Omit<Annotation, 'id'> = {
        annotation_type: 'highlight',
        selected_text: selectedText,
        color: '#FFFF00',
        page_number: 1,
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
        page_number: 1,
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

  // Use Google Docs viewer as fallback for PDF viewing
  const viewerUrl = `https://docs.google.com/viewer?url=${encodeURIComponent(pdfUrl)}&embedded=true`;

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
          {/* Quick Annotate Button */}
          <button
            onClick={() => setShowQuickAnnotate(!showQuickAnnotate)}
            className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-md transition-colors ${
              showQuickAnnotate ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Quick Add</span>
          </button>
          
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
      <div className="flex-1 bg-gray-100 relative">
        {/* PDF Display */}
        <iframe
          src={viewerUrl}
          className="w-full h-full"
          title="PDF Viewer"
        />
        
        {/* Quick Annotate Panel */}
        {showQuickAnnotate && (
          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 w-96 z-20">
            <h3 className="font-semibold text-sm mb-3">Quick Annotate</h3>
            <p className="text-xs text-gray-600 mb-3">
              Copy text from the PDF and paste it here to annotate
            </p>
            <textarea
              value={quickAnnotateText}
              onChange={(e) => setQuickAnnotateText(e.target.value)}
              placeholder="Paste or type the text you want to annotate..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-3"
              rows={3}
              autoFocus
            />
            {quickAnnotateText && (
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setSelectedText(quickAnnotateText);
                    handleHighlight();
                    setQuickAnnotateText('');
                    setShowQuickAnnotate(false);
                  }}
                  className="flex-1 px-3 py-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 rounded-md text-sm font-medium transition-colors"
                >
                  <svg className="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
                  </svg>
                  Highlight
                </button>
                <button
                  onClick={() => {
                    setSelectedText(quickAnnotateText);
                    setShowNoteDialog(true);
                    setShowQuickAnnotate(false);
                  }}
                  className="flex-1 px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-md text-sm font-medium transition-colors"
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Add Note
                </button>
              </div>
            )}
          </div>
        )}

        {/* Selection Popup */}
        {showPopup && (
          <div 
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
              {annotations.map((annotation) => (
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

export default PDFViewer;
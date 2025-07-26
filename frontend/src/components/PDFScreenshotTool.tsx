import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Paper } from '../types';
import { createFlashcard, saveAnnotation } from '../utils/annotations';

interface PDFScreenshotToolProps {
  paper: Paper;
  pdfUrl: string;
  isActive: boolean;
  onClose: () => void;
  pdfContainer: HTMLElement | null;
}

interface SelectionRect {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  width: number;
  height: number;
}

export const PDFScreenshotTool: React.FC<PDFScreenshotToolProps> = ({
  paper,
  pdfUrl,
  isActive,
  onClose,
  pdfContainer,
}) => {
  const [isSelecting, setIsSelecting] = useState(false);
  const [selection, setSelection] = useState<SelectionRect | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [showActionMenu, setShowActionMenu] = useState(false);
  const [flashcardPrompt, setFlashcardPrompt] = useState('');
  const [noteText, setNoteText] = useState('');
  const [actionType, setActionType] = useState<'flashcard' | 'note' | null>(null);

  // Reset when inactive
  useEffect(() => {
    if (!isActive) {
      setIsSelecting(false);
      setSelection(null);
      setCapturedImage(null);
      setShowActionMenu(false);
      setFlashcardPrompt('');
      setNoteText('');
      setActionType(null);
    }
  }, [isActive]);

  // Mouse handlers - work directly on the PDF container like highlighting does
  useEffect(() => {
    if (!isActive || !pdfContainer) return;

    const handleMouseDown = (e: MouseEvent) => {
      // Prevent default to avoid text selection conflicts
      e.preventDefault();
      e.stopPropagation();
      
      // Get position relative to the PDF container
      const rect = pdfContainer.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setIsSelecting(true);
      setSelection({
        startX: x,
        startY: y,
        endX: x,
        endY: y,
        width: 0,
        height: 0
      });
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isSelecting || !selection) return;
      
      const rect = pdfContainer.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setSelection(prev => {
        if (!prev) return null;
        return {
          ...prev,
          endX: x,
          endY: y,
          width: Math.abs(x - prev.startX),
          height: Math.abs(y - prev.startY)
        };
      });
    };

    const handleMouseUp = async (e: MouseEvent) => {
      if (!isSelecting || !selection) return;
      
      setIsSelecting(false);
      
      // Only capture if selection is large enough
      if (selection.width > 20 && selection.height > 20) {
        await captureScreenshot();
      } else {
        setSelection(null);
      }
    };

    // Add event listeners to the PDF container
    pdfContainer.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // Disable text selection while screenshot tool is active
    const originalUserSelect = pdfContainer.style.userSelect;
    pdfContainer.style.userSelect = 'none';

    return () => {
      pdfContainer.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      
      // Restore text selection
      pdfContainer.style.userSelect = originalUserSelect;
    };
  }, [isActive, pdfContainer, isSelecting, selection]);

  const captureScreenshot = async () => {
    if (!selection || !pdfContainer) return;

    try {
      // Get the actual PDF canvas(es) - react-pdf-viewer renders to canvas elements
      const canvases = pdfContainer.querySelectorAll('.rpv-core__canvas-layer canvas, .rpv-core__canvasLayer canvas');
      
      if (canvases.length === 0) {
        console.error('No PDF canvases found');
        return;
      }

      // Create a temporary canvas to capture the selection
      const captureCanvas = document.createElement('canvas');
      captureCanvas.width = selection.width;
      captureCanvas.height = selection.height;
      const ctx = captureCanvas.getContext('2d');
      
      if (!ctx) return;

      // Fill with white background
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, selection.width, selection.height);

      // Get the selection bounds
      const selX = Math.min(selection.startX, selection.endX);
      const selY = Math.min(selection.startY, selection.endY);

      // Find which canvas(es) contain our selection and draw the relevant parts
      canvases.forEach((element) => {
        const canvas = element as HTMLCanvasElement;
        const canvasRect = canvas.getBoundingClientRect();
        const containerRect = pdfContainer.getBoundingClientRect();
        
        // Canvas position relative to container
        const canvasX = canvasRect.left - containerRect.left;
        const canvasY = canvasRect.top - containerRect.top;
        
        // Check if this canvas intersects with our selection
        if (canvasX < selX + selection.width && 
            canvasX + canvasRect.width > selX &&
            canvasY < selY + selection.height && 
            canvasY + canvasRect.height > selY) {
          
          // Calculate the intersection area
          const srcX = Math.max(0, selX - canvasX);
          const srcY = Math.max(0, selY - canvasY);
          const destX = Math.max(0, canvasX - selX);
          const destY = Math.max(0, canvasY - selY);
          const width = Math.min(canvas.width, selX + selection.width - canvasX) - srcX;
          const height = Math.min(canvas.height, selY + selection.height - canvasY) - srcY;
          
          // Scale factor (canvas internal size vs display size)
          const scaleX = canvas.width / canvasRect.width;
          const scaleY = canvas.height / canvasRect.height;
          
          // Draw the intersecting part
          ctx.drawImage(
            canvas,
            srcX * scaleX, srcY * scaleY, width * scaleX, height * scaleY,
            destX, destY, width, height
          );
        }
      });

      // Convert to image
      const imageData = captureCanvas.toDataURL('image/png');
      setCapturedImage(imageData);
      setShowActionMenu(true);
      
    } catch (error) {
      console.error('Screenshot capture failed:', error);
      alert('Failed to capture screenshot. Please try again.');
    }
  };

  const handleCreateFlashcard = () => {
    if (!capturedImage || !flashcardPrompt) return;
    
    const paperId = paper.doi || paper.full_text_url || paper.title;
    createFlashcard({
      paperId,
      pdfUrl,
      frontText: flashcardPrompt,
      backText: '',
      frontImage: capturedImage,
      tags: ['screenshot', 'visual'],
      category: 'Visual Content'
    });
    
    onClose();
  };

  const handleCreateNote = () => {
    if (!capturedImage || !noteText) return;
    
    const paperId = paper.doi || paper.full_text_url || paper.title;
    saveAnnotation({
      paperId,
      pdfUrl,
      type: 'image-note',
      text: noteText,
      image: capturedImage,
      note: noteText,
    });
    
    onClose();
  };

  if (!isActive) return null;

  const selectionStyle = selection ? {
    position: 'absolute' as const,
    left: Math.min(selection.startX, selection.endX),
    top: Math.min(selection.startY, selection.endY),
    width: selection.width,
    height: selection.height,
    border: '2px solid #007bff',
    backgroundColor: 'rgba(0, 123, 255, 0.1)',
    pointerEvents: 'none' as const,
    zIndex: 1000,
  } : {};

  return (
    <>
      {/* Selection rectangle */}
      {selection && (
        <div style={selectionStyle} />
      )}

      {/* Instructions */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          fontSize: '14px',
          pointerEvents: 'none',
          zIndex: 1001,
        }}
      >
        📷 Click and drag to select area for screenshot
      </div>
      
      {/* Close Button */}
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          backgroundColor: '#dc3545',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          padding: '8px 12px',
          cursor: 'pointer',
          fontSize: '14px',
          zIndex: 1001,
        }}
      >
        ✕ Close
      </button>

      {/* Action Menu Modal */}
      {showActionMenu && capturedImage && (
        <div
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            padding: '20px',
            zIndex: 2000,
            maxWidth: '500px',
            width: '90%',
          }}
        >
          <h3 style={{ marginBottom: '10px' }}>Screenshot Captured!</h3>
          
          <div style={{ marginBottom: '15px', textAlign: 'center' }}>
            <img 
              src={capturedImage} 
              alt="Screenshot preview" 
              style={{ 
                maxWidth: '100%', 
                maxHeight: '200px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }} 
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <button
              onClick={() => setActionType('flashcard')}
              style={{
                flex: 1,
                padding: '10px',
                backgroundColor: actionType === 'flashcard' ? '#007bff' : '#f8f9fa',
                color: actionType === 'flashcard' ? 'white' : 'black',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              🃏 Create Flashcard
            </button>
            <button
              onClick={() => setActionType('note')}
              style={{
                flex: 1,
                padding: '10px',
                backgroundColor: actionType === 'note' ? '#007bff' : '#f8f9fa',
                color: actionType === 'note' ? 'white' : 'black',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              📝 Create Note
            </button>
          </div>

          {actionType === 'flashcard' && (
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>
                Question/Prompt for this image:
              </label>
              <input
                type="text"
                value={flashcardPrompt}
                onChange={(e) => setFlashcardPrompt(e.target.value)}
                placeholder="e.g., 'What does this equation represent?'"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                }}
                autoFocus
              />
            </div>
          )}

          {actionType === 'note' && (
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>
                Description/Note:
              </label>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Describe what this image shows..."
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  minHeight: '80px',
                }}
                autoFocus
              />
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={actionType === 'flashcard' ? handleCreateFlashcard : handleCreateNote}
              disabled={
                (actionType === 'flashcard' && !flashcardPrompt) ||
                (actionType === 'note' && !noteText)
              }
              style={{
                flex: 1,
                padding: '10px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                opacity: 
                  ((actionType === 'flashcard' && !flashcardPrompt) ||
                  (actionType === 'note' && !noteText)) ? 0.5 : 1,
              }}
            >
              Save
            </button>
            <button
              onClick={() => {
                setShowActionMenu(false);
                setCapturedImage(null);
                setSelection(null);
                setActionType(null);
              }}
              style={{
                flex: 1,
                padding: '10px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default PDFScreenshotTool;
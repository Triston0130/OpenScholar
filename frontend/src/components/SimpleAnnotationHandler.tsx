import React, { useEffect } from 'react';

interface SimpleAnnotationHandlerProps {
  onTextSelected: (text: string, position: { x: number; y: number }) => void;
}

const SimpleAnnotationHandler: React.FC<SimpleAnnotationHandlerProps> = ({ onTextSelected }) => {
  useEffect(() => {
    const handleMouseUp = (event: MouseEvent) => {
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) return;

      const selectedText = selection.toString().trim();
      if (selectedText.length === 0) return;

      try {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        if (rect.width === 0 && rect.height === 0) return;

        // Check if selection is within a PDF viewer
        const target = event.target as HTMLElement;
        const pdfContainer = target.closest('.pdf-viewer-wrapper');
        if (!pdfContainer) return;

        console.log('Text selected via manual detection:', selectedText);
        
        onTextSelected(selectedText, {
          x: rect.left + rect.width / 2,
          y: rect.top
        });

      } catch (error) {
        console.warn('Error handling text selection:', error);
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [onTextSelected]);

  return null; // This component doesn't render anything
};

export default SimpleAnnotationHandler;
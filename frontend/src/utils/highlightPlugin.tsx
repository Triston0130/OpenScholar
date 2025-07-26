import React from 'react';
import { Plugin, PluginRenderPageLayer } from '@react-pdf-viewer/core';
import { Annotation } from './annotations';

interface HighlightPluginProps {
  annotations: Annotation[];
  onHighlightClick?: (annotation: Annotation) => void;
  onTextSelection?: (text: string, pageIndex: number, rects: any[]) => void;
}

// Highlight overlay component
const HighlightOverlay: React.FC<{
  annotation: Annotation;
  onHighlightClick?: (annotation: Annotation) => void;
}> = ({ annotation, onHighlightClick }) => {
  const [isHovered, setIsHovered] = React.useState(false);

  if (!annotation.textPosition?.rects) return null;

  return (
    <>
      {annotation.textPosition.rects.map((rect: any, index: number) => (
        <div
          key={`${annotation.id}-rect-${index}`}
          className="pdf-highlight-overlay"
          style={{
            position: 'absolute',
            left: `${rect.left}px`,
            top: `${rect.top}px`,
            width: `${rect.width}px`,
            height: `${rect.height}px`,
            backgroundColor: annotation.color || '#ffeb3b',
            opacity: isHovered ? 0.6 : 0.4,
            pointerEvents: 'auto',
            cursor: 'pointer',
            mixBlendMode: 'multiply',
            transition: 'opacity 0.2s ease-in-out',
          }}
          onClick={() => onHighlightClick?.(annotation)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        />
      ))}
      {annotation.type === 'note' && annotation.textPosition.rects.length > 0 && (
        <NoteIndicator annotation={annotation} />
      )}
    </>
  );
};

// Note indicator component
const NoteIndicator: React.FC<{ annotation: Annotation }> = ({ annotation }) => {
  const [showTooltip, setShowTooltip] = React.useState(false);
  const [tooltipPosition, setTooltipPosition] = React.useState({ x: 0, y: 0 });

  if (!annotation.textPosition?.rects || annotation.textPosition.rects.length === 0) {
    return null;
  }
  const firstRect = annotation.textPosition.rects[0] as any;

  const handleMouseEnter = (e: React.MouseEvent) => {
    setTooltipPosition({ x: e.clientX + 10, y: e.clientY });
    setShowTooltip(true);
  };

  return (
    <>
      <div
        className="pdf-note-indicator"
        style={{
          position: 'absolute',
          left: `${firstRect.left + firstRect.width}px`,
          top: `${firstRect.top}px`,
          width: '20px',
          height: '20px',
          cursor: 'pointer',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        title={annotation.note || ''}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowTooltip(false)}
      >
        📝
      </div>
      {showTooltip && (
        <div
          className="pdf-note-tooltip"
          style={{
            position: 'fixed',
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`,
            zIndex: 1001,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '14px',
            maxWidth: '300px',
            pointerEvents: 'none',
          }}
        >
          {annotation.note || ''}
        </div>
      )}
    </>
  );
};

export const highlightPlugin = (props: HighlightPluginProps): Plugin => {
  const { annotations, onHighlightClick, onTextSelection } = props;

  // Use onTextLayerRender instead of renderPageLayer
  const onTextLayerRender = (e: any) => {
    console.log('[highlightPlugin] onTextLayerRender called for page:', e.pageIndex);
    
    // We'll add highlight rendering logic here after text layer is ready
    setTimeout(() => {
      const { pageIndex } = e;
      
      // Filter annotations for this page
      const pageAnnotations = annotations.filter(
        ann => ann.pageNumber === pageIndex + 1 && (ann.type === 'highlight' || ann.type === 'note')
      );
      
      console.log('[highlightPlugin] Found', pageAnnotations.length, 'annotations for page', pageIndex + 1);
      
      // For now, just log - we'll add DOM manipulation here if needed
    }, 100);
  };

  // Handle text selection
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.toString().trim().length === 0) return;

    const range = selection.getRangeAt(0);
    const rects = Array.from(range.getClientRects());
    
    // Find which page this selection is on
    const container = range.commonAncestorContainer;
    const pageElement = container.nodeType === Node.TEXT_NODE
      ? container.parentElement?.closest('[data-page-number]')
      : (container as Element).closest('[data-page-number]');
    
    if (pageElement) {
      const pageNumber = parseInt(pageElement.getAttribute('data-page-number') || '1');
      onTextSelection?.(selection.toString(), pageNumber - 1, rects);
    }
  };

  return {
    onTextLayerRender,
    onDocumentLoad: () => {
      // Add global selection handler
      document.addEventListener('mouseup', handleTextSelection);
      
      // Return cleanup function
      return () => {
        document.removeEventListener('mouseup', handleTextSelection);
      };
    },
  };
};
import React, { useState, useEffect, useRef } from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import { Paper } from '../types';
import { resolvePDFUrl, PDFSource, isPDFUrl } from '../utils/pdfUrlResolver';

interface PDFViewerProps {
  paper: Paper;
  pdfUrl: string;
  collectionId?: string;
  onClose: () => void;
}

const PDFViewerMultiSource: React.FC<PDFViewerProps> = ({ paper, pdfUrl, collectionId, onClose }) => {
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0);
  const [pdfSources, setPdfSources] = useState<PDFSource[]>([]);
  const [loadError, setLoadError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedText, setSelectedText] = useState('');
  const [showPopup, setShowPopup] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [forceIframe, setForceIframe] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    // Resolve all possible PDF sources
    const sources = resolvePDFUrl(paper);
    
    // Add the provided pdfUrl as the first source if it's not already included
    if (pdfUrl && !sources.some(s => s.url === pdfUrl)) {
      sources.unshift({
        url: pdfUrl,
        type: isPDFUrl(pdfUrl) ? 'direct' : 'viewer',
        source: 'Provided URL'
      });
    }
    
    setPdfSources(sources);
  }, [paper, pdfUrl]);

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

  const handleLoadError = () => {
    setLoadError(true);
    setIsLoading(false);
    
    // If it's a direct PDF that failed, try it as an iframe
    if (currentSource?.type === 'direct' && !forceIframe) {
      setForceIframe(true);
      setLoadError(false);
      setIsLoading(true);
      return;
    }
    
    // Try next source if available
    if (currentSourceIndex < pdfSources.length - 1) {
      setTimeout(() => {
        setCurrentSourceIndex(currentSourceIndex + 1);
        setLoadError(false);
        setIsLoading(true);
        setForceIframe(false);
      }, 1000);
    }
  };

  const handleLoadSuccess = () => {
    setLoadError(false);
    setIsLoading(false);
  };

  const tryPreviousSource = () => {
    if (currentSourceIndex > 0) {
      setCurrentSourceIndex(currentSourceIndex - 1);
      setLoadError(false);
      setIsLoading(true);
      setForceIframe(false);
    }
  };

  const tryNextSource = () => {
    if (currentSourceIndex < pdfSources.length - 1) {
      setCurrentSourceIndex(currentSourceIndex + 1);
      setLoadError(false);
      setIsLoading(true);
      setForceIframe(false);
    }
  };

  const handleHighlight = async () => {
    // Implement highlight functionality
    console.log('Highlighting:', selectedText);
    setShowPopup(false);
    window.getSelection()?.removeAllRanges();
  };

  const handleAddNote = () => {
    // Implement note functionality
    console.log('Adding note for:', selectedText);
    setShowPopup(false);
  };

  const handleFlashcard = () => {
    // Implement flashcard functionality
    console.log('Creating flashcard for:', selectedText);
    setShowPopup(false);
    window.getSelection()?.removeAllRanges();
  };

  const currentSource = pdfSources[currentSourceIndex];

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
          {/* Source selector */}
          {pdfSources.length > 1 && (
            <div className="flex items-center space-x-2">
              <button
                onClick={tryPreviousSource}
                disabled={currentSourceIndex === 0}
                className="p-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span className="text-sm">
                {currentSource?.source} ({currentSourceIndex + 1}/{pdfSources.length})
              </span>
              <button
                onClick={tryNextSource}
                disabled={currentSourceIndex === pdfSources.length - 1}
                className="p-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          )}
          
          <a
            href={currentSource?.url}
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
        {currentSource && (
          <>
            {currentSource.type === 'direct' && !forceIframe ? (
              <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
                <div style={{ height: '100%' }}>
                  {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-600">Loading PDF from {currentSource.source}...</p>
                      </div>
                    </div>
                  )}
                  <Viewer 
                    fileUrl={currentSource.url} 
                    plugins={[defaultLayoutPluginInstance]}
                    onDocumentLoad={handleLoadSuccess}
                    renderError={(error: any) => {
                      handleLoadError();
                      return (
                        <div className="text-center p-8">
                          <p className="text-red-600">Failed to load PDF</p>
                        </div>
                      );
                    }}
                  />
                </div>
              </Worker>
            ) : (
              // Fallback to iframe for viewer types or when PDF.js fails
              <div className="w-full h-full relative">
                {currentSource.type === 'viewer' || currentSource.source === 'Google Docs Viewer' ? (
                  <iframe
                    src={currentSource.url}
                    className="w-full h-full"
                    title="PDF Viewer"
                    onLoad={handleLoadSuccess}
                    onError={handleLoadError}
                  />
                ) : (
                  // For direct URLs that might be HTML, show a message
                  <div className="flex items-center justify-center h-full bg-white">
                    <div className="text-center p-8 max-w-2xl">
                      <svg className="w-16 h-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <h3 className="text-lg font-semibold mb-2">This appears to be a webpage, not a PDF</h3>
                      <p className="text-gray-600 mb-4">
                        The link provided leads to an HTML page instead of a PDF file. 
                        You may need to look for a "Download PDF" button on the publisher's website.
                      </p>
                      <div className="space-y-3">
                        <a
                          href={currentSource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Open in new tab
                        </a>
                        {currentSourceIndex < pdfSources.length - 1 && (
                          <button
                            onClick={tryNextSource}
                            className="block mx-auto px-4 py-2 text-blue-600 hover:text-blue-700"
                          >
                            Try next source →
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-4">
                        Tip: Some publishers require you to be on their website to download PDFs
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Error state */}
        {loadError && currentSourceIndex === pdfSources.length - 1 && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center p-8">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-lg font-semibold mb-2">Unable to load PDF</h3>
              <p className="text-gray-600 mb-4">
                We tried {pdfSources.length} different sources but couldn't load the PDF.
              </p>
              <div className="space-y-2">
                <a
                  href={pdfSources[0]?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Try opening in new tab
                </a>
                <p className="text-sm text-gray-500">
                  You may need institutional access or a subscription
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Selection Popup */}
        {showPopup && currentSource?.type === 'direct' && (
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
      </div>
    </div>
  );
};

export default PDFViewerMultiSource;
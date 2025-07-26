import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Worker, Viewer, DocumentLoadEvent } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import './PDFViewerSmart.css';
import { Paper } from '../types';
import HTMLViewer from './HTMLViewer';
import { createFlashcard, getAnnotationsByPdfUrl, Annotation, saveAnnotation } from '../utils/annotations';
import AnnotationsPanel from './AnnotationsPanel';
import { highlightPlugin } from '@react-pdf-viewer/highlight';
import '@react-pdf-viewer/highlight/lib/styles/index.css';
import FlashcardPanel from './FlashcardPanel';
import AnnotationMenu from './AnnotationMenu';
import TextToSpeech from './TextToSpeech';
import TextbookProcessor from './TextbookProcessor';
import PDFScreenshotTool from './PDFScreenshotTool';

// Extend Window interface for DOAB PDF override
declare global {
  interface Window {
    DOAB_PDF_OVERRIDE?: string;
  }
}

interface PDFViewerProps {
  paper: Paper;
  pdfUrl: string;
  collectionId?: string;
  onClose: () => void;
}

type ViewerMode = 'detecting' | 'pdf-direct' | 'html-viewer' | 'external' | 'error';

const PDFViewerSmart: React.FC<PDFViewerProps> = ({ paper, pdfUrl, collectionId, onClose }) => {
  console.log('[PDFViewerSmart] Component mounted with props:', { paper, pdfUrl, collectionId });
  
  // All hooks must be declared before any conditional returns
  const [viewerMode, setViewerMode] = useState<ViewerMode>('detecting');
  const [errorMessage, setErrorMessage] = useState('');
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [showAnnotationsPanel, setShowAnnotationsPanel] = useState(false);
  const [useProxy, setUseProxy] = useState(false);
  const [showFlashcardReview, setShowFlashcardReview] = useState(false);
  const [showAnnotationMenu, setShowAnnotationMenu] = useState(false);
  const [activePanel, setActivePanel] = useState<'annotations' | 'flashcards' | null>(null);
  const [selectedText, setSelectedText] = useState('');
  const [selectedAreas, setSelectedAreas] = useState<any[]>([]);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const [showTextToSpeech, setShowTextToSpeech] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [showTextbookProcessor, setShowTextbookProcessor] = useState(false);
  const [showScreenshotTool, setShowScreenshotTool] = useState(false);
  const [currentPageNumber, setCurrentPageNumber] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [currentReadingSentence, setCurrentReadingSentence] = useState<number>(-1);
  const [ttsHighlightAreas, setTtsHighlightAreas] = useState<any[]>([]);
  const [pdfTextMap, setPdfTextMap] = useState<Map<number, any[]>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);
  const pdfDocRef = useRef<any>(null);
  const pdfViewerRef = useRef<HTMLDivElement>(null);

  // Handler functions for the annotation menu
  const handleCreateHighlight = useCallback((color: string, label: string) => {
    if (!selectedText || selectedAreas.length === 0) return;
    
    const paperId = paper.doi || paper.full_text_url || paper.title;
    
    saveAnnotation({
      paperId,
      pdfUrl,
      type: 'highlight',
      text: selectedText,
      highlightAreas: selectedAreas,
      pageNumber: selectedAreas[0]?.pageIndex + 1,
      color,
      label,
      category: label,
    });
    
    // Force re-render
    const updated = getAnnotationsByPdfUrl(pdfUrl);
    setAnnotations(updated);
    
    // Clear selection
    setSelectedText('');
    setSelectedAreas([]);
  }, [paper, pdfUrl, selectedText, selectedAreas]);
  
  const handleCreateNote = useCallback((noteText: string, color: string) => {
    if (!selectedText || selectedAreas.length === 0) return;
    
    const paperId = paper.doi || paper.full_text_url || paper.title;
    
    saveAnnotation({
      paperId,
      pdfUrl,
      type: 'note',
      text: selectedText,
      note: noteText,
      highlightAreas: selectedAreas,
      pageNumber: selectedAreas[0]?.pageIndex + 1,
      color,
      label: 'Note',
    });
    
    // Force re-render
    const updated = getAnnotationsByPdfUrl(pdfUrl);
    setAnnotations(updated);
    
    // Clear selection
    setSelectedText('');
    setSelectedAreas([]);
  }, [paper, pdfUrl, selectedText, selectedAreas]);
  
  const handleCreateFlashcard = useCallback((front: string, back: string) => {
    if (!selectedText || selectedAreas.length === 0) return;
    
    const paperId = paper.doi || paper.full_text_url || paper.title;
    
    createFlashcard({
      paperId,
      pdfUrl,
      text: selectedText,
      frontText: front,
      backText: back,
      pageNumber: selectedAreas[0]?.pageIndex + 1
    });
    
    // Clear selection
    setSelectedText('');
    setSelectedAreas([]);
  }, [paper, pdfUrl, selectedText, selectedAreas]);

  // Create plugins with render callbacks but better positioning
  const highlightPluginInstance = highlightPlugin({
    renderHighlightTarget: (props) => {
      console.log('Text selected:', props.selectedText, 'Areas:', props.highlightAreas);
      
      // Better positioning calculation - use selection region for menu positioning
      const menuX = Math.min(window.innerWidth / 2, window.innerWidth - 200);
      const menuY = 100;
      
      return (
        <div
          data-annotation-target
          style={{
            background: 'rgba(59, 130, 246, 0.2)',
            border: '2px solid #3b82f6',
            borderRadius: '4px',
            // Use absolute positioning with proper coordinates
            position: 'absolute',
            left: props.selectionRegion.left + '%',
            top: props.selectionRegion.top + '%',
            width: props.selectionRegion.width + '%',
            height: props.selectionRegion.height + '%',
            cursor: 'pointer',
            zIndex: 1000,
            animation: 'pulse 1s infinite',
            // Ensure proper box sizing
            boxSizing: 'border-box',
            // Prevent text selection on the overlay
            userSelect: 'none',
            // Improve rendering
            backfaceVisibility: 'hidden',
          }}
          onClick={(e) => {
            e.stopPropagation();
            console.log('Opening annotation menu');
            
            // Store selection data - keep raw percentage values from the plugin
            setSelectedText(props.selectedText);
            setSelectedAreas(props.highlightAreas); // Keep exactly as provided by plugin
            setMenuPosition({ x: menuX, y: menuY }); // Use calculated positioning
            setShowAnnotationMenu(true);
          }}
          title="Click to open annotation menu"
        >
          <div
            style={{
              position: 'absolute',
              top: '-35px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: '#1f2937',
              color: 'white',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '500',
              whiteSpace: 'nowrap',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              pointerEvents: 'none',
              // Prevent tooltip from causing alignment issues
              zIndex: 1001,
            }}
          >
            🎯 Click to annotate
          </div>
        </div>
      );
    },
    renderHighlights: (props) => (
      <>
        {/* TTS Reading Highlights */}
        {ttsHighlightAreas
          .filter(area => area.pageIndex === props.pageIndex)
          .map((area, idx) => {
            const cssProps = props.getCssProperties(area, props.rotation || 0);
            return (
              <div
                key={`tts-${idx}`}
                className="tts-highlight-area"
                style={{
                  background: '#ffeb3b',
                  opacity: 0.5,
                  position: 'absolute',
                  left: cssProps.left,
                  top: cssProps.top,
                  width: cssProps.width,
                  height: cssProps.height,
                  transform: cssProps.transform || 'none',
                  transformOrigin: cssProps.transformOrigin || 'top left',
                  zIndex: 5,
                  pointerEvents: 'none',
                  transition: 'all 0.2s ease',
                  mixBlendMode: 'multiply',
                }}
              />
            );
          })}
        
        {/* Regular Annotations */}
        {annotations
          .filter(ann => ann.highlightAreas && (ann.type === 'highlight' || ann.type === 'note'))
          .map(ann => ann.highlightAreas
            ?.filter(area => area.pageIndex === props.pageIndex)
            .map((area, idx) => {
              // Get proper CSS properties with correct positioning
              const cssProps = props.getCssProperties(area, props.rotation || 0);
              
              return (
                <div
                  key={`${ann.id}-${idx}`}
                  className="pdf-highlight-rendered"
                  style={{
                    background: ann.color || '#ffeb3b',
                    opacity: ann.type === 'note' ? 0.3 : 0.4,
                    border: ann.type === 'note' ? `2px solid ${ann.color}` : 'none',
                    borderRadius: ann.type === 'note' ? '2px' : '0',
                    cursor: ann.type === 'note' ? 'pointer' : 'default',
                    // Use absolute positioning to fix alignment issues
                    position: 'absolute',
                    left: cssProps.left,
                    top: cssProps.top,
                    width: cssProps.width,
                    height: cssProps.height,
                    transform: cssProps.transform || 'none',
                    transformOrigin: cssProps.transformOrigin || 'top left',
                    // Add z-index to ensure highlights appear correctly
                    zIndex: 10,
                    // Improve rendering
                    pointerEvents: 'auto',
                    mixBlendMode: 'multiply',
                  }}
                  onClick={() => {
                    if (ann.type === 'note' && ann.note) {
                      alert(`Note: ${ann.note}`);
                    }
                  }}
                  title={ann.type === 'highlight' ? `${ann.label || 'Highlight'}: ${ann.text.substring(0, 100)}` : `Note: ${ann.note}`}
                >
                  {ann.type === 'note' && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '-4px',
                        right: '-4px',
                        background: ann.color || '#60a5fa',
                        borderRadius: '50%',
                        width: '16px',
                        height: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        color: 'white',
                        fontWeight: 'bold',
                        zIndex: 11,
                      }}
                    >
                      !
                    </div>
                  )}
                  {ann.label && ann.type === 'highlight' && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '-20px',
                        left: '0',
                        background: ann.color,
                        color: 'white',
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: '500',
                        whiteSpace: 'nowrap',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        zIndex: 11,
                      }}
                    >
                      {ann.label}
                    </div>
                  )}
                </div>
              );
            })
          )}
      </>
    ),
  });
  
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    sidebarTabs: () => [],
    toolbarPlugin: {},
  });

  // Helper function to resolve DOI to direct PDF URL
  const resolvePdfFromDoi = (doi: string): string | null => {
    // Springer/Nature pattern
    if (doi.startsWith('10.1007/') || doi.startsWith('10.1038/')) {
      return `https://link.springer.com/content/pdf/${doi}.pdf`;
    }
    
    // BioMed Central pattern (using bmcpublichealth as fallback subdomain)
    if (doi.startsWith('10.1186/')) {
      return `https://bmcpublichealth.biomedcentral.com/counter/pdf/${doi}.pdf`;
    }
    
    // PLOS pattern
    if (doi.startsWith('10.1371/')) {
      // Extract journal and ID from DOI
      const match = doi.match(/10\.1371\/journal\.(\w+)\.(\d+)/);
      if (match) {
        return `https://journals.plos.org/plos${match[1]}/article/file?id=${doi}&type=printable`;
      }
    }
    
    // No known pattern - return null to let backend handle it
    return null;
  };

  // Extract PDF URL from DOAB handle pages and PLOS articles
  useEffect(() => {
    const extractPdfUrl = async () => {
      // Internet Archive / Open Library extraction
      if ((paper.source === 'Open Library' || paper.source === 'Internet Archive') && pdfUrl.includes('archive.org')) {
        console.log('[PDFViewerSmart] Extracting PDF URL from Internet Archive:', pdfUrl);
        
        try {
          // Internet Archive has predictable PDF URLs based on the item identifier
          // Extract identifier from URL patterns like:
          // https://archive.org/details/entangledarchaeo0000hodd
          // https://archive.org/stream/entangledarchaeo0000hodd
          
          let identifier = null;
          
          // Try to extract from /details/ URL
          const detailsMatch = pdfUrl.match(/archive\.org\/details\/([^\/\?#]+)/);
          if (detailsMatch) {
            identifier = detailsMatch[1];
          }
          
          // Try to extract from /stream/ URL
          if (!identifier) {
            const streamMatch = pdfUrl.match(/archive\.org\/stream\/([^\/\?#]+)/);
            if (streamMatch) {
              identifier = streamMatch[1];
            }
          }
          
          if (identifier) {
            console.log('[PDFViewerSmart] Found Internet Archive identifier:', identifier);
            // Don't try to construct URL, fetch the page to find actual PDF links
          }
          
          // Always fetch the page to find PDF links (even if we have identifier)
          {
            // If we can't extract identifier, try fetching the page
            const response = await fetch(`/api/proxy-html?url=${encodeURIComponent(pdfUrl)}`);
            const data = await response.json();
            
            if (data.content) {
              const dom = new DOMParser().parseFromString(data.content, 'text/html');
              
              // Look for PDF download links on Internet Archive pages
              // Try multiple selectors for different page layouts
              const selectors = [
                'a[href*=".pdf"]',
                'a[href*="/download/"][href*=".pdf"]',
                '.download-pill a[href*=".pdf"]',
                '.item-download-options a[href*=".pdf"]',
                'a.stealth[href*=".pdf"]',
                '.files-list a[href*=".pdf"]',
                '.download-button[href*=".pdf"]'
              ];
              
              let foundPdfUrl = null;
              
              // Try each selector
              for (const selector of selectors) {
                try {
                  const links = dom.querySelectorAll(selector);
                  for (let i = 0; i < links.length; i++) {
                    const link = links[i];
                    const href = link.getAttribute('href') || '';
                    const text = link.textContent || '';
                    
                    // Skip thumbnail PDFs and other non-main PDFs
                    if (href.includes('_thumb.pdf') || href.includes('_small.pdf')) {
                      continue;
                    }
                    
                    if (href.includes('.pdf')) {
                      foundPdfUrl = href;
                      break;
                    }
                  }
                  if (foundPdfUrl) break;
                } catch (e) {
                  continue;
                }
              }
              
              // If no PDF found with specific selectors, try all links
              if (!foundPdfUrl) {
                const allLinks = dom.querySelectorAll('a[href]');
                console.log('[PDFViewerSmart] Searching all links for PDF...');
                
                for (let i = 0; i < allLinks.length; i++) {
                  const link = allLinks[i];
                  const href = link.getAttribute('href') || '';
                  const text = link.textContent || '';
                  
                  // Look for PDF links
                  if (href.includes('.pdf') && !href.includes('_thumb.pdf') && !href.includes('_small.pdf')) {
                    foundPdfUrl = href;
                    console.log(`[PDFViewerSmart] Found PDF link: "${text}" -> ${href}`);
                    break;
                  }
                }
                
                // If still no PDF, check for online reader (some books are view-only)
                if (!foundPdfUrl && identifier) {
                  // Try the online reader URL for books that can't be downloaded
                  const readerUrl = `https://archive.org/stream/${identifier}`;
                  console.log('[PDFViewerSmart] No downloadable PDF found, trying online reader:', readerUrl);
                  
                  // For online-only books, we should use the HTML viewer
                  // Don't set DOAB_PDF_OVERRIDE in this case
                  return;
                }
              }
              
              if (foundPdfUrl) {
                let extractedPdfUrl = foundPdfUrl;
                
                // Make URL absolute if needed
                if (!extractedPdfUrl.startsWith('http')) {
                  if (extractedPdfUrl.startsWith('//')) {
                    extractedPdfUrl = 'https:' + extractedPdfUrl;
                  } else if (extractedPdfUrl.startsWith('/')) {
                    extractedPdfUrl = 'https://archive.org' + extractedPdfUrl;
                  }
                }
                
                console.log('[PDFViewerSmart] Found Internet Archive PDF URL:', extractedPdfUrl);
                
                setUseProxy(true);
                setViewerMode('pdf-direct');
                window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
                
                return;
              } else {
                console.log('[PDFViewerSmart] No PDF found on Internet Archive page');
                
                // Log available file types for debugging
                const fileLinks = dom.querySelectorAll('a[href*="/download/"]');
                const fileTypes = new Set();
                for (let i = 0; i < fileLinks.length; i++) {
                  const href = fileLinks[i].getAttribute('href') || '';
                  const match = href.match(/\.(\w+)$/);
                  if (match) {
                    fileTypes.add(match[1].toUpperCase());
                  }
                }
                if (fileTypes.size > 0) {
                  console.log('[PDFViewerSmart] Available file types:', Array.from(fileTypes).join(', '));
                }
              }
            }
          }
        } catch (error) {
          console.error('[PDFViewerSmart] Error extracting Internet Archive PDF URL:', error);
        }
      }
      
      // OAPEN extraction
      else if (paper.source === 'OAPEN' && (pdfUrl.includes('library.oapen.org') || pdfUrl.includes('oapen.org'))) {
        console.log('[PDFViewerSmart] Extracting PDF URL from OAPEN page:', pdfUrl);
        
        // Check if it's already a viewer URL (these need special handling)
        if (pdfUrl.includes('/viewer/')) {
          // Extract the book ID from viewer URL
          // Format: https://library.oapen.org/viewer/web/viewer.html?file=...
          const urlParams = new URLSearchParams(pdfUrl.split('?')[1] || '');
          const fileParam = urlParams.get('file');
          
          if (fileParam) {
            // The file parameter contains the encoded PDF URL
            const decodedPdfUrl = decodeURIComponent(fileParam);
            console.log('[PDFViewerSmart] Extracted PDF URL from viewer:', decodedPdfUrl);
            
            setUseProxy(true);
            setViewerMode('pdf-direct');
            window.DOAB_PDF_OVERRIDE = decodedPdfUrl;
            return;
          }
        }
        
        try {
          // Use the proxy-html endpoint to fetch the OAPEN page
          const response = await fetch(`/api/proxy-html?url=${encodeURIComponent(pdfUrl)}`);
          const data = await response.json();
          
          if (data.content) {
            // Parse the HTML to find PDF link
            const dom = new DOMParser().parseFromString(data.content, 'text/html');
            
            // Look for download links - OAPEN uses various patterns
            // Try multiple selectors
            const selectors = [
              'a[href*="/bitstream/"][href$=".pdf"]',
              'a[href*="/download?"][href$=".pdf"]',
              'a[href*="download.php"][href*="pdf"]',
              'a.download-link[href$=".pdf"]',
              'a[href*="/viewer/"][href$=".pdf"]',
              // Look for buttons with PDF text
              'a:has-text("PDF")',
              'button:has-text("PDF")',
              // Common download button patterns
              'a.btn-download[href*="pdf"]',
              'a.download-button[href*="pdf"]'
            ];
            
            let pdfLink = null;
            for (const selector of selectors) {
              try {
                pdfLink = dom.querySelector(selector);
                if (pdfLink) break;
              } catch (e) {
                // Some selectors might not be supported
                continue;
              }
            }
            
            // If no link found with selectors, search for PDF URLs in href attributes
            if (!pdfLink) {
              const allLinks = dom.querySelectorAll('a[href]');
              for (let i = 0; i < allLinks.length; i++) {
                const link = allLinks[i];
                const href = link.getAttribute('href') || '';
                const linkText = link.textContent || '';
                // Look for PDF download links - OAPEN specific patterns
                if (href.includes('.pdf') || 
                    href.includes('/bitstream/') ||
                    href.includes('/download') ||
                    (href.includes('format=pdf')) ||
                    (linkText.toUpperCase().includes('PDF') && (href.includes('download') || href.includes('bitstream')))) {
                  pdfLink = link;
                  break;
                }
              }
            }
            
            if (pdfLink) {
              const hrefAttr = pdfLink.getAttribute('href');
              
              if (hrefAttr) {
                let extractedPdfUrl = hrefAttr;
                
                // Make URL absolute if needed
                if (!extractedPdfUrl.startsWith('http')) {
                  if (extractedPdfUrl.startsWith('/')) {
                    // Extract base URL from current URL
                    const urlObj = new URL(pdfUrl);
                    extractedPdfUrl = urlObj.origin + extractedPdfUrl;
                  } else {
                    // Relative to current path
                    const baseUrl = pdfUrl.substring(0, pdfUrl.lastIndexOf('/'));
                    extractedPdfUrl = baseUrl + '/' + extractedPdfUrl;
                  }
                }
                
                console.log('[PDFViewerSmart] Found OAPEN PDF URL:', extractedPdfUrl);
                
                // Update the component to use the PDF URL
                setUseProxy(true);
                setViewerMode('pdf-direct');
                
                // Override the pdfUrl for this session
                window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
                
                return;
              }
            } else {
              console.log('[PDFViewerSmart] No PDF link found in OAPEN page');
              // Log all links for debugging
              const allLinks = dom.querySelectorAll('a[href]');
              console.log('[PDFViewerSmart] Available links on page:');
              for (let i = 0; i < allLinks.length; i++) {
                const link = allLinks[i];
                const href = link.getAttribute('href') || '';
                const text = link.textContent?.trim() || '';
                if (text.includes('PDF') || href.includes('pdf') || href.includes('download')) {
                  console.log(`  - Text: "${text}", Href: "${href}"`);
                }
              }
            }
          }
        } catch (error) {
          console.error('[PDFViewerSmart] Error extracting OAPEN PDF URL:', error);
        }
      }
      
      // DOAB extraction
      else if (paper.source === 'DOAB' && pdfUrl.includes('/handle/')) {
        console.log('[PDFViewerSmart] Extracting PDF URL from DOAB handle page:', pdfUrl);
        
        try {
          // Use the proxy-html endpoint to fetch the handle page
          const response = await fetch(`/api/proxy-html?url=${encodeURIComponent(pdfUrl)}`);
          const data = await response.json();
          
          if (data.content) {
            // Parse the HTML to find PDF link
            const dom = new DOMParser().parseFromString(data.content, 'text/html');
            
            // Look for bitstream PDF links
            const pdfLink = dom.querySelector('a[href*="bitstream"][href$=".pdf"]');
            
            if (pdfLink) {
              const hrefAttr = pdfLink.getAttribute('href');
              
              if (hrefAttr) {
                let extractedPdfUrl = hrefAttr;
                
                // Make URL absolute if needed
                if (!extractedPdfUrl.startsWith('http')) {
                  if (extractedPdfUrl.startsWith('/')) {
                    extractedPdfUrl = 'https://directory.doabooks.org' + extractedPdfUrl;
                  } else {
                    // Relative to current path
                    const baseUrl = pdfUrl.substring(0, pdfUrl.lastIndexOf('/'));
                    extractedPdfUrl = baseUrl + '/' + extractedPdfUrl;
                  }
                }
                
                console.log('[PDFViewerSmart] Found PDF URL:', extractedPdfUrl);
                
                // Update the component to use the PDF URL
                setUseProxy(true);
                setViewerMode('pdf-direct');
                
                // Override the pdfUrl for this session
                window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
                
                return;
              }
            }
          }
        } catch (error) {
          console.error('[PDFViewerSmart] Error extracting DOAB PDF URL:', error);
        }
      }
      
      // PLOS extraction
      else if (paper.source === 'PLOS' && (pdfUrl.includes('plos.org') || pdfUrl.includes('plosone.org'))) {
        console.log('[PDFViewerSmart] Extracting PDF URL from PLOS article:', pdfUrl);
        
        try {
          // PLOS has a predictable pattern - just append ?type=printable to get PDF
          // e.g., https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456
          // becomes https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0123456&type=printable
          
          let extractedPdfUrl = pdfUrl;
          
          // Check if it's already a PDF URL
          if (!pdfUrl.includes('type=printable') && !pdfUrl.includes('/file?')) {
            // Replace /article? with /article/file? and add type=printable
            if (pdfUrl.includes('/article?')) {
              extractedPdfUrl = pdfUrl.replace('/article?', '/article/file?') + '&type=printable';
            } else if (pdfUrl.includes('/article/')) {
              // Handle URLs like /article/id/... 
              const articleMatch = pdfUrl.match(/(.+\/article)(\/.+)/);
              if (articleMatch) {
                extractedPdfUrl = articleMatch[1] + '/file' + articleMatch[2] + '?type=printable';
              }
            }
          }
          
          console.log('[PDFViewerSmart] Generated PLOS PDF URL:', extractedPdfUrl);
          
          // Update the component to use the PDF URL
          setUseProxy(true);
          setViewerMode('pdf-direct');
          
          // Override the pdfUrl for this session
          window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
          
          return;
        } catch (error) {
          console.error('[PDFViewerSmart] Error extracting PLOS PDF URL:', error);
        }
      }
      
      // Handle any DOI URL
      else if (pdfUrl.includes('doi.org/')) {
        console.log('[PDFViewerSmart] Detected DOI URL:', pdfUrl);
        
        try {
          // Extract the DOI from the URL
          const doiMatch = pdfUrl.match(/doi\.org\/(10\.\d+\/[^?#]+)/);
          if (doiMatch) {
            const doi = doiMatch[1];
            console.log('[PDFViewerSmart] Extracted DOI:', doi);
            
            // Try to resolve to direct PDF URL
            const resolvedPdfUrl = resolvePdfFromDoi(doi);
            
            if (resolvedPdfUrl) {
              console.log('[PDFViewerSmart] Resolved PDF URL:', resolvedPdfUrl);
              
              // Update the component to use the PDF URL
              setUseProxy(true);
              setViewerMode('pdf-direct');
              
              // Override the pdfUrl for this session
              window.DOAB_PDF_OVERRIDE = resolvedPdfUrl;
              
              return;
            } else {
              console.log('[PDFViewerSmart] No known PDF pattern for DOI:', doi);
            }
          }
        } catch (error) {
          console.error('[PDFViewerSmart] Error resolving DOI:', error);
        }
      }
      
      // ERIC extraction
      else if (pdfUrl.includes('eric.ed.gov')) {
        console.log('[PDFViewerSmart] Extracting PDF URL from ERIC:', pdfUrl);
        
        // ERIC landing pages look like https://eric.ed.gov/?id=EJ1369874
        // Real PDFs are at https://files.eric.ed.gov/fulltext/EJ1369874.pdf
        const idMatch = pdfUrl.match(/[?&]id=(E[JD]\d+)/i);
        
        if (idMatch) {
          const ericId = idMatch[1];
          const extractedPdfUrl = `https://files.eric.ed.gov/fulltext/${ericId}.pdf`;
          
          console.log('[PDFViewerSmart] Generated ERIC PDF URL:', extractedPdfUrl);
          
          setUseProxy(true);
          setViewerMode('pdf-direct');
          window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
          
          return;
        } else {
          console.log('[PDFViewerSmart] Could not extract ERIC ID from URL');
        }
      }
      
      // Handle direct publisher URLs
      else if (pdfUrl.includes('biomedcentral.com') && pdfUrl.includes('/articles/')) {
        // BMC direct article URLs
        const doiMatch = pdfUrl.match(/\/articles\/(10\.\d+\/[^?#]+)/);
        if (doiMatch) {
          const doi = doiMatch[1];
          const baseUrl = pdfUrl.substring(0, pdfUrl.indexOf('/articles/'));
          const extractedPdfUrl = `${baseUrl}/counter/pdf/${doi}.pdf`;
          
          console.log('[PDFViewerSmart] Generated BMC PDF URL:', extractedPdfUrl);
          
          setUseProxy(true);
          setViewerMode('pdf-direct');
          window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
          
          return;
        }
      }
      else if (pdfUrl.includes('nature.com') && pdfUrl.includes('/articles/')) {
        // Nature direct article URLs
        const articleMatch = pdfUrl.match(/\/articles\/([^?#]+)/);
        if (articleMatch) {
          const articleId = articleMatch[1];
          const extractedPdfUrl = `https://www.nature.com/articles/${articleId}.pdf`;
          
          console.log('[PDFViewerSmart] Generated Nature PDF URL:', extractedPdfUrl);
          
          setUseProxy(true);
          setViewerMode('pdf-direct');
          window.DOAB_PDF_OVERRIDE = extractedPdfUrl;
          
          return;
        }
      }
      
      // If not DOAB/PLOS or extraction failed, proceed with normal detection
      detectBestViewer();
    };
    
    if (pdfUrl) {
      extractPdfUrl();
    }
  }, [pdfUrl, paper.source]);

  // Load existing annotations
  useEffect(() => {
    if (pdfUrl) {
      const loadedAnnotations = getAnnotationsByPdfUrl(pdfUrl);
      setAnnotations(loadedAnnotations);
    }
    
    // Listen for annotation changes
    const handleAnnotationsChanged = () => {
      if (pdfUrl) {
        const updated = getAnnotationsByPdfUrl(pdfUrl);
        setAnnotations(updated);
      }
    };
    
    window.addEventListener('annotationsChanged', handleAnnotationsChanged);
    return () => {
      window.removeEventListener('annotationsChanged', handleAnnotationsChanged);
    };
  }, [pdfUrl]);

  // Close annotation menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showAnnotationMenu) {
        const target = event.target as HTMLElement;
        if (!target.closest('.annotation-menu') && !target.closest('[data-annotation-target]')) {
          setShowAnnotationMenu(false);
          setSelectedText('');
          setSelectedAreas([]);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showAnnotationMenu]);

  // Cleanup DOAB override on unmount
  useEffect(() => {
    return () => {
      if (window.DOAB_PDF_OVERRIDE) {
        delete window.DOAB_PDF_OVERRIDE;
      }
    };
  }, []);

  const detectBestViewer = async () => {
    console.log('[PDFViewerSmart] detectBestViewer called with URL:', pdfUrl);
    setViewerMode('detecting');
    setErrorMessage('');

    try {
      let finalUrl = pdfUrl;
      
      // First, check if this URL needs PDF extraction (LibreTexts or OTL)
      const needsExtraction = (pdfUrl.includes('libretexts.org') || 
                             pdfUrl.includes('open.umn.edu/opentextbooks')) &&
                             !pdfUrl.includes('/@api/deki/pages/');
      
      console.log('[PDFViewerSmart] URL:', pdfUrl);
      console.log('[PDFViewerSmart] Needs extraction?', needsExtraction);
      console.log('[PDFViewerSmart] Includes libretexts.org/Bookshelves?', pdfUrl.includes('libretexts.org/Bookshelves'));
      console.log('[PDFViewerSmart] Includes /print?format=pdf?', pdfUrl.includes('/print?format=pdf'));
      
      if (needsExtraction) {
        console.log('[PDFViewerSmart] Attempting PDF extraction for:', pdfUrl);
        try {
          const extractResponse = await fetch('/extract-pdf-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: pdfUrl })
          });
          
          if (extractResponse.ok) {
            const extractData = await extractResponse.json();
            console.log('[PDFViewerSmart] Extract response data:', extractData);
            if (extractData.pdf_url && extractData.pdf_url !== pdfUrl) {
              finalUrl = extractData.pdf_url;
              console.log('[PDFViewerSmart] PDF extracted:', finalUrl);
            } else {
              console.log('[PDFViewerSmart] No PDF extracted, using original URL');
            }
          } else {
            console.log('[PDFViewerSmart] Extract response failed:', extractResponse.status, extractResponse.statusText);
          }
        } catch (extractError) {
          console.log('[PDFViewerSmart] PDF extraction failed, using original URL');
        }
      }
      
      // Skip proxy for local uploads
      const isLocalUpload = finalUrl.startsWith('/uploads');
      const checkUrl = isLocalUpload ? finalUrl : `/api/proxy-pdf?url=${encodeURIComponent(finalUrl)}`;
      
      // Make HEAD request to check content type
      const response = await fetch(checkUrl, { method: 'HEAD' });
      const contentType = response.headers.get('content-type') || 'unknown';
      
      console.log('[PDFViewerSmart]', finalUrl, '→', contentType, response.status);
      
      // Update the pdfUrl state if we extracted a different URL
      if (finalUrl !== pdfUrl) {
        // This will cause a re-render, but that's okay
        console.log('[PDFViewerSmart] Updating pdfUrl from', pdfUrl, 'to', finalUrl);
      }
      
      // Decide viewer based on actual content type
      if (contentType.includes('pdf')) {
        // It's a PDF - use PDF viewer with proxy (except for local uploads)
        setUseProxy(!isLocalUpload);
        setViewerMode('pdf-direct');
      } else if (contentType.includes('html') || contentType.includes('text')) {
        // It's HTML - use HTML viewer
        setViewerMode('html-viewer');
      } else {
        // Unknown content type - fall back to URL pattern detection
        const urlLower = finalUrl.toLowerCase();
        
        // Check if URL pattern suggests it's a PDF
        const isProbablyPdf = urlLower.includes('.pdf') || 
                             urlLower.includes('/pdf/') || 
                             urlLower.includes('arxiv.org/pdf/') ||
                             urlLower.includes('format=pdf') ||
                             urlLower.includes('/print?format=pdf') ||
                             urlLower.includes('pmc/articles/') ||
                             urlLower.includes('library.oapen.org') ||
                             urlLower.includes('doabooks.org') ||
                             urlLower.includes('oapen.org/download') ||
                             urlLower.includes('archive.org/details/') ||
                             urlLower.includes('archive.org/stream/');

        if (isProbablyPdf) {
          setUseProxy(true);
          setViewerMode('pdf-direct');
        } else {
          setViewerMode('html-viewer');
        }
      }
    } catch (error) {
      console.error('[PDFViewerSmart] Error detecting content type:', error);
      
      // Fall back to URL pattern detection
      const urlLower = pdfUrl.toLowerCase();
      
      // Check if domain needs special handling - these are known PDF sources
      const needsSpecialHandling = urlLower.includes('biomedcentral.com') ||
                                  urlLower.includes('plos.org') ||
                                  urlLower.includes('journals.plos.org') ||
                                  urlLower.includes('eric.ed.gov') ||
                                  urlLower.includes('files.eric.ed.gov') ||
                                  urlLower.includes('crossref.org') ||
                                  urlLower.includes('doi.org') ||
                                  urlLower.includes('library.oapen.org') ||
                                  urlLower.includes('doabooks.org') ||
                                  urlLower.includes('oapen.org/download') ||
                                  urlLower.includes('archive.org/details/') ||
                                  urlLower.includes('archive.org/stream/') ||
                                  urlLower.includes('.pdf');

      if (needsSpecialHandling) {
        // These sources often have PDFs even without .pdf extension
        setUseProxy(true);
        setViewerMode('pdf-direct');
      } else {
        // Default to HTML viewer
        setViewerMode('html-viewer');
      }
    }
  };

  const handlePdfLoadError = () => {
    // If direct PDF viewing fails without proxy, try with proxy
    if (viewerMode === 'pdf-direct' && !useProxy) {
      setUseProxy(true);
      // Force re-render with proxy
      setViewerMode('detecting');
      setTimeout(() => setViewerMode('pdf-direct'), 100);
    } else if (viewerMode === 'pdf-direct' && useProxy) {
      // If proxy also fails, try HTML viewer
      setViewerMode('html-viewer');
      setUseProxy(false);
    } else if (viewerMode === 'html-viewer') {
      // If HTML viewer also fails, show external link
      setViewerMode('external');
      setErrorMessage('Unable to preview this document. It may require authentication or special access.');
    }
  };

  const handlePdfLoadSuccess = async (e: DocumentLoadEvent) => {
    console.log('PDF loaded successfully');
    // Store the PDF document reference
    pdfDocRef.current = e.doc;
    
    // Set total pages
    if (e.doc && e.doc.numPages) {
      setTotalPages(e.doc.numPages);
    }
    
    // Extract text positions for TTS highlighting
    if (e.doc) {
      extractTextPositions(e.doc);
    }
    
    // Set up text selection handler after PDF loads
    if (highlightPluginInstance) {
      // Plugin is ready
      console.log('Highlight plugin ready');
    }
  };
  
  // Find highlight areas for current words being spoken
  const findWordHighlightAreas = (currentWords: string[], sentenceIndex: number) => {
    const areas: any[] = [];
    
    // Only process if we have words to highlight
    if (!currentWords || currentWords.length === 0) return areas;
    
    // Get the current word and clean it
    const currentWord = currentWords[0]?.toLowerCase().trim();
    if (!currentWord || currentWord.length < 2) return areas;
    
    // Remove punctuation from the word for better matching
    const cleanWord = currentWord.replace(/[.,!?;:'"]/g, '');
    
    console.log('[TTS] Looking for word:', cleanWord);
    
    // Track if we found the word on the current visible page
    let foundOnCurrentPage = false;
    
    // Search through pages, prioritizing current page
    pdfTextMap.forEach((textItems, pageIndex) => {
      // Skip if we already found on current page and this is a different page
      if (foundOnCurrentPage && pageIndex !== currentPageNumber - 1) return;
      
      textItems.forEach((item, itemIndex) => {
        // Skip empty items
        if (!item.text || item.text.trim().length === 0) return;
        
        // Check for word match
        const itemText = item.text.toLowerCase();
        const itemWords = itemText.split(/\s+/).map((w: string) => w.replace(/[.,!?;:'"]/g, ''));
        
        // Look for exact word match
        const wordIndex = itemWords.findIndex((itemWord: string) => 
          itemWord === cleanWord || 
          (cleanWord.length > 3 && itemWord.startsWith(cleanWord))
        );
        
        if (wordIndex !== -1) {
          // Found the word!
          console.log('[TTS] Found word in item:', item.text, 'at position', item.x, item.y);
          
          const pageWidth = item.pageWidth;
          const pageHeight = item.pageHeight;
          
          // Calculate the actual word position within the text item
          // If the text item contains multiple words, we need to estimate where our word is
          let wordStartX = item.x;
          let wordWidth = item.width;
          
          if (itemWords.length > 1 && wordIndex > 0) {
            // Estimate the position of the word within the text item
            const textBeforeWord = itemWords.slice(0, wordIndex).join(' ') + ' ';
            const wordRatio = textBeforeWord.length / item.text.length;
            wordStartX = item.x + (item.width * wordRatio);
            wordWidth = (cleanWord.length / item.text.length) * item.width;
          } else if (itemWords.length > 1) {
            // First word in multi-word item
            wordWidth = (cleanWord.length / item.text.length) * item.width;
          }
          
          // For react-pdf-viewer, the Y coordinate needs special handling
          // PDF.js gives us Y from bottom, but with text baseline
          // We need to convert to top-based coordinates
          const textBaseline = item.y; // This is the baseline of the text
          const textTop = textBaseline + (item.fontSize * 0.8); // Approximate top of text
          const topY = pageHeight - textTop;
          
          // Create highlight area with percentages
          const area = {
            pageIndex: pageIndex,
            left: (wordStartX / pageWidth) * 100,
            top: (topY / pageHeight) * 100,
            width: (wordWidth / pageWidth) * 100,
            height: ((item.fontSize * 1.2) / pageHeight) * 100 // Use font size for height
          };
          
          console.log('[TTS] Created highlight area:', area);
          
          // Only add if on current page or we haven't found anything yet
          if (pageIndex === currentPageNumber - 1) {
            foundOnCurrentPage = true;
            areas.push(area);
          } else if (!foundOnCurrentPage && areas.length === 0) {
            areas.push(area);
          }
        }
      });
    });
    
    // Return only the first match to avoid multiple highlights
    return areas.slice(0, 1);
  };
  
  // Extract text positions from all pages
  const extractTextPositions = async (pdfDoc: any) => {
    const textMap = new Map<number, any[]>();
    
    try {
      for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
        const page = await pdfDoc.getPage(pageNum);
        const textContent = await page.getTextContent();
        
        // Get page dimensions
        const viewport = page.getViewport({ scale: 1.0 });
        const pageWidth = viewport.width;
        const pageHeight = viewport.height;
        
        // Process text items with their positions
        const textItems = textContent.items.map((item: any) => {
          // Transform contains [scaleX, skewX, skewY, scaleY, x, y]
          const transform = item.transform;
          const x = transform[4];
          const y = transform[5];
          
          // Calculate width and height based on transform and text
          const fontSize = Math.abs(transform[0]); // Scale factor is roughly font size
          const width = item.width || (item.str.length * fontSize * 0.5); // Estimate if not provided
          const height = item.height || fontSize * 1.2; // Line height is typically 1.2x font size
          
          return {
            text: item.str,
            x: x,
            y: y,
            width: width,
            height: height,
            fontSize: fontSize,
            transform: transform,
            pageIndex: pageNum - 1,
            pageWidth: pageWidth,
            pageHeight: pageHeight
          };
        });
        
        // Group text items by line (items with similar Y coordinates)
        const lines: any[] = [];
        let currentLine: any[] = [];
        let lastY = -1;
        
        // Sort by Y first
        textItems.sort((a: any, b: any) => b.y - a.y);
        
        textItems.forEach((item: any) => {
          if (lastY === -1 || Math.abs(item.y - lastY) < 5) {
            // Same line
            currentLine.push(item);
            lastY = item.y;
          } else {
            // New line
            if (currentLine.length > 0) {
              // Sort items in line by X position
              currentLine.sort((a, b) => a.x - b.x);
              lines.push(currentLine);
            }
            currentLine = [item];
            lastY = item.y;
          }
        });
        
        // Don't forget the last line
        if (currentLine.length > 0) {
          currentLine.sort((a, b) => a.x - b.x);
          lines.push(currentLine);
        }
        
        // Flatten back but now properly ordered
        const orderedItems = lines.flat();
        
        textMap.set(pageNum - 1, orderedItems);
      }
      
      setPdfTextMap(textMap);
      console.log('Text positions extracted. Total pages:', textMap.size);
      
      // Log sample data from first page for debugging
      const firstPageItems = textMap.get(0);
      if (firstPageItems && firstPageItems.length > 0) {
        console.log('Sample text items from first page:');
        firstPageItems.slice(0, 5).forEach(item => {
          console.log(`Text: "${item.text}", X: ${item.x.toFixed(2)}, Y: ${item.y.toFixed(2)}, Width: ${item.width.toFixed(2)}, Height: ${item.height.toFixed(2)}`);
        });
      }
    } catch (error) {
      console.error('Error extracting text positions:', error);
    }
  };
  
  // Backend extraction fallback
  const tryBackendExtraction = async () => {
    try {
      console.log('[TTS] Attempting backend text extraction...');
      
      // Use the effective PDF URL (with overrides)
      const effectivePdfUrl = window.DOAB_PDF_OVERRIDE || pdfUrl;
      
      const response = await fetch('/api/extract-pdf-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pdf_url: effectivePdfUrl,
          max_pages: 50 // Limit to first 50 pages for performance
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.success && data.text) {
          console.log(`[TTS] Backend extraction successful. Extracted ${data.text.length} characters`);
          setExtractedText(data.text);
        } else {
          console.error('[TTS] Backend extraction returned no text:', data.error);
          setExtractedText('Unable to extract text from this PDF. The document might be scanned, protected, or in an unsupported format.');
        }
      } else {
        console.error('[TTS] Backend extraction failed with status:', response.status);
        setExtractedText('Unable to extract text from this PDF. Please try downloading the PDF and using a dedicated PDF reader.');
      }
    } catch (error) {
      console.error('[TTS] Backend extraction error:', error);
      setExtractedText('Unable to extract text from this PDF. Network error or server issue.');
    }
  };

  // Extract PDF text when TTS is opened
  useEffect(() => {
    const extractPdfText = async () => {
      if (showTextToSpeech && !extractedText && viewerMode === 'pdf-direct') {
        try {
          setExtractedText('Extracting text from PDF...');
          
          // Try to get PDF document reference
          let doc = pdfDocRef.current;
          
          // If not available yet, try to get it from the viewer
          if (!doc) {
            console.log('[TTS] PDF document not in ref, trying to get from viewer...');
            
            // Wait a bit for PDF to load if needed
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Try again
            doc = pdfDocRef.current;
            
            if (!doc) {
              console.error('[TTS] PDF document still not available');
              setExtractedText('PDF is still loading. Please try again in a moment.');
              return;
            }
          }
          
          const numPages = doc.numPages;
          let fullText = '';
          
          console.log(`[TTS] Starting text extraction from ${numPages} pages`);
          
          // Import all utilities for perfect extraction
          const { AdvancedTextExtractor } = await import('../utils/advancedTextExtractor');
          const { TTSFallbackHandler } = await import('../utils/ttsFallbackHandler');
          const { TTSDebugger } = await import('../utils/ttsDebugger');
          
          const extractor = new AdvancedTextExtractor();
          const ttsDebugger = new TTSDebugger();
          
          // Process each page with advanced extraction
          for (let i = 1; i <= numPages; i++) {
            ttsDebugger.log(`Processing page ${i}/${numPages}`);
            
            try {
              const page = await doc.getPage(i);
              const textContent = await page.getTextContent();
              const viewport = page.getViewport({ scale: 1.0 });
              
              // Debug analysis
              const debugInfo = ttsDebugger.analyzeTextItems(textContent.items, i);
              if (debugInfo.issues.length > 0) {
                console.warn(`Page ${i} issues:`, debugInfo.issues);
              }
              
              // Use advanced extractor for perfect text ordering
              const pageText = extractor.extractText(textContent.items, viewport);
              
              if (pageText.trim()) {
                fullText += `Page ${i}:\n${pageText}\n\n`;
              }
            } catch (pageError) {
              console.error(`[TTS] Error extracting text from page ${i}:`, pageError);
              // Continue with other pages
            }
          }
          
          // Apply comprehensive post-processing and fallback handling
          fullText = TTSFallbackHandler.prepareTextForTTS(fullText);
          
          // Validate the extracted text
          const validation = TTSFallbackHandler.validateExtractedText(fullText);
          if (!validation.isValid) {
            console.warn('TTS extraction warnings:', validation.warnings);
            console.info('Suggestions:', validation.suggestions);
          }
          
          // Generate debug report in development
          if (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development') {
            console.log('TTS Debug Report:', ttsDebugger.generateReport());
          }
          
          if (fullText && fullText.trim().length > 10) {
            setExtractedText(fullText);
            console.log(`[TTS] Text extraction complete. Extracted ${fullText.length} characters`);
          } else {
            // If no text extracted, try backend extraction as fallback
            console.log('[TTS] Frontend extraction yielded no text, trying backend extraction...');
            await tryBackendExtraction();
          }
        } catch (error) {
          console.error('[TTS] Error extracting PDF text:', error);
          
          // Try backend extraction as fallback
          console.log('[TTS] Frontend extraction failed, trying backend extraction...');
          await tryBackendExtraction();
        }
      }
    };
    
    extractPdfText();
  }, [showTextToSpeech, extractedText, viewerMode]);

  // Generate URLs - use DOAB override if available
  const effectivePdfUrl = window.DOAB_PDF_OVERRIDE || pdfUrl;
  const isLocalUpload = effectivePdfUrl.startsWith('/uploads');
  const proxyUrl = (useProxy && !isLocalUpload) ? `/api/proxy-pdf?url=${encodeURIComponent(effectivePdfUrl)}` : effectivePdfUrl;
  const displayUrl = viewerMode === 'pdf-direct' ? proxyUrl : effectivePdfUrl;

  console.log('[PDFViewerSmart] Rendering with:', { paper, pdfUrl, viewerMode });
  
  // Safety check
  if (!paper || !pdfUrl) {
    console.error('[PDFViewerSmart] Missing required props:', { paper, pdfUrl });
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg">
          <p className="text-red-600">Error: Missing paper or PDF URL</p>
          <button onClick={onClose} className="mt-4 px-4 py-2 bg-gray-200 rounded">Close</button>
        </div>
      </div>
    );
  }
  
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
          {/* View mode indicator */}
          <span className="text-sm text-gray-500">
            {viewerMode === 'detecting' && 'Detecting viewer...'}
            {viewerMode === 'pdf-direct' && (useProxy ? 'PDF Viewer (Proxied)' : 'PDF Viewer')}
            {viewerMode === 'html-viewer' && 'HTML Viewer'}
          </span>

          {/* Panel Toggle Buttons */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActivePanel(activePanel === 'annotations' ? null : 'annotations')}
              className={`flex items-center space-x-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                activePanel === 'annotations' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
              </svg>
              <span>{annotations.length}</span>
            </button>
            
            <button
              onClick={() => setActivePanel(activePanel === 'flashcards' ? null : 'flashcards')}
              className={`flex items-center space-x-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                activePanel === 'flashcards' ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span>Flashcards</span>
            </button>
            
            <button
              onClick={() => setShowScreenshotTool(!showScreenshotTool)}
              className={`flex items-center space-x-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                showScreenshotTool ? 'bg-purple-100 text-purple-700' : 'text-gray-700 hover:text-gray-900'
              }`}
              title="Screenshot Tool - Capture figures, equations, and diagrams"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>📷</span>
            </button>
            
            <button
              onClick={() => {
                setShowTextToSpeech(!showTextToSpeech);
                // For HTML viewer, extract text from the DOM
                if (!showTextToSpeech && !extractedText && viewerMode === 'html-viewer') {
                  // Extract text from HTML viewer with proper structure
                  const htmlContent = document.querySelector('.html-viewer-content');
                  if (htmlContent) {
                    // Create a tree walker to traverse text nodes in document order
                    const walker = document.createTreeWalker(
                      htmlContent,
                      NodeFilter.SHOW_TEXT,
                      {
                        acceptNode: (node) => {
                          const parent = node.parentElement;
                          // Skip script, style, and other non-content elements
                          if (parent && ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(parent.tagName)) {
                            return NodeFilter.FILTER_REJECT;
                          }
                          // Skip empty text nodes
                          const text = node.textContent?.trim();
                          return text ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                        }
                      }
                    );
                    
                    const textParts: string[] = [];
                    let currentNode;
                    let lastParent: Element | null = null;
                    
                    while (currentNode = walker.nextNode()) {
                      const text = currentNode.textContent?.trim();
                      if (text) {
                        const parent = currentNode.parentElement;
                        
                        // Add paragraph breaks for block-level elements
                        if (parent && lastParent && parent !== lastParent) {
                          const blockTags = ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI', 'BLOCKQUOTE', 'SECTION', 'ARTICLE'];
                          if (blockTags.includes(parent.tagName) || blockTags.includes(lastParent.tagName)) {
                            textParts.push('\n\n');
                          }
                        }
                        
                        textParts.push(text);
                        lastParent = parent;
                      }
                    }
                    
                    const extractedText = textParts.join(' ').replace(/\s+/g, ' ').trim();
                    setExtractedText(extractedText || 'No text content found.');
                  }
                }
              }}
              className={`flex items-center space-x-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                showTextToSpeech ? 'bg-white text-green-700 shadow-sm' : 'text-gray-700 hover:text-gray-900'
              }`}
              title="Text-to-Speech (Read aloud)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              <span>Read Aloud</span>
            </button>
          </div>
          
          {/* Textbook Processing Button */}
          {viewerMode === 'pdf-direct' && (
            <button
              onClick={() => setShowTextbookProcessor(true)}
              className="flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200"
              title="Process as Textbook"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Process Textbook</span>
            </button>
          )}
          
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Open Original
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-gray-100 relative flex" ref={containerRef}>
        {/* PDF Viewer Container */}
        <div className="flex-1 relative">
          {/* Loading state */}
          {viewerMode === 'detecting' && (
            <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Detecting best viewer...</p>
            </div>
          </div>
        )}

        {/* PDF Direct Viewer */}
        {viewerMode === 'pdf-direct' && (
          <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
            <div className="pdf-viewer-wrapper" ref={pdfViewerRef} style={{ height: 'calc(100vh - 120px)' }}>
              <Viewer 
                fileUrl={displayUrl} 
                plugins={[highlightPluginInstance, defaultLayoutPluginInstance]}
                onDocumentLoad={handlePdfLoadSuccess}
                renderError={(error: any) => {
                  // Schedule the state update for next tick to avoid the warning
                  setTimeout(() => handlePdfLoadError(), 0);
                  return (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-600">Switching to alternative viewer...</p>
                    </div>
                  );
                }}
              />
              
              {/* Screenshot Tool Overlay - Only render when active */}
              {showScreenshotTool && (
                <PDFScreenshotTool
                  paper={paper}
                  pdfUrl={pdfUrl}
                  isActive={showScreenshotTool}
                  onClose={() => setShowScreenshotTool(false)}
                  pdfContainer={pdfViewerRef.current}
                />
              )}
            </div>
          </Worker>
        )}

        {/* HTML Viewer for non-PDF content */}
        {viewerMode === 'html-viewer' && (
          <HTMLViewer 
            url={pdfUrl} 
            onError={handlePdfLoadError}
          />
        )}

        {/* External Link Fallback */}
        {viewerMode === 'external' && (
          <div className="flex items-center justify-center h-full bg-white">
            <div className="text-center p-8 max-w-2xl">
              <svg className="w-16 h-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-lg font-semibold mb-2">Unable to display document</h3>
              <p className="text-gray-600 mb-4">{errorMessage}</p>
              <div className="space-y-4">
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Open in New Tab
                </a>
                <p className="text-sm text-gray-500">
                  You may need to log in to the publisher's website or have institutional access
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {viewerMode === 'error' && (
          <div className="flex items-center justify-center h-full bg-white">
            <div className="text-center p-8">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-semibold mb-2">Error loading document</h3>
              <p className="text-gray-600">{errorMessage}</p>
            </div>
          </div>
        )}
        </div>

        {/* Side Panel */}
        {activePanel && (
          <div className="w-96 bg-white border-l border-gray-200 overflow-hidden flex flex-col">
            {activePanel === 'annotations' ? (
              <AnnotationsPanel
                pdfUrl={pdfUrl}
                isOpen={true}
                onClose={() => setActivePanel(null)}
                onAnnotationClick={(annotation) => {
                  console.log('Annotation clicked:', annotation);
                }}
              />
            ) : (
              <FlashcardPanel 
                paperId={paper.doi || paper.full_text_url || paper.title}
                paper={paper}
                pdfUrl={pdfUrl}
                extractedText={extractedText}
              />
            )}
          </div>
        )}
      </div>

      {/* Remove old Annotations Panel */}
      {false && <AnnotationsPanel
        pdfUrl={pdfUrl}
        isOpen={showAnnotationsPanel}
        onClose={() => setShowAnnotationsPanel(false)}
        onAnnotationClick={(annotation) => {
          // TODO: Scroll to annotation in PDF
          console.log('Annotation clicked:', annotation);
        }}
      />}

      {/* Annotation Menu */}
      {showAnnotationMenu && (
        <AnnotationMenu
          selectedText={selectedText}
          position={menuPosition}
          onHighlight={handleCreateHighlight}
          onNote={handleCreateNote}
          onFlashcard={handleCreateFlashcard}
          onClose={() => {
            setShowAnnotationMenu(false);
            setSelectedText('');
            setSelectedAreas([]);
          }}
        />
      )}

      {/* Text-to-Speech Component */}
      <TextToSpeech
        text={extractedText || 'Please wait while we extract text from the PDF...'}
        isOpen={showTextToSpeech}
        onClose={() => setShowTextToSpeech(false)}
        paper={paper}
        pdfContainer={pdfViewerRef.current}
        currentPage={currentPageNumber}
        totalPages={totalPages || 1}
        onPageChange={(page) => {
          // Navigate to specific page when TTS requests it
          if (pdfDocRef.current && page >= 1 && page <= (totalPages || 1)) {
            setCurrentPageNumber(page);
            // For react-pdf-viewer, we need to use the plugin API
            // This is a placeholder - actual implementation depends on viewer instance
            console.log('TTS requested page:', page);
          }
        }}
        onWordsHighlight={(currentWords, sentenceIndex) => {
          // Find word positions in the PDF and create highlight areas
          if (currentWords && pdfTextMap.size > 0) {
            const areas = findWordHighlightAreas(currentWords, sentenceIndex);
            setTtsHighlightAreas(areas);
          } else {
            setTtsHighlightAreas([]);
          }
        }}
        onReadingComplete={() => {
          // Clear reading state when done
          setCurrentReadingSentence(-1);
          setTtsHighlightAreas([]);
        }}
      />

      {/* Textbook Processor Component */}
      <TextbookProcessor
        paper={paper}
        isOpen={showTextbookProcessor}
        onClose={() => setShowTextbookProcessor(false)}
        onProcessComplete={() => {
          setShowTextbookProcessor(false);
          // Could reload collection or update UI here
        }}
      />

    </div>
  );
};

export default PDFViewerSmart;
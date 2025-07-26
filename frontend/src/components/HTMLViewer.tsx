import React, { useState, useEffect } from 'react';
import axios from 'axios';
// @ts-ignore
import DOMPurify from 'dompurify';

interface HTMLViewerProps {
  url: string;
  onError: () => void;
}

const HTMLViewer: React.FC<HTMLViewerProps> = ({ url, onError }) => {
  const [content, setContent] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContent();
  }, [url]);

  const fetchContent = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('Fetching HTML from:', url);
      
      const response = await axios.get(`/api/proxy-html`, {
        params: { url }
      });
      
      console.log('HTML proxy response:', response.data);
      
      if (response.data.success) {
        // Process the HTML to fix image URLs before sanitization
        const parser = new DOMParser();
        const doc = parser.parseFromString(response.data.content, 'text/html');
        
        // Restore figures from publisher placeholders (Elsevier, Springer, ScienceDirect, etc.)
        // Look for various anchor patterns used by publishers
        const figureAnchors = doc.querySelectorAll(
          'a[data-asset-type="image"], ' +
          'a[data-type="fig"], ' +
          'a.btn-fig, ' +
          'a.fig-download, ' +
          'a[href*="#fig"], ' +
          'a[href*="/fig/"], ' +
          'figure a[href*="Open in a new tab"]'
        );
        
        figureAnchors.forEach((anchor: Element) => {
          // Try to get asset ID from various attributes or extract from href
          let assetId = anchor.getAttribute('data-asset-id') || 
                       anchor.getAttribute('data-id') ||
                       anchor.getAttribute('data-fig-id');
          
          // If no explicit ID, try to extract from href (e.g., "#fig0002" → "fig0002")
          const href = anchor.getAttribute('href');
          if (!assetId && href) {
            const match = href.match(/#?(fig|gr|figure|image)[\d\w]+/i);
            if (match) {
              assetId = match[0].replace('#', '');
            }
          }
          
          // For some publishers, the figure number might be in the text
          if (!assetId && anchor.textContent) {
            const textMatch = anchor.textContent.match(/(?:Fig(?:ure)?|Image|Graphic)\s*(\d+)/i);
            if (textMatch) {
              assetId = `fig${textMatch[1]}`;
            }
          }
          
          // Look for meta tags that contain the actual image URL
          let imageUrl: string | null = null;
          
          if (assetId) {
            // Elsevier pattern: <meta name="citation_graphical_abstract" content="gr2:https://...">
            // Also check various meta tag patterns
            const metaSelectors = [
              `meta[content*="${assetId}:"]`,
              `meta[name*="figure"][content*="${assetId}"]`,
              `meta[name*="image"][content*="${assetId}"]`,
              `meta[property*="image"][content*="${assetId}"]`
            ];
            
            for (const selector of metaSelectors) {
              const meta = doc.querySelector(selector) as HTMLMetaElement;
              if (meta) {
                const content = meta.getAttribute('content');
                if (content) {
                  // Handle different formats: "id:url" or just "url"
                  if (content.includes(':') && content.includes(assetId)) {
                    imageUrl = content.substring(content.indexOf(':') + 1);
                  } else if (content.includes('http')) {
                    imageUrl = content;
                  }
                  break;
                }
              }
            }
          }
          
          // Springer/Nature pattern: might have data-src or data-url attributes
          if (!imageUrl) {
            imageUrl = anchor.getAttribute('data-src') || 
                      anchor.getAttribute('data-url') || 
                      anchor.getAttribute('href');
          }
          
          // If we found an image URL, create an img element
          if (imageUrl && (imageUrl.includes('http') || imageUrl.startsWith('/'))) {
            const img = doc.createElement('img');
            img.src = imageUrl;
            img.alt = anchor.textContent?.trim() || (assetId ? `Figure ${assetId}` : 'Figure');
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            if (assetId) {
              img.setAttribute('data-asset-id', assetId);
            }
            
            // Wrap in figure if not already in one
            const figure = anchor.closest('figure');
            if (figure) {
              // Replace just the anchor inside the figure
              anchor.parentNode?.replaceChild(img, anchor);
            } else {
              // Create a figure element
              const newFigure = doc.createElement('figure');
              newFigure.style.margin = '2em 0';
              newFigure.style.textAlign = 'center';
              newFigure.appendChild(img);
              
              // Add caption if there's text
              const captionText = anchor.textContent?.replace(/Open in a new tab/i, '').trim();
              if (captionText && !captionText.match(/^(Fig(?:ure)?\.?\s*\d+\.?)$/i)) {
                const figcaption = doc.createElement('figcaption');
                figcaption.textContent = captionText;
                figcaption.style.marginTop = '0.5em';
                figcaption.style.fontSize = '0.9em';
                figcaption.style.color = '#666';
                newFigure.appendChild(figcaption);
              }
              
              anchor.parentNode?.replaceChild(newFigure, anchor);
            }
          }
        });
        
        // Also check for lazy-loaded images with data-src
        doc.querySelectorAll('img[data-src], img[data-original]').forEach(img => {
          const dataSrc = img.getAttribute('data-src') || img.getAttribute('data-original');
          if (dataSrc) {
            img.setAttribute('src', dataSrc);
          }
        });
        
        // Fix all image URLs to be absolute
        doc.querySelectorAll('img').forEach(img => {
          const src = img.getAttribute('src');
          if (src && !src.startsWith('data:')) {
            // If it's already a proxy URL, leave it
            if (src.startsWith('/api/proxy-image')) {
              return;
            }
            
            // If it's a relative URL or absolute URL, ensure it's absolute
            try {
              let absoluteSrc: string;
              
              if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('//')) {
                // Already absolute
                absoluteSrc = src.startsWith('//') ? 'https:' + src : src;
              } else {
                // Relative URL - make it absolute using the document URL
                absoluteSrc = new URL(src, url).href;
              }
              
              // Use proxy for all external images
              img.setAttribute('src', `/api/proxy-image?url=${encodeURIComponent(absoluteSrc)}`);
              img.setAttribute('loading', 'lazy');
              
              if (!img.getAttribute('alt')) {
                img.setAttribute('alt', 'Figure');
              }
            } catch (e) {
              console.error('Error processing image URL:', src, e);
            }
          }
        });
        
        // Also fix any srcset attributes
        doc.querySelectorAll('img[srcset]').forEach(img => {
          try {
            const srcset = img.getAttribute('srcset');
            if (srcset) {
              const newSrcset = srcset.split(',').map(src => {
                const [srcUrl, descriptor] = src.trim().split(/\s+/);
                const absoluteUrl = new URL(srcUrl, url).href;
                return `/api/proxy-image?url=${encodeURIComponent(absoluteUrl)} ${descriptor || ''}`;
              }).join(', ');
              img.setAttribute('srcset', newSrcset);
            }
          } catch (e) {
            console.error('Error processing srcset:', e);
          }
        });
        
        // Get the processed HTML
        const processedHtml = doc.documentElement.outerHTML;
        
        // Additional client-side sanitization with DOMPurify
        const sanitizedContent = DOMPurify.sanitize(processedHtml, {
          ADD_TAGS: ['style', 'img', 'figure', 'figcaption'],
          ADD_ATTR: ['target', 'rel', 'style', 'src', 'srcset', 'loading', 'alt', 'width', 'height', 'class', 'id'],
          ALLOW_DATA_ATTR: false,
          KEEP_CONTENT: true
        });
        
        setContent(sanitizedContent);
        setTitle(response.data.title);
      } else {
        throw new Error('Failed to fetch content');
      }
    } catch (err: any) {
      console.error('Error fetching HTML:', err);
      console.error('Error details:', err.response?.data || err.message);
      setError(err.response?.data?.detail || 'Failed to load content');
      onError();
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading content...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-8">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold mb-2">Error loading content</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="bg-white max-w-5xl mx-auto my-8 shadow-lg rounded-lg">
        <div className="p-8">
          {title && title !== "Document" && (
            <div className="mb-8 pb-6 border-b border-gray-200">
              <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
            </div>
          )}
          {/* Render enhanced HTML content */}
          <div 
            className="article-content html-viewer-content"
            dangerouslySetInnerHTML={{ __html: content }}
            style={{
              fontSize: '16px',
              lineHeight: '1.6',
              color: '#333',
              maxWidth: '100%',
              wordWrap: 'break-word',
            }}
          />
        </div>
      </div>
      
      {/* Additional styles for the rendered content */}
      <style dangerouslySetInnerHTML={{ __html: `
        .article-content h1,
        .article-content h2,
        .article-content h3,
        .article-content h4,
        .article-content h5,
        .article-content h6 {
          font-weight: 600;
          line-height: 1.25;
          margin-top: 2rem;
          margin-bottom: 1rem;
          color: #1a202c;
        }
        
        .article-content h1 { font-size: 2rem; }
        .article-content h2 { font-size: 1.75rem; }
        .article-content h3 { font-size: 1.5rem; }
        .article-content h4 { font-size: 1.25rem; }
        
        .article-content p {
          margin-bottom: 1.25rem;
          line-height: 1.75;
        }
        
        .article-content a {
          color: #2563eb;
          text-decoration: none;
          transition: color 0.2s;
        }
        
        .article-content a:hover {
          color: #1d4ed8;
          text-decoration: underline;
        }
        
        .article-content img {
          max-width: 100%;
          height: auto;
          margin: 2rem auto;
          display: block;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .article-content figure {
          margin: 2rem 0;
          text-align: center;
        }
        
        .article-content figcaption {
          margin-top: 0.75rem;
          font-size: 0.875rem;
          color: #6b7280;
          font-style: italic;
        }
        
        .article-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 2rem 0;
          font-size: 0.875rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .article-content th,
        .article-content td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .article-content th {
          background-color: #f9fafb;
          font-weight: 600;
          color: #374151;
          border-bottom: 2px solid #e5e7eb;
        }
        
        .article-content tr:hover {
          background-color: #f9fafb;
        }
        
        .article-content ul,
        .article-content ol {
          margin: 1.25rem 0;
          padding-left: 2rem;
        }
        
        .article-content li {
          margin-bottom: 0.5rem;
        }
        
        .article-content blockquote {
          border-left: 4px solid #e5e7eb;
          padding-left: 1.5rem;
          margin: 2rem 0;
          font-style: italic;
          color: #4b5563;
        }
        
        .article-content code {
          background-color: #f3f4f6;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-size: 0.875rem;
          font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        }
        
        .article-content pre {
          background-color: #1f2937;
          color: #f9fafb;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1.5rem 0;
        }
        
        .article-content pre code {
          background-color: transparent;
          padding: 0;
          color: inherit;
        }
        
        .article-content hr {
          border: 0;
          height: 1px;
          background-color: #e5e7eb;
          margin: 3rem 0;
        }
        
        /* Academic paper specific styles */
        .article-content .fm-author,
        .article-content .contrib-group {
          color: #4b5563;
          margin: 1rem 0;
        }
        
        .article-content .xref {
          color: #2563eb;
          font-size: 0.875rem;
          vertical-align: super;
        }
        
        .article-content .sec {
          margin: 2.5rem 0;
        }
        
        .article-content .title {
          font-weight: 600;
          margin-bottom: 1rem;
          color: #1f2937;
        }
        
        /* Remove any unwanted elements */
        .article-content .ncbi-alerts,
        .article-content .search-input,
        .article-content .pmc-sidebar,
        .article-content .usa-banner {
          display: none !important;
        }
      ` }} />
    </div>
  );
};

export default HTMLViewer;
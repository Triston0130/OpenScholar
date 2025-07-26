import React, { useState } from 'react';
import { Paper } from '../types';
import { fetchExternalPaper } from '../utils/api';

interface AddExternalPaperModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddPaper: (paper: Paper, pdfFile?: File) => void;
}

const AddExternalPaperModal: React.FC<AddExternalPaperModalProps> = ({
  isOpen,
  onClose,
  onAddPaper
}) => {
  const [activeTab, setActiveTab] = useState<'doi' | 'isbn' | 'bibtex' | 'pdf'>('doi');
  const [doiInput, setDoiInput] = useState('');
  const [isbnInput, setIsbnInput] = useState('');
  const [bibtexInput, setBibtexInput] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewPaper, setPreviewPaper] = useState<Paper | null>(null);

  const fetchPaperFromDOI = async (doi: string): Promise<Paper> => {
    // Clean up DOI input
    const cleanDOI = doi.replace(/^https?:\/\/(dx\.)?doi\.org\//, '').trim();
    
    // Call backend API through utility function
    return await fetchExternalPaper(cleanDOI);
  };

  const fetchBookFromISBN = async (isbn: string): Promise<Paper> => {
    // Clean up ISBN (remove dashes, spaces)
    const cleanISBN = isbn.replace(/[-\s]/g, '').trim();
    
    // Validate ISBN (10 or 13 digits)
    if (!/^\d{10}$|^\d{13}$/.test(cleanISBN)) {
      throw new Error('Invalid ISBN format. Please enter a 10 or 13 digit ISBN.');
    }
    
    // Call backend API for ISBN lookup
    const response = await fetch(`/api/external/isbn/${cleanISBN}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch book information');
    }
    
    const bookData = await response.json();
    
    // Convert book data to Paper format
    return {
      title: bookData.title || 'Unknown Title',
      authors: bookData.authors || ['Unknown Author'],
      year: bookData.publishedDate?.substring(0, 4) || new Date().getFullYear().toString(),
      journal: bookData.publisher || 'Book',
      abstract: bookData.description || 'No description available',
      doi: '',
      full_text_url: bookData.previewLink || '',
      source: 'External (ISBN)',
      isbn: cleanISBN,
      pageCount: bookData.pageCount,
      categories: bookData.categories,
      thumbnail: bookData.thumbnail
    } as Paper;
  };

  const parseBibTeX = (bibtexText: string): Paper[] => {
    const papers: Paper[] = [];
    
    // Simple BibTeX parser - this is a basic implementation
    const entries = bibtexText.match(/@\w+\{[^@]+\}/g);
    
    if (!entries) {
      throw new Error('No valid BibTeX entries found');
    }
    
    entries.forEach(entry => {
      const lines = entry.split('\n').map(line => line.trim());
      const paper: Partial<Paper> = {};
      
      // Extract entry type and key
      const firstLine = lines[0];
      const entryMatch = firstLine.match(/@(\w+)\{([^,]+),?/);
      if (!entryMatch) return;
      
      // Parse fields
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        const fieldMatch = line.match(/(\w+)\s*=\s*[{"']([^}"']+)[}"'],?/);
        if (fieldMatch) {
          const [, field, value] = fieldMatch;
          
          switch (field.toLowerCase()) {
            case 'title':
              paper.title = value;
              break;
            case 'author':
              paper.authors = value.split(' and ').map(author => author.trim());
              break;
            case 'abstract':
              paper.abstract = value;
              break;
            case 'year':
              paper.year = value;
              break;
            case 'journal':
            case 'booktitle':
              paper.journal = value;
              break;
            case 'doi':
              paper.doi = value;
              break;
            case 'url':
              paper.full_text_url = value;
              break;
          }
        }
      }
      
      // Set defaults and add to papers array
      const completePaper: Paper = {
        title: paper.title || 'Unknown Title',
        authors: paper.authors || ['Unknown Author'],
        abstract: paper.abstract || 'No abstract available',
        year: paper.year || 'Unknown',
        journal: paper.journal || 'Unknown Journal',
        doi: paper.doi || undefined,
        full_text_url: paper.full_text_url || '',
        source: 'External (BibTeX)',
        citation_count: undefined,
        influential_citation_count: undefined
      };
      
      papers.push(completePaper);
    });
    
    return papers;
  };

  const handleDOISubmit = async () => {
    if (!doiInput.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const paper = await fetchPaperFromDOI(doiInput);
      setPreviewPaper(paper);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch paper');
    } finally {
      setIsLoading(false);
    }
  };

  const handleISBNSubmit = async () => {
    if (!isbnInput.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const book = await fetchBookFromISBN(isbnInput);
      setPreviewPaper(book);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch book information');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBibTeXSubmit = async () => {
    if (!bibtexInput.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const papers = parseBibTeX(bibtexInput);
      if (papers.length === 1) {
        setPreviewPaper(papers[0]);
      } else {
        // Handle multiple papers - for now, just take the first one
        // TODO: Allow user to select which paper to add
        setPreviewPaper(papers[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse BibTeX');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPaper = () => {
    if (previewPaper) {
      onAddPaper(previewPaper, pdfFile || undefined);
      handleClose();
    }
  };

  const handlePdfOnlyUpload = async () => {
    if (!pdfFile) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Try to extract DOI from filename
      const filename = pdfFile.name;
      const doiPattern = /10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+/;
      const doiMatch = filename.match(doiPattern);
      
      let paper: Paper;
      
      if (doiMatch) {
        // Found a DOI in the filename, try to fetch metadata
        const extractedDoi = doiMatch[0];
        try {
          const fetchedPaper = await fetchPaperFromDOI(extractedDoi);
          paper = {
            ...fetchedPaper,
            source: 'External'
          };
          // Show preview with fetched metadata
          setPreviewPaper(paper);
        } catch (error) {
          console.error('Failed to fetch metadata for DOI:', error);
          // Fall back to creating paper with filename
          paper = {
            title: filename.replace(/\.pdf$/i, '').replace(doiPattern, '').trim() || 'Untitled',
            authors: ['Unknown'],
            year: new Date().getFullYear().toString(),
            journal: 'External (PDF Upload)',
            abstract: 'PDF uploaded directly. DOI found but metadata fetch failed.',
            full_text_url: '', // Will be set after upload
            doi: extractedDoi,
            source: 'External'
          };
          setPreviewPaper(paper);
        }
      } else {
        // No DOI found, create paper with filename
        paper = {
          title: filename.replace(/\.pdf$/i, '').trim() || 'Untitled',
          authors: ['Unknown'],
          year: new Date().getFullYear().toString(),
          journal: 'External (PDF Upload)',
          abstract: 'PDF uploaded directly. Metadata extraction pending.',
          full_text_url: '', // Will be set after upload
          doi: '',
          source: 'External'
        };
        setPreviewPaper(paper);
      }
      
      // Auto-add after preview if no DOI, otherwise let user confirm
      if (!doiMatch) {
        setTimeout(() => {
          onAddPaper(paper, pdfFile);
          handleClose();
        }, 1000);
      }
    } catch (err) {
      setError('Failed to process PDF');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setDoiInput('');
    setIsbnInput('');
    setBibtexInput('');
    setPdfFile(null);
    setPreviewPaper(null);
    setError(null);
    setIsLoading(false);
    onClose();
  };

  const handlePdfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Add External Paper
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('doi')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'doi'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Add by DOI
          </button>
          <button
            onClick={() => setActiveTab('isbn')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'isbn'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Add by ISBN
          </button>
          <button
            onClick={() => setActiveTab('bibtex')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'bibtex'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Upload BibTeX
          </button>
          <button
            onClick={() => setActiveTab('pdf')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'pdf'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Upload PDF
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'doi' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="doi" className="block text-sm font-medium text-gray-700 mb-2">
                  DOI or DOI URL
                </label>
                <input
                  id="doi"
                  type="text"
                  value={doiInput}
                  onChange={(e) => setDoiInput(e.target.value)}
                  placeholder="10.1000/xyz123 or https://doi.org/10.1000/xyz123"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button
                onClick={handleDOISubmit}
                disabled={isLoading || !doiInput.trim()}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Fetching...' : 'Fetch Paper'}
              </button>
              
              {/* Optional PDF Upload for DOI */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Have the PDF? (Optional)
                </label>
                <div className="mt-1 flex items-center">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfChange}
                    className="hidden"
                    id="doi-pdf-upload"
                  />
                  <label
                    htmlFor="doi-pdf-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    {pdfFile ? pdfFile.name : 'Choose PDF file'}
                  </label>
                </div>
                {pdfFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    PDF will be stored with the paper metadata
                  </p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'isbn' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="isbn" className="block text-sm font-medium text-gray-700 mb-2">
                  ISBN Number
                </label>
                <input
                  id="isbn"
                  type="text"
                  value={isbnInput}
                  onChange={(e) => setIsbnInput(e.target.value)}
                  placeholder="978-3-16-148410-0 or 0-7167-0344-0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Enter ISBN-10 or ISBN-13 with or without dashes
                </p>
              </div>
              <button
                onClick={handleISBNSubmit}
                disabled={isLoading || !isbnInput.trim()}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Looking up book...' : 'Find Book'}
              </button>
              
              {/* Optional PDF Upload for ISBN */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Have the PDF? (Optional)
                </label>
                <div className="mt-1 flex items-center">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfChange}
                    className="hidden"
                    id="isbn-pdf-upload"
                  />
                  <label
                    htmlFor="isbn-pdf-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    {pdfFile ? pdfFile.name : 'Choose PDF file'}
                  </label>
                </div>
                {pdfFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    PDF will be stored with the book metadata
                  </p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'bibtex' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="bibtex" className="block text-sm font-medium text-gray-700 mb-2">
                  BibTeX Entry
                </label>
                <textarea
                  id="bibtex"
                  value={bibtexInput}
                  onChange={(e) => setBibtexInput(e.target.value)}
                  placeholder="@article{key,
  title={Paper Title},
  author={Author Name and Another Author},
  journal={Journal Name},
  year={2024},
  doi={10.1000/xyz123}
}"
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 resize-none font-mono"
                />
              </div>
              <button
                onClick={handleBibTeXSubmit}
                disabled={isLoading || !bibtexInput.trim()}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Parsing...' : 'Parse BibTeX'}
              </button>
              
              {/* Optional PDF Upload for BibTeX */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Have the PDF? (Optional)
                </label>
                <div className="mt-1 flex items-center">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfChange}
                    className="hidden"
                    id="bibtex-pdf-upload"
                  />
                  <label
                    htmlFor="bibtex-pdf-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    {pdfFile ? pdfFile.name : 'Choose PDF file'}
                  </label>
                </div>
                {pdfFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    PDF will be stored with the paper metadata
                  </p>
                )}
              </div>
            </div>
          )}

          {/* PDF Upload Tab */}
          {activeTab === 'pdf' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload PDF File
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="pdf-file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>Upload a PDF</span>
                        <input
                          id="pdf-file-upload"
                          name="pdf-file-upload"
                          type="file"
                          accept="application/pdf"
                          className="sr-only"
                          onChange={handlePdfChange}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PDF up to 50MB</p>
                  </div>
                </div>
              </div>
              
              {pdfFile && (
                <div className="mt-4 p-4 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-900">Selected file:</p>
                  <p className="text-sm text-gray-600 mt-1">{pdfFile.name}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    ({(pdfFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                </div>
              )}
              
              <div className="p-4 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> We'll try to extract metadata from the PDF (title, authors, etc.) 
                  or you can manually enter the information after upload.
                </p>
              </div>
              
              <button
                onClick={handlePdfOnlyUpload}
                disabled={isLoading || !pdfFile}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Processing...' : 'Upload PDF'}
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Preview */}
          {previewPaper && (
            <div className="mt-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
              <h4 className="font-medium text-gray-900 mb-2">Preview:</h4>
              <div className="space-y-2 text-sm">
                <p><strong>Title:</strong> {previewPaper.title}</p>
                <p><strong>Authors:</strong> {previewPaper.authors.join(', ')}</p>
                <p><strong>Year:</strong> {previewPaper.year}</p>
                <p><strong>Journal:</strong> {previewPaper.journal}</p>
                {previewPaper.doi && <p><strong>DOI:</strong> {previewPaper.doi}</p>}
                {previewPaper.full_text_url && (
                  <p><strong>Full Text:</strong> <a href={previewPaper.full_text_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Available</a></p>
                )}
                <p><strong>Abstract:</strong> {previewPaper.abstract.substring(0, 200)}...</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {previewPaper && (
          <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAddPaper}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Add to Collection
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddExternalPaperModal;
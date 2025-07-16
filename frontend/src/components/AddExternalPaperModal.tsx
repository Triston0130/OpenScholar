import React, { useState } from 'react';
import { Paper } from '../types';
import { fetchExternalPaper } from '../utils/api';

interface AddExternalPaperModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddPaper: (paper: Paper) => void;
}

const AddExternalPaperModal: React.FC<AddExternalPaperModalProps> = ({
  isOpen,
  onClose,
  onAddPaper
}) => {
  const [activeTab, setActiveTab] = useState<'doi' | 'bibtex'>('doi');
  const [doiInput, setDoiInput] = useState('');
  const [bibtexInput, setBibtexInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewPaper, setPreviewPaper] = useState<Paper | null>(null);

  const fetchPaperFromDOI = async (doi: string): Promise<Paper> => {
    // Clean up DOI input
    const cleanDOI = doi.replace(/^https?:\/\/(dx\.)?doi\.org\//, '').trim();
    
    // Call backend API through utility function
    return await fetchExternalPaper(cleanDOI);
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
        full_text_url: paper.full_text_url || undefined,
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
      onAddPaper(previewPaper);
      handleClose();
    }
  };

  const handleClose = () => {
    setDoiInput('');
    setBibtexInput('');
    setPreviewPaper(null);
    setError(null);
    setIsLoading(false);
    onClose();
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
            onClick={() => setActiveTab('bibtex')}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'bibtex'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Upload BibTeX
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
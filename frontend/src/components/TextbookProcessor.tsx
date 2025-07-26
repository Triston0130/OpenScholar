import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { Paper } from '../types';

interface TextbookProcessorProps {
  paper: Paper;
  isOpen: boolean;
  onClose: () => void;
  onProcessComplete?: () => void;
}

interface TextbookStatus {
  status: 'idle' | 'processing' | 'completed' | 'error';
  textbook_id?: string;
  title?: string;
  total_chunks?: number;
  chapters?: number;
  sections?: number;
  processing_time?: number;
  error?: string;
}

interface ChunkResult {
  chunk_id: string;
  success: boolean;
  result_type: string;
  content: any;
  tokens_used: number;
}

const TextbookProcessor: React.FC<TextbookProcessorProps> = ({
  paper,
  isOpen,
  onClose,
  onProcessComplete
}) => {
  const [status, setStatus] = useState<TextbookStatus>({ status: 'idle' });
  const [textbookId, setTextbookId] = useState<string | null>(null);
  const [selectedChapters, setSelectedChapters] = useState<number[]>([]);
  const [processingType, setProcessingType] = useState<'summary' | 'flashcards' | 'notes' | 'questions'>('summary');
  const [isProcessingChunks, setIsProcessingChunks] = useState(false);
  const [chunkResults, setChunkResults] = useState<ChunkResult[]>([]);
  const [textbookStructure, setTextbookStructure] = useState<any>(null);

  useEffect(() => {
    if (isOpen && paper.full_text_url && status.status === 'idle') {
      processTextbook();
    }
  }, [isOpen, paper]);

  const processTextbook = async () => {
    setStatus({ status: 'processing' });
    
    try {
      const response = await api.post('/api/ai/textbook/process', {
        pdf_url: paper.full_text_url,
        paper_id: paper.doi || paper.title,
        collection_id: 'default', // TODO: Get actual collection ID
        processing_options: {
          chunk_size: 800,
          extract_tables: true,
          extract_images: false
        },
        ai_config: {
          api_key: localStorage.getItem('openai_api_key') || '',
          model: 'gpt-3.5-turbo',
          temperature: 0.7
        }
      });

      if (response.data.success) {
        setTextbookId(response.data.textbook_id);
        // Start polling for status
        pollStatus(response.data.textbook_id);
      }
    } catch (error) {
      console.error('Error processing textbook:', error);
      setStatus({ status: 'error', error: 'Failed to process textbook' });
    }
  };

  const pollStatus = async (tbId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/api/ai/textbook/status/${tbId}`);
        
        if (response.data.status === 'completed') {
          clearInterval(pollInterval);
          setStatus({
            status: 'completed',
            textbook_id: tbId,
            title: response.data.title,
            total_chunks: response.data.total_chunks,
            chapters: response.data.chapters,
            sections: response.data.sections,
            processing_time: response.data.processing_time
          });
          
          // Fetch structure
          fetchTextbookStructure(tbId);
        } else if (response.data.status === 'error') {
          clearInterval(pollInterval);
          setStatus({ status: 'error', error: response.data.error });
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        setStatus({ status: 'error', error: 'Failed to check status' });
      }
    }, 2000); // Poll every 2 seconds
  };

  const fetchTextbookStructure = async (tbId: string) => {
    try {
      const response = await api.get(`/api/ai/textbook/structure/${tbId}`);
      setTextbookStructure(response.data);
    } catch (error) {
      console.error('Error fetching structure:', error);
    }
  };

  const processSelectedChapters = async () => {
    if (!textbookId || selectedChapters.length === 0) return;
    
    setIsProcessingChunks(true);
    setChunkResults([]);
    
    try {
      // First, get chapter summaries
      if (processingType === 'summary') {
        const response = await api.post('/api/ai/textbook/summarize-chapters', {
          textbook_id: textbookId,
          chapter_numbers: selectedChapters,
          ai_config: {
            api_key: localStorage.getItem('openai_api_key') || '',
            model: 'gpt-3.5-turbo'
          },
          summary_type: 'comprehensive'
        });
        
        // Display summaries
        console.log('Chapter summaries:', response.data);
      } else {
        // Process individual chunks
        // Get chunk IDs for selected chapters
        const chunkIds: string[] = [];
        if (textbookStructure) {
          Object.entries(textbookStructure.chapters).forEach(([chapterKey, chapterData]: [string, any]) => {
            const chapterNum = parseInt(chapterKey.replace('chapter_', ''));
            if (selectedChapters.includes(chapterNum)) {
              Object.values(chapterData.sections).forEach((section: any) => {
                section.chunks.forEach((chunk: any) => {
                  chunkIds.push(chunk.chunk_id);
                });
              });
            }
          });
        }
        
        const response = await api.post('/api/ai/textbook/process-chunks', {
          textbook_id: textbookId,
          chunk_ids: chunkIds.slice(0, 10), // Process first 10 chunks as demo
          processing_type: processingType,
          ai_config: {
            api_key: localStorage.getItem('openai_api_key') || '',
            model: 'gpt-3.5-turbo',
            temperature: 0.7
          },
          options: {
            num_flashcards: 5,
            difficulty: 'intermediate',
            style: 'cornell',
            question_types: ['comprehension', 'application', 'analysis']
          }
        });
        
        setChunkResults(response.data);
      }
    } catch (error) {
      console.error('Error processing chunks:', error);
    } finally {
      setIsProcessingChunks(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Textbook Processing</h2>
          <p className="text-sm text-gray-600 mt-1">{paper.title}</p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {status.status === 'processing' && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-600">Processing textbook structure...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a few minutes for large documents</p>
            </div>
          )}

          {status.status === 'completed' && (
            <div className="space-y-6">
              {/* Processing Stats */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900">Processing Complete</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                  <div>
                    <p className="text-sm text-blue-600">Total Chunks</p>
                    <p className="text-xl font-bold text-blue-900">{status.total_chunks}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-600">Chapters</p>
                    <p className="text-xl font-bold text-blue-900">{status.chapters}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-600">Sections</p>
                    <p className="text-xl font-bold text-blue-900">{status.sections}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-600">Time</p>
                    <p className="text-xl font-bold text-blue-900">{status.processing_time?.toFixed(1)}s</p>
                  </div>
                </div>
              </div>

              {/* Chapter Selection */}
              {textbookStructure && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Select Chapters to Process</h3>
                  <div className="max-h-48 overflow-y-auto border rounded-lg p-3">
                    {Object.entries(textbookStructure.chapters).map(([chapterKey, chapterData]: [string, any]) => {
                      const chapterNum = parseInt(chapterKey.replace('chapter_', ''));
                      return (
                        <label key={chapterKey} className="flex items-center p-2 hover:bg-gray-50 rounded">
                          <input
                            type="checkbox"
                            checked={selectedChapters.includes(chapterNum)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedChapters([...selectedChapters, chapterNum]);
                              } else {
                                setSelectedChapters(selectedChapters.filter(n => n !== chapterNum));
                              }
                            }}
                            className="mr-3"
                          />
                          <span className="font-medium">Chapter {chapterNum}</span>
                          {chapterData.title && <span className="ml-2 text-gray-600">- {chapterData.title}</span>}
                          <span className="ml-auto text-sm text-gray-500">{chapterData.chunk_count} chunks</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Processing Type Selection */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Processing Type</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <button
                    onClick={() => setProcessingType('summary')}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      processingType === 'summary' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <p className="font-medium">Summary</p>
                    <p className="text-xs mt-1">Chapter summaries</p>
                  </button>
                  <button
                    onClick={() => setProcessingType('flashcards')}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      processingType === 'flashcards' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <p className="font-medium">Flashcards</p>
                    <p className="text-xs mt-1">Study cards</p>
                  </button>
                  <button
                    onClick={() => setProcessingType('notes')}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      processingType === 'notes' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <p className="font-medium">Notes</p>
                    <p className="text-xs mt-1">Study notes</p>
                  </button>
                  <button
                    onClick={() => setProcessingType('questions')}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      processingType === 'questions' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <p className="font-medium">Questions</p>
                    <p className="text-xs mt-1">Practice Q&A</p>
                  </button>
                </div>
              </div>

              {/* Results Display */}
              {chunkResults.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Results</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {chunkResults.map((result) => (
                      <div key={result.chunk_id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            Chunk: {result.chunk_id}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {result.success ? 'Success' : 'Failed'}
                          </span>
                        </div>
                        {result.success && (
                          <div className="text-sm text-gray-600">
                            <pre className="whitespace-pre-wrap">
                              {JSON.stringify(result.content, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {status.status === 'error' && (
            <div className="text-center py-8">
              <div className="text-red-500 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-red-600">{status.error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Close
          </button>
          
          {status.status === 'completed' && (
            <button
              onClick={processSelectedChapters}
              disabled={selectedChapters.length === 0 || isProcessingChunks}
              className={`px-6 py-2 rounded-md text-white font-medium ${
                selectedChapters.length === 0 || isProcessingChunks
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isProcessingChunks ? 'Processing...' : `Process ${selectedChapters.length} Chapters`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TextbookProcessor;
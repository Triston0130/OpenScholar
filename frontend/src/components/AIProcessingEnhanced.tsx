import React, { useState } from 'react';
import { processCollectionEnhanced } from '../utils/aiEnhanced';
import { Paper } from '../types';
import toast from 'react-hot-toast';

interface AIProcessingEnhancedProps {
  isOpen: boolean;
  onClose: () => void;
  collectionId: string;
  collectionName: string;
  papers: Paper[];
  onComplete: () => void;
}

const AIProcessingEnhanced: React.FC<AIProcessingEnhancedProps> = ({
  isOpen,
  onClose,
  collectionId,
  collectionName,
  papers,
  onComplete
}) => {
  const [apiKey, setApiKey] = useState(localStorage.getItem('openai_api_key') || '');
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    currentStep: '',
    percentage: 0
  });
  
  // Options state
  const [generateTags, setGenerateTags] = useState(true);
  const [tagCount, setTagCount] = useState(20);
  const [generateNotes, setGenerateNotes] = useState(true);
  const [noteSections, setNoteSections] = useState({
    summary: true,
    keyTerms: true,
    methodology: true,
    findings: true,
    implications: true,
    criticalAnalysis: false
  });
  const [generateFlashcards, setGenerateFlashcards] = useState(true);
  const [flashcardCount, setFlashcardCount] = useState(15);
  const [flashcardDifficulty, setFlashcardDifficulty] = useState('intermediate');

  const handleProcess = async () => {
    if (!apiKey) {
      toast.error('Please enter your OpenAI API key');
      return;
    }

    // Save API key
    localStorage.setItem('openai_api_key', apiKey);

    setIsProcessing(true);
    const toastId = toast.loading('Starting AI processing...');

    try {
      const selectedSections = Object.entries(noteSections)
        .filter(([_, selected]) => selected)
        .map(([section, _]) => section);

      await processCollectionEnhanced(
        collectionId,
        papers,
        {
          generateTags,
          generateNotes,
          generateFlashcards,
          tagCount,
          flashcardCount,
          flashcardDifficulty,
          noteSections: selectedSections
        },
        {
          apiKey,
          model,
          temperature: 0.7,
          extractFullText: true
        },
        (progress) => {
          setProgress({
            ...progress,
            percentage: Math.round((progress.current / progress.total) * 100)
          });
          toast.loading(progress.currentStep, { id: toastId });
        }
      );

      toast.success('AI processing completed successfully!', { id: toastId });
      onComplete();
      onClose();
    } catch (error: any) {
      console.error('AI processing error:', error);
      toast.error(error.message || 'Failed to process papers', { id: toastId });
    } finally {
      setIsProcessing(false);
    }
  };

  // Calculate estimated cost
  const calculateCost = () => {
    const baseRate = model === 'gpt-3.5-turbo' ? 0.001 : 0.01;
    const itemsPerPaper = (generateTags ? 1 : 0) + (generateNotes ? 1 : 0) + (generateFlashcards ? 1.5 : 0);
    return (papers.length * itemsPerPaper * baseRate).toFixed(3);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">Enhanced AI Processing</h2>
            <p className="text-gray-600">Process {papers.length} papers in "{collectionName}"</p>
          </div>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {!isProcessing ? (
          <div className="space-y-6">
            {/* API Configuration */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">API Configuration</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OpenAI API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Faster, Cheaper)</option>
                  <option value="gpt-4-0125-preview">GPT-4 Turbo (Best Quality)</option>
                </select>
              </div>
            </div>

            {/* Tags Generation */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-lg">Tag Generation</h3>
                <input
                  type="checkbox"
                  checked={generateTags}
                  onChange={(e) => setGenerateTags(e.target.checked)}
                  className="h-5 w-5 text-blue-600 rounded"
                />
              </div>
              {generateTags && (
                <div>
                  <label className="text-sm text-gray-600">
                    Number of tags per paper: {tagCount}
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="30"
                    value={tagCount}
                    onChange={(e) => setTagCount(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Generates comprehensive tags across multiple categories
                  </p>
                </div>
              )}
            </div>

            {/* Notes Generation */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-lg">Notes Generation</h3>
                <input
                  type="checkbox"
                  checked={generateNotes}
                  onChange={(e) => setGenerateNotes(e.target.checked)}
                  className="h-5 w-5 text-blue-600 rounded"
                />
              </div>
              {generateNotes && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">Select sections to generate:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries({
                      summary: 'Comprehensive Summary',
                      keyTerms: 'Key Terms & Definitions',
                      methodology: 'Methodology Details',
                      findings: 'Key Findings',
                      implications: 'Implications & Applications',
                      criticalAnalysis: 'Critical Analysis'
                    }).map(([key, label]) => (
                      <label key={key} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={noteSections[key as keyof typeof noteSections]}
                          onChange={(e) => setNoteSections({
                            ...noteSections,
                            [key]: e.target.checked
                          })}
                          className="h-4 w-4 text-blue-600 rounded"
                        />
                        <span className="text-sm">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Flashcards Generation */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-lg">Flashcard Generation</h3>
                <input
                  type="checkbox"
                  checked={generateFlashcards}
                  onChange={(e) => setGenerateFlashcards(e.target.checked)}
                  className="h-5 w-5 text-purple-600 rounded"
                />
              </div>
              {generateFlashcards && (
                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-gray-600">
                      Flashcards per paper: {flashcardCount}
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="25"
                      value={flashcardCount}
                      onChange={(e) => setFlashcardCount(parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 block mb-2">
                      Difficulty Level
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                        <button
                          key={level}
                          onClick={() => setFlashcardDifficulty(level)}
                          className={`px-3 py-2 text-sm rounded capitalize ${
                            flashcardDifficulty === level
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-100 hover:bg-gray-200'
                          }`}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Cost Estimate */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">Estimated Cost</h3>
              <div className="text-sm text-blue-800">
                <p>Papers: {papers.length}</p>
                <p>Operations per paper: {(generateTags ? 1 : 0) + (generateNotes ? 1 : 0) + (generateFlashcards ? 1 : 0)}</p>
                <p className="font-semibold mt-2">Total: ${calculateCost()}</p>
              </div>
            </div>

            {/* Process Button */}
            <button
              onClick={handleProcess}
              disabled={!apiKey || (!generateTags && !generateNotes && !generateFlashcards)}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Start Enhanced Processing
            </button>
          </div>
        ) : (
          <div className="py-8">
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Processing Progress</span>
                <span className="text-sm font-medium text-gray-700">{progress.percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
            </div>
            
            <div className="text-center">
              <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-gray-700 font-medium">{progress.currentStep}</p>
              <p className="text-sm text-gray-500 mt-2">
                Processing {progress.current} of {progress.total} items
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIProcessingEnhanced;
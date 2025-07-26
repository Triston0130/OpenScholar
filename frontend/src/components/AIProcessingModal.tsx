import React, { useState, useEffect } from 'react';
import { testOpenAIKey } from '../utils/api';

interface AIProcessingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProcess: (config: AIConfig) => void;
  collectionName: string;
  paperCount: number;
  folderName?: string;
}

export interface AIConfig {
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
  processEmptyOnly: boolean;
  extractFullText: boolean;
  noteTypes: {
    summary: boolean;
    keyTerms: boolean;
    topics: boolean;
    methodology: boolean;
    findings: boolean;
    implications: boolean;
    flashcards?: boolean;
    flashcard_count?: number;
    flashcard_difficulty?: 'beginner' | 'intermediate' | 'advanced';
  };
}

const AIProcessingModal: React.FC<AIProcessingModalProps> = ({
  isOpen,
  onClose,
  onProcess,
  collectionName,
  paperCount,
  folderName
}) => {
  const [apiKey, setApiKey] = useState('');
  const [savedApiKey, setSavedApiKey] = useState('');
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1500);
  const [processEmptyOnly, setProcessEmptyOnly] = useState(true);
  const [extractFullText, setExtractFullText] = useState(true);
  const [isTestingKey, setIsTestingKey] = useState(false);
  const [keyValid, setKeyValid] = useState<boolean | null>(null);
  const [keyMessage, setKeyMessage] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [noteTypes, setNoteTypes] = useState({
    summary: true,
    keyTerms: true,
    topics: true,
    methodology: true,
    findings: true,
    implications: false,
    flashcards: false,
    flashcard_count: 10,
    flashcard_difficulty: 'intermediate' as 'beginner' | 'intermediate' | 'advanced'
  });

  // Model information with accurate token limits
  const modelInfo = {
    'gpt-3.5-turbo': {
      name: 'GPT-3.5 Turbo',
      description: 'Fast and cost-effective for most tasks',
      costPerPaper: 0.001,
      maxOutputTokens: 4096
    },
    'gpt-4-0125-preview': {
      name: 'GPT-4 Turbo (Latest)',
      description: 'Latest GPT-4 Turbo with 128K context window',
      costPerPaper: 0.010,
      maxOutputTokens: 4096
    },
    'gpt-4-1106-preview': {
      name: 'GPT-4 Turbo',
      description: 'GPT-4 Turbo with 128K context window',
      costPerPaper: 0.010,
      maxOutputTokens: 4096
    },
    'gpt-4': {
      name: 'GPT-4',
      description: 'Original GPT-4 with 8K context window',
      costPerPaper: 0.030,
      maxOutputTokens: 4096
    }
  };

  useEffect(() => {
    // Load saved API key from localStorage
    const saved = localStorage.getItem('openai_api_key');
    if (saved) {
      setSavedApiKey(saved);
      setApiKey(saved);
    }
  }, []);

  const handleTestApiKey = async () => {
    if (!apiKey) return;
    
    setIsTestingKey(true);
    setKeyValid(null);
    setKeyMessage('');

    try {
      const result = await testOpenAIKey(apiKey);
      setKeyValid(result.valid);
      setKeyMessage(result.message);
      
      if (result.valid) {
        // Save valid key
        localStorage.setItem('openai_api_key', apiKey);
        setSavedApiKey(apiKey);
      }
    } catch (error) {
      setKeyValid(false);
      setKeyMessage('Failed to test API key');
    } finally {
      setIsTestingKey(false);
    }
  };

  const handleProcess = () => {
    if (!apiKey || keyValid === false) {
      alert('Please enter a valid API key');
      return;
    }

    // Check if at least one note type is selected
    const hasSelectedNoteType = Object.values(noteTypes).some(selected => selected);
    if (!hasSelectedNoteType) {
      alert('Please select at least one note content type');
      return;
    }
    
    const config = {
      apiKey,
      model,
      temperature,
      maxTokens,
      processEmptyOnly,
      extractFullText,
      noteTypes
    };
    console.log('Processing with config:', config);
    onProcess(config);
  };

  const costMultiplier = extractFullText ? 2.5 : 1; // Full text analysis costs more
  const flashcardMultiplier = noteTypes.flashcards ? 1.3 : 1; // Flashcards add ~30% more cost
  const estimatedCost = paperCount * modelInfo[model as keyof typeof modelInfo].costPerPaper * costMultiplier * flashcardMultiplier;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                🤖 AI-Powered Note & Tag Generation
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Process {folderName ? `"${folderName}" folder` : `"${collectionName}" collection`} with {paperCount} papers
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* API Key Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key
            </label>
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-2.5 text-gray-500 hover:text-gray-700"
                  >
                    {showApiKey ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                <button
                  onClick={handleTestApiKey}
                  disabled={!apiKey || isTestingKey}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    isTestingKey
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isTestingKey ? 'Testing...' : 'Test Key'}
                </button>
              </div>
              
              {keyValid !== null && (
                <div className={`flex items-center gap-2 text-sm ${keyValid ? 'text-green-600' : 'text-red-600'}`}>
                  {keyValid ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                  {keyMessage}
                </div>
              )}
              
              <p className="text-xs text-gray-500">
                Get your API key from{' '}
                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  OpenAI Platform
                </a>
              </p>
            </div>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <select
              value={model}
              onChange={(e) => {
                const newModel = e.target.value;
                console.log('Changing model to:', newModel);
                setModel(newModel);
                // Reset max tokens if switching to GPT-3.5 and current value is too high
                if (newModel === 'gpt-3.5-turbo' && maxTokens > 4000) {
                  console.log('Resetting maxTokens to 4000 for GPT-3.5');
                  setMaxTokens(4000);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              {Object.entries(modelInfo).map(([key, info]) => (
                <option key={key} value={key}>
                  {info.name} - ${info.costPerPaper}/paper
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-600">
              {modelInfo[model as keyof typeof modelInfo].description}
              {model === 'gpt-3.5-turbo' && (
                <span className="block mt-1 text-xs text-amber-600">
                  Note: GPT-3.5 Turbo has a 4,000 token output limit
                </span>
              )}
            </p>
          </div>

          {/* Advanced Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700">Advanced Settings</h3>
            
            {/* Temperature */}
            <div>
              <label className="flex items-center justify-between text-sm text-gray-600">
                <span>Temperature (Creativity)</span>
                <span className="font-medium">{temperature}</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full mt-1"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Focused</span>
                <span>Creative</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div>
              <label className="flex items-center justify-between text-sm text-gray-600">
                <span>Max Response Length</span>
                <span className="font-medium">{maxTokens} tokens</span>
              </label>
              <input
                type="range"
                min="500"
                max={modelInfo[model as keyof typeof modelInfo]?.maxOutputTokens || 4096}
                step="100"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full mt-1"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Brief (500)</span>
                <span>Very Detailed ({modelInfo[model as keyof typeof modelInfo]?.maxOutputTokens || 4096})</span>
              </div>
            </div>

            {/* Process Empty Only */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="processEmptyOnly"
                checked={processEmptyOnly}
                onChange={(e) => setProcessEmptyOnly(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="processEmptyOnly" className="ml-2 text-sm text-gray-700">
                Only process papers without existing notes/tags
              </label>
            </div>

            {/* Extract Full Text */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="extractFullText"
                checked={extractFullText}
                onChange={(e) => setExtractFullText(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="extractFullText" className="ml-2 text-sm text-gray-700">
                Extract and analyze full paper text when available (PDF)
                <span className="text-xs text-gray-500 block ml-6">
                  When enabled, the AI will download and read entire papers instead of just abstracts
                </span>
              </label>
            </div>
          </div>

          {/* Note Types Selection */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700">Note Content Types</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries({
                summary: 'Summary',
                keyTerms: 'Key Terms & Definitions',
                topics: 'Main Topics',
                methodology: 'Methodology',
                findings: 'Key Findings',
                implications: 'Implications & Applications'
              }).map(([key, label]) => (
                <div key={key} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`noteType-${key}`}
                    checked={Boolean(noteTypes[key as keyof typeof noteTypes])}
                    onChange={(e) => setNoteTypes({
                      ...noteTypes,
                      [key]: e.target.checked
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor={`noteType-${key}`} className="ml-2 text-sm text-gray-700">
                    {label}
                  </label>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              Selected content types will be included in the generated notes
            </p>
            
            {/* Flashcard Generation Section */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center mb-3">
                <input
                  type="checkbox"
                  id="generate-flashcards"
                  checked={noteTypes.flashcards}
                  onChange={(e) => setNoteTypes({
                    ...noteTypes,
                    flashcards: e.target.checked
                  })}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="generate-flashcards" className="ml-2 text-sm font-medium text-gray-700">
                  Generate AI Flashcards
                </label>
              </div>
              
              {noteTypes.flashcards && (
                <div className="ml-6 space-y-3">
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Number of Flashcards: {noteTypes.flashcard_count}
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="20"
                      value={noteTypes.flashcard_count}
                      onChange={(e) => setNoteTypes({
                        ...noteTypes,
                        flashcard_count: parseInt(e.target.value)
                      })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                  
                  <div>
                    <label className="text-xs font-medium text-gray-600 mb-1 block">
                      Difficulty Level
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setNoteTypes({
                            ...noteTypes,
                            flashcard_difficulty: level
                          })}
                          className={`px-2 py-1 text-xs rounded capitalize ${
                            noteTypes.flashcard_difficulty === level
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
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
          </div>

          {/* Cost Estimate */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">Cost Estimate</h3>
            <div className="space-y-1 text-sm text-blue-800">
              <div className="flex justify-between">
                <span>Papers to process:</span>
                <span className="font-medium">{paperCount}</span>
              </div>
              <div className="flex justify-between">
                <span>Cost per paper:</span>
                <span className="font-medium">${modelInfo[model as keyof typeof modelInfo].costPerPaper}</span>
              </div>
              {noteTypes.flashcards && (
                <div className="flex justify-between text-purple-700">
                  <span>Flashcards ({noteTypes.flashcard_count} per paper):</span>
                  <span className="font-medium">+30%</span>
                </div>
              )}
              <div className="border-t border-blue-200 pt-1 mt-1">
                <div className="flex justify-between font-medium">
                  <span>Estimated total:</span>
                  <span>${estimatedCost.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Important Notes</h3>
                <ul className="mt-1 text-sm text-yellow-700 space-y-1">
                  <li>• Processing may take several minutes depending on the number of papers</li>
                  <li>• You will be charged by OpenAI based on actual usage</li>
                  <li>• Generated content will supplement, not replace, your existing notes</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleProcess}
            disabled={!apiKey || keyValid === false}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              !apiKey || keyValid === false
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Start Processing
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIProcessingModal;
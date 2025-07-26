import React, { useState } from 'react';
import { Paper } from '../types';
import { processPapersWithAI } from '../utils/api';
import { createMultipleFlashcards } from '../utils/annotations';
import toast from 'react-hot-toast';

interface ProcessedPaperWithFlashcards {
  paper_id: string;
  title: string;
  tags: string[];
  notes: string;
  flashcards?: Array<{
    front: string;
    back: string;
    category?: string;
    difficulty?: string;
  }>;
  success: boolean;
  error_message?: string;
}

interface AIFlashcardGeneratorSimpleProps {
  paper: Paper;
  pdfUrl: string;
  onClose: () => void;
  onFlashcardsGenerated: () => void;
}

interface Config {
  model: string;
  flashcard_count: number;
  flashcard_difficulty: 'beginner' | 'intermediate' | 'advanced';
}

const AIFlashcardGeneratorSimple: React.FC<AIFlashcardGeneratorSimpleProps> = ({
  paper,
  pdfUrl,
  onClose,
  onFlashcardsGenerated
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [config, setConfig] = useState<Config>({
    model: 'gpt-3.5-turbo',
    flashcard_count: 10,
    flashcard_difficulty: 'intermediate'
  });

  const handleGenerate = async () => {
    const apiKey = localStorage.getItem('openai_api_key');
    if (!apiKey) {
      toast.error('Please set your OpenAI API key in the AI processing settings');
      return;
    }

    setIsGenerating(true);
    const toastId = toast.loading('Generating flashcards...');

    try {
      // Prepare the paper data
      const paperData = {
        doi: paper.doi,
        title: paper.title,
        authors: paper.authors || [],
        year: paper.year,
        abstract: paper.abstract,
        journal: paper.journal,
        url: paper.full_text_url,  // Paper type uses full_text_url
        pdf_url: pdfUrl,
        full_text_url: paper.full_text_url || pdfUrl,
        source: paper.source
      };

      // Use the existing AI processing endpoint with flashcard generation enabled
      const response = await processPapersWithAI(
        [paperData],
        {
          apiKey: apiKey,  // Fixed: use apiKey not api_key
          model: config.model,
          temperature: 0.7,
          maxTokens: 2000,  // Fixed: use maxTokens not max_tokens
          noteTypes: {      // Fixed: use noteTypes not note_types
            summary: false,
            keyTerms: false,
            topics: false,
            methodology: false,
            findings: false,
            implications: false,
            flashcards: true,
            flashcard_count: config.flashcard_count,
            flashcard_difficulty: config.flashcard_difficulty
          } as any,  // Cast to any to include flashcard properties
          processEmptyOnly: false,
          extractFullText: true  // Fixed: use extractFullText not extract_full_text
        }
      );

      if (response.processed_papers && response.processed_papers.length > 0) {
        const processedPaper = response.processed_papers[0] as ProcessedPaperWithFlashcards;
        
        if (processedPaper.success && processedPaper.flashcards && processedPaper.flashcards.length > 0) {
          const paperId = paper.doi || paper.full_text_url || paper.title;
          
          // Create flashcards using the existing system
          createMultipleFlashcards(paperId, pdfUrl, processedPaper.flashcards);
          
          toast.success(`Generated ${processedPaper.flashcards.length} flashcards!`, { id: toastId });
          onFlashcardsGenerated();
          onClose();
        } else {
          toast.error(processedPaper.error_message || 'Failed to generate flashcards', { id: toastId });
        }
      } else {
        toast.error('No response from AI processing', { id: toastId });
      }
    } catch (error: any) {
      console.error('Error generating flashcards:', error);
      toast.error(error.message || 'Failed to generate flashcards', { id: toastId });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Generate AI Flashcards</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              AI Model
            </label>
            <select
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Fast)</option>
              <option value="gpt-4-0125-preview">GPT-4 Turbo (Best)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Number of Flashcards: {config.flashcard_count}
            </label>
            <input
              type="range"
              min="5"
              max="20"
              value={config.flashcard_count}
              onChange={(e) => setConfig({ ...config, flashcard_count: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Difficulty Level
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setConfig({ ...config, flashcard_difficulty: level })}
                  className={`px-3 py-2 rounded capitalize text-sm ${
                    config.flashcard_difficulty === level
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm text-blue-800">
              Flashcards will be generated from the paper's full text using AI. 
              Make sure you have set your OpenAI API key in the main AI settings.
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className={`w-full py-2 px-4 rounded-md font-medium ${
              isGenerating
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isGenerating ? 'Generating...' : `Generate ${config.flashcard_count} Flashcards`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIFlashcardGeneratorSimple;
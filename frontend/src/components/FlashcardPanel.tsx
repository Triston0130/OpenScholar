import React, { useState, useEffect } from 'react';
import { Flashcard, getAllAnnotations, updateAnnotation } from '../utils/annotations';
import AIFlashcardGeneratorSimple from './AIFlashcardGeneratorSimple';
import { Paper } from '../types';

interface FlashcardPanelProps {
  paperId?: string;
  paper?: Paper;
  pdfUrl?: string;
  extractedText?: string;
}

const FlashcardPanel: React.FC<FlashcardPanelProps> = ({ paperId, paper, pdfUrl, extractedText }) => {
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [studyStats, setStudyStats] = useState({ studied: 0, correct: 0, incorrect: 0 });
  const [isFlipped, setIsFlipped] = useState(false);
  const [showAIGenerator, setShowAIGenerator] = useState(false);

  useEffect(() => {
    loadFlashcards();
  }, [paperId]);

  const loadFlashcards = () => {
    const allAnnotations = getAllAnnotations();
    let flashcardAnnotations = allAnnotations.filter(ann => ann.type === 'flashcard') as Flashcard[];
    
    // Filter by paperId if provided
    if (paperId) {
      flashcardAnnotations = flashcardAnnotations.filter(card => card.paperId === paperId);
    }
    
    // Sort by next review date (due cards first)
    const sortedCards = flashcardAnnotations.sort((a, b) => {
      const dateA = a.nextReviewDate ? new Date(a.nextReviewDate).getTime() : 0;
      const dateB = b.nextReviewDate ? new Date(b.nextReviewDate).getTime() : 0;
      return dateA - dateB;
    });

    setFlashcards(sortedCards);
    setCurrentIndex(0);
    setShowAnswer(false);
    setIsFlipped(false);
    setStudyStats({ studied: 0, correct: 0, incorrect: 0 });
  };

  const handleAIFlashcardsGenerated = () => {
    // Reload flashcards to show the new ones
    loadFlashcards();
  };

  const currentCard = flashcards[currentIndex];

  const calculateNextReview = (difficulty: number, quality: number): Date => {
    const now = new Date();
    let interval = 1;

    if (quality >= 3) {
      if (difficulty < 2) interval = 1;
      else if (difficulty < 3) interval = 3;
      else if (difficulty < 4) interval = 7;
      else interval = 14;
    } else {
      interval = 0.25; // 6 hours
    }

    now.setDate(now.getDate() + interval);
    return now;
  };

  const handleAnswer = (quality: number) => {
    if (!currentCard) return;

    const newDifficulty = Math.max(1, Math.min(5, 
      (currentCard.difficulty || 2.5) + (0.1 - (5 - quality) * 0.08)
    ));

    const nextReview = calculateNextReview(newDifficulty, quality);

    updateAnnotation(currentCard.id, {
      difficulty: newDifficulty,
      nextReviewDate: nextReview
    } as any);

    setStudyStats(prev => ({
      studied: prev.studied + 1,
      correct: quality >= 3 ? prev.correct + 1 : prev.correct,
      incorrect: quality < 3 ? prev.incorrect + 1 : prev.incorrect
    }));

    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
      setIsFlipped(false);
    } else {
      // Reset to beginning
      loadFlashcards();
    }
  };

  if (flashcards.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center">
        <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Flashcards Yet</h3>
        <p className="text-sm text-gray-600 mb-4">
          Create flashcards by selecting text and choosing "Create Flashcard" from the menu.
        </p>
      </div>
    );
  }

  const progress = ((currentIndex + 1) / flashcards.length) * 100;
  const getDifficultyColor = (difficulty: number = 2.5) => {
    if (difficulty < 2) return 'text-green-600';
    if (difficulty < 3.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Flashcard Review
          </h3>
          <div className="flex items-center space-x-4">
            {paper && pdfUrl && (
              <button
                onClick={() => setShowAIGenerator(true)}
                className="px-3 py-1.5 text-sm bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-colors flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generate AI Flashcards</span>
              </button>
            )}
            <span className="text-sm text-gray-600">
              {currentIndex + 1} / {flashcards.length}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between mt-3 text-xs">
          <span className="text-green-600">✓ {studyStats.correct} correct</span>
          <span className="text-red-600">✗ {studyStats.incorrect} incorrect</span>
          <span className={getDifficultyColor(currentCard?.difficulty)}>
            Difficulty: {currentCard?.difficulty?.toFixed(1) || '2.5'}
          </span>
        </div>
      </div>

      {/* Card */}
      <div className="flex-1 p-6 flex items-center justify-center">
        {currentCard && (
          <div 
            className="w-full max-w-md"
            style={{ perspective: '1000px' }}
          >
            <div
              className={`relative w-full h-64 transition-transform duration-600 transform-style-preserve-3d cursor-pointer ${
                isFlipped ? 'rotate-y-180' : ''
              }`}
              onClick={() => setIsFlipped(!isFlipped)}
              style={{
                transformStyle: 'preserve-3d',
                transition: 'transform 0.6s',
                transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
              }}
            >
              {/* Front */}
              <div 
                className="absolute inset-0 bg-white rounded-xl shadow-lg p-6 flex items-center justify-center backface-hidden overflow-auto"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <div className="text-center w-full">
                  <p className="text-xs text-gray-500 mb-2">Question</p>
                  {currentCard.frontImage && (
                    <div className="mb-4">
                      <img 
                        src={currentCard.frontImage} 
                        alt="Flashcard visual" 
                        className="max-w-full max-h-40 mx-auto rounded border"
                      />
                    </div>
                  )}
                  <p className="text-lg text-gray-900">{currentCard.front}</p>
                  <p className="text-xs text-gray-400 mt-4">Click to flip</p>
                </div>
              </div>

              {/* Back */}
              <div 
                className="absolute inset-0 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-lg p-6 flex items-center justify-center backface-hidden overflow-auto"
                style={{ 
                  backfaceVisibility: 'hidden',
                  transform: 'rotateY(180deg)'
                }}
              >
                <div className="text-center w-full">
                  <p className="text-xs text-gray-500 mb-2">Answer</p>
                  {currentCard.backImage && (
                    <div className="mb-4">
                      <img 
                        src={currentCard.backImage} 
                        alt="Answer visual" 
                        className="max-w-full max-h-40 mx-auto rounded border"
                      />
                    </div>
                  )}
                  <p className="text-lg text-gray-900">{currentCard.back || (currentCard.backImage ? '' : 'No answer')}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action buttons */}
      {isFlipped && currentCard && (
        <div className="p-4 bg-white border-t">
          <p className="text-xs text-gray-600 text-center mb-3">How well did you know this?</p>
          <div className="grid grid-cols-4 gap-2">
            <button
              onClick={() => handleAnswer(1)}
              className="py-2 px-3 text-xs font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
            >
              Again
            </button>
            <button
              onClick={() => handleAnswer(2)}
              className="py-2 px-3 text-xs font-medium text-white bg-orange-500 rounded-lg hover:bg-orange-600 transition-colors"
            >
              Hard
            </button>
            <button
              onClick={() => handleAnswer(3)}
              className="py-2 px-3 text-xs font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
            >
              Good
            </button>
            <button
              onClick={() => handleAnswer(4)}
              className="py-2 px-3 text-xs font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors"
            >
              Easy
            </button>
          </div>
        </div>
      )}
      
      {/* AI Flashcard Generator Modal */}
      {showAIGenerator && paper && pdfUrl && (
        <AIFlashcardGeneratorSimple
          paper={paper}
          pdfUrl={pdfUrl}
          onClose={() => setShowAIGenerator(false)}
          onFlashcardsGenerated={handleAIFlashcardsGenerated}
        />
      )}
    </div>
  );
};

export default FlashcardPanel;
import React, { useState, useEffect, useCallback } from 'react';
import { Flashcard, getAllAnnotations, updateAnnotation } from '../utils/annotations';

interface FlashcardReviewProps {
  isOpen: boolean;
  onClose: () => void;
  paperId?: string;
}

const FlashcardReview: React.FC<FlashcardReviewProps> = ({ isOpen, onClose, paperId }) => {
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [studyStats, setStudyStats] = useState({ studied: 0, correct: 0, incorrect: 0 });
  const [reviewMode, setReviewMode] = useState<'study' | 'browse' | 'grid'>('browse');

  useEffect(() => {
    if (isOpen) {
      loadFlashcards();
    }
  }, [isOpen, paperId]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      // Grid view shortcuts
      if (reviewMode === 'grid') {
        if (e.key === 'Escape') {
          setReviewMode('browse');
        } else if (e.key === 'Enter') {
          setReviewMode('browse');
        }
        return;
      }

      // Regular shortcuts
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        setShowAnswer(!showAnswer);
      } else if (e.key === 'ArrowRight' || e.key === 'j') {
        e.preventDefault();
        nextCard();
      } else if (e.key === 'ArrowLeft' || e.key === 'k') {
        e.preventDefault();
        previousCard();
      } else if (e.key === 'ArrowDown' && currentIndex < flashcards.length - 5) {
        e.preventDefault();
        setCurrentIndex(Math.min(currentIndex + 5, flashcards.length - 1));
        setShowAnswer(false);
      } else if (e.key === 'ArrowUp' && currentIndex >= 5) {
        e.preventDefault();
        setCurrentIndex(currentIndex - 5);
        setShowAnswer(false);
      } else if (e.key === 'g') {
        e.preventDefault();
        setReviewMode('grid');
      } else if (e.key === 'Escape') {
        onClose();
      } else if (showAnswer && reviewMode === 'study') {
        if (e.key === '1') handleAnswer(1);
        else if (e.key === '2') handleAnswer(2);
        else if (e.key === '3') handleAnswer(3);
        else if (e.key === '4') handleAnswer(4);
        else if (e.key === '5') handleAnswer(5);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen, showAnswer, currentIndex, flashcards, reviewMode]);

  const loadFlashcards = () => {
    const allAnnotations = getAllAnnotations();
    let flashcardAnnotations = allAnnotations.filter(ann => ann.type === 'flashcard') as Flashcard[];
    
    if (paperId) {
      flashcardAnnotations = flashcardAnnotations.filter(card => card.paperId === paperId);
    }
    
    const sortedCards = flashcardAnnotations.sort((a, b) => {
      const dateA = a.nextReviewDate ? new Date(a.nextReviewDate).getTime() : 0;
      const dateB = b.nextReviewDate ? new Date(b.nextReviewDate).getTime() : 0;
      return dateA - dateB;
    });

    setFlashcards(sortedCards);
    setCurrentIndex(0);
    setShowAnswer(false);
    setStudyStats({ studied: 0, correct: 0, incorrect: 0 });
  };

  const nextCard = useCallback(() => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
    }
  }, [currentIndex, flashcards.length]);

  const previousCard = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setShowAnswer(false);
    }
  }, [currentIndex]);

  const calculateNextReview = (difficulty: number, quality: number): Date => {
    const now = new Date();
    let interval = 1;

    if (quality >= 3) {
      if (difficulty < 2) interval = 1;
      else if (difficulty < 3) interval = 3;
      else if (difficulty < 4) interval = 7;
      else interval = 14;
    } else {
      interval = 0.25;
    }

    now.setDate(now.getDate() + interval);
    return now;
  };

  const handleAnswer = (quality: number) => {
    if (!currentCard || reviewMode !== 'study') return;

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

    nextCard();
  };

  const currentCard = flashcards[currentIndex];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-xl font-semibold">Flashcard Review</h2>
              {flashcards.length > 0 && (
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setReviewMode('study')}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      reviewMode === 'study' ? 'bg-white shadow-sm font-medium' : 'text-gray-600'
                    }`}
                  >
                    Study Mode
                  </button>
                  <button
                    onClick={() => setReviewMode('browse')}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      reviewMode === 'browse' ? 'bg-white shadow-sm font-medium' : 'text-gray-600'
                    }`}
                  >
                    Browse
                  </button>
                  <button
                    onClick={() => setReviewMode('grid')}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      reviewMode === 'grid' ? 'bg-white shadow-sm font-medium' : 'text-gray-600'
                    }`}
                  >
                    Grid View
                  </button>
                </div>
              )}
            </div>
            
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {flashcards.length > 0 && (
            <div className="mt-3">
              {/* Progress Bar */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">
                  Card {currentIndex + 1} of {flashcards.length}
                </span>
                {reviewMode === 'study' && studyStats.studied > 0 && (
                  <div className="flex items-center space-x-3 text-sm">
                    <span className="text-green-600">✓ {studyStats.correct}</span>
                    <span className="text-red-600">✗ {studyStats.incorrect}</span>
                    <span className="text-gray-600 font-medium">
                      {Math.round((studyStats.correct / studyStats.studied) * 100)}% correct
                    </span>
                  </div>
                )}
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                  style={{ width: `${((currentIndex + 1) / flashcards.length) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-auto p-6">
          {flashcards.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Flashcards Yet</h3>
                <p className="text-sm text-gray-600">Create flashcards by selecting text or screenshots!</p>
              </div>
            </div>
          ) : reviewMode === 'grid' ? (
            // Grid View
            <div className="h-full overflow-auto">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {flashcards.map((card, index) => (
                  <div
                    key={card.id}
                    onClick={() => {
                      setCurrentIndex(index);
                      setReviewMode('browse');
                      setShowAnswer(false);
                    }}
                    className={`bg-white rounded-lg shadow-md p-4 cursor-pointer hover:shadow-lg transition-all ${
                      index === currentIndex ? 'ring-2 ring-blue-500' : ''
                    }`}
                  >
                    {card.frontImage ? (
                      <img 
                        src={card.frontImage} 
                        alt="Card thumbnail" 
                        className="w-full h-32 object-cover rounded mb-2"
                      />
                    ) : (
                      <div className="w-full h-32 bg-gray-100 rounded mb-2 flex items-center justify-center">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                    )}
                    <p className="text-sm text-gray-900 font-medium line-clamp-2">{card.front}</p>
                    {card.tags && card.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {card.tags.slice(0, 2).map((tag, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : currentCard && (
            <div className="h-full flex items-center justify-center">
              <div className="w-full max-w-2xl">
                {/* Card */}
                <div 
                  className={`bg-white rounded-xl shadow-lg overflow-hidden cursor-pointer transition-all duration-300 ${
                    showAnswer ? 'ring-2 ring-blue-500' : ''
                  }`}
                  onClick={() => setShowAnswer(!showAnswer)}
                >
                  {/* Question Side */}
                  <div className={`p-8 ${showAnswer ? 'border-b bg-gray-50' : ''}`}>
                    <div>
                      <p className="text-sm font-medium text-gray-500 mb-4">QUESTION</p>
                      
                      {/* Front Image */}
                      {currentCard.frontImage && (
                        <div className="mb-4">
                          <img 
                            src={currentCard.frontImage} 
                            alt="Question visual" 
                            className="max-w-full max-h-64 mx-auto rounded-lg border shadow-sm"
                          />
                        </div>
                      )}
                      
                      <p className="text-xl text-gray-900 text-center">{currentCard.front}</p>
                      
                      {!showAnswer && (
                        <p className="text-sm text-gray-400 text-center mt-6">
                          Click or press SPACE to reveal answer
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Answer Side */}
                  {showAnswer && (
                    <div className="p-8">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-4">ANSWER</p>
                        
                        {/* Back Image */}
                        {currentCard.backImage && (
                          <div className="mb-4">
                            <img 
                              src={currentCard.backImage} 
                              alt="Answer visual" 
                              className="max-w-full max-h-64 mx-auto rounded-lg border shadow-sm"
                            />
                          </div>
                        )}
                        
                        <p className="text-xl text-gray-900 text-center">
                          {currentCard.back || (currentCard.backImage ? 'See image above' : 'No answer provided')}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Tags */}
                {currentCard.tags && currentCard.tags.length > 0 && (
                  <div className="mt-4 flex justify-center flex-wrap gap-2">
                    {currentCard.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {flashcards.length > 0 && (
          <div className="border-t px-6 py-4">
            {reviewMode === 'study' && showAnswer ? (
              <div>
                <p className="text-center text-sm text-gray-600 mb-3">How well did you know this?</p>
                <div className="flex justify-center space-x-2">
                  <button
                    onClick={() => handleAnswer(1)}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                  >
                    <span className="font-medium">1</span>
                    <span className="text-xs ml-1">Again</span>
                  </button>
                  <button
                    onClick={() => handleAnswer(2)}
                    className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors"
                  >
                    <span className="font-medium">2</span>
                    <span className="text-xs ml-1">Hard</span>
                  </button>
                  <button
                    onClick={() => handleAnswer(3)}
                    className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
                  >
                    <span className="font-medium">3</span>
                    <span className="text-xs ml-1">Good</span>
                  </button>
                  <button
                    onClick={() => handleAnswer(4)}
                    className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                  >
                    <span className="font-medium">4</span>
                    <span className="text-xs ml-1">Easy</span>
                  </button>
                  <button
                    onClick={() => handleAnswer(5)}
                    className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                  >
                    <span className="font-medium">5</span>
                    <span className="text-xs ml-1">Perfect</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex justify-between items-center">
                <button
                  onClick={previousCard}
                  disabled={currentIndex === 0}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                    currentIndex === 0 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span>Previous</span>
                </button>

                <div className="text-center text-xs text-gray-500">
                  <p>← → or J/K Navigate • ↑↓ Jump 5 • SPACE Flip • G Grid • ESC Close</p>
                </div>
                
                <button
                  onClick={nextCard}
                  disabled={currentIndex === flashcards.length - 1}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                    currentIndex === flashcards.length - 1 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  <span>Next</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FlashcardReview;
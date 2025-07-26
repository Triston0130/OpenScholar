import React, { useState, useEffect } from 'react';
import { Flashcard, getAllAnnotations, updateAnnotation } from '../utils/annotations';
import { getAllCollectionsWithPapers } from '../utils/collections';

interface FlashcardStack {
  id: string;
  name: string;
  cards: Flashcard[];
  type: 'collection' | 'paper' | 'all';
  color?: string;
}

interface FlashcardsPageProps {
  onNavigate: (page: 'search' | 'flashcards' | 'landing') => void;
}

const FlashcardsPage: React.FC<FlashcardsPageProps> = ({ onNavigate }) => {
  const [stacks, setStacks] = useState<FlashcardStack[]>([]);
  const [selectedStack, setSelectedStack] = useState<FlashcardStack | null>(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [studyStats, setStudyStats] = useState({ studied: 0, correct: 0, incorrect: 0 });

  useEffect(() => {
    loadFlashcardStacks();
  }, []);

  const loadFlashcardStacks = () => {
    const allAnnotations = getAllAnnotations();
    const flashcards = allAnnotations.filter(ann => ann.type === 'flashcard') as Flashcard[];
    
    // Group by collection
    const collections = getAllCollectionsWithPapers();
    const stacksMap = new Map<string, FlashcardStack>();
    
    // Create "All Cards" stack
    if (flashcards.length > 0) {
      stacksMap.set('all', {
        id: 'all',
        name: 'All Flashcards',
        cards: flashcards,
        type: 'all',
        color: '#8b5cf6'
      });
    }
    
    // Group by collection
    collections.forEach(collection => {
      const collectionCards = flashcards.filter(card => {
        return collection.papers.some(paper => 
          card.paperId === paper.doi || 
          card.paperId === paper.full_text_url || 
          card.paperId === paper.title
        );
      });
      
      if (collectionCards.length > 0) {
        stacksMap.set(collection.id, {
          id: collection.id,
          name: collection.name,
          cards: collectionCards,
          type: 'collection',
          color: collection.color
        });
      }
    });
    
    // Group remaining by paper
    const paperGroups = new Map<string, Flashcard[]>();
    flashcards.forEach(card => {
      const isInCollection = Array.from(stacksMap.values()).some(stack => 
        stack.type === 'collection' && stack.cards.includes(card)
      );
      
      if (!isInCollection && card.paperId) {
        if (!paperGroups.has(card.paperId)) {
          paperGroups.set(card.paperId, []);
        }
        paperGroups.get(card.paperId)!.push(card);
      }
    });
    
    // Create stacks for papers with multiple cards
    paperGroups.forEach((cards, paperId) => {
      if (cards.length >= 3) { // Only create stack if 3+ cards
        const paperTitle = paperId.substring(0, 30) + '...';
        stacksMap.set(paperId, {
          id: paperId,
          name: paperTitle,
          cards: cards,
          type: 'paper',
          color: '#64748b'
        });
      }
    });
    
    setStacks(Array.from(stacksMap.values()));
  };

  const handleCardAnswer = (quality: number) => {
    if (!selectedStack || !selectedStack.cards[currentCardIndex]) return;
    
    const currentCard = selectedStack.cards[currentCardIndex];
    
    // Calculate new difficulty
    const newDifficulty = Math.max(1, Math.min(5, 
      (currentCard.difficulty || 2.5) + (0.1 - (5 - quality) * 0.08)
    ));
    
    // Calculate next review date
    const now = new Date();
    let interval = 1;
    if (quality >= 3) {
      if (newDifficulty < 2) interval = 1;
      else if (newDifficulty < 3) interval = 3;
      else if (newDifficulty < 4) interval = 7;
      else interval = 14;
    } else {
      interval = 0.25; // 6 hours
    }
    now.setDate(now.getDate() + interval);
    
    // Update the flashcard
    updateAnnotation(currentCard.id, {
      difficulty: newDifficulty,
      nextReviewDate: now
    } as any);
    
    // Update stats
    setStudyStats(prev => ({
      studied: prev.studied + 1,
      correct: quality >= 3 ? prev.correct + 1 : prev.correct,
      incorrect: quality < 3 ? prev.incorrect + 1 : prev.incorrect
    }));
    
    // Move to next card
    if (currentCardIndex < selectedStack.cards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsFlipped(false);
    } else {
      // End of stack
      alert(`Stack complete! Studied: ${studyStats.studied + 1}, Correct: ${quality >= 3 ? studyStats.correct + 1 : studyStats.correct}`);
      setSelectedStack(null);
      setCurrentCardIndex(0);
      setStudyStats({ studied: 0, correct: 0, incorrect: 0 });
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Main stack view
  if (!selectedStack) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <button
              onClick={() => onNavigate('search')}
              className="mb-4 flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Search
            </button>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Flashcard Stacks</h1>
            <p className="text-lg text-gray-600">Review your flashcards organized by collection</p>
          </div>
          
          {stacks.length === 0 ? (
            <div className="text-center py-16">
              <svg className="w-24 h-24 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Flashcards Yet</h3>
              <p className="text-gray-600">Create flashcards while reading papers by selecting text and choosing "Create Flashcard"</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {stacks.map((stack) => {
                const dueCards = stack.cards.filter(card => {
                  if (!card.nextReviewDate) return true;
                  return new Date(card.nextReviewDate) <= new Date();
                }).length;
                
                return (
                  <div
                    key={stack.id}
                    onClick={() => setSelectedStack(stack)}
                    className="relative group cursor-pointer transform transition-all duration-300 hover:scale-105"
                  >
                    {/* Stack effect - background cards */}
                    <div 
                      className="absolute inset-0 bg-white rounded-xl shadow-lg transform rotate-3 group-hover:rotate-6 transition-transform"
                      style={{ backgroundColor: stack.color + '20' }}
                    />
                    <div 
                      className="absolute inset-0 bg-white rounded-xl shadow-lg transform -rotate-2 group-hover:-rotate-4 transition-transform"
                      style={{ backgroundColor: stack.color + '30' }}
                    />
                    
                    {/* Main card */}
                    <div 
                      className="relative bg-white rounded-xl shadow-xl p-6 h-48 flex flex-col justify-between overflow-hidden"
                      style={{ borderTop: `4px solid ${stack.color}` }}
                    >
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                          {stack.name}
                        </h3>
                        <div className="flex items-center text-sm text-gray-600 space-x-4">
                          <span>{stack.cards.length} cards</span>
                          {dueCards > 0 && (
                            <span className="text-purple-600 font-medium">{dueCards} due</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500 capitalize">{stack.type}</span>
                        <div className="flex items-center space-x-1">
                          <div className="w-2 h-2 rounded-full bg-green-400" />
                          <div className="w-2 h-2 rounded-full bg-yellow-400" />
                          <div className="w-2 h-2 rounded-full bg-red-400" />
                        </div>
                      </div>
                      
                      {/* Hover overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-purple-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-xl" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Study view
  const currentCard = selectedStack.cards[currentCardIndex];
  const progress = ((currentCardIndex + 1) / selectedStack.cards.length) * 100;

  return (
    <div className={`min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-sm shadow-sm px-6 py-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  setSelectedStack(null);
                  setCurrentCardIndex(0);
                  setIsFlipped(false);
                  if (isFullscreen) toggleFullscreen();
                }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{selectedStack.name}</h2>
                <p className="text-sm text-gray-600">Card {currentCardIndex + 1} of {selectedStack.cards.length}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-green-600">✓ {studyStats.correct}</span>
                <span className="text-red-600">✗ {studyStats.incorrect}</span>
              </div>
              <button
                onClick={toggleFullscreen}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isFullscreen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  )}
                </svg>
              </button>
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="max-w-4xl mx-auto mt-3">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Card Container */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div 
            className="w-full max-w-2xl h-96"
            style={{ perspective: '1000px' }}
          >
            <div
              className={`relative w-full h-full transition-transform duration-700 transform-style-preserve-3d cursor-pointer ${
                isFlipped ? 'rotate-y-180' : ''
              }`}
              onClick={() => setIsFlipped(!isFlipped)}
              style={{
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
              }}
            >
              {/* Front */}
              <div 
                className="absolute inset-0 bg-white rounded-2xl shadow-2xl p-8 flex items-center justify-center backface-hidden"
                style={{ 
                  backfaceVisibility: 'hidden',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                }}
              >
                <div className="text-center">
                  <p className="text-white/80 text-sm mb-4">Question</p>
                  <p className="text-2xl text-white font-medium">{currentCard.front}</p>
                  <p className="text-white/60 text-sm mt-8">Tap to reveal answer</p>
                </div>
              </div>

              {/* Back */}
              <div 
                className="absolute inset-0 bg-white rounded-2xl shadow-2xl p-8 flex items-center justify-center backface-hidden"
                style={{ 
                  backfaceVisibility: 'hidden',
                  transform: 'rotateY(180deg)',
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                }}
              >
                <div className="text-center">
                  <p className="text-white/80 text-sm mb-4">Answer</p>
                  <p className="text-2xl text-white font-medium">{currentCard.back}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Answer Buttons */}
        {isFlipped && (
          <div className="bg-white/80 backdrop-blur-sm p-6 border-t">
            <div className="max-w-2xl mx-auto">
              <p className="text-center text-gray-600 mb-4">How well did you know this?</p>
              <div className="grid grid-cols-4 gap-3">
                <button
                  onClick={() => handleCardAnswer(1)}
                  className="py-3 px-4 text-white bg-gradient-to-r from-red-500 to-red-600 rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
                >
                  Again
                </button>
                <button
                  onClick={() => handleCardAnswer(2)}
                  className="py-3 px-4 text-white bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
                >
                  Hard
                </button>
                <button
                  onClick={() => handleCardAnswer(3)}
                  className="py-3 px-4 text-white bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
                >
                  Good
                </button>
                <button
                  onClick={() => handleCardAnswer(4)}
                  className="py-3 px-4 text-white bg-gradient-to-r from-green-500 to-green-600 rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
                >
                  Easy
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FlashcardsPage;
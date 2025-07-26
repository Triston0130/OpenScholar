import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Paper } from '../types';

interface TextToSpeechProps {
  text: string;
  isOpen: boolean;
  onClose: () => void;
  paper?: Paper;
  pdfContainer?: HTMLElement | null;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onWordsHighlight?: (currentWords: string[], sentenceIndex: number) => void;
  onReadingComplete?: () => void;
}

interface ReadingPosition {
  sentenceIndex: number;
  wordIndex: number;
  charIndex: number;
  pageNumber: number;
}

const TextToSpeech: React.FC<TextToSpeechProps> = ({ 
  text, 
  isOpen, 
  onClose,
  paper,
  pdfContainer,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  onWordsHighlight,
  onReadingComplete
}) => {
  // Core state
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const [volume, setVolume] = useState(1);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  
  // Reading position state
  const [readingPosition, setReadingPosition] = useState<ReadingPosition>({
    sentenceIndex: 0,
    wordIndex: 0,
    charIndex: 0,
    pageNumber: currentPage
  });
  
  // UI state
  const [isExpanded, setIsExpanded] = useState(false);
  const [showVoiceMenu, setShowVoiceMenu] = useState(false);
  const [readingMode, setReadingMode] = useState<'continuous' | 'sentence' | 'paragraph'>('continuous');
  
  // Refs
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const controlBarRef = useRef<HTMLDivElement>(null);
  
  // Parse text into structured data with advanced sentence detection
  const parseSentences = (text: string): string[] => {
    // Comprehensive list of abbreviations
    const abbreviations = [
      // Titles
      'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Rev.', 'Hon.', 'Pres.', 'Gov.', 'Gen.', 'Sen.', 'Rep.',
      // Academic
      'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'B.S.', 'M.S.', 'LL.B.', 'LL.M.', 'J.D.', 'D.D.S.', 'Ph.D', 'Ed.D.',
      // Common
      'Jr.', 'Sr.', 'Co.', 'Corp.', 'Inc.', 'Ltd.', 'LLC.', 'L.P.', 'P.C.',
      // Academic/Scientific
      'vs.', 'etc.', 'i.e.', 'e.g.', 'cf.', 'al.', 'et al.', 'ibid.', 'op. cit.', 'loc. cit.',
      'Fig.', 'fig.', 'Eq.', 'eq.', 'pp.', 'p.', 'Vol.', 'vol.', 'No.', 'no.', 'Sec.', 'Ch.',
      // Units
      'ft.', 'in.', 'cm.', 'mm.', 'km.', 'kg.', 'lb.', 'oz.', 'pt.', 'gal.',
      // Time
      'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.',
      'Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.',
      'a.m.', 'p.m.', 'A.M.', 'P.M.'
    ];
    
    // Create a map for efficient lookup
    const abbrMap = new Map();
    abbreviations.forEach((abbr, index) => {
      abbrMap.set(abbr.toLowerCase(), `__ABBR${index}__`);
    });
    
    // Replace abbreviations with placeholders
    let processedText = text;
    
    // Handle special cases like "et al." which might have variable spacing
    processedText = processedText.replace(/\bet\s+al\./gi, '__ETAL__');
    
    // Replace numbered lists (e.g., "1. ", "2. ")
    processedText = processedText.replace(/(\d+)\.\s+/g, '$1__DOT__ ');
    
    // Replace decimal numbers (e.g., "3.14")
    processedText = processedText.replace(/(\d+)\.(\d+)/g, '$1__DECIMAL__$2');
    
    // Replace abbreviations
    abbreviations.forEach((abbr, index) => {
      const escaped = abbr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b${escaped}`, 'gi');
      processedText = processedText.replace(regex, `__ABBR${index}__`);
    });
    
    // Advanced sentence splitting
    const sentences: string[] = [];
    let currentSentence = '';
    let i = 0;
    
    while (i < processedText.length) {
      currentSentence += processedText[i];
      
      // Check for sentence endings
      if ('.!?'.includes(processedText[i])) {
        // Look ahead to determine if this is really a sentence ending
        let isEndOfSentence = false;
        let j = i + 1;
        
        // Skip any additional punctuation
        while (j < processedText.length && '.!?'.includes(processedText[j])) {
          currentSentence += processedText[j];
          j++;
        }
        
        // Skip whitespace
        while (j < processedText.length && /\s/.test(processedText[j])) {
          j++;
        }
        
        if (j >= processedText.length) {
          // End of text
          isEndOfSentence = true;
        } else if (j < processedText.length) {
          // Check what follows
          const nextChar = processedText[j];
          const nextWord = processedText.substring(j).match(/^\w+/)?.[0] || '';
          
          // It's a new sentence if:
          // 1. Next character is uppercase
          // 2. Or it's a quote followed by uppercase
          // 3. Or it's a number starting a list
          const quoteChars = ['"', "'", '\u201C', '\u201D', '\u2018', '\u2019']; // straight and curly quotes
          if (/[A-Z]/.test(nextChar) || 
              (quoteChars.includes(nextChar) && j + 1 < processedText.length && /[A-Z]/.test(processedText[j + 1])) ||
              /\d/.test(nextChar)) {
            
            // Additional checks to avoid false positives
            // Don't split if it looks like a citation (e.g., "Smith (2020). found")
            const beforeDot = currentSentence.slice(-20);
            if (!/\(\d{4}\)\.?$/.test(beforeDot)) {
              isEndOfSentence = true;
            }
          }
        }
        
        if (isEndOfSentence) {
          sentences.push(currentSentence.trim());
          currentSentence = '';
          i = j - 1; // Will be incremented at loop end
        }
      }
      
      i++;
    }
    
    // Add any remaining text
    if (currentSentence.trim()) {
      sentences.push(currentSentence.trim());
    }
    
    // Restore placeholders and clean up
    return sentences.map(sentence => {
      let restored = sentence;
      
      // Restore special replacements
      restored = restored.replace(/__ETAL__/g, 'et al.');
      restored = restored.replace(/(\d+)__DOT__\s*/g, '$1. ');
      restored = restored.replace(/(\d+)__DECIMAL__(\d+)/g, '$1.$2');
      
      // Restore abbreviations
      abbreviations.forEach((abbr, index) => {
        const placeholder = `__ABBR${index}__`;
        restored = restored.replace(new RegExp(placeholder, 'g'), abbr);
      });
      
      // Clean up extra spaces
      restored = restored.replace(/\s+/g, ' ').trim();
      
      return restored;
    }).filter(s => s.length > 5); // Filter out very short fragments
  };
  
  const sentences = parseSentences(text);
  const words = text.split(/\s+/).filter(w => w.trim());
  
  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Select default voice (prefer English voices)
      if (!selectedVoice && availableVoices.length > 0) {
        const englishVoice = availableVoices.find(v => v.lang.startsWith('en'));
        setSelectedVoice(englishVoice || availableVoices[0]);
      }
    };
    
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [selectedVoice]);
  
  // Clean up speech on unmount or close
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);
  
  // Create and configure utterance
  const createUtterance = useCallback((textToSpeak: string, startOffset: number = 0) => {
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;
    
    // Track word positions for highlighting
    let currentWordIndex = 0;
    const wordsInText = textToSpeak.split(/\s+/).filter(w => w.trim());
    
    utterance.onboundary = (event) => {
      if (event.name === 'word' && onWordsHighlight) {
        // Get exact character position
        const charIndex = event.charIndex;
        
        // Find word boundaries more accurately
        let wordStart = charIndex;
        let wordEnd = charIndex;
        
        // Move back to find start of word
        while (wordStart > 0 && /\w/.test(textToSpeak[wordStart - 1])) {
          wordStart--;
        }
        
        // Move forward to find end of word
        while (wordEnd < textToSpeak.length && /\w/.test(textToSpeak[wordEnd])) {
          wordEnd++;
        }
        
        // Extract the current word
        const currentWord = textToSpeak.substring(wordStart, wordEnd);
        
        if (currentWord && currentWord.trim()) {
          // Calculate which word number this is
          const textBefore = textToSpeak.substring(0, wordStart);
          const wordsBeforeCount = textBefore.split(/\s+/).filter(w => w.trim()).length;
          currentWordIndex = wordsBeforeCount;
          
          // Ensure we don't go out of bounds
          currentWordIndex = Math.max(0, Math.min(currentWordIndex, wordsInText.length - 1));
          
          // Pass the clean word for highlighting
          onWordsHighlight([currentWord.trim()], readingPosition.sentenceIndex);
        }
      }
    };
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      currentWordIndex = 0;
      
      // Highlight first word
      if (onWordsHighlight && wordsInText.length > 0) {
        onWordsHighlight([wordsInText[0]], readingPosition.sentenceIndex);
      }
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      
      // Clear highlights
      if (onWordsHighlight) {
        onWordsHighlight([], -1);
      }
      
      // Auto-advance in continuous mode
      if (readingMode === 'continuous' && readingPosition.sentenceIndex < sentences.length - 1) {
        setReadingPosition(prev => ({
          ...prev,
          sentenceIndex: prev.sentenceIndex + 1,
          wordIndex: 0,
          charIndex: 0
        }));
        
        // Start next sentence after a brief pause
        setTimeout(() => {
          speakFromPosition(readingPosition.sentenceIndex + 1);
        }, 300);
      } else if (readingPosition.sentenceIndex >= sentences.length - 1) {
        // Reading complete
        if (onReadingComplete) {
          onReadingComplete();
        }
      }
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
    };
    
    return utterance;
  }, [selectedVoice, rate, pitch, volume, readingMode, sentences, readingPosition, onWordsHighlight, onReadingComplete, currentPage]);
  
  // Speak from a specific position
  const speakFromPosition = useCallback((sentenceIndex: number = readingPosition.sentenceIndex) => {
    window.speechSynthesis.cancel();
    
    let textToSpeak = '';
    let startOffset = 0;
    
    // Calculate character offset to current position
    for (let i = 0; i < sentenceIndex; i++) {
      startOffset += sentences[i].length + 1; // +1 for space/punctuation
    }
    
    switch (readingMode) {
      case 'sentence':
        textToSpeak = sentences[sentenceIndex] || '';
        break;
      case 'continuous':
        // Read from current sentence to end
        textToSpeak = sentences.slice(sentenceIndex).join(' ');
        break;
      default:
        textToSpeak = sentences[sentenceIndex] || '';
    }
    
    if (textToSpeak) {
      const utterance = createUtterance(textToSpeak, startOffset);
      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    }
  }, [readingPosition.sentenceIndex, sentences, readingMode, createUtterance]);
  
  // Control functions
  const play = useCallback(() => {
    if (isPaused && utteranceRef.current) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    } else {
      speakFromPosition();
    }
  }, [isPaused, speakFromPosition]);
  
  const pause = useCallback(() => {
    if (isSpeaking) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  }, [isSpeaking]);
  
  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setReadingPosition({
      sentenceIndex: 0,
      wordIndex: 0,
      charIndex: 0,
      pageNumber: currentPage
    });
    
    // Clear highlights
    if (onWordsHighlight) {
      onWordsHighlight([], -1);
    }
    if (onReadingComplete) {
      onReadingComplete();
    }
  }, [currentPage, onWordsHighlight, onReadingComplete]);
  
  const skipToSentence = useCallback((index: number) => {
    const clampedIndex = Math.max(0, Math.min(index, sentences.length - 1));
    setReadingPosition(prev => ({
      ...prev,
      sentenceIndex: clampedIndex,
      wordIndex: 0,
      charIndex: 0
    }));
    
    if (isSpeaking) {
      speakFromPosition(clampedIndex);
    }
  }, [sentences.length, isSpeaking, speakFromPosition]);
  
  const nextSentence = () => skipToSentence(readingPosition.sentenceIndex + 1);
  const previousSentence = () => skipToSentence(readingPosition.sentenceIndex - 1);
  
  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't interfere with form inputs
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (isSpeaking && !isPaused) {
            pause();
          } else {
            play();
          }
          break;
        case 'Escape':
          stop();
          onClose();
          break;
        case 'ArrowRight':
          nextSentence();
          break;
        case 'ArrowLeft':
          previousSentence();
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen, isSpeaking, isPaused, play, pause, stop, onClose, nextSentence, previousSentence]);
  
  if (!isOpen) return null;
  
  const progress = ((readingPosition.sentenceIndex + 1) / sentences.length) * 100;
  
  return (
    <>
      {/* Minimal floating control bar */}
      <div 
        ref={controlBarRef}
        className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white rounded-full shadow-2xl transition-all duration-300 z-50 ${
          isExpanded ? 'w-auto' : 'w-auto'
        }`}
      >
        <div className="flex items-center">
          {/* Main controls section */}
          <div className="flex items-center px-4 py-3">
            {/* Play/Pause Button */}
            {!isSpeaking || isPaused ? (
              <button
                onClick={play}
                className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                title="Play (Space)"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </button>
            ) : (
              <button
                onClick={pause}
                className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                title="Pause (Space)"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                </svg>
              </button>
            )}
            
            {/* Previous */}
            <button
              onClick={previousSentence}
              disabled={readingPosition.sentenceIndex === 0}
              className="p-2 hover:bg-gray-800 rounded-full transition-colors disabled:opacity-50"
              title="Previous (←)"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
              </svg>
            </button>
            
            {/* Next */}
            <button
              onClick={nextSentence}
              disabled={readingPosition.sentenceIndex >= sentences.length - 1}
              className="p-2 hover:bg-gray-800 rounded-full transition-colors disabled:opacity-50"
              title="Next (→)"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
              </svg>
            </button>
            
            {/* Progress indicator */}
            <div className="mx-4 flex items-center">
              <span className="text-xs text-gray-400 mr-2">
                {readingPosition.sentenceIndex + 1}/{sentences.length}
              </span>
              <div className="w-32 h-1 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            
            {/* Speed control */}
            <div className="flex items-center mx-2">
              <button
                onClick={() => setRate(Math.max(0.5, rate - 0.1))}
                className="p-1 hover:bg-gray-800 rounded transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <span className="text-xs mx-2 w-12 text-center">{rate.toFixed(1)}x</span>
              <button
                onClick={() => setRate(Math.min(2, rate + 0.1))}
                className="p-1 hover:bg-gray-800 rounded transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
            
            {/* Expand/Collapse button */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 hover:bg-gray-800 rounded-full transition-colors ml-2"
            >
              <svg 
                className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
          
          {/* Close button */}
          <button
            onClick={() => {
              stop();
              onClose();
            }}
            className="p-2 hover:bg-gray-800 rounded-full transition-colors mr-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Expanded settings */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-700">
            <div className="mt-3 space-y-3">
              {/* Voice selection */}
              <div className="relative">
                <button
                  onClick={() => setShowVoiceMenu(!showVoiceMenu)}
                  className="w-full text-left px-3 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-between"
                >
                  <span className="text-sm truncate">
                    {selectedVoice?.name || 'Select voice'}
                  </span>
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showVoiceMenu && (
                  <div className="absolute bottom-full mb-2 left-0 w-full max-h-48 overflow-y-auto bg-gray-800 rounded-lg shadow-xl">
                    {voices.map(voice => (
                      <button
                        key={voice.name}
                        onClick={() => {
                          setSelectedVoice(voice);
                          setShowVoiceMenu(false);
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-700 transition-colors text-sm"
                      >
                        {voice.name} ({voice.lang})
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Pitch control */}
              <div className="flex items-center">
                <span className="text-xs text-gray-400 w-12">Pitch</span>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={pitch}
                  onChange={(e) => setPitch(parseFloat(e.target.value))}
                  className="flex-1 mx-2"
                />
                <span className="text-xs w-10 text-right">{pitch.toFixed(1)}</span>
              </div>
              
              {/* Volume control */}
              <div className="flex items-center">
                <span className="text-xs text-gray-400 w-12">Vol</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                  className="flex-1 mx-2"
                />
                <span className="text-xs w-10 text-right">{Math.round(volume * 100)}%</span>
              </div>
              
              {/* Reading mode */}
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-400">Mode:</span>
                {['continuous', 'sentence'].map(mode => (
                  <button
                    key={mode}
                    onClick={() => setReadingMode(mode as any)}
                    className={`px-3 py-1 text-xs rounded-full capitalize transition-colors ${
                      readingMode === mode
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Status indicator when speaking */}
      {isSpeaking && !isPaused && (
        <div className="fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-3 text-sm shadow-lg z-50">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
          <span>Reading sentence {readingPosition.sentenceIndex + 1} of {sentences.length}</span>
        </div>
      )}
    </>
  );
};

export default TextToSpeech;
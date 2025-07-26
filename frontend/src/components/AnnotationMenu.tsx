import React, { useState } from 'react';

interface AnnotationMenuProps {
  selectedText: string;
  position: { x: number; y: number };
  onHighlight: (color: string, label: string) => void;
  onNote: (text: string, color: string) => void;
  onFlashcard: (front: string, back: string) => void;
  onClose: () => void;
}

const HIGHLIGHT_COLORS = [
  // Primary colors
  { color: '#ffeb3b', name: 'Yellow', label: 'Important' },
  { color: '#fff176', name: 'Light Yellow', label: 'Notable' },
  { color: '#f57f17', name: 'Deep Yellow', label: 'Key Point' },
  
  { color: '#ff9800', name: 'Orange', label: 'Key Concept' },
  { color: '#ffcc02', name: 'Amber', label: 'Insight' },
  { color: '#ff6f00', name: 'Deep Orange', label: 'Core Idea' },
  
  { color: '#f44336', name: 'Red', label: 'Critical' },
  { color: '#ef5350', name: 'Light Red', label: 'Warning' },
  { color: '#c62828', name: 'Dark Red', label: 'Error/Issue' },
  
  { color: '#4caf50', name: 'Green', label: 'Definition' },
  { color: '#81c784', name: 'Light Green', label: 'Positive' },
  { color: '#2e7d32', name: 'Dark Green', label: 'Fact' },
  
  { color: '#2196f3', name: 'Blue', label: 'Example' },
  { color: '#64b5f6', name: 'Light Blue', label: 'Reference' },
  { color: '#1565c0', name: 'Dark Blue', label: 'Theory' },
  
  { color: '#9c27b0', name: 'Purple', label: 'Question' },
  { color: '#ba68c8', name: 'Light Purple', label: 'Hypothesis' },
  { color: '#6a1b9a', name: 'Dark Purple', label: 'Analysis' },
  
  { color: '#e91e63', name: 'Pink', label: 'Method' },
  { color: '#f48fb1', name: 'Light Pink', label: 'Process' },
  { color: '#ad1457', name: 'Deep Pink', label: 'Technique' },
  
  { color: '#607d8b', name: 'Gray', label: 'Context' },
  { color: '#90a4ae', name: 'Light Gray', label: 'Background' },
  { color: '#37474f', name: 'Dark Gray', label: 'Summary' },
  
  // Additional colors
  { color: '#00bcd4', name: 'Cyan', label: 'Data' },
  { color: '#795548', name: 'Brown', label: 'Historical' },
  { color: '#009688', name: 'Teal', label: 'Result' },
  { color: '#ff5722', name: 'Deep Orange', label: 'Challenge' },
  { color: '#3f51b5', name: 'Indigo', label: 'Principle' },
];

const AnnotationMenu: React.FC<AnnotationMenuProps> = ({
  selectedText,
  position,
  onHighlight,
  onNote,
  onFlashcard,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'highlight' | 'note' | 'flashcard'>('highlight');
  const [selectedColor, setSelectedColor] = useState(HIGHLIGHT_COLORS[0]);
  const [customLabel, setCustomLabel] = useState('');
  const [noteText, setNoteText] = useState('');
  const [flashcardBack, setFlashcardBack] = useState('');

  const handleHighlight = () => {
    const label = customLabel.trim() || selectedColor.label;
    onHighlight(selectedColor.color, label);
    onClose();
  };

  const handleNote = () => {
    if (!noteText.trim()) return;
    onNote(noteText.trim(), selectedColor.color);
    onClose();
  };

  const handleFlashcard = () => {
    if (!flashcardBack.trim()) return;
    onFlashcard(selectedText, flashcardBack.trim());
    onClose();
  };

  const maxWidth = 280;
  const maxHeight = 350;
  
  // Calculate available space - constrain to PDF viewer area
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const pdfViewerHeight = viewportHeight - 100; // Account for header
  
  // Adjust X position to keep menu on screen
  let adjustedX = position.x - (maxWidth / 2); // Center horizontally on selection
  adjustedX = Math.max(20, Math.min(adjustedX, viewportWidth - maxWidth - 20));
  
  // Adjust Y position - prefer showing above selection to avoid PDF content overlap
  let adjustedY = position.y - maxHeight - 20; // Show above by default
  
  // If not enough space above, show below
  if (adjustedY < 100) {
    adjustedY = position.y + 60;
  }
  
  // Final bounds check - ensure it fits in viewport
  if (adjustedY + maxHeight > pdfViewerHeight) {
    adjustedY = pdfViewerHeight - maxHeight - 20;
  }
  
  // Ensure minimum top margin
  adjustedY = Math.max(100, adjustedY);

  return (
    <div
      className="annotation-menu fixed rounded-lg shadow-2xl border-2 border-gray-400 z-[9999]"
      style={{
        left: `${adjustedX}px`,
        top: `${adjustedY}px`,
        width: `${maxWidth}px`,
        maxHeight: `${maxHeight}px`,
        backgroundColor: '#ffffff',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        flexDirection: 'column',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header with selected text preview */}
      <div className="p-2 border-b border-gray-200 bg-gray-50 rounded-t-lg flex-shrink-0" style={{ backgroundColor: '#f9fafb' }}>
        <div className="flex items-start justify-between">
          <div className="flex-1 mr-2">
            <p className="text-xs font-medium text-gray-700 mb-1">Selected Text:</p>
            <p className="text-xs text-gray-600 line-clamp-2 p-1.5 rounded text-[10px] leading-tight" style={{ backgroundColor: '#ffffff' }}>
              "{selectedText.length > 60 ? selectedText.substring(0, 60) + '...' : selectedText}"
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-200 rounded-full transition-colors flex-shrink-0"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b flex-shrink-0">
        {[
          { key: 'highlight', label: 'Highlight', icon: '🖍️' },
          { key: 'note', label: 'Note', icon: '📝' },
          { key: 'flashcard', label: 'Flashcard', icon: '🎴' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex-1 px-2 py-1.5 text-xs font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-3 overflow-y-auto flex-1" style={{ backgroundColor: '#ffffff' }}>
        {activeTab === 'highlight' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Choose Color & Category:
              </label>
              <div className="grid grid-cols-3 gap-1 max-h-40 overflow-y-auto">
                {HIGHLIGHT_COLORS.map((colorOption) => (
                  <button
                    key={colorOption.color}
                    onClick={() => setSelectedColor(colorOption)}
                    className={`flex items-center p-1.5 rounded-md border transition-all text-left ${
                      selectedColor.color === colorOption.color
                        ? 'border-gray-400 bg-gray-50 ring-2 ring-blue-500'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    title={`${colorOption.name} - ${colorOption.label}`}
                  >
                    <div
                      className="w-3 h-3 rounded-full mr-1.5 border border-gray-300 flex-shrink-0"
                      style={{ backgroundColor: colorOption.color }}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-[10px] font-medium text-gray-900 truncate">
                        {colorOption.name}
                      </div>
                      <div className="text-[9px] text-gray-500 truncate">
                        {colorOption.label}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Custom Label (optional):
              </label>
              <input
                type="text"
                value={customLabel}
                onChange={(e) => setCustomLabel(e.target.value)}
                placeholder={`Default: "${selectedColor.label}"`}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleHighlight}
              className="w-full py-2 px-4 bg-yellow-500 hover:bg-yellow-600 text-white font-medium rounded-md transition-colors"
            >
              Create Highlight
            </button>
          </div>
        )}

        {activeTab === 'note' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Note Color:
              </label>
              <div className="grid grid-cols-4 gap-1 max-h-20 overflow-y-auto">
                {HIGHLIGHT_COLORS.slice(0, 12).map((colorOption) => (
                  <button
                    key={colorOption.color}
                    onClick={() => setSelectedColor(colorOption)}
                    className={`flex items-center px-2 py-1 rounded border text-xs ${
                      selectedColor.color === colorOption.color
                        ? 'border-gray-400 bg-gray-50 ring-2 ring-blue-500'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    title={colorOption.name}
                  >
                    <div
                      className="w-3 h-3 rounded-full mr-1"
                      style={{ backgroundColor: colorOption.color }}
                    />
                    <span className="truncate text-[10px]">{colorOption.name.split(' ')[0]}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Note:
              </label>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add your thoughts, questions, or insights..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
              />
            </div>

            <button
              onClick={handleNote}
              disabled={!noteText.trim()}
              className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
            >
              Add Note
            </button>
          </div>
        )}

        {activeTab === 'flashcard' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Front (Question):
              </label>
              <div className="px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm">
                {selectedText}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Back (Answer):
              </label>
              <textarea
                value={flashcardBack}
                onChange={(e) => setFlashcardBack(e.target.value)}
                placeholder="Enter the answer or explanation..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={3}
              />
            </div>

            <button
              onClick={handleFlashcard}
              disabled={!flashcardBack.trim()}
              className="w-full py-2 px-4 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
            >
              Create Flashcard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnnotationMenu;
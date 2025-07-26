import React, { useState } from 'react';

interface Color {
  hex: string;
  name: string;
}

interface ColorPickerProps {
  selectedColor: string;
  selectedName: string;
  onColorSelect: (color: string, name: string) => void;
  onClose: () => void;
}

const ColorPicker: React.FC<ColorPickerProps> = ({ selectedColor, selectedName, onColorSelect, onClose }) => {
  const [customName, setCustomName] = useState(selectedName);
  const [customColor, setCustomColor] = useState(selectedColor);

  const presetColors: Color[] = [
    { hex: '#ffeb3b', name: 'Yellow' },
    { hex: '#4ade80', name: 'Green' },
    { hex: '#60a5fa', name: 'Blue' },
    { hex: '#f87171', name: 'Red' },
    { hex: '#c084fc', name: 'Purple' },
    { hex: '#fb923c', name: 'Orange' },
    { hex: '#a78bfa', name: 'Violet' },
    { hex: '#fbbf24', name: 'Amber' },
    { hex: '#34d399', name: 'Emerald' },
    { hex: '#f472b6', name: 'Pink' },
  ];

  const handleSubmit = () => {
    onColorSelect(customColor, customName || 'Custom');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-semibold mb-4">Choose Highlight Color</h3>
        
        {/* Preset colors */}
        <div className="grid grid-cols-5 gap-3 mb-6">
          {presetColors.map((color) => (
            <button
              key={color.hex}
              onClick={() => {
                setCustomColor(color.hex);
                setCustomName(color.name);
              }}
              className={`w-12 h-12 rounded-lg border-2 transition-all ${
                customColor === color.hex ? 'border-gray-800 scale-110' : 'border-gray-300'
              }`}
              style={{ backgroundColor: color.hex }}
              title={color.name}
            />
          ))}
        </div>

        {/* Custom color input */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom Color
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={customColor}
                onChange={(e) => setCustomColor(e.target.value)}
                className="h-10 w-20"
              />
              <input
                type="text"
                value={customColor}
                onChange={(e) => setCustomColor(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                placeholder="#000000"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Color Name (for organization)
            </label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g., Important, Definition, Question"
            />
          </div>
        </div>

        {/* Preview */}
        <div className="mt-6 p-3 rounded-lg" style={{ backgroundColor: customColor + '40' }}>
          <p className="text-sm">
            Preview: This is how your highlight will look
          </p>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Apply Color
          </button>
        </div>
      </div>
    </div>
  );
};

export default ColorPicker;
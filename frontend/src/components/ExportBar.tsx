import React, { useState } from 'react';
import { Paper } from '../types';

interface ExportBarProps {
  papers: Paper[];
  onExport: (format: 'csv' | 'json' | 'bib') => void;
  isExporting: boolean;
}

const ExportBar: React.FC<ExportBarProps> = ({ papers, onExport, isExporting }) => {
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'json' | 'bib'>('bib');

  const handleExport = () => {
    onExport(selectedFormat);
  };

  const getFormatDescription = (format: string) => {
    switch (format) {
      case 'bib':
        return 'BibTeX - Citation managers (Zotero, Mendeley)';
      case 'csv':
        return 'CSV - Spreadsheets (Excel, Google Sheets)';
      case 'json':
        return 'JSON - Raw structured data';
      default:
        return '';
    }
  };

  if (papers.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Export Results
          </h3>
          <p className="text-sm text-gray-600">
            Export {papers.length} paper{papers.length !== 1 ? 's' : ''} in your preferred format
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          {/* Format Selection */}
          <div className="min-w-0 flex-1 sm:min-w-64">
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value as 'csv' | 'json' | 'bib')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            >
              <option value="bib">BibTeX (.bib)</option>
              <option value="csv">CSV (.csv)</option>
              <option value="json">JSON (.json)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {getFormatDescription(selectedFormat)}
            </p>
          </div>

          {/* Export Button */}
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="px-6 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 focus:ring-4 focus:ring-green-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
          >
            {isExporting ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Exporting...
              </div>
            ) : (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export {selectedFormat.toUpperCase()}
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportBar;
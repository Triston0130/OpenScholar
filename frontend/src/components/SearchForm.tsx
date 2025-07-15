import React, { useState } from 'react';
import { SearchRequest } from '../types';

interface SearchFormProps {
  onSearch: (searchRequest: SearchRequest) => void;
  isLoading: boolean;
}

const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const [yearStart, setYearStart] = useState<number>(2000);
  const [yearEnd, setYearEnd] = useState<number>(new Date().getFullYear());
  const [discipline, setDiscipline] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [publicationType, setPublicationType] = useState('');
  const [studyType, setStudyType] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const searchRequest: SearchRequest = {
      query: query.trim(),
      year_start: yearStart,
      year_end: yearEnd,
      discipline: discipline || undefined,
      education_level: educationLevel || undefined,
      publication_type: publicationType || undefined,
      study_type: studyType || undefined,
    };

    onSearch(searchRequest);
  };

  const currentYear = new Date().getFullYear();

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Search Query */}
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Search Keywords
          </label>
          <input
            type="text"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter keywords (e.g., child nutrition, language development)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            required
          />
        </div>

        {/* Filters Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Year Range */}
          <div>
            <label htmlFor="yearStart" className="block text-sm font-medium text-gray-700 mb-2">
              Start Year
            </label>
            <input
              type="number"
              id="yearStart"
              value={yearStart}
              onChange={(e) => setYearStart(parseInt(e.target.value))}
              min="1900"
              max={currentYear}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="yearEnd" className="block text-sm font-medium text-gray-700 mb-2">
              End Year
            </label>
            <input
              type="number"
              id="yearEnd"
              value={yearEnd}
              onChange={(e) => setYearEnd(parseInt(e.target.value))}
              min="1900"
              max={currentYear}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Discipline */}
          <div>
            <label htmlFor="discipline" className="block text-sm font-medium text-gray-700 mb-2">
              Discipline
            </label>
            <select
              id="discipline"
              value={discipline}
              onChange={(e) => setDiscipline(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Disciplines</option>
              <option value="education">Education</option>
              <option value="psychology">Psychology</option>
              <option value="child development">Child Development</option>
              <option value="early childhood">Early Childhood</option>
            </select>
          </div>

          {/* Education Level */}
          <div>
            <label htmlFor="educationLevel" className="block text-sm font-medium text-gray-700 mb-2">
              Education Level
            </label>
            <select
              id="educationLevel"
              value={educationLevel}
              onChange={(e) => setEducationLevel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Levels</option>
              <option value="early childhood">Early Childhood</option>
              <option value="k-12">K-12</option>
              <option value="higher ed">Higher Education</option>
            </select>
          </div>
        </div>

        {/* Additional Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Publication Type */}
          <div>
            <label htmlFor="publicationType" className="block text-sm font-medium text-gray-700 mb-2">
              Publication Type
            </label>
            <select
              id="publicationType"
              value={publicationType}
              onChange={(e) => setPublicationType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="journal">Journal Article</option>
              <option value="conference">Conference Paper</option>
              <option value="book">Book/Chapter</option>
              <option value="thesis">Thesis/Dissertation</option>
            </select>
          </div>

          {/* Study Type */}
          <div>
            <label htmlFor="studyType" className="block text-sm font-medium text-gray-700 mb-2">
              Study Type
            </label>
            <select
              id="studyType"
              value={studyType}
              onChange={(e) => setStudyType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Studies</option>
              <option value="experimental">Experimental</option>
              <option value="survey">Survey/Questionnaire</option>
              <option value="review">Literature Review</option>
              <option value="meta-analysis">Meta-Analysis</option>
              <option value="case study">Case Study</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="w-full md:w-auto px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:ring-4 focus:ring-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </div>
            ) : (
              'Search Papers'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchForm;
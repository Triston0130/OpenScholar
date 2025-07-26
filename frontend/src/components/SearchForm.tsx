import React, { useState } from 'react';
import { SearchRequest } from '../types';
import SearchTipsModal from './SearchTipsModal';
import ApiKeyModal from './ApiKeyModal';
import { hasApiKey } from '../utils/apiKeys';

interface Source {
  id: string;
  name: string;
  description: string;
  requiresApiKey?: boolean;
}

interface SearchFormProps {
  onSearch: (searchRequest: SearchRequest) => void;
  isLoading: boolean;
}

const sourceGroups = [
  {
    name: 'Education & General',
    sources: [
      { id: 'ERIC', name: 'ERIC', description: 'Education Resources' },
      { id: 'OpenAlex', name: 'OpenAlex', description: '200M+ papers' },
      { id: 'Crossref', name: 'Crossref', description: 'DOI database' },
      { id: 'DOAJ', name: 'DOAJ', description: 'Open Access Journals' },
    ]
  },
  {
    name: 'Life Sciences',
    sources: [
      { id: 'PubMed Central', name: 'PMC', description: 'Open Access' },
      { id: 'PubMed', name: 'PubMed', description: 'Citations' },
      { id: 'Europe PMC', name: 'Europe PMC', description: 'Full Text' },
    ]
  },
  {
    name: 'STEM & AI',
    sources: [
      { id: 'arXiv', name: 'arXiv', description: 'Preprints' },
      { id: 'Semantic Scholar', name: 'S2', description: 'AI-powered' },
      { id: 'CORE', name: 'CORE', description: 'Open Access', requiresApiKey: true },
    ]
  },
  {
    name: 'Books & OER',
    sources: [
      { id: 'DOAB', name: 'DOAB', description: 'Open Access Books' },
      { id: 'Open Textbook Library', name: 'Open Textbook', description: '📚 CC Textbooks' },
      { id: 'Pressbooks', name: 'Pressbooks', description: '📖 OER Networks' },
      { id: 'LibreTexts', name: 'LibreTexts', description: '📗 OER Textbooks' },
      { id: 'MERLOT', name: 'MERLOT', description: '⭐ Peer-reviewed OER', requiresApiKey: true },
      { id: 'OER Commons', name: 'OER Commons', description: '🎓 Ed Resources', requiresApiKey: true },
      { id: 'MIT OpenCourseWare', name: 'MIT OCW', description: '🏛️ Course Materials', requiresApiKey: true },
      { id: 'Project Gutenberg', name: 'Gutenberg', description: 'Public Domain' },
      { id: 'Internet Archive', name: 'Archive.org', description: 'Digital Library' },
      { id: 'Open Library', name: 'OpenLibrary', description: 'Book Metadata' },
      { id: 'OpenStax', name: 'OpenStax', description: 'Free Textbooks' },
      { id: 'OAPEN', name: 'OAPEN', description: 'Academic Books' },
      { id: 'Google Books', name: 'Google Books', description: 'Full Access Books' },
      { id: 'BHL', name: 'BHL', description: 'Biodiversity', requiresApiKey: true },
      { id: 'NLM Bookshelf', name: 'NLM Books', description: 'Medical Texts' },
    ]
  },
  {
    name: 'Articles',
    sources: [
      { id: 'PLOS', name: 'PLOS', description: 'Open Science' },
      { id: 'BioMed Central', name: 'BMC', description: 'Biomedical', requiresApiKey: true },
      { id: 'BASE', name: 'BASE', description: 'Academic Search', requiresApiKey: true },
      { id: 'Unpaywall', name: 'Unpaywall', description: 'Free Versions' },
      { id: 'Google Search', name: 'Google Search', description: '🔍 PDFs Only', requiresApiKey: true },
    ]
  }
];

const availableSources = sourceGroups.flatMap(group => group.sources);

const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const [yearStart, setYearStart] = useState<number>(2000);
  const [yearEnd, setYearEnd] = useState<number>(new Date().getFullYear());
  const [discipline, setDiscipline] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [publicationType, setPublicationType] = useState('');
  const [studyType, setStudyType] = useState('');
  const [minCitations, setMinCitations] = useState<string>('');
  const [selectedSources, setSelectedSources] = useState<string[]>(
    availableSources.filter(s => !s.requiresApiKey || hasApiKey(s.id)).map(s => s.id)
  );
  const [requireAuthors, setRequireAuthors] = useState(true);
  const [showSearchTips, setShowSearchTips] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [apiKeySourceId, setApiKeySourceId] = useState<string | undefined>(undefined);
  const [showSources, setShowSources] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (selectedSources.length === 0) {
      alert('Please select at least one source to search.');
      return;
    }

    const searchRequest: SearchRequest = {
      query: query.trim(),
      year_start: yearStart,
      year_end: yearEnd,
      discipline: discipline || undefined,
      education_level: educationLevel || undefined,
      publication_type: publicationType || undefined,
      study_type: studyType || undefined,
      min_citations: minCitations ? parseInt(minCitations) : undefined,
      sources: selectedSources,
      require_authors: requireAuthors,
    };

    onSearch(searchRequest);
  };

  const handleSourceToggle = (sourceId: string) => {
    setSelectedSources(prev => 
      prev.includes(sourceId) 
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  const handleSelectAllSources = () => {
    setSelectedSources(availableSources.filter(s => !s.requiresApiKey || hasApiKey(s.id)).map(s => s.id));
  };

  const handleDeselectAllSources = () => {
    setSelectedSources([]);
  };

  const currentYear = new Date().getFullYear();
  
  // Calculate actual available sources (not greyed out)
  const actualAvailableSources = availableSources.filter(s => !s.requiresApiKey || hasApiKey(s.id));

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Search Query */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="query" className="block text-sm font-medium text-gray-700">
              Search Keywords
            </label>
            <button
              type="button"
              onClick={() => setShowSearchTips(true)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Search tips
            </button>
          </div>
          <input
            type="text"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter keywords (e.g., child nutrition, language development)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            required
          />
          
          {/* Popular Search Examples */}
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-2">Popular searches:</p>
            <div className="flex flex-wrap gap-2">
              {["childhood obesity", "reading comprehension", "STEM education", "machine learning", "neural networks", "quantum computing", "social emotional learning", "mindfulness in schools", "digital literacy"].map((example, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => setQuery(example)}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-blue-100 hover:text-blue-700 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Sources Selection */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <button
              type="button"
              onClick={() => setShowSources(!showSources)}
              className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <svg
                className={`w-4 h-4 mr-2 transform transition-transform ${
                  showSources ? 'rotate-90' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
              Sources to Search ({selectedSources.length}/{availableSources.length} selected)
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleSelectAllSources}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Select All
              </button>
              <span className="text-gray-300">•</span>
              <button
                type="button"
                onClick={handleDeselectAllSources}
                className="text-xs text-gray-600 hover:text-gray-700 font-medium"
              >
                Deselect All
              </button>
            </div>
          </div>
          {showSources && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {sourceGroups.map((group) => (
              <div key={group.name} className="border border-gray-200 rounded-lg p-3">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">{group.name}</h4>
                <div className="space-y-1">
                  {group.sources.map((source) => (
                    <label
                      key={source.id}
                      className={`flex items-center p-1.5 rounded cursor-pointer transition-colors text-sm relative ${
                        source.requiresApiKey && !hasApiKey(source.id)
                          ? 'bg-gray-100 text-gray-500 opacity-75' 
                          : selectedSources.includes(source.id)
                          ? 'bg-blue-50 text-blue-700'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedSources.includes(source.id)}
                        onChange={() => handleSourceToggle(source.id)}
                        disabled={source.requiresApiKey && !hasApiKey(source.id)}
                        className={`h-3.5 w-3.5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded ${
                          source.requiresApiKey && !hasApiKey(source.id) ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      />
                      <span className={`ml-2 font-medium ${source.requiresApiKey ? 'text-gray-400' : ''}`}>
                        {source.name}
                      </span>
                      <span className={`ml-1 text-xs ${source.requiresApiKey ? 'text-gray-400' : 'text-gray-500'}`}>
                        - {source.description}
                      </span>
                      {source.requiresApiKey && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setApiKeySourceId(source.id);
                            setShowApiKeyModal(true);
                          }}
                          className="ml-auto p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          title={hasApiKey(source.id) ? `${source.name} API key configured` : `Configure ${source.name} API key`}
                        >
                          {hasApiKey(source.id) ? (
                            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                            </svg>
                          )}
                        </button>
                      )}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            </div>
          )}
          {selectedSources.length === 0 && (
            <p className="text-sm text-red-600 mt-2">
              Please select at least one source to search.
            </p>
          )}
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
              <option value="computer science">Computer Science</option>
              <option value="mathematics">Mathematics</option>
              <option value="physics">Physics</option>
              <option value="biology">Biology</option>
              <option value="statistics">Statistics</option>
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

          {/* Minimum Citations Filter */}
          <div>
            <label htmlFor="minCitations" className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Citations
            </label>
            <select
              id="minCitations"
              value={minCitations}
              onChange={(e) => setMinCitations(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Any Citation Count</option>
              <option value="1">1+ citations</option>
              <option value="5">5+ citations</option>
              <option value="10">10+ citations (Well-cited)</option>
              <option value="25">25+ citations (Popular)</option>
              <option value="50">50+ citations (Influential)</option>
              <option value="100">100+ citations (Highly influential)</option>
              <option value="250">250+ citations (Landmark)</option>
            </select>
          </div>

          {/* Quality Filters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Quality Filters
            </label>
            <div className="space-y-2">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={requireAuthors}
                  onChange={(e) => setRequireAuthors(e.target.checked)}
                  className="mt-0.5 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-2">
                  <div className="text-sm text-gray-900">
                    Require named authors
                  </div>
                  <div className="text-xs text-gray-500">
                    Excludes conference abstracts and incomplete entries
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-center pt-4">
          <button
            type="submit"
            disabled={isLoading || !query.trim() || selectedSources.length === 0}
            className="px-12 py-4 bg-blue-600 text-white font-semibold text-lg rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching research papers...
              </div>
            ) : (
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search Academic Papers
              </div>
            )}
          </button>
        </div>
      </form>

      {/* Search Tips Modal */}
      <SearchTipsModal 
        isOpen={showSearchTips}
        onClose={() => setShowSearchTips(false)}
      />

      {/* API Key Configuration Modal */}
      <ApiKeyModal
        isOpen={showApiKeyModal}
        sourceId={apiKeySourceId}
        onClose={() => {
          setShowApiKeyModal(false);
          setApiKeySourceId(undefined);
        }}
      />
    </div>
  );
};

export default SearchForm;
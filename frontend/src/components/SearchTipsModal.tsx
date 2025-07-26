import React from 'react';

interface SearchTipsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SearchTipsModal: React.FC<SearchTipsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-xl font-semibold text-gray-900">Search Tips for OpenScholar</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left Column - How Search Works */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4">How OpenScholar Search Works</h4>
              
              <div className="space-y-4">
                <div>
                  <h5 className="font-medium text-gray-800 mb-2">🔍 Basic Keyword Search</h5>
                  <div className="bg-blue-50 p-3 rounded-lg text-sm">
                    <p className="text-blue-700 mb-1">OpenScholar searches for your keywords in:</p>
                    <p className="text-blue-700">• Paper titles</p>
                    <p className="text-blue-700">• Abstracts (when available)</p>
                    <p className="text-blue-700">• Journal names</p>
                    <p className="text-blue-600 mt-2 font-medium">Multiple words = ANY match (OR search)</p>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-800 mb-2">✨ Automatic Query Enhancement</h5>
                  <div className="bg-green-50 p-3 rounded-lg text-sm">
                    <p className="text-green-700 mb-1">The system automatically expands:</p>
                    <p className="text-green-700">• ML → machine learning</p>
                    <p className="text-green-700">• AI → artificial intelligence</p>
                    <p className="text-green-700">• CBT → cognitive behavioral therapy</p>
                    <p className="text-green-700">• And many other common abbreviations</p>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-800 mb-2">📊 Result Ranking</h5>
                  <div className="bg-purple-50 p-3 rounded-lg text-sm">
                    <p className="text-purple-700 mb-1">Results are ranked by:</p>
                    <p className="text-purple-700">• Keyword relevance (BM25 scoring)</p>
                    <p className="text-purple-700">• Citation count (higher = better)</p>
                    <p className="text-purple-700">• Title matches (2x boost)</p>
                    <p className="text-purple-700">• Recency (slight boost for 2020+)</p>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-800 mb-2">⚡ Search Speed</h5>
                  <div className="bg-yellow-50 p-3 rounded-lg text-sm">
                    <p className="text-yellow-700">• Searches 20+ databases simultaneously</p>
                    <p className="text-yellow-700">• Takes 30-60 seconds for complete results</p>
                    <p className="text-yellow-700">• Results appear as they come in</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Filters That Work */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Filters That Actually Work</h4>
              
              <div className="space-y-4">
                <div>
                  <h5 className="font-medium text-gray-800 mb-2">✅ Working Filters</h5>
                  <div className="bg-green-50 p-3 rounded-lg text-sm">
                    <p className="text-green-700 font-medium mb-1">These filters work as expected:</p>
                    <p className="text-green-700">• <strong>Year Range:</strong> Filters by publication year</p>
                    <p className="text-green-700">• <strong>Min Citations:</strong> Only shows papers with X+ citations</p>
                    <p className="text-green-700">• <strong>Sources:</strong> Select which databases to search</p>
                    <p className="text-green-700">• <strong>Require Authors:</strong> Excludes anonymous papers</p>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-800 mb-2">⚠️ Filters That Add Keywords</h5>
                  <div className="bg-amber-50 p-3 rounded-lg text-sm">
                    <p className="text-amber-700 font-medium mb-1">These filters enhance your search with related terms:</p>
                    <p className="text-amber-700">• <strong>Discipline:</strong> Adds field-specific keywords</p>
                    <p className="text-amber-700">• <strong>Education Level:</strong> Adds age/grade keywords</p>
                    <p className="text-amber-700">• <strong>Publication Type:</strong> Adds format keywords</p>
                    <p className="text-amber-700">• <strong>Study Type:</strong> Adds methodology keywords</p>
                    <p className="text-amber-600 mt-2 text-xs">They expand your search to find more relevant results</p>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-800 mb-2">📚 Source Selection Tips</h5>
                  <div className="bg-blue-50 p-3 rounded-lg text-sm">
                    <p className="text-blue-700">• <strong>Papers:</strong> arXiv, PubMed, Semantic Scholar</p>
                    <p className="text-blue-700">• <strong>Books:</strong> DOAB, Open Library, Google Books</p>
                    <p className="text-blue-700">• <strong>Education:</strong> ERIC</p>
                    <p className="text-blue-700">• <strong>Free versions:</strong> Unpaywall, PMC</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filter Examples */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">How Filters Expand Your Search</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="font-medium text-gray-900 mb-2">Publication Type Examples:</p>
                <p className="text-gray-700">• <strong>Journal Article:</strong> adds "journal, article, peer-reviewed"</p>
                <p className="text-gray-700">• <strong>Conference Paper:</strong> adds "conference, proceedings, symposium"</p>
                <p className="text-gray-700">• <strong>Book:</strong> adds "book, textbook, monograph, chapter"</p>
                <p className="text-gray-700">• <strong>Thesis:</strong> adds "thesis, dissertation, doctoral"</p>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="font-medium text-gray-900 mb-2">Study Type Examples:</p>
                <p className="text-gray-700">• <strong>Experimental:</strong> adds "experiment, randomized, RCT"</p>
                <p className="text-gray-700">• <strong>Survey:</strong> adds "survey, questionnaire, cross-sectional"</p>
                <p className="text-gray-700">• <strong>Review:</strong> adds "review, systematic review, synthesis"</p>
                <p className="text-gray-700">• <strong>Meta-analysis:</strong> adds "meta-analysis, pooled analysis"</p>
              </div>
            </div>
          </div>

          {/* Bottom Section - Effective Search Strategies */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Effective Search Strategies</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900 mb-2">🎯 For Best Results</h5>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• <strong>Use 2-4 keywords:</strong> "machine learning education"</li>
                  <li>• <strong>Be specific:</strong> "reading comprehension elementary"</li>
                  <li>• <strong>Include the context:</strong> "anxiety treatment children"</li>
                  <li>• <strong>Try variations:</strong> If results are low, try synonyms</li>
                </ul>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900 mb-2">📈 Finding Quality Papers</h5>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• <strong>Set min citations to 10+</strong> for recognized work</li>
                  <li>• <strong>Use year 2015+</strong> for recent research</li>
                  <li>• <strong>Select 5-10 relevant sources</strong> (not all 23)</li>
                  <li>• <strong>Check multiple result pages</strong> - best isn't always first</li>
                </ul>
              </div>
            </div>
          </div>

          {/* What Doesn't Work */}
          <div className="mt-6 p-4 bg-gray-100 rounded-lg">
            <h5 className="font-medium text-gray-900 mb-2">🚫 What Doesn't Work (Yet)</h5>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Quoted phrases don't guarantee exact matches (despite being parsed)</li>
              <li>• Boolean operators (AND, OR, NOT) work inconsistently across sources</li>
              <li>• Field searches like "author:smith" are ignored</li>
              <li>• + and - operators have limited effect</li>
              <li>• No way to search by DOI or specific identifiers</li>
            </ul>
          </div>

          {/* Understanding Results */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h5 className="font-medium text-gray-900 mb-2">📖 Understanding Your Results</h5>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Each source searches for up to 75 papers</li>
              <li>• All results are combined and ranked by relevance</li>
              <li>• Shows 20 papers per page (can change to 10, 30, or 50)</li>
              <li>• Use pagination to see all results</li>
              <li>• Papers without abstracts are still included</li>
              <li>• Duplicates are removed automatically</li>
              <li>• Total results shown at bottom (often 100s-1000s)</li>
            </ul>
          </div>

        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Got it, thanks!
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchTipsModal;
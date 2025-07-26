import React, { useState } from 'react';

interface RankingExplanation {
  score: number;
  primary_factors: string[];
  key_features: {
    relevance_score: number;
    citation_impact: number;
    source_quality: number;
    query_match: number;
    recency: string;
  };
}

interface SearchMetrics {
  query: string;
  query_intent: {
    type: string;
    specificity: string;
    domain_indicators: string[];
  };
  timing: {
    total_seconds: number;
    per_result_ms: number;
  };
  result_stats: {
    total_retrieved: number;
    total_curated: number;
    avg_score: number;
    score_range: [number, number];
  };
  source_distribution: Record<string, {
    retrieved: number;
    in_final: number;
    precision: number;
  }>;
  temporal_distribution: Record<string, number>;
  citation_stats: {
    mean: number;
    median: number;
    highly_cited: number;
    uncited: number;
  };
  diversity_metrics: {
    unique_sources: number;
    unique_authors: number;
    year_span: number;
  };
  quality_indicators: {
    peer_reviewed: number;
    recent_5_years: number;
    has_citations: number;
  };
}

interface SearchRelevanceInfoProps {
  totalResults: number;
  sortBy: string;
  searchQuery: string;
  searchMetrics?: SearchMetrics;
  useAdvancedRanking?: boolean;
}

const SearchRelevanceInfo: React.FC<SearchRelevanceInfoProps> = ({ 
  totalResults, 
  sortBy, 
  searchQuery,
  searchMetrics,
  useAdvancedRanking = false
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-sm font-medium text-blue-900">
              {useAdvancedRanking ? 'Advanced AI-Powered Ranking' : 'Search Results Ranked by'} {sortBy === 'relevance' ? 'Relevance' : sortBy === 'newest' ? 'Newest First' : sortBy === 'oldest' ? 'Oldest First' : 'Most Cited'}
            </h3>
          </div>
          <p className="mt-1 text-sm text-blue-700">
            {useAdvancedRanking ? (
              <>
                Results ranked using state-of-the-art learning-to-rank with 40+ features including 
                semantic similarity, citation impact, temporal relevance, and source reputation.
                {searchMetrics && ` Processed in ${searchMetrics.timing.total_seconds}s.`}
              </>
            ) : sortBy === 'relevance' ? (
              <>
                Results are ranked using our BM25 algorithm that considers keyword matching in titles and abstracts, 
                plus boosts for recent papers, high citation counts, and exact phrase matches.
              </>
            ) : (
              `Papers sorted by ${sortBy === 'newest' ? 'publication date (newest first)' : 
                                 sortBy === 'oldest' ? 'publication date (oldest first)' : 
                                 'citation count (most cited first)'}.`
            )}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {searchMetrics && (
            <button
              onClick={() => setShowMetrics(!showMetrics)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium whitespace-nowrap"
            >
              {showMetrics ? 'Hide metrics' : 'View metrics'}
            </button>
          )}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium whitespace-nowrap"
          >
            {showDetails ? 'Hide details' : 'How it works'}
          </button>
        </div>
      </div>

      {showMetrics && searchMetrics && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <h4 className="font-medium text-blue-900 mb-3">Search Analytics</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-3">
              <h5 className="font-medium text-blue-800 mb-2">Performance</h5>
              <ul className="space-y-1 text-blue-700">
                <li>Total retrieved: {searchMetrics.result_stats.total_retrieved.toLocaleString()}</li>
                <li>Final results: {searchMetrics.result_stats.total_curated.toLocaleString()}</li>
                <li>Avg relevance: {(searchMetrics.result_stats.avg_score * 100).toFixed(1)}%</li>
                <li>Processing: {searchMetrics.timing.total_seconds}s</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg p-3">
              <h5 className="font-medium text-blue-800 mb-2">Quality Metrics</h5>
              <ul className="space-y-1 text-blue-700">
                <li>Peer reviewed: {searchMetrics.quality_indicators.peer_reviewed}</li>
                <li>Recent (≤5yr): {searchMetrics.quality_indicators.recent_5_years}</li>
                <li>Avg citations: {searchMetrics.citation_stats.mean.toFixed(1)}</li>
                <li>Highly cited: {searchMetrics.citation_stats.highly_cited}</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg p-3">
              <h5 className="font-medium text-blue-800 mb-2">Diversity</h5>
              <ul className="space-y-1 text-blue-700">
                <li>Sources used: {searchMetrics.diversity_metrics.unique_sources}</li>
                <li>Unique authors: {searchMetrics.diversity_metrics.unique_authors}</li>
                <li>Year span: {searchMetrics.diversity_metrics.year_span} years</li>
                <li>Query type: {searchMetrics.query_intent.type}</li>
              </ul>
            </div>
          </div>
          
          {Object.keys(searchMetrics.source_distribution).length > 0 && (
            <div className="mt-3 bg-white rounded-lg p-3">
              <h5 className="font-medium text-blue-800 mb-2">Top Sources</h5>
              <div className="flex flex-wrap gap-2">
                {Object.entries(searchMetrics.source_distribution)
                  .sort((a, b) => b[1].in_final - a[1].in_final)
                  .slice(0, 8)
                  .map(([source, stats]) => (
                    <span key={source} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {source}: {stats.in_final}
                    </span>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showDetails && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          {useAdvancedRanking ? (
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-blue-900 mb-3">Advanced Ranking Features</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="bg-white rounded-lg p-3">
                    <h5 className="font-medium text-blue-800 mb-2">Text Relevance (40%)</h5>
                    <ul className="space-y-1 text-blue-700">
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>BM25 scoring:</strong> Field-weighted keyword matching</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Phrase matching:</strong> Bigram/trigram detection</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Query coverage:</strong> Term completeness analysis</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Semantic similarity:</strong> Conceptual matching</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3">
                    <h5 className="font-medium text-blue-800 mb-2">Academic Impact (30%)</h5>
                    <ul className="space-y-1 text-blue-700">
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Citation velocity:</strong> Citations per year</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Citation percentile:</strong> Field-normalized impact</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Influential citations:</strong> High-impact references</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>H-index estimate:</strong> Author reputation</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3">
                    <h5 className="font-medium text-blue-800 mb-2">Source Quality (20%)</h5>
                    <ul className="space-y-1 text-blue-700">
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Source reputation:</strong> Database quality scores</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Peer review status:</strong> Editorial verification</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Journal impact:</strong> Venue prestige factor</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Domain expertise:</strong> Source specialization</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3">
                    <h5 className="font-medium text-blue-800 mb-2">Temporal & Diversity (10%)</h5>
                    <ul className="space-y-1 text-blue-700">
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Temporal relevance:</strong> Recency vs impact balance</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Result diversity:</strong> Topic coverage optimization</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Query intent:</strong> Search type detection</span>
                      </li>
                      <li className="flex items-start">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2 mt-0.5"></span>
                        <span><strong>Novelty scoring:</strong> Unique perspectives</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="bg-blue-100 rounded-lg p-3">
                <h5 className="font-medium text-blue-900 mb-2">Multi-Stage Pipeline</h5>
                <ol className="text-sm text-blue-700 space-y-1">
                  <li>1. <strong>Source Enhancement:</strong> Apply database-specific optimizations</li>
                  <li>2. <strong>Feature Extraction:</strong> Compute 40+ ranking features per paper</li>
                  <li>3. <strong>Score Normalization:</strong> Cross-source calibration and scaling</li>
                  <li>4. <strong>ML Ranking:</strong> Gradient boosting model with learned weights</li>
                  <li>5. <strong>Result Curation:</strong> Diversity and quality post-processing</li>
                  <li>6. <strong>Explanation Generation:</strong> Transparent ranking rationale</li>
                </ol>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-blue-900 mb-2">Relevance Factors:</h4>
                <ul className="space-y-1 text-blue-700">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <strong>Title matching:</strong> 3x weight for keywords in title
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <strong>Abstract matching:</strong> Content relevance scoring
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <strong>Exact phrases:</strong> 2x boost for exact query matches
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <strong>Recent papers:</strong> 10% boost for 2020+ publications
                  </li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-blue-900 mb-2">Quality Indicators:</h4>
                <ul className="space-y-1 text-blue-700">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    <strong>Citation boost:</strong> Logarithmic boost for high-cited papers
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    <strong>Influential citations:</strong> Additional weight for impact
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    <strong>Open access:</strong> All results are freely accessible
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    <strong>Author quality:</strong> Only papers with named authors
                  </li>
                </ul>
              </div>
            </div>
          )}
          
          <div className="mt-4 p-3 bg-blue-100 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-1">Your Search:</h4>
            <p className="text-sm text-blue-700">
              Searching for "<strong>{searchQuery}</strong>" across {totalResults.toLocaleString()} results.
              {searchMetrics && searchMetrics.query_intent.domain_indicators.length > 0 && (
                <> Detected domains: {searchMetrics.query_intent.domain_indicators.join(', ')}.</>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchRelevanceInfo;
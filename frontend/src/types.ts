export interface Paper {
  title: string;
  authors: string[];
  abstract: string;
  year: string;
  source: string;
  full_text_url: string;
  doi?: string;
  journal?: string;
  citation_count?: number;
  influential_citation_count?: number;
  relevance_score?: number;
  relevance_factors?: {
    title_match?: number;
    abstract_match?: number;
    citation_boost?: number;
    recency_boost?: number;
    exact_phrase_match?: boolean;
  };
  // Book-specific fields
  content_type?: 'paper' | 'book';
  isbn?: string;
  publisher?: string;
  page_count?: number;
  language?: string;
  subjects?: string[];
  download_formats?: string[];
}

export interface SearchRequest {
  query: string;
  year_start?: number;
  year_end?: number;
  discipline?: string;
  education_level?: string;
  publication_type?: string;
  study_type?: string;
  min_citations?: number;
  sort_by?: 'relevance' | 'newest' | 'oldest' | 'citations';
  page?: number;
  per_page?: number;
  sources?: string[];
  require_authors?: boolean;
}

export interface SearchResponse {
  total_results: number;
  papers: Paper[];
  sources_queried: string[];
  source_counts?: Record<string, number>;  // Number of results from each source
}

export interface ExportRequest {
  papers: Paper[];
  format: 'csv' | 'json' | 'bib';
}
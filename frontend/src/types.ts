export interface Paper {
  title: string;
  authors: string[];
  abstract: string;
  year: string;
  source: string;
  full_text_url?: string;
  doi?: string;
  journal?: string;
  citation_count?: number;
  influential_citation_count?: number;
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
}

export interface SearchResponse {
  total_results: number;
  papers: Paper[];
  sources_queried: string[];
}

export interface ExportRequest {
  papers: Paper[];
  format: 'csv' | 'json' | 'bib';
}
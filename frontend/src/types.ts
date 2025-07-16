export interface Paper {
  title: string;
  authors: string[];
  abstract: string;
  year: string;
  source: string;
  full_text_url?: string;
  doi?: string;
  journal?: string;
}

export interface SearchRequest {
  query: string;
  year_start?: number;
  year_end?: number;
  discipline?: string;
  education_level?: string;
  publication_type?: string;
  study_type?: string;
  sort_by?: 'relevance' | 'newest' | 'oldest';
  page?: number;
  per_page?: number;
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
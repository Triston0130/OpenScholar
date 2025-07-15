import React, { useState } from 'react';
import { Paper } from '../types';

interface ResultCardProps {
  paper: Paper;
}

const ResultCard: React.FC<ResultCardProps> = ({ paper }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const formatAuthors = (authors: string[]) => {
    if (!authors || authors.length === 0) return 'No authors listed';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', ')} et al.`;
  };

  const getSourceColor = (source: string) => {
    const colors: { [key: string]: string } = {
      'ERIC': 'bg-blue-100 text-blue-800',
      'CORE': 'bg-green-100 text-green-800', 
      'DOAJ': 'bg-purple-100 text-purple-800',
      'Europe PMC': 'bg-red-100 text-red-800',
      'PubMed Central': 'bg-orange-100 text-orange-800',
    };
    return colors[source] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Title */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2 leading-tight">
        {paper.full_text_url ? (
          <a
            href={paper.full_text_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 hover:underline"
          >
            {paper.title}
          </a>
        ) : (
          paper.title
        )}
      </h3>

      {/* Authors and Year */}
      <div className="flex flex-wrap items-center gap-2 mb-3 text-sm text-gray-600">
        <span>{formatAuthors(paper.authors)}</span>
        {paper.year && (
          <>
            <span>•</span>
            <span>{paper.year}</span>
          </>
        )}
      </div>

      {/* Source and Journal Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSourceColor(paper.source)}`}>
          Source: {paper.source}
        </span>
        {paper.journal && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {paper.journal}
          </span>
        )}
      </div>

      {/* Abstract */}
      <div className="mb-4">
        <p className="text-gray-700 leading-relaxed">
          {isExpanded ? paper.abstract : truncateText(paper.abstract, 300)}
        </p>
        {paper.abstract.length > 300 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium mt-2 focus:outline-none"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Links */}
      <div className="flex flex-wrap gap-4 pt-4 border-t border-gray-200">
        {paper.full_text_url && (
          <a
            href={paper.full_text_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Full Text
          </a>
        )}
        
        {paper.doi && (
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            DOI: {paper.doi}
          </a>
        )}
      </div>
    </div>
  );
};

export default ResultCard;
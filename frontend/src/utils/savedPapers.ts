import { Paper } from '../types';

const SAVED_PAPERS_KEY = 'openscholar_saved_papers';

export interface SavedPaper extends Paper {
  savedAt: string;
  tags?: string[];
}

export const getSavedPapers = (): SavedPaper[] => {
  try {
    const saved = localStorage.getItem(SAVED_PAPERS_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch (error) {
    console.error('Error loading saved papers:', error);
    return [];
  }
};

export const savePaper = (paper: Paper): void => {
  try {
    const savedPapers = getSavedPapers();
    const paperWithMetadata: SavedPaper = {
      ...paper,
      savedAt: new Date().toISOString(),
      tags: []
    };
    
    // Check if already saved (by DOI or title)
    const isAlreadySaved = savedPapers.some(savedPaper => 
      (paper.doi && savedPaper.doi === paper.doi) ||
      savedPaper.title === paper.title
    );
    
    if (!isAlreadySaved) {
      savedPapers.unshift(paperWithMetadata); // Add to beginning
      localStorage.setItem(SAVED_PAPERS_KEY, JSON.stringify(savedPapers));
      // Dispatch custom event to update UI
      window.dispatchEvent(new CustomEvent('savedPapersChanged'));
    }
  } catch (error) {
    console.error('Error saving paper:', error);
  }
};

export const unsavePaper = (paper: Paper): void => {
  try {
    const savedPapers = getSavedPapers();
    const filteredPapers = savedPapers.filter(savedPaper => 
      !(
        (paper.doi && savedPaper.doi === paper.doi) ||
        savedPaper.title === paper.title
      )
    );
    localStorage.setItem(SAVED_PAPERS_KEY, JSON.stringify(filteredPapers));
    // Dispatch custom event to update UI
    window.dispatchEvent(new CustomEvent('savedPapersChanged'));
  } catch (error) {
    console.error('Error removing saved paper:', error);
  }
};

export const isPaperSaved = (paper: Paper): boolean => {
  try {
    const savedPapers = getSavedPapers();
    return savedPapers.some(savedPaper => 
      (paper.doi && savedPaper.doi === paper.doi) ||
      savedPaper.title === paper.title
    );
  } catch (error) {
    console.error('Error checking if paper is saved:', error);
    return false;
  }
};

export const exportSavedPapers = (format: 'bibtex' | 'pdf-list' | 'summary'): string => {
  const savedPapers = getSavedPapers();
  
  switch (format) {
    case 'bibtex':
      return generateBibTeX(savedPapers);
    case 'pdf-list':
      return generatePDFList(savedPapers);
    case 'summary':
      return generateSummary(savedPapers);
    default:
      return '';
  }
};

const generateBibTeX = (papers: SavedPaper[]): string => {
  return papers.map(paper => {
    const key = paper.doi ? paper.doi.replace(/[^a-zA-Z0-9]/g, '') : 
                paper.title.replace(/[^a-zA-Z0-9]/g, '').substring(0, 20);
    
    return `@article{${key},
  title={${paper.title}},
  author={${paper.authors.join(' and ')}},
  year={${paper.year}},
  journal={${paper.journal || 'Unknown'}},
  abstract={${paper.abstract}},
  url={${paper.full_text_url || ''}},
  doi={${paper.doi || ''}},
  source={${paper.source}}
}`;
  }).join('\n\n');
};

const generatePDFList = (papers: SavedPaper[]): string => {
  const pdfPapers = papers.filter(paper => paper.full_text_url);
  
  return `# Saved Papers - PDF Links (${pdfPapers.length} papers)

${pdfPapers.map((paper, index) => 
`${index + 1}. **${paper.title}**
   - Authors: ${paper.authors.join(', ')}
   - Year: ${paper.year}
   - Source: ${paper.source}
   - PDF: ${paper.full_text_url}
   - DOI: ${paper.doi || 'N/A'}
`).join('\n')}

Generated on ${new Date().toLocaleDateString()}`;
};

const generateSummary = (papers: SavedPaper[]): string => {
  const yearCounts: Record<string, number> = {};
  const sourceCounts: Record<string, number> = {};
  
  papers.forEach(paper => {
    yearCounts[paper.year] = (yearCounts[paper.year] || 0) + 1;
    sourceCounts[paper.source] = (sourceCounts[paper.source] || 0) + 1;
  });
  
  const sortedYears = Object.entries(yearCounts).sort(([a], [b]) => Number(b) - Number(a));
  const sortedSources = Object.entries(sourceCounts).sort(([,a], [,b]) => b - a);
  
  return `# Saved Papers Collection Summary

## Overview
- **Total Papers**: ${papers.length}
- **Papers with PDFs**: ${papers.filter(p => p.full_text_url).length}
- **Collection Started**: ${papers.length > 0 ? new Date(papers[papers.length - 1].savedAt).toLocaleDateString() : 'N/A'}
- **Last Updated**: ${papers.length > 0 ? new Date(papers[0].savedAt).toLocaleDateString() : 'N/A'}

## Papers by Year
${sortedYears.map(([year, count]) => `- ${year}: ${count} papers`).join('\n')}

## Papers by Source
${sortedSources.map(([source, count]) => `- ${source}: ${count} papers`).join('\n')}

## Recent Papers (Last 5 saved)
${papers.slice(0, 5).map((paper, index) => 
`${index + 1}. **${paper.title}** (${paper.year})
   - Authors: ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}
   - Saved: ${new Date(paper.savedAt).toLocaleDateString()}
`).join('\n')}

Generated on ${new Date().toLocaleDateString()}`;
};
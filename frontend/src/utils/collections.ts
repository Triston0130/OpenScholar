import { Paper } from '../types';
import { exportCitations } from './citationFormatter';

const COLLECTIONS_KEY = 'openscholar_collections';

export interface Collection {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  color?: string;
}

export interface SavedPaper extends Paper {
  savedAt: string;
  tags?: string[];
  notes?: string;
}

export interface CollectionWithPapers extends Collection {
  papers: SavedPaper[];
}

// Collection Management
export const getCollections = (): Collection[] => {
  try {
    const data = localStorage.getItem(COLLECTIONS_KEY);
    const collections = data ? JSON.parse(data).collections || [] : [];
    
    // Ensure default collection exists
    if (collections.length === 0) {
      const defaultCollection: Collection = {
        id: 'default',
        name: 'My Papers',
        description: 'Default collection for saved papers',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        color: '#3B82F6'
      };
      collections.push(defaultCollection);
      saveCollectionsData({ collections, papers: {} });
    }
    
    return collections;
  } catch (error) {
    console.error('Error loading collections:', error);
    return [];
  }
};

export const createCollection = (name: string, description?: string, color?: string): Collection => {
  const collection: Collection = {
    id: generateId(),
    name,
    description,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    color: color || getRandomColor()
  };
  
  const data = getCollectionsData();
  data.collections.push(collection);
  saveCollectionsData(data);
  
  return collection;
};

export const updateCollection = (id: string, updates: Partial<Collection>): void => {
  const data = getCollectionsData();
  const index = data.collections.findIndex((c: Collection) => c.id === id);
  if (index !== -1) {
    data.collections[index] = {
      ...data.collections[index],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    saveCollectionsData(data);
  }
};

export const deleteCollection = (id: string): void => {
  if (id === 'default') return; // Can't delete default collection
  
  const data = getCollectionsData();
  data.collections = data.collections.filter((c: Collection) => c.id !== id);
  delete data.papers[id];
  saveCollectionsData(data);
  dispatchCollectionsChange();
};

// Paper Management
export const addPaperToCollection = (
  paper: Paper, 
  collectionId: string, 
  tags: string[] = [], 
  notes: string = ''
): void => {
  const data = getCollectionsData();
  
  if (!data.papers[collectionId]) {
    data.papers[collectionId] = [];
  }
  
  const savedPaper: SavedPaper = {
    ...paper,
    savedAt: new Date().toISOString(),
    tags: tags,
    notes: notes
  };
  
  // Check if already in collection
  const isAlreadySaved = data.papers[collectionId].some((p: SavedPaper) => 
    (paper.doi && p.doi === paper.doi) || p.title === paper.title
  );
  
  if (!isAlreadySaved) {
    data.papers[collectionId].unshift(savedPaper);
    
    // Update collection timestamp
    const collection = data.collections.find((c: Collection) => c.id === collectionId);
    if (collection) {
      collection.updatedAt = new Date().toISOString();
    }
    
    saveCollectionsData(data);
    dispatchCollectionsChange();
  }
};

export const removePaperFromCollection = (paper: Paper, collectionId: string): void => {
  const data = getCollectionsData();
  
  if (data.papers[collectionId]) {
    data.papers[collectionId] = data.papers[collectionId].filter((p: SavedPaper) => 
      !((paper.doi && p.doi === paper.doi) || p.title === paper.title)
    );
    
    // Update collection timestamp
    const collection = data.collections.find((c: Collection) => c.id === collectionId);
    if (collection) {
      collection.updatedAt = new Date().toISOString();
    }
    
    saveCollectionsData(data);
    dispatchCollectionsChange();
  }
};

export const updatePaperTagsAndNotes = (
  paper: Paper, 
  collectionId: string, 
  tags: string[], 
  notes: string
): void => {
  const data = getCollectionsData();
  
  if (data.papers[collectionId]) {
    const paperIndex = data.papers[collectionId].findIndex((p: SavedPaper) => 
      (paper.doi && p.doi === paper.doi) || p.title === paper.title
    );
    
    if (paperIndex !== -1) {
      data.papers[collectionId][paperIndex] = {
        ...data.papers[collectionId][paperIndex],
        tags: tags,
        notes: notes
      };
      
      // Update collection timestamp
      const collection = data.collections.find((c: Collection) => c.id === collectionId);
      if (collection) {
        collection.updatedAt = new Date().toISOString();
      }
      
      saveCollectionsData(data);
      dispatchCollectionsChange();
    }
  }
};

export const getAllTags = (): string[] => {
  const data = getCollectionsData();
  const allTags = new Set<string>();
  
  Object.values(data.papers).forEach((papers: SavedPaper[]) => {
    papers.forEach((paper: SavedPaper) => {
      if (paper.tags) {
        paper.tags.forEach((tag: string) => allTags.add(tag));
      }
    });
  });
  
  return Array.from(allTags).sort();
};

export const getCollectionPapers = (collectionId: string): SavedPaper[] => {
  const data = getCollectionsData();
  return data.papers[collectionId] || [];
};

export const isPaperInCollection = (paper: Paper, collectionId: string): boolean => {
  const papers = getCollectionPapers(collectionId);
  return papers.some((p: SavedPaper) => 
    (paper.doi && p.doi === paper.doi) || p.title === paper.title
  );
};

export const getPaperCollections = (paper: Paper): Collection[] => {
  const collections = getCollections();
  return collections.filter((collection: Collection) => 
    isPaperInCollection(paper, collection.id)
  );
};

export const getAllCollectionsWithPapers = (): CollectionWithPapers[] => {
  const collections = getCollections();
  return collections.map((collection: Collection) => ({
    ...collection,
    papers: getCollectionPapers(collection.id)
  }));
};

// Statistics
export const getCollectionStats = (collectionId: string) => {
  const papers = getCollectionPapers(collectionId);
  const yearCounts: Record<string, number> = {};
  const sourceCounts: Record<string, number> = {};
  
  papers.forEach(paper => {
    yearCounts[paper.year] = (yearCounts[paper.year] || 0) + 1;
    sourceCounts[paper.source] = (sourceCounts[paper.source] || 0) + 1;
  });
  
  return {
    totalPapers: papers.length,
    papersWithPDFs: papers.filter((p: SavedPaper) => p.full_text_url).length,
    yearCounts,
    sourceCounts,
    oldestPaper: papers.length > 0 ? Math.min(...papers.map((p: SavedPaper) => parseInt(p.year) || 9999)) : null,
    newestPaper: papers.length > 0 ? Math.max(...papers.map((p: SavedPaper) => parseInt(p.year) || 0)) : null
  };
};

// Export functionality per collection
export const exportCollection = (collectionId: string, format: 'bibtex' | 'pdf-list' | 'summary' | 'apa' | 'mla' | 'chicago'): string => {
  const collection = getCollections().find((c: Collection) => c.id === collectionId);
  const papers = getCollectionPapers(collectionId);
  
  if (!collection) return '';
  
  switch (format) {
    case 'bibtex':
      return generateBibTeX(papers, collection.name);
    case 'pdf-list':
      return generatePDFList(papers, collection.name);
    case 'summary':
      return generateCollectionSummary(collection, papers);
    case 'apa':
      return exportCitations(papers, 'apa', collection.name);
    case 'mla':
      return exportCitations(papers, 'mla', collection.name);
    case 'chicago':
      return exportCitations(papers, 'chicago', collection.name);
    default:
      return '';
  }
};

// Helper functions
const getCollectionsData = () => {
  try {
    const data = localStorage.getItem(COLLECTIONS_KEY);
    return data ? JSON.parse(data) : { collections: [], papers: {} };
  } catch (error) {
    console.error('Error parsing collections data:', error);
    return { collections: [], papers: {} };
  }
};

const saveCollectionsData = (data: any) => {
  try {
    localStorage.setItem(COLLECTIONS_KEY, JSON.stringify(data));
  } catch (error) {
    console.error('Error saving collections data:', error);
  }
};

const dispatchCollectionsChange = () => {
  window.dispatchEvent(new CustomEvent('collectionsChanged'));
};

const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

const getRandomColor = (): string => {
  const colors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
    '#8B5CF6', '#F97316', '#06B6D4', '#84CC16',
    '#EC4899', '#6366F1', '#14B8A6', '#F472B6'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

const generateBibTeX = (papers: SavedPaper[], collectionName: string): string => {
  const header = `% BibTeX export from OpenScholar\n% Collection: ${collectionName}\n% Generated: ${new Date().toLocaleDateString()}\n\n`;
  
  const entries = papers.map((paper: SavedPaper) => {
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
  source={${paper.source}},
  note={Saved to ${collectionName} on ${new Date(paper.savedAt).toLocaleDateString()}}
}`;
  }).join('\n\n');
  
  return header + entries;
};

const generatePDFList = (papers: SavedPaper[], collectionName: string): string => {
  const pdfPapers = papers.filter((paper: SavedPaper) => paper.full_text_url);
  
  return `# ${collectionName} - PDF Links

${pdfPapers.length} papers with full-text PDFs

${pdfPapers.map((paper: SavedPaper, index: number) => 
`## ${index + 1}. ${paper.title}

- **Authors:** ${paper.authors.join(', ')}
- **Year:** ${paper.year}
- **Source:** ${paper.source}
- **PDF:** [Download](${paper.full_text_url})
- **DOI:** ${paper.doi || 'N/A'}
- **Saved:** ${new Date(paper.savedAt).toLocaleDateString()}

---`).join('\n\n')}

*Generated from OpenScholar on ${new Date().toLocaleDateString()}*`;
};

const generateCollectionSummary = (collection: Collection, papers: SavedPaper[]): string => {
  const stats = getCollectionStats(collection.id);
  
  return `# ${collection.name} - Collection Summary

**Description:** ${collection.description || 'No description'}
**Created:** ${new Date(collection.createdAt).toLocaleDateString()}
**Last Updated:** ${new Date(collection.updatedAt).toLocaleDateString()}

## Statistics
- **Total Papers:** ${stats.totalPapers}
- **Papers with PDFs:** ${stats.papersWithPDFs}
- **Date Range:** ${stats.oldestPaper || 'N/A'} - ${stats.newestPaper || 'N/A'}

## Papers by Year
${Object.entries(stats.yearCounts)
  .sort(([a], [b]) => Number(b) - Number(a))
  .map(([year, count]: [string, number]) => `- ${year}: ${count} papers`)
  .join('\n')}

## Papers by Source
${Object.entries(stats.sourceCounts)
  .sort(([,a], [,b]) => b - a)
  .map(([source, count]: [string, number]) => `- ${source}: ${count} papers`)
  .join('\n')}

## Recent Papers (Last 5 added)
${papers.slice(0, 5).map((paper: SavedPaper, index: number) => 
`${index + 1}. **${paper.title}** (${paper.year})
   - Authors: ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}
   - Added: ${new Date(paper.savedAt).toLocaleDateString()}
`).join('\n')}

*Generated from OpenScholar on ${new Date().toLocaleDateString()}*`;
};
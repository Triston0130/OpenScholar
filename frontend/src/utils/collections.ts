import { Paper } from '../types';
import { exportCitations } from './citationFormatter';
import { v4 as uuidv4 } from 'uuid';

const COLLECTIONS_KEY = 'openscholar_collections';
const DEFAULT_COLLECTION_UUID = '00000000-0000-0000-0000-000000000000';

export interface Collection {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  color?: string;
}

export interface Folder {
  id: string;
  name: string;
  collectionId: string;
  parentId?: string;
  createdAt: string;
  updatedAt: string;
  color?: string;
}

export interface SavedPaper extends Paper {
  savedAt: string;
  tags?: string[];
  notes?: string;
  folderId?: string;
}

export interface CollectionWithPapers extends Collection {
  papers: SavedPaper[];
  folders: Folder[];
}

// Sync local collections with backend
export const syncCollectionsWithBackend = async (): Promise<void> => {
  try {
    const accessToken = localStorage.getItem('openscholar_access_token');
    if (!accessToken) return;
    
    const { getCollections: getBackendCollections, createCollection: createBackendCollection } = await import('./api');
    
    // Get collections from both sources
    const localData = getCollectionsData();
    const localCollections = localData.collections || [];
    const backendCollections = await getBackendCollections();
    
    // Create a map of backend collections by name for easy lookup
    const backendByName = new Map(backendCollections.map(c => [c.name, c]));
    
    // Sync local collections to backend
    for (const localCollection of localCollections) {
      const backendCollection = backendByName.get(localCollection.name);
      
      if (!backendCollection && localCollection.id !== DEFAULT_COLLECTION_UUID) {
        // Create in backend if it doesn't exist
        try {
          const created = await createBackendCollection({
            name: localCollection.name,
            description: localCollection.description,
            color: localCollection.color,
            is_public: false
          });
          
          // Update local collection with backend ID
          localCollection.id = created.id;
        } catch (error) {
          console.error(`Failed to sync collection ${localCollection.name} to backend:`, error);
        }
      } else if (backendCollection) {
        // Update local collection ID to match backend
        localCollection.id = backendCollection.id;
      }
    }
    
    // Save updated local data
    saveCollectionsData(localData);
  } catch (error) {
    console.error('Failed to sync collections with backend:', error);
  }
};

// Collection Management
export const getCollections = (): Collection[] => {
  try {
    const data = getCollectionsData();
    const collections = data.collections || [];
    
    // Ensure default collection exists
    if (collections.length === 0) {
      const defaultCollection: Collection = {
        id: DEFAULT_COLLECTION_UUID,
        name: 'My Papers',
        description: 'Default collection for saved papers',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        color: '#3B82F6'
      };
      collections.push(defaultCollection);
      // Preserve existing papers and folders data
      saveCollectionsData({ collections, papers: data.papers, folders: data.folders });
    }
    
    return collections;
  } catch (error) {
    console.error('Error loading collections:', error);
    return [];
  }
};

export const createCollection = async (name: string, description?: string, color?: string): Promise<Collection> => {
  try {
    // First try to create in backend if user is authenticated
    const accessToken = localStorage.getItem('openscholar_access_token');
    if (accessToken) {
      const { createCollection: createBackendCollection } = await import('./api');
      const backendCollection = await createBackendCollection({
        name,
        description,
        color: color || getRandomColor(),
        is_public: false
      });
      
      // Create local collection with backend ID
      const collection: Collection = {
        id: backendCollection.id,
        name: backendCollection.name,
        description: backendCollection.description,
        createdAt: backendCollection.created_at.toString(),
        updatedAt: backendCollection.updated_at?.toString() || backendCollection.created_at.toString(),
        color: backendCollection.color || getRandomColor()
      };
      
      const data = getCollectionsData();
      data.collections.push(collection);
      saveCollectionsData(data);
      dispatchCollectionsChange();
      
      return collection;
    }
  } catch (error) {
    console.error('Failed to create collection in backend:', error);
    // Fall through to local-only creation
  }
  
  // Fallback to local-only collection
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
  dispatchCollectionsChange();
  
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
  if (id === DEFAULT_COLLECTION_UUID) return; // Can't delete default collection
  
  const data = getCollectionsData();
  data.collections = data.collections.filter((c: Collection) => c.id !== id);
  delete data.papers[id];
  delete data.folders[id];
  saveCollectionsData(data);
  dispatchCollectionsChange();
};

// Helper function to find existing tags and notes for a paper across all collections
const findExistingPaperMetadata = (paper: Paper, data: CollectionsData): { tags: string[], notes: string } => {
  let existingTags: string[] = [];
  let existingNotes: string = '';
  
  // Search through all collections for this paper
  for (const [collId, papers] of Object.entries(data.papers)) {
    if (Array.isArray(papers)) {
      const existingPaper = papers.find((p: SavedPaper) => 
        (paper.doi && p.doi === paper.doi) || p.title === paper.title
      );
      
      if (existingPaper) {
        // Merge tags (avoiding duplicates)
        if (existingPaper.tags && existingPaper.tags.length > 0) {
          existingTags = Array.from(new Set([...existingTags, ...existingPaper.tags]));
        }
        
        // Use the longest/most detailed notes
        if (existingPaper.notes && existingPaper.notes.length > existingNotes.length) {
          existingNotes = existingPaper.notes;
        }
      }
    }
  }
  
  return { tags: existingTags, notes: existingNotes };
};

// Paper Management
export const addPaperToCollection = async (
  paper: Paper, 
  collectionId: string, 
  tags: string[] = [], 
  notes: string = '',
  folderId?: string,
  pdfFile?: File
): Promise<void> => {
  // If we have a PDF file, upload it first and update the paper's full_text_url
  let paperToSave = { ...paper };
  
  if (pdfFile) {
    try {
      // Import the upload function
      const { uploadPdf } = await import('./api');
      const pdfUrl = await uploadPdf(pdfFile);
      paperToSave.full_text_url = pdfUrl;
    } catch (error) {
      console.error('Failed to upload PDF:', error);
      // Continue without the uploaded PDF
    }
  }
  
  const data = getCollectionsData();
  
  if (!data.papers[collectionId]) {
    data.papers[collectionId] = [];
  }
  
  // If no tags/notes provided, check if paper exists in other collections
  let finalTags = tags;
  let finalNotes = notes;
  
  if (tags.length === 0 && notes === '') {
    const existing = findExistingPaperMetadata(paperToSave, data);
    finalTags = existing.tags;
    finalNotes = existing.notes;
  }
  
  const savedPaper: SavedPaper = {
    ...paperToSave,
    savedAt: new Date().toISOString(),
    tags: finalTags,
    notes: finalNotes,
    folderId: folderId
  };
  
  // Check if already in collection
  const isAlreadySaved = data.papers[collectionId].some((p: SavedPaper) => 
    (paperToSave.doi && p.doi === paperToSave.doi) || p.title === paperToSave.title
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
  
  Object.values(data.papers).forEach((papers) => {
    if (Array.isArray(papers)) {
      papers.forEach((paper: SavedPaper) => {
        if (paper.tags) {
          paper.tags.forEach((tag: string) => allTags.add(tag));
        }
      });
    }
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
    papers: getCollectionPapers(collection.id),
    folders: getFolders(collection.id)
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
interface CollectionsData {
  collections: Collection[];
  papers: Record<string, SavedPaper[]>;
  folders: Record<string, Folder[]>;
}

// Check if a string is a valid UUID
const isValidUUID = (id: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
};

// Migrate old collection IDs to UUIDs
const migrateCollectionIds = (data: CollectionsData): CollectionsData => {
  const idMap: { [oldId: string]: string } = {};
  let needsMigration = false;

  // Check if any collections need migration
  data.collections.forEach((collection: Collection) => {
    if (!isValidUUID(collection.id)) {
      needsMigration = true;
      const newId = collection.id === 'default' ? DEFAULT_COLLECTION_UUID : uuidv4();
      idMap[collection.id] = newId;
    }
  });

  if (!needsMigration) {
    return data;
  }

  // Migrate collections
  data.collections = data.collections.map((collection: Collection) => {
    if (idMap[collection.id]) {
      return { ...collection, id: idMap[collection.id] };
    }
    return collection;
  });

  // Migrate papers
  const newPapers: { [key: string]: SavedPaper[] } = {};
  Object.entries(data.papers).forEach(([collectionId, papers]) => {
    const newId = idMap[collectionId] || collectionId;
    newPapers[newId] = papers;
  });
  data.papers = newPapers;

  // Migrate folders
  const newFolders: { [key: string]: Folder[] } = {};
  Object.entries(data.folders).forEach(([collectionId, folders]) => {
    const newId = idMap[collectionId] || collectionId;
    newFolders[newId] = folders.map((folder: Folder) => ({
      ...folder,
      collectionId: newId
    }));
  });
  data.folders = newFolders;

  return data;
};

const getCollectionsData = (): CollectionsData => {
  try {
    const data = localStorage.getItem(COLLECTIONS_KEY);
    const parsedData = data ? JSON.parse(data) : { collections: [], papers: {}, folders: {} };
    
    // Migrate old IDs to UUIDs
    const migratedData = migrateCollectionIds(parsedData);
    
    // Save migrated data if it was changed
    if (data && JSON.stringify(parsedData) !== JSON.stringify(migratedData)) {
      localStorage.setItem(COLLECTIONS_KEY, JSON.stringify(migratedData));
    }
    
    return migratedData;
  } catch (error) {
    console.error('Error parsing collections data:', error);
    return { collections: [], papers: {}, folders: {} };
  }
};

const saveCollectionsData = (data: CollectionsData) => {
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
  return uuidv4();
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

// Folder Management
export const getFolders = (collectionId: string): Folder[] => {
  const data = getCollectionsData();
  return data.folders[collectionId] || [];
};

export const createFolder = (collectionId: string, name: string, parentId?: string, color?: string): Folder => {
  const folder: Folder = {
    id: generateId(),
    name,
    collectionId,
    parentId,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    color: color || getRandomColor()
  };
  
  const data = getCollectionsData();
  if (!data.folders[collectionId]) {
    data.folders[collectionId] = [];
  }
  data.folders[collectionId].push(folder);
  saveCollectionsData(data);
  dispatchCollectionsChange();
  
  return folder;
};

export const updateFolder = (folderId: string, collectionId: string, updates: Partial<Folder>): void => {
  const data = getCollectionsData();
  if (data.folders[collectionId]) {
    const index = data.folders[collectionId].findIndex(f => f.id === folderId);
    if (index !== -1) {
      data.folders[collectionId][index] = {
        ...data.folders[collectionId][index],
        ...updates,
        updatedAt: new Date().toISOString()
      };
      saveCollectionsData(data);
      dispatchCollectionsChange();
    }
  }
};

export const deleteFolder = (folderId: string, collectionId: string): void => {
  const data = getCollectionsData();
  
  if (data.folders[collectionId]) {
    // Remove the folder
    data.folders[collectionId] = data.folders[collectionId].filter(f => f.id !== folderId);
    
    // Remove folderId from papers that were in this folder
    if (data.papers[collectionId]) {
      data.papers[collectionId] = data.papers[collectionId].map(paper => ({
        ...paper,
        folderId: paper.folderId === folderId ? undefined : paper.folderId
      }));
    }
    
    // Recursively delete child folders
    const childFolders = data.folders[collectionId].filter(f => f.parentId === folderId);
    for (const childFolder of childFolders) {
      deleteFolder(childFolder.id, collectionId);
    }
    
    saveCollectionsData(data);
    dispatchCollectionsChange();
  }
};

export const getFolderPapers = (collectionId: string, folderId?: string): SavedPaper[] => {
  const papers = getCollectionPapers(collectionId);
  return papers.filter(paper => paper.folderId === folderId);
};

export const movePaperToFolder = (paper: Paper, collectionId: string, folderId?: string): void => {
  const data = getCollectionsData();
  
  if (data.papers[collectionId]) {
    const paperIndex = data.papers[collectionId].findIndex((p: SavedPaper) => 
      (paper.doi && p.doi === paper.doi) || p.title === paper.title
    );
    
    if (paperIndex !== -1) {
      data.papers[collectionId][paperIndex] = {
        ...data.papers[collectionId][paperIndex],
        folderId: folderId
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
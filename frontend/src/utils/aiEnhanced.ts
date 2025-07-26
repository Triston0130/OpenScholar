import { api } from './api';
import { Paper } from '../types';
import { createMultipleFlashcards } from './annotations';
import { updatePaperTagsAndNotes } from './collections';

interface EnhancedAIConfig {
  apiKey: string;
  model: string;
  temperature?: number;
  extractFullText?: boolean;
}

interface ProcessingProgress {
  current: number;
  total: number;
  currentStep: string;
  results: {
    tags: string[];
    notes: Record<string, string>;
    flashcards: any[];
  };
}

// Helper function to detect if a paper is likely a textbook
async function checkIfTextbook(paper: Paper, config: EnhancedAIConfig): Promise<boolean> {
  const titleLower = paper.title.toLowerCase();
  const textbookIndicators = [
    'textbook', 'introduction to', 'fundamentals of', 'principles of',
    'handbook', 'guide to', 'manual', 'primer on'
  ];
  
  // Check title for textbook indicators
  const hasTextbookTitle = textbookIndicators.some(indicator => titleLower.includes(indicator));
  
  // Check if it's from a known textbook source
  const textbookSources = ['open textbook', 'openstax', 'libretexts', 'oer commons'];
  const isTextbookSource = textbookSources.some(source => 
    paper.source?.toLowerCase().includes(source) || 
    paper.journal?.toLowerCase().includes(source)
  );
  
  // Check page count if available (textbooks are typically long)
  // This would need backend support to get page count
  
  return hasTextbookTitle || isTextbookSource;
}

// Process textbook with intelligent chunking
async function processTextbook(
  paper: Paper,
  collectionId: string,
  config: EnhancedAIConfig,
  onProgress?: (message: string) => void
): Promise<{
  tags: string[];
  notes: string;
  flashcards: any[];
}> {
  if (onProgress) onProgress(`Detected textbook: ${paper.title}. Using intelligent processing...`);
  
  // Call special textbook processing endpoint
  const response = await api.post('/api/ai/enhanced/process-textbook', {
    paper_id: paper.doi || paper.title,
    paper_data: {
      title: paper.title,
      authors: paper.authors,
      year: paper.year,
      abstract: paper.abstract,
      journal: paper.journal,
      doi: paper.doi,
      full_text_url: paper.full_text_url
    },
    api_key: config.apiKey,
    model: config.model,
    temperature: 0.3, // Lower temperature for consistency
    extract_full_text: true,
    processing_options: {
      chunk_by_chapters: true,
      flashcards_per_chapter: 10,
      tags_per_chapter: 2,
      generate_comprehensive_notes: true
    }
  });

  if (response.data.success) {
    return {
      tags: response.data.unique_tags || [],
      notes: response.data.structured_notes || '',
      flashcards: response.data.all_flashcards || []
    };
  }
  
  // Fallback to regular processing
  return { tags: [], notes: '', flashcards: [] };
}

export async function generateEnhancedTags(
  paper: Paper,
  config: EnhancedAIConfig,
  tagCount: number = 20
) {
  const paperData = {
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    abstract: paper.abstract,
    journal: paper.journal,
    doi: paper.doi,
    full_text_url: paper.full_text_url
  };

  const response = await api.post('/api/ai/enhanced/generate-tags', {
    paper_id: paper.doi || paper.title,
    paper_data: paperData,
    api_key: config.apiKey,
    model: config.model,
    temperature: config.temperature || 0.7,
    extract_full_text: config.extractFullText !== false,
    tag_count: tagCount,
    tag_categories: [
      "core_concepts",
      "methodology", 
      "applications",
      "field_of_study",
      "theoretical_framework",
      "techniques",
      "data_types",
      "outcomes"
    ]
  });

  return response.data;
}

export async function generateEnhancedNotes(
  paper: Paper,
  config: EnhancedAIConfig,
  sections: string[] = ["summary", "key_terms", "methodology", "findings", "implications"]
) {
  const paperData = {
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    abstract: paper.abstract,
    journal: paper.journal,
    doi: paper.doi,
    full_text_url: paper.full_text_url
  };

  const response = await api.post('/api/ai/enhanced/generate-notes', {
    paper_id: paper.doi || paper.title,
    paper_data: paperData,
    api_key: config.apiKey,
    model: config.model,
    temperature: config.temperature || 0.7,
    extract_full_text: config.extractFullText !== false,
    note_sections: sections,
    max_tokens: 3000
  });

  return response.data;
}

export async function generateEnhancedFlashcards(
  paper: Paper,
  pdfUrl: string,
  config: EnhancedAIConfig,
  options: {
    flashcardCount?: number;
    difficulty?: string;
    focusAreas?: string[];
  } = {}
) {
  const paperData = {
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    abstract: paper.abstract,
    journal: paper.journal,
    doi: paper.doi,
    full_text_url: paper.full_text_url,
    pdf_url: pdfUrl
  };

  const response = await api.post('/api/ai/enhanced/generate-flashcards', {
    paper_id: paper.doi || paper.title,
    paper_data: paperData,
    api_key: config.apiKey,
    model: config.model,
    temperature: config.temperature || 0.7,
    extract_full_text: config.extractFullText !== false,
    flashcard_count: options.flashcardCount || 15,
    difficulty_level: options.difficulty || 'intermediate',
    focus_areas: options.focusAreas,
    include_quotes: true
  });

  if (response.data.success && response.data.flashcards) {
    // Store flashcards locally
    const paperId = paper.doi || paper.full_text_url || paper.title;
    createMultipleFlashcards(paperId, pdfUrl, response.data.flashcards);
  }

  return response.data;
}

export async function processCollectionEnhanced(
  collectionId: string,
  papers: Paper[],
  options: {
    generateTags: boolean;
    generateNotes: boolean;
    generateFlashcards: boolean;
    tagCount?: number;
    flashcardCount?: number;
    flashcardDifficulty?: string;
    noteSections?: string[];
  },
  config: EnhancedAIConfig,
  onProgress?: (progress: ProcessingProgress) => void
) {
  const results: ProcessingProgress = {
    current: 0,
    total: papers.length * (
      (options.generateTags ? 1 : 0) +
      (options.generateNotes ? 1 : 0) +
      (options.generateFlashcards ? 1 : 0)
    ),
    currentStep: 'Initializing...',
    results: {
      tags: [],
      notes: {},
      flashcards: []
    }
  };

  const processedPapers = [];

  for (const paper of papers) {
    const paperResults = {
      paper_id: paper.doi || paper.title,
      title: paper.title,
      tags: [] as string[],
      notes: {} as Record<string, string>,
      flashcards: [] as any[]
    };

    // Check if this might be a textbook
    const pdfUrl = paper.full_text_url || '';
    const isLikelyTextbook = await checkIfTextbook(paper, config);

    if (isLikelyTextbook) {
      // Process as textbook - all at once for efficiency
      results.currentStep = `Processing textbook: ${paper.title}`;
      if (onProgress) onProgress(results);

      try {
        const textbookResults = await processTextbook(
          paper, 
          collectionId, 
          config,
          (message) => {
            results.currentStep = message;
            if (onProgress) onProgress(results);
          }
        );

        paperResults.tags = textbookResults.tags;
        paperResults.notes = {
          comprehensive: textbookResults.notes
        };
        paperResults.flashcards = textbookResults.flashcards;

        // Save flashcards immediately for textbooks
        if (textbookResults.flashcards.length > 0) {
          const paperId = paper.doi || paper.full_text_url || paper.title;
          createMultipleFlashcards(paperId, pdfUrl, textbookResults.flashcards);
        }

        // Update progress for all operations
        if (options.generateTags) results.current++;
        if (options.generateNotes) results.current++;
        if (options.generateFlashcards) results.current++;
      } catch (error) {
        console.error('Error processing textbook:', error);
      }
    } else {
      // Regular processing for non-textbooks
      // Generate tags
      if (options.generateTags) {
        results.currentStep = `Generating tags for: ${paper.title}`;
        if (onProgress) onProgress(results);

        try {
          const tagResponse = await generateEnhancedTags(paper, config, options.tagCount);
          if (tagResponse.success) {
            paperResults.tags = tagResponse.tags.map((t: any) => t.tag);
          }
        } catch (error) {
          console.error('Error generating tags:', error);
        }
        
        results.current++;
      }

      // Generate notes
      if (options.generateNotes) {
        results.currentStep = `Generating notes for: ${paper.title}`;
        if (onProgress) onProgress(results);

        try {
          const notesResponse = await generateEnhancedNotes(paper, config, options.noteSections);
          if (notesResponse.success) {
            paperResults.notes = notesResponse.notes;
          }
        } catch (error) {
          console.error('Error generating notes:', error);
        }
        
        results.current++;
      }

      // Generate flashcards
      if (options.generateFlashcards) {
        results.currentStep = `Generating flashcards for: ${paper.title}`;
        if (onProgress) onProgress(results);

        try {
          const flashcardResponse = await generateEnhancedFlashcards(
            paper,
            paper.full_text_url,
            config,
            {
              flashcardCount: options.flashcardCount,
              difficulty: options.flashcardDifficulty
            }
          );
          if (flashcardResponse.success) {
            paperResults.flashcards = flashcardResponse.flashcards;
          }
        } catch (error) {
          console.error('Error generating flashcards:', error);
        }
        
        results.current++;
      }
    }

    // Save tags and notes to local storage
    if (paperResults.tags.length > 0 || Object.keys(paperResults.notes).length > 0) {
      // Convert notes object to string format for storage
      const notesString = Object.entries(paperResults.notes)
        .map(([section, content]) => `## ${section}\n${content}`)
        .join('\n\n');
      
      // First ensure the paper is in the collection
      const { addPaperToCollection, isPaperInCollection } = await import('./collections');
      
      // Check if paper is already in collection
      if (!isPaperInCollection(paper, collectionId)) {
        // Add paper to collection with the generated tags and notes
        await addPaperToCollection(
          paper,
          collectionId,
          paperResults.tags,
          notesString
        );
      } else {
        // Paper already exists, update its tags and notes
        updatePaperTagsAndNotes(
          paper,
          collectionId,
          paperResults.tags,
          notesString
        );
      }
    }

    processedPapers.push(paperResults);

    // Small delay between papers
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Call the backend to save results
  try {
    await api.post('/api/ai/enhanced/process-collection-enhanced', {
      collection_id: collectionId,
      process_options: {
        tags: options.generateTags,
        notes: options.generateNotes,
        flashcards: options.generateFlashcards
      },
      ai_config: {
        api_key: config.apiKey,
        model: config.model,
        tag_count: options.tagCount,
        flashcard_count: options.flashcardCount,
        difficulty_level: options.flashcardDifficulty,
        note_sections: options.noteSections
      }
    });
  } catch (error) {
    console.error('Error saving to backend:', error);
  }

  return processedPapers;
}
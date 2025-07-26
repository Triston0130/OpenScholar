// Simple ID generation function
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export interface Annotation {
  id: string;
  paperId: string;
  pdfUrl: string;
  type: 'highlight' | 'note' | 'flashcard' | 'image-note';
  text: string;
  note?: string;
  image?: string; // Base64 image data for screenshot annotations
  pageNumber?: number;
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  textPosition?: {
    start: number;
    end: number;
    rects?: any[];
  };
  highlightAreas?: any[];
  color?: string;
  colorName?: string;
  label?: string;
  category?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Flashcard {
  id: string;
  paperId: string;
  pdfUrl: string;
  type: 'flashcard';
  text: string;
  note?: string;
  pageNumber?: number;
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  color?: string;
  createdAt: Date;
  updatedAt: Date;
  front: string;
  back: string;
  frontImage?: string; // Base64 image data for front of card
  backImage?: string;  // Base64 image data for back of card
  tags?: string[];     // Tags for organization
  nextReviewDate?: Date;
  difficulty?: number;
  category?: string;
  aiGenerated?: boolean;
}

const ANNOTATIONS_KEY = 'openscholar_annotations';

// Get all annotations
export function getAllAnnotations(): Annotation[] {
  try {
    const stored = localStorage.getItem(ANNOTATIONS_KEY);
    if (!stored) return [];
    
    const annotations = JSON.parse(stored);
    // Convert date strings back to Date objects
    return annotations.map((ann: any) => ({
      ...ann,
      createdAt: new Date(ann.createdAt),
      updatedAt: new Date(ann.updatedAt),
      nextReviewDate: ann.nextReviewDate ? new Date(ann.nextReviewDate) : undefined
    }));
  } catch (error) {
    console.error('Error loading annotations:', error);
    return [];
  }
}

// Get annotations for a specific paper
export function getAnnotationsByPaper(paperId: string): Annotation[] {
  const all = getAllAnnotations();
  return all.filter(ann => ann.paperId === paperId);
}

// Get annotations by PDF URL
export function getAnnotationsByPdfUrl(pdfUrl: string): Annotation[] {
  const all = getAllAnnotations();
  return all.filter(ann => ann.pdfUrl === pdfUrl);
}

// Save an annotation
export function saveAnnotation(annotation: Omit<Annotation, 'id' | 'createdAt' | 'updatedAt'>): Annotation {
  const newAnnotation: Annotation = {
    ...annotation,
    id: generateId(),
    createdAt: new Date(),
    updatedAt: new Date()
  };
  
  const all = getAllAnnotations();
  all.push(newAnnotation);
  localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(all));
  
  // Dispatch event for other components to update
  window.dispatchEvent(new CustomEvent('annotationsChanged', { 
    detail: { annotation: newAnnotation, action: 'add' } 
  }));
  
  return newAnnotation;
}

// Update an annotation
export function updateAnnotation(id: string, updates: Partial<Annotation>): Annotation | null {
  const all = getAllAnnotations();
  const index = all.findIndex(ann => ann.id === id);
  
  if (index === -1) return null;
  
  all[index] = {
    ...all[index],
    ...updates,
    updatedAt: new Date()
  };
  
  localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(all));
  
  // Dispatch event
  window.dispatchEvent(new CustomEvent('annotationsChanged', { 
    detail: { annotation: all[index], action: 'update' } 
  }));
  
  return all[index];
}

// Delete an annotation
export function deleteAnnotation(id: string): boolean {
  const all = getAllAnnotations();
  const filtered = all.filter(ann => ann.id !== id);
  
  if (filtered.length === all.length) return false;
  
  localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(filtered));
  
  // Dispatch event
  window.dispatchEvent(new CustomEvent('annotationsChanged', { 
    detail: { annotationId: id, action: 'delete' } 
  }));
  
  return true;
}

// Create a highlight
export function createHighlight(
  paperId: string,
  pdfUrl: string,
  text: string,
  pageNumber?: number,
  position?: Annotation['position'],
  color: string = '#ffeb3b'
): Annotation {
  return saveAnnotation({
    paperId,
    pdfUrl,
    type: 'highlight',
    text,
    pageNumber,
    position,
    color
  });
}

// Create a note
export function createNote(
  paperId: string,
  pdfUrl: string,
  text: string,
  note: string,
  pageNumber?: number,
  position?: Annotation['position']
): Annotation {
  return saveAnnotation({
    paperId,
    pdfUrl,
    type: 'note',
    text,
    note,
    pageNumber,
    position
  });
}

// Create a flashcard
export function createFlashcard(options: {
  paperId: string;
  pdfUrl: string;
  text?: string;
  frontText?: string;
  backText?: string;
  frontImage?: string;
  backImage?: string;
  tags?: string[];
  pageNumber?: number;
  category?: string;
  difficulty?: number;
}): Flashcard {
  const flashcard: Flashcard = {
    id: generateId(),
    paperId: options.paperId,
    pdfUrl: options.pdfUrl,
    type: 'flashcard',
    text: options.text || options.frontText || '',
    front: options.frontText || options.text || '',
    back: options.backText || '',
    frontImage: options.frontImage,
    backImage: options.backImage,
    tags: options.tags,
    pageNumber: options.pageNumber,
    difficulty: options.difficulty || 2.5,
    nextReviewDate: new Date(),
    createdAt: new Date(),
    updatedAt: new Date(),
    category: options.category
  };
  
  const all = getAllAnnotations();
  all.push(flashcard as any);
  localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(all));
  
  // Dispatch event
  window.dispatchEvent(new CustomEvent('annotationsChanged', { 
    detail: { annotation: flashcard, action: 'add' } 
  }));
  
  return flashcard;
}

// Legacy createFlashcard function for backward compatibility
export function createFlashcardLegacy(
  paperId: string,
  pdfUrl: string,
  text: string,
  front?: string,
  back?: string,
  category?: string,
  difficulty?: number
): Flashcard {
  return createFlashcard({
    paperId,
    pdfUrl,
    text,
    frontText: front,
    backText: back,
    category,
    difficulty
  });
}

// Create multiple flashcards from AI generation
export function createMultipleFlashcards(
  paperId: string,
  pdfUrl: string,
  flashcards: Array<{
    front: string;
    back: string;
    category?: string;
    difficulty?: string;
    related_quote?: string;
  }>
): Flashcard[] {
  const createdFlashcards: Flashcard[] = [];
  
  for (const fc of flashcards) {
    const difficultyMap = {
      'beginner': 1,
      'intermediate': 2.5,
      'advanced': 4
    };
    
    const flashcard: Flashcard = {
      id: generateId(),
      paperId,
      pdfUrl,
      type: 'flashcard',
      text: fc.related_quote || fc.front,
      front: fc.front,
      back: fc.back,
      difficulty: difficultyMap[fc.difficulty as keyof typeof difficultyMap] || 2.5,
      nextReviewDate: new Date(),
      createdAt: new Date(),
      updatedAt: new Date(),
      category: fc.category,
      aiGenerated: true
    };
    
    createdFlashcards.push(flashcard);
  }
  
  // Save all at once
  const all = getAllAnnotations();
  all.push(...(createdFlashcards as any[]));
  localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(all));
  
  // Dispatch event
  window.dispatchEvent(new CustomEvent('annotationsChanged', { 
    detail: { flashcards: createdFlashcards, action: 'add-multiple' } 
  }));
  
  return createdFlashcards;
}

// Export annotations
export function exportAnnotations(paperId?: string): string {
  const annotations = paperId ? getAnnotationsByPaper(paperId) : getAllAnnotations();
  return JSON.stringify(annotations, null, 2);
}

// Import annotations
export function importAnnotations(jsonString: string): boolean {
  try {
    const imported = JSON.parse(jsonString);
    if (!Array.isArray(imported)) return false;
    
    const all = getAllAnnotations();
    const newAnnotations = imported.map((ann: any) => ({
      ...ann,
      id: ann.id || generateId(),
      createdAt: new Date(ann.createdAt || Date.now()),
      updatedAt: new Date(ann.updatedAt || Date.now())
    }));
    
    const combined = [...all, ...newAnnotations];
    localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(combined));
    
    window.dispatchEvent(new CustomEvent('annotationsChanged', { 
      detail: { action: 'import', count: newAnnotations.length } 
    }));
    
    return true;
  } catch (error) {
    console.error('Error importing annotations:', error);
    return false;
  }
}
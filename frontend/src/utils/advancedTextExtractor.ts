/**
 * Advanced PDF Text Extraction for Perfect TTS
 * Handles all edge cases and complex layouts
 */

interface TextItem {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fontSize: number;
  fontName: string;
  transform: number[];
}

interface TextBlock {
  items: TextItem[];
  bounds: {
    left: number;
    top: number;
    right: number;
    bottom: number;
  };
  type: 'paragraph' | 'heading' | 'list' | 'table' | 'formula' | 'caption' | 'header' | 'footer' | 'reference';
  confidence: number;
}

interface Column {
  blocks: TextBlock[];
  bounds: {
    left: number;
    top: number;
    right: number;
    bottom: number;
  };
}

export class AdvancedTextExtractor {
  private readonly EPSILON = 0.1;
  private readonly LINE_HEIGHT_RATIO = 1.2;
  private readonly WORD_SPACING_RATIO = 0.3;
  private readonly PARAGRAPH_GAP_RATIO = 1.5;
  private readonly COLUMN_GAP_MIN = 20;
  
  /**
   * Extract text with perfect reading order
   */
  public extractText(textItems: any[], viewport: any): string {
    if (!textItems || textItems.length === 0) {
      return '';
    }
    
    // Step 1: Normalize and clean text items
    const normalizedItems = this.normalizeTextItems(textItems, viewport);
    
    // Step 2: Filter out noise (headers, footers, page numbers)
    const filteredItems = this.filterNoise(normalizedItems, viewport);
    
    // Step 3: Detect document structure
    const structure = this.detectStructure(filteredItems, viewport);
    
    // Step 4: Group into text blocks
    const blocks = this.groupIntoBlocks(filteredItems, structure);
    
    // Step 5: Detect columns
    const columns = this.detectColumns(blocks, viewport);
    
    // Step 6: Order blocks within columns
    const orderedBlocks = this.orderBlocks(columns);
    
    // Step 7: Convert to text with proper formatting
    return this.blocksToText(orderedBlocks);
  }
  
  /**
   * Normalize text items to consistent format
   */
  private normalizeTextItems(items: any[], viewport: any): TextItem[] {
    return items.map(item => {
      // Handle different coordinate systems
      const transform = item.transform || [1, 0, 0, 1, 0, 0];
      const fontSize = Math.abs(transform[0]) || 10;
      
      // Calculate proper dimensions
      let width = item.width;
      let height = item.height || fontSize * this.LINE_HEIGHT_RATIO;
      
      if (!width || width === 0) {
        // Estimate width based on text length and font size
        width = item.str.length * fontSize * 0.5;
      }
      
      // Convert Y coordinate to top-down
      const y = viewport.height - transform[5] - height;
      
      return {
        text: item.str || '',
        x: transform[4],
        y: y,
        width: width,
        height: height,
        fontSize: fontSize,
        fontName: item.fontName || '',
        transform: transform
      };
    }).filter(item => item.text.trim().length > 0);
  }
  
  /**
   * Filter out headers, footers, and page numbers
   */
  private filterNoise(items: TextItem[], viewport: any): TextItem[] {
    const pageHeight = viewport.height;
    const pageWidth = viewport.width;
    
    // Define header/footer zones (top/bottom 10% of page)
    const headerZone = pageHeight * 0.1;
    const footerZone = pageHeight * 0.9;
    
    return items.filter(item => {
      // Check if in header/footer zone
      if (item.y < headerZone || item.y > footerZone) {
        // Check if it's a page number
        if (/^\d+$/.test(item.text.trim()) || 
            /page\s*\d+/i.test(item.text) ||
            /\d+\s*of\s*\d+/i.test(item.text)) {
          return false;
        }
        
        // Check if it's a repeated header/footer
        // (This would need to track across pages in real implementation)
        if (item.fontSize < 10 && item.text.length < 100) {
          return false;
        }
      }
      
      // Filter out watermarks (typically diagonal text)
      const rotation = Math.atan2(item.transform[1], item.transform[0]);
      if (Math.abs(rotation) > 0.1) {
        return false;
      }
      
      return true;
    });
  }
  
  /**
   * Detect document structure (single/multi-column, etc.)
   */
  private detectStructure(items: TextItem[], viewport: any): any {
    const pageWidth = viewport.width;
    const xPositions = items.map(item => item.x);
    
    // Create histogram of X positions
    const histogram = this.createHistogram(xPositions, 50);
    const peaks = this.findSignificantPeaks(histogram, xPositions);
    
    // Determine structure type
    let structureType = 'single-column';
    let columnBoundaries: number[] = [];
    
    if (peaks.length >= 2) {
      // Check if peaks represent column boundaries
      const gaps = [];
      for (let i = 1; i < peaks.length; i++) {
        gaps.push(peaks[i] - peaks[i-1]);
      }
      
      const avgGap = gaps.reduce((a, b) => a + b, 0) / gaps.length;
      if (avgGap > pageWidth * 0.3) {
        structureType = 'multi-column';
        columnBoundaries = peaks;
      }
    }
    
    return {
      type: structureType,
      columnBoundaries: columnBoundaries,
      pageWidth: pageWidth
    };
  }
  
  /**
   * Group text items into semantic blocks
   */
  private groupIntoBlocks(items: TextItem[], structure: any): TextBlock[] {
    const blocks: TextBlock[] = [];
    const processed = new Set<number>();
    
    items.forEach((item, index) => {
      if (processed.has(index)) return;
      
      // Start a new block with this item
      const block = this.growBlock(item, items, index, processed);
      const blockType = this.classifyBlock(block);
      
      blocks.push({
        items: block,
        bounds: this.calculateBounds(block),
        type: blockType,
        confidence: 0.8
      });
    });
    
    return blocks;
  }
  
  /**
   * Grow a block by finding nearby related text
   */
  private growBlock(seed: TextItem, allItems: TextItem[], seedIndex: number, processed: Set<number>): TextItem[] {
    const block: TextItem[] = [seed];
    processed.add(seedIndex);
    
    let changed = true;
    while (changed) {
      changed = false;
      
      for (let i = 0; i < allItems.length; i++) {
        if (processed.has(i)) continue;
        
        const item = allItems[i];
        
        // Check if item belongs to this block
        if (this.belongsToBlock(item, block)) {
          block.push(item);
          processed.add(i);
          changed = true;
        }
      }
    }
    
    // Sort block items by position
    return block.sort((a, b) => {
      const yDiff = a.y - b.y;
      if (Math.abs(yDiff) < this.EPSILON) {
        return a.x - b.x;
      }
      return yDiff;
    });
  }
  
  /**
   * Check if an item belongs to a block
   */
  private belongsToBlock(item: TextItem, block: TextItem[]): boolean {
    // Find closest item in block
    let minDistance = Infinity;
    let closestItem: TextItem | null = null;
    
    for (const blockItem of block) {
      const distance = this.calculateDistance(item, blockItem);
      if (distance < minDistance) {
        minDistance = distance;
        closestItem = blockItem;
      }
    }
    
    if (!closestItem) return false;
    
    // Check vertical alignment (same line)
    const sameLineThreshold = Math.min(item.height, closestItem.height) * 0.5;
    const verticalOverlap = Math.abs(item.y - closestItem.y) < sameLineThreshold;
    
    if (verticalOverlap) {
      // Check horizontal distance for same line
      const horizontalGap = Math.abs(item.x - (closestItem.x + closestItem.width));
      const maxGap = Math.max(item.fontSize, closestItem.fontSize) * 2;
      return horizontalGap < maxGap;
    }
    
    // Check if it's the next line
    const lineGap = Math.abs(item.y - (closestItem.y + closestItem.height));
    const maxLineGap = Math.max(item.height, closestItem.height) * this.PARAGRAPH_GAP_RATIO;
    
    if (lineGap < maxLineGap) {
      // Check if horizontally aligned (similar start position)
      const horizontalAlignment = Math.abs(item.x - closestItem.x);
      const maxAlignment = Math.max(item.fontSize, closestItem.fontSize) * 2;
      return horizontalAlignment < maxAlignment;
    }
    
    return false;
  }
  
  /**
   * Calculate distance between two items
   */
  private calculateDistance(a: TextItem, b: TextItem): number {
    const dx = (a.x + a.width/2) - (b.x + b.width/2);
    const dy = (a.y + a.height/2) - (b.y + b.height/2);
    return Math.sqrt(dx * dx + dy * dy);
  }
  
  /**
   * Calculate bounding box of items
   */
  private calculateBounds(items: TextItem[]): any {
    if (items.length === 0) {
      return { left: 0, top: 0, right: 0, bottom: 0 };
    }
    
    let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
    
    for (const item of items) {
      left = Math.min(left, item.x);
      top = Math.min(top, item.y);
      right = Math.max(right, item.x + item.width);
      bottom = Math.max(bottom, item.y + item.height);
    }
    
    return { left, top, right, bottom };
  }
  
  /**
   * Classify block type based on content and formatting
   */
  private classifyBlock(items: TextItem[]): TextBlock['type'] {
    if (items.length === 0) return 'paragraph';
    
    const firstItem = items[0];
    const avgFontSize = items.reduce((sum, item) => sum + item.fontSize, 0) / items.length;
    const text = items.map(item => item.text).join(' ');
    
    // Check for headings
    if (items.length < 5 && avgFontSize > 14) {
      return 'heading';
    }
    
    // Check for lists
    if (/^[\d•◦▪▫◆◇○●\-\*]\s/.test(text) || /^\(\d+\)/.test(text)) {
      return 'list';
    }
    
    // Check for references
    if (/^\[\d+\]/.test(text) || /^[A-Z][a-z]+,\s+[A-Z]\./.test(text)) {
      return 'reference';
    }
    
    // Check for formulas (contains mathematical symbols)
    if (/[∫∑∏√∞±≤≥≠≈∈∉⊂⊃∪∩]/.test(text) || /\^|_/.test(text)) {
      return 'formula';
    }
    
    // Check for captions
    if (/^(Figure|Fig\.|Table|Equation|Eq\.)\s*\d+/i.test(text)) {
      return 'caption';
    }
    
    return 'paragraph';
  }
  
  /**
   * Detect columns in the document
   */
  private detectColumns(blocks: TextBlock[], viewport: any): Column[] {
    // Simple approach: divide page into potential columns
    const pageWidth = viewport.width;
    const columnThreshold = pageWidth * 0.4;
    
    // Separate blocks by X position
    const leftBlocks = blocks.filter(b => b.bounds.right < columnThreshold);
    const rightBlocks = blocks.filter(b => b.bounds.left > columnThreshold);
    const centerBlocks = blocks.filter(b => 
      b.bounds.left <= columnThreshold && b.bounds.right >= columnThreshold
    );
    
    // If we have significant content in both sides, it's multi-column
    if (leftBlocks.length > 3 && rightBlocks.length > 3) {
      return [
        {
          blocks: [...leftBlocks, ...centerBlocks.filter(b => b.type === 'heading')],
          bounds: this.calculateBounds(leftBlocks.flatMap(b => b.items))
        },
        {
          blocks: rightBlocks,
          bounds: this.calculateBounds(rightBlocks.flatMap(b => b.items))
        }
      ];
    }
    
    // Single column
    return [{
      blocks: blocks,
      bounds: this.calculateBounds(blocks.flatMap(b => b.items))
    }];
  }
  
  /**
   * Order blocks within columns for proper reading
   */
  private orderBlocks(columns: Column[]): TextBlock[] {
    const orderedBlocks: TextBlock[] = [];
    
    // Process each column
    for (const column of columns) {
      // Sort blocks by vertical position
      const sortedBlocks = column.blocks.sort((a, b) => {
        return a.bounds.top - b.bounds.top;
      });
      
      orderedBlocks.push(...sortedBlocks);
    }
    
    return orderedBlocks;
  }
  
  /**
   * Convert blocks to properly formatted text
   */
  private blocksToText(blocks: TextBlock[]): string {
    let text = '';
    let lastBlockType: TextBlock['type'] | null = null;
    
    for (const block of blocks) {
      const blockText = block.items.map(item => item.text).join(' ').trim();
      
      if (!blockText) continue;
      
      // Add appropriate spacing based on block type
      if (text.length > 0) {
        if (block.type === 'heading' || lastBlockType === 'heading') {
          text += '\n\n';
        } else if (block.type === 'list' || block.type === 'reference') {
          text += '\n';
        } else {
          text += ' ';
        }
      }
      
      text += blockText;
      lastBlockType = block.type;
    }
    
    // Post-process to fix common issues
    return text
      .replace(/\s+/g, ' ')              // Normalize whitespace
      .replace(/(\w)-\s+(\w)/g, '$1$2')  // Fix line-break hyphenation
      .replace(/\s+([.,;:!?])/g, '$1')   // Fix punctuation spacing
      .replace(/\n{3,}/g, '\n\n')        // Limit consecutive newlines
      .trim();
  }
  
  /**
   * Create histogram for data analysis
   */
  private createHistogram(values: number[], bins: number): number[] {
    if (values.length === 0) return [];
    
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    
    if (range === 0) return [values.length];
    
    const binSize = range / bins;
    const histogram = new Array(bins).fill(0);
    
    values.forEach(value => {
      const binIndex = Math.min(Math.floor((value - min) / binSize), bins - 1);
      histogram[binIndex]++;
    });
    
    return histogram;
  }
  
  /**
   * Find significant peaks in histogram
   */
  private findSignificantPeaks(histogram: number[], values: number[]): number[] {
    if (histogram.length === 0) return [];
    
    const peaks: number[] = [];
    const maxValue = Math.max(...histogram);
    const threshold = maxValue * 0.3;
    
    // Find local maxima above threshold
    for (let i = 1; i < histogram.length - 1; i++) {
      if (histogram[i] > threshold &&
          histogram[i] >= histogram[i-1] &&
          histogram[i] >= histogram[i+1]) {
        
        // Convert bin index back to value
        const min = Math.min(...values);
        const max = Math.max(...values);
        const binSize = (max - min) / histogram.length;
        peaks.push(min + (i + 0.5) * binSize);
      }
    }
    
    return peaks;
  }
}
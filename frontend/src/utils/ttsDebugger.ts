/**
 * Comprehensive TTS Debugging Utility
 * Helps identify and fix all text extraction issues
 */

interface TextItem {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fontSize: number;
  fontName: string;
  dir: string;
}

interface DebugInfo {
  pageNumber: number;
  totalItems: number;
  issues: string[];
  recommendations: string[];
}

export class TTSDebugger {
  private debugLog: string[] = [];
  private issues: Map<string, number> = new Map();

  public analyzeTextItems(items: TextItem[], pageNum: number): DebugInfo {
    const issues: string[] = [];
    const recommendations: string[] = [];
    
    // 1. Check for overlapping text items
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        if (this.areOverlapping(items[i], items[j])) {
          issues.push(`Overlapping text at (${items[i].x.toFixed(1)}, ${items[i].y.toFixed(1)}): "${items[i].text}" and "${items[j].text}"`);
        }
      }
    }
    
    // 2. Check for suspicious gaps
    const sortedByY = [...items].sort((a, b) => a.y - b.y);
    for (let i = 1; i < sortedByY.length; i++) {
      const gap = sortedByY[i].y - (sortedByY[i-1].y + sortedByY[i-1].height);
      if (gap > 100) {
        issues.push(`Large vertical gap (${gap.toFixed(1)}px) between "${sortedByY[i-1].text}" and "${sortedByY[i].text}"`);
      }
    }
    
    // 3. Check for text direction issues
    const rtlItems = items.filter(item => item.dir === 'rtl');
    if (rtlItems.length > 0) {
      issues.push(`Found ${rtlItems.length} RTL text items that may need special handling`);
      recommendations.push('Implement RTL text handling');
    }
    
    // 4. Check for very small or very large fonts
    const fontSizes = items.map(item => item.fontSize);
    const avgFontSize = fontSizes.reduce((a, b) => a + b, 0) / fontSizes.length;
    
    items.forEach(item => {
      if (item.fontSize < avgFontSize * 0.5) {
        issues.push(`Very small font (${item.fontSize.toFixed(1)}): "${item.text}"`);
      } else if (item.fontSize > avgFontSize * 2) {
        issues.push(`Very large font (${item.fontSize.toFixed(1)}): "${item.text}"`);
      }
    });
    
    // 5. Check for mathematical symbols and formulas
    const mathPatterns = [
      /[∫∑∏√∞±≤≥≠≈∈∉⊂⊃∪∩]/,
      /\\[a-zA-Z]+\{/,  // LaTeX commands
      /\^|_/,           // Superscripts/subscripts
      /[αβγδεζηθικλμνξοπρστυφχψω]/  // Greek letters
    ];
    
    items.forEach(item => {
      if (mathPatterns.some(pattern => pattern.test(item.text))) {
        issues.push(`Mathematical content detected: "${item.text}"`);
        recommendations.push('Add special handling for mathematical formulas');
      }
    });
    
    // 6. Check for headers and footers
    const pageHeight = Math.max(...items.map(item => item.y + item.height));
    const topItems = items.filter(item => item.y < pageHeight * 0.1);
    const bottomItems = items.filter(item => item.y > pageHeight * 0.9);
    
    if (topItems.length > 0) {
      const headerText = topItems.map(item => item.text).join(' ');
      if (headerText.match(/\d+/) || headerText.match(/page/i)) {
        issues.push(`Potential header detected: "${headerText}"`);
        recommendations.push('Consider filtering out headers');
      }
    }
    
    if (bottomItems.length > 0) {
      const footerText = bottomItems.map(item => item.text).join(' ');
      if (footerText.match(/\d+/) || footerText.match(/page/i)) {
        issues.push(`Potential footer detected: "${footerText}"`);
        recommendations.push('Consider filtering out footers');
      }
    }
    
    // 7. Check for columns
    const xPositions = items.map(item => item.x);
    const xHistogram = this.createHistogram(xPositions, 20);
    const peaks = this.findPeaks(xHistogram);
    
    if (peaks.length >= 2) {
      issues.push(`Detected ${peaks.length} potential columns at X positions: ${peaks.join(', ')}`);
      recommendations.push('Ensure column detection algorithm handles this layout');
    }
    
    // 8. Check for tables
    const alignedItems = this.findAlignedItems(items);
    if (alignedItems.length > 5) {
      issues.push(`Potential table detected with ${alignedItems.length} aligned items`);
      recommendations.push('Add table-specific text extraction');
    }
    
    return {
      pageNumber: pageNum,
      totalItems: items.length,
      issues,
      recommendations: [...new Set(recommendations)]
    };
  }
  
  private areOverlapping(a: TextItem, b: TextItem): boolean {
    return !(a.x + a.width < b.x || b.x + b.width < a.x ||
             a.y + a.height < b.y || b.y + b.height < a.y);
  }
  
  private createHistogram(values: number[], bins: number): number[] {
    const min = Math.min(...values);
    const max = Math.max(...values);
    const binSize = (max - min) / bins;
    const histogram = new Array(bins).fill(0);
    
    values.forEach(value => {
      const binIndex = Math.min(Math.floor((value - min) / binSize), bins - 1);
      histogram[binIndex]++;
    });
    
    return histogram;
  }
  
  private findPeaks(histogram: number[]): number[] {
    const peaks: number[] = [];
    const threshold = Math.max(...histogram) * 0.3;
    
    for (let i = 1; i < histogram.length - 1; i++) {
      if (histogram[i] > threshold &&
          histogram[i] >= histogram[i - 1] &&
          histogram[i] >= histogram[i + 1]) {
        peaks.push(i);
      }
    }
    
    return peaks;
  }
  
  private findAlignedItems(items: TextItem[]): TextItem[] {
    const aligned: TextItem[] = [];
    const tolerance = 2; // pixels
    
    for (const item of items) {
      const sameX = items.filter(i => 
        Math.abs(i.x - item.x) < tolerance && i !== item
      );
      const sameY = items.filter(i => 
        Math.abs(i.y - item.y) < tolerance && i !== item
      );
      
      if (sameX.length >= 2 || sameY.length >= 2) {
        aligned.push(item);
      }
    }
    
    return aligned;
  }
  
  public generateReport(): string {
    const issueCount = new Map<string, number>();
    
    this.issues.forEach((count, issue) => {
      issueCount.set(issue, count);
    });
    
    let report = '=== TTS Debug Report ===\n\n';
    report += 'Top Issues:\n';
    
    const sortedIssues = Array.from(issueCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    
    sortedIssues.forEach(([issue, count]) => {
      report += `- ${issue}: ${count} occurrences\n`;
    });
    
    report += '\n\nDebug Log:\n';
    report += this.debugLog.slice(-50).join('\n');
    
    return report;
  }
  
  public log(message: string): void {
    const timestamp = new Date().toISOString();
    this.debugLog.push(`[${timestamp}] ${message}`);
    console.log(`[TTS Debug] ${message}`);
  }
  
  public trackIssue(issue: string): void {
    this.issues.set(issue, (this.issues.get(issue) || 0) + 1);
  }
}
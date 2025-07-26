/**
 * TTS Fallback Handler
 * Ensures graceful degradation for any edge cases
 */

export class TTSFallbackHandler {
  /**
   * Clean and prepare text for TTS with multiple fallback strategies
   */
  public static prepareTextForTTS(text: string): string {
    if (!text) return '';
    
    try {
      // Strategy 1: Advanced cleaning
      let cleaned = this.advancedTextCleaning(text);
      
      // Strategy 2: Fix known problematic patterns
      cleaned = this.fixProblematicPatterns(cleaned);
      
      // Strategy 3: Ensure readable output
      cleaned = this.ensureReadability(cleaned);
      
      return cleaned;
    } catch (error) {
      console.error('TTS preparation error, using basic fallback:', error);
      // Ultimate fallback: basic cleaning
      return this.basicFallback(text);
    }
  }
  
  /**
   * Advanced text cleaning with all edge cases
   */
  private static advancedTextCleaning(text: string): string {
    return text
      // Fix encoding issues
      .replace(/â€™/g, "'")
      .replace(/â€œ/g, '"')
      .replace(/â€/g, '"')
      .replace(/â€"/g, '–')
      .replace(/â€"/g, '—')
      .replace(/Ã©/g, 'é')
      .replace(/Ã¨/g, 'è')
      .replace(/Ã¼/g, 'ü')
      .replace(/Ã¶/g, 'ö')
      .replace(/Ã¤/g, 'ä')
      
      // Fix mathematical symbols
      .replace(/\\alpha/g, 'α')
      .replace(/\\beta/g, 'β')
      .replace(/\\gamma/g, 'γ')
      .replace(/\\delta/g, 'δ')
      .replace(/\\sum/g, '∑')
      .replace(/\\int/g, '∫')
      .replace(/\\infty/g, '∞')
      .replace(/\\pm/g, '±')
      
      // Fix hyphenation
      .replace(/(\w+)-\s*\n\s*(\w+)/g, '$1$2')
      .replace(/(\w+)-\s+(\w+)/g, '$1$2')
      
      // Fix ligatures
      .replace(/ﬁ/g, 'fi')
      .replace(/ﬂ/g, 'fl')
      .replace(/ﬀ/g, 'ff')
      .replace(/ﬃ/g, 'ffi')
      .replace(/ﬄ/g, 'ffl')
      
      // Fix spacing issues
      .replace(/\s+/g, ' ')
      .replace(/\s+([.,;:!?])/g, '$1')
      .replace(/([.,;:!?])\s*([.,;:!?])/g, '$1$2')
      
      // Fix quotes
      .replace(/``/g, '"')
      .replace(/''/g, '"')
      .replace(/`/g, "'")
      
      // Remove control characters
      .replace(/[\x00-\x1F\x7F-\x9F]/g, '')
      
      // Fix common OCR errors
      .replace(/\bl\s+(?=[A-Z])/g, 'I ')  // l -> I at sentence start
      .replace(/\b0(?=[a-zA-Z])/g, 'O')   // 0 -> O
      .replace(/\b(?:[1l])(?=\s)/g, 'I')  // 1 or l -> I
      
      .trim();
  }
  
  /**
   * Fix known problematic patterns
   */
  private static fixProblematicPatterns(text: string): string {
    // Fix references that might be jumbled
    text = text.replace(/\[\s*(\d+)\s*\]/g, '[$1]');
    
    // Fix equations that might be broken
    text = text.replace(/(\w)\s*=\s*(\w)/g, '$1 = $2');
    
    // Fix URLs that might be broken
    text = text.replace(/https?\s*:\s*\/\s*\//g, 'https://');
    
    // Fix email addresses
    text = text.replace(/(\w+)\s*@\s*(\w+)/g, '$1@$2');
    
    // Fix numbered lists
    text = text.replace(/\n\s*(\d+)\s*\.\s*/g, '\n$1. ');
    
    // Fix bullet points
    text = text.replace(/\n\s*[•◦▪▫◆◇○●\-\*]\s*/g, '\n• ');
    
    // Fix parentheses spacing
    text = text.replace(/\(\s+/g, '(');
    text = text.replace(/\s+\)/g, ')');
    
    // Fix quote spacing
    text = text.replace(/"\s+/g, '"');
    text = text.replace(/\s+"/g, '"');
    
    return text;
  }
  
  /**
   * Ensure text is readable by TTS
   */
  private static ensureReadability(text: string): string {
    // Expand common abbreviations for better pronunciation
    const expansions: { [key: string]: string } = {
      'vs.': 'versus',
      'etc.': 'et cetera',
      'i.e.': 'that is',
      'e.g.': 'for example',
      'cf.': 'compare',
      'viz.': 'namely',
      'ca.': 'circa',
      'Inc.': 'Incorporated',
      'Corp.': 'Corporation',
      'Ltd.': 'Limited',
      'Co.': 'Company'
    };
    
    for (const [abbr, expansion] of Object.entries(expansions)) {
      const regex = new RegExp(`\\b${abbr.replace('.', '\\.')}`, 'gi');
      text = text.replace(regex, expansion);
    }
    
    // Handle special characters that TTS might struggle with
    text = text
      .replace(/–/g, ' dash ')
      .replace(/—/g, ' dash ')
      .replace(/…/g, '...')
      .replace(/™/g, ' trademark ')
      .replace(/®/g, ' registered ')
      .replace(/©/g, ' copyright ')
      .replace(/°/g, ' degrees ')
      .replace(/±/g, ' plus or minus ')
      .replace(/×/g, ' times ')
      .replace(/÷/g, ' divided by ')
      .replace(/≈/g, ' approximately ')
      .replace(/≠/g, ' not equal to ')
      .replace(/≤/g, ' less than or equal to ')
      .replace(/≥/g, ' greater than or equal to ')
      .replace(/∞/g, ' infinity ');
    
    return text;
  }
  
  /**
   * Basic fallback for when everything else fails
   */
  private static basicFallback(text: string): string {
    // Just ensure basic readability
    return text
      .replace(/[^\x20-\x7E\n]/g, ' ')  // Keep only printable ASCII + newlines
      .replace(/\s+/g, ' ')              // Normalize whitespace
      .replace(/\n+/g, '\n')             // Normalize newlines
      .trim();
  }
  
  /**
   * Validate extracted text and provide warnings
   */
  public static validateExtractedText(text: string): {
    isValid: boolean;
    warnings: string[];
    suggestions: string[];
  } {
    const warnings: string[] = [];
    const suggestions: string[] = [];
    
    // Check for common issues
    if (text.length === 0) {
      warnings.push('No text extracted');
      suggestions.push('Check if PDF is scanned or image-based');
    }
    
    // Check for garbled text
    const garbledRatio = (text.match(/[^\x20-\x7E\n]/g) || []).length / text.length;
    if (garbledRatio > 0.1) {
      warnings.push('High proportion of non-ASCII characters detected');
      suggestions.push('PDF might have encoding issues');
    }
    
    // Check for excessive whitespace
    if (text.includes('     ')) {
      warnings.push('Excessive whitespace detected');
      suggestions.push('Column detection might need adjustment');
    }
    
    // Check for broken words
    if ((text.match(/\w-\s+\w/g) || []).length > 5) {
      warnings.push('Multiple hyphenated words detected');
      suggestions.push('Line-break hyphenation might need fixing');
    }
    
    // Check for mathematical content
    if (text.match(/[∫∑∏√∞±≤≥≠≈]/)) {
      warnings.push('Mathematical symbols detected');
      suggestions.push('Consider using specialized math TTS');
    }
    
    return {
      isValid: warnings.length === 0,
      warnings,
      suggestions
    };
  }
}
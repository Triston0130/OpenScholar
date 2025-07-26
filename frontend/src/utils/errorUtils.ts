// src/utils/errorUtils.ts
export const createNetworkError = (response: Response): Error => {
  return new Error(`Network error: ${response.status} ${response.statusText}`);
};

export const createValidationError = (message: string, field?: string): Error => {
  const fullMessage = field ? `${field}: ${message}` : message;
  return new Error(`Validation error: ${fullMessage}`);
};

export const createAPIError = (message: string, endpoint?: string): Error => {
  const fullMessage = endpoint ? `API error at ${endpoint}: ${message}` : `API error: ${message}`;
  return new Error(fullMessage);
};

export const isNetworkError = (error: unknown): boolean => {
  return error instanceof Error && 
    (error.message.includes('fetch') || 
     error.message.includes('Network') || 
     error.name === 'NetworkError');
};

export const sanitizeErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    // Remove sensitive information from error messages
    return error.message
      .replace(/api[_-]?key[s]?[=:]\s*[\w-]+/gi, 'api_key=***')
      .replace(/token[s]?[=:]\s*[\w-]+/gi, 'token=***')
      .replace(/password[s]?[=:]\s*[\w-]+/gi, 'password=***');
  }
  
  if (typeof error === 'string') {
    return error
      .replace(/api[_-]?key[s]?[=:]\s*[\w-]+/gi, 'api_key=***')
      .replace(/token[s]?[=:]\s*[\w-]+/gi, 'token=***')
      .replace(/password[s]?[=:]\s*[\w-]+/gi, 'password=***');
  }
  
  return 'An unknown error occurred';
};

// Rate limiting utilities
export const withRetry = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt === maxRetries) {
        throw lastError;
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
    }
  }
  
  throw lastError!;
};

// Input validation utilities
export const validateSearchQuery = (query: string): string | null => {
  if (!query || !query.trim()) {
    return 'Search query cannot be empty';
  }
  
  if (query.length > 500) {
    return 'Search query too long (maximum 500 characters)';
  }
  
  // Check for potentially dangerous patterns
  const forbiddenPatterns = [
    /<script[^>]*>/i,
    /javascript:/i,
    /vbscript:/i,
  ];
  
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(query)) {
      return 'Search query contains invalid characters';
    }
  }
  
  return null;
};

export const validateYear = (year: number | null): string | null => {
  if (year === null) return null;
  
  const currentYear = new Date().getFullYear();
  if (year < 1900 || year > currentYear + 1) {
    return `Year must be between 1900 and ${currentYear + 1}`;
  }
  
  return null;
};

export const validateYearRange = (startYear: number | null, endYear: number | null): string | null => {
  if (startYear === null || endYear === null) return null;
  
  const startError = validateYear(startYear);
  if (startError) return startError;
  
  const endError = validateYear(endYear);
  if (endError) return endError;
  
  if (startYear > endYear) {
    return 'Start year cannot be greater than end year';
  }
  
  return null;
};

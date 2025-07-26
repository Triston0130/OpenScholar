// src/hooks/useErrorHandler.ts
import { useState, useCallback } from 'react';

export interface AppError {
  message: string;
  type: 'network' | 'validation' | 'api' | 'unknown';
  details?: any;
  timestamp: Date;
}

export const useErrorHandler = () => {
  const [errors, setErrors] = useState<AppError[]>([]);

  const handleError = useCallback((error: unknown, type: AppError['type'] = 'unknown') => {
    let message = 'An unexpected error occurred';
    let details;

    if (error instanceof Error) {
      message = error.message;
      details = error.stack;
    } else if (typeof error === 'string') {
      message = error;
    } else {
      details = error;
    }

    const appError: AppError = {
      message,
      type,
      details,
      timestamp: new Date()
    };

    setErrors(prev => [...prev, appError]);

    // Log error
    console.error('Application error:', appError);

    return appError;
  }, []);

  const clearError = useCallback((index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index));
  }, []);

  const clearAllErrors = useCallback(() => {
    setErrors([]);
  }, []);

  return {
    errors,
    handleError,
    clearError,
    clearAllErrors
  };
};

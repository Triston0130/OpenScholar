// src/components/ErrorDisplay.tsx
import React, { useEffect } from 'react';
import { AppError } from '../hooks/useErrorHandler';

interface ErrorToastProps {
  error: AppError;
  onClose: () => void;
  autoCloseMs?: number;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({ 
  error, 
  onClose, 
  autoCloseMs = 5000 
}) => {
  useEffect(() => {
    if (autoCloseMs > 0) {
      const timer = setTimeout(onClose, autoCloseMs);
      return () => clearTimeout(timer);
    }
  }, [onClose, autoCloseMs]);

  const getErrorIcon = (type: AppError['type']) => {
    switch (type) {
      case 'network': return '🌐';
      case 'validation': return '⚠️';
      case 'api': return '🔧';
      default: return '❌';
    }
  };

  const getErrorColor = (type: AppError['type']) => {
    switch (type) {
      case 'network': return 'bg-blue-100 border-blue-500 text-blue-800';
      case 'validation': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'api': return 'bg-red-100 border-red-500 text-red-800';
      default: return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  return (
    <div className={`error-toast ${getErrorColor(error.type)} border-l-4 p-4 mb-2 rounded shadow-lg animate-slide-in max-w-md`}>
      <div className="flex items-start">
        <span className="flex-shrink-0 text-lg mr-3">
          {getErrorIcon(error.type)}
        </span>
        <div className="flex-1">
          <h4 className="font-semibold text-sm">
            {error.type.charAt(0).toUpperCase() + error.type.slice(1)} Error
          </h4>
          <p className="text-sm mt-1">{error.message}</p>
          {process.env.NODE_ENV === 'development' && error.details && (
            <details className="mt-2">
              <summary className="text-xs cursor-pointer">Details</summary>
              <pre className="text-xs mt-1 bg-gray-800 text-white p-2 rounded overflow-auto max-h-32">
                {typeof error.details === 'string' ? error.details : JSON.stringify(error.details, null, 2)}
              </pre>
            </details>
          )}
        </div>
        <button 
          onClick={onClose}
          className="flex-shrink-0 ml-4 text-gray-500 hover:text-gray-700 text-lg leading-none"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

interface ErrorDisplayProps {
  errors: AppError[];
  onClearError: (index: number) => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ errors, onClearError }) => {
  if (errors.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      {errors.map((error, index) => (
        <ErrorToast
          key={`${error.timestamp.getTime()}-${index}`}
          error={error}
          onClose={() => onClearError(index)}
        />
      ))}
    </div>
  );
};

// Retry wrapper component
interface RetryWrapperProps {
  children: React.ReactNode;
  maxRetries?: number;
  onRetry?: () => void | Promise<void>;
  retryDelay?: number;
}

export const RetryWrapper: React.FC<RetryWrapperProps> = ({
  children,
  maxRetries = 3,
  onRetry,
  retryDelay = 1000
}) => {
  const [retryCount, setRetryCount] = React.useState(0);
  const [isRetrying, setIsRetrying] = React.useState(false);

  const handleRetry = async () => {
    if (retryCount >= maxRetries) return;
    
    setIsRetrying(true);
    
    try {
      if (onRetry) {
        await onRetry();
      }
      
      // Add delay before retry
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      
      setRetryCount(prev => prev + 1);
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div className="retry-wrapper">
      {children}
      {/* This would typically be rendered by an error boundary fallback */}
    </div>
  );
};

export default ErrorDisplay;

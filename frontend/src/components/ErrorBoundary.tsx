// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
    
    // Log error to external service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error tracking service (Sentry, LogRocket, etc.)
      this.logErrorToService(error, errorInfo);
    }
    
    this.setState({
      error,
      errorInfo
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private logErrorToService(error: Error, errorInfo: ErrorInfo) {
    // TODO: Implement actual error logging service
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };
    
    console.error('Production error logged:', errorData);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  public render() {
    if (this.state.hasError) {
      // Render custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary p-8 text-center bg-red-50 border border-red-200 rounded-lg max-w-2xl mx-auto mt-8">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-red-800 mb-4">Something went wrong</h2>
          <p className="text-red-700 mb-6">We're sorry, but something unexpected happened.</p>
          
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="text-left bg-gray-800 text-white p-4 rounded mb-4">
              <summary className="cursor-pointer font-semibold">Error Details (Development)</summary>
              <pre className="mt-2 text-sm overflow-auto">{this.state.error.toString()}</pre>
              <pre className="mt-2 text-sm overflow-auto">{this.state.errorInfo?.componentStack}</pre>
            </details>
          )}
          
          <div className="space-x-4">
            <button 
              onClick={this.handleRetry}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
            >
              Try Again
            </button>
            <button 
              onClick={() => window.location.reload()}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Search-specific error boundary
interface SearchErrorBoundaryProps {
  children: ReactNode;
  onSearchError?: (error: Error) => void;
}

export const SearchErrorBoundary: React.FC<SearchErrorBoundaryProps> = ({ 
  children, 
  onSearchError 
}) => {
  const fallback = (
    <div className="search-error-fallback bg-yellow-50 border border-yellow-200 rounded-lg p-6 mx-4">
      <div className="text-center">
        <div className="text-4xl mb-3">🔍</div>
        <h3 className="text-lg font-semibold text-yellow-800 mb-2">Search Error</h3>
        <p className="text-yellow-700 mb-4">There was a problem with your search. Please try again with different terms.</p>
        <div className="text-left bg-white p-4 rounded border">
          <h4 className="font-semibold text-yellow-800 mb-2">Suggestions:</h4>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• Check your spelling</li>
            <li>• Try broader search terms</li>
            <li>• Remove special characters</li>
            <li>• Try searching for different keywords</li>
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <ErrorBoundary fallback={fallback} onError={onSearchError}>
      {children}
    </ErrorBoundary>
  );
};

export default ErrorBoundary;

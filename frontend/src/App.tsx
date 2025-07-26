import React, { useState, useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import LandingPage from './pages/LandingPage';
import FlashcardsPage from './pages/FlashcardsPage';
import { ErrorBoundary, SearchErrorBoundary } from './components/ErrorBoundary';
import { ErrorDisplay } from './components/ErrorDisplay';
import { useErrorHandler } from './hooks/useErrorHandler';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { initializeBackupSystem } from './utils/collectionBackup';

type PageType = 'search' | 'flashcards' | 'landing';

function AppContent() {
  const { errors, clearError } = useErrorHandler();
  const { isAuthenticated, isLoading } = useAuth();
  const [currentPage, setCurrentPage] = useState<PageType>('search');

  // Initialize backup system on app start
  useEffect(() => {
    initializeBackupSystem();
  }, []);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Pass navigation function to child components
  const navigate = (page: PageType) => {
    setCurrentPage(page);
  };

  return (
    <div className="App">
      {/* Global error display */}
      <ErrorDisplay errors={errors} onClearError={clearError} />
      
      {/* Show appropriate page based on state */}
      {!isAuthenticated ? (
        <LandingPage />
      ) : currentPage === 'flashcards' ? (
        <FlashcardsPage onNavigate={navigate} />
      ) : (
        <SearchErrorBoundary>
          <SearchPage onNavigate={navigate} />
        </SearchErrorBoundary>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <ErrorBoundary>
        <AppContent />
      </ErrorBoundary>
    </AuthProvider>
  );
}

export default App;

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import AuthModal from '../components/AuthModal';

const LandingPage: React.FC = () => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleShowLogin = () => {
    setAuthMode('login');
    setShowAuthModal(true);
  };

  const handleShowRegister = () => {
    setAuthMode('register');
    setShowAuthModal(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Logo/Title */}
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            OpenScholar
          </h1>
          <p className="text-xl text-gray-700 mb-12">
            Your AI-powered academic research assistant
          </p>

          {/* Hero Section */}
          <div className="bg-white rounded-lg shadow-xl p-8 mb-12">
            <h2 className="text-3xl font-semibold text-gray-800 mb-6">
              Discover Academic Papers with Ease
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Search across multiple databases including arXiv, PubMed, CrossRef, and more.
              Save papers to collections, export citations, and accelerate your research.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleShowLogin}
                className="px-8 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={handleShowRegister}
                className="px-8 py-3 bg-gray-800 text-white font-medium rounded-md hover:bg-gray-900 transition-colors"
              >
                Create Account
              </button>
            </div>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold mb-2">Multi-Database Search</h3>
              <p className="text-gray-600">
                Search across arXiv, PubMed, Semantic Scholar, and more from one interface
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-xl font-semibold mb-2">Organize Collections</h3>
              <p className="text-gray-600">
                Save papers to custom collections and manage your research library
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-semibold mb-2">Export Citations</h3>
              <p className="text-gray-600">
                Export citations in BibTeX, CSV, or JSON format for your papers
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />
    </div>
  );
};

export default LandingPage;
import React, { useState, useEffect } from 'react';
import { getApiKeys, saveApiKeys, getApiKey } from '../utils/apiKeys';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceId?: string;
}

interface ApiKeyConfig {
  id: string;
  name: string;
  description: string;
  helpUrl: string;
}

const API_KEY_CONFIGS: Record<string, ApiKeyConfig> = {
  'BHL': {
    id: 'BHL',
    name: 'Biodiversity Heritage Library',
    description: 'Access to natural history and biodiversity literature',
    helpUrl: 'https://www.biodiversitylibrary.org/api3/docs/docs.html'
  },
  'BioMed Central': {
    id: 'BioMed Central',
    name: 'BioMed Central (Springer Nature)',
    description: 'Open access biomedical research articles',
    helpUrl: 'https://dev.springernature.com/'
  },
  'BASE': {
    id: 'BASE',
    name: 'BASE Academic Search',
    description: 'Academic search engine (requires IP whitelisting)',
    helpUrl: 'https://www.base-search.net/about/download/base_interface.pdf'
  },
  'MIT OpenCourseWare': {
    id: 'MIT OpenCourseWare',
    name: 'MIT OpenCourseWare',
    description: 'Full-text search of MIT course materials using Google Custom Search Engine',
    helpUrl: '/mit-ocw-setup.html'
  },
  'MERLOT': {
    id: 'MERLOT',
    name: 'MERLOT',
    description: 'Multimedia Educational Resource for Learning and Online Teaching',
    helpUrl: 'https://info.merlot.org/merlothelp/topic.htm#t=MERLOT_REST_APIs.htm'
  },
  'OER Commons': {
    id: 'OER Commons',
    name: 'OER Commons',
    description: 'Open Educational Resources from various institutions',
    helpUrl: 'https://www.oercommons.org/api-docs'
  },
  'CORE': {
    id: 'CORE',
    name: 'CORE',
    description: 'World\'s largest collection of open access research papers',
    helpUrl: 'https://core.ac.uk/documentation'
  },
  'Google Search': {
    id: 'Google Search',
    name: 'Google Custom Search',
    description: 'Search the web for PDF-only academic papers using Google Custom Search API',
    helpUrl: 'https://developers.google.com/custom-search/v1/introduction'
  }
};

const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ isOpen, onClose, sourceId }) => {
  const [apiKey, setApiKey] = useState('');
  const [searchEngineId, setSearchEngineId] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const config = sourceId ? API_KEY_CONFIGS[sourceId] : null;
  const isGoogleSearch = sourceId === 'Google Search';

  useEffect(() => {
    if (isOpen && sourceId) {
      if (isGoogleSearch) {
        // For Google Search, load both API key and Search Engine ID
        const existingKey = getApiKey(sourceId) || '';
        const searchEngineKey = getApiKey(`${sourceId}_ENGINE_ID`) || '';
        setApiKey(existingKey);
        setSearchEngineId(searchEngineKey);
      } else {
        const existingKey = getApiKey(sourceId) || '';
        setApiKey(existingKey);
      }
      setSaved(false);
      setShowKey(false);
    }
  }, [isOpen, sourceId, isGoogleSearch]);

  const handleSave = async () => {
    if (!sourceId) return;
    
    setSaving(true);
    try {
      const allKeys = getApiKeys();
      let updatedKeys;
      
      if (isGoogleSearch) {
        // For Google Search, save both API key and Search Engine ID
        updatedKeys = {
          ...allKeys,
          [sourceId]: apiKey,
          [`${sourceId}_ENGINE_ID`]: searchEngineId
        };
      } else {
        updatedKeys = {
          ...allKeys,
          [sourceId]: apiKey
        };
      }
      
      saveApiKeys(updatedKeys);
      setSaved(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to save API key:', error);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !config) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Configure {config.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="px-6 py-4">
          <div className="mb-4">
            <p className="text-sm text-gray-600">{config.description}</p>
            <a
              href={config.helpUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 mt-2 inline-flex items-center"
            >
              Get API key
              <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
              </svg>
            </a>
          </div>

          {isGoogleSearch ? (
            // Special handling for Google Search - requires both API Key and Search Engine ID
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Search API Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your Google Search API key"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showKey ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.542 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Custom Search Engine ID
                </label>
                <input
                  type="text"
                  value={searchEngineId}
                  onChange={(e) => setSearchEngineId(e.target.value)}
                  placeholder="Enter your Custom Search Engine ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-xs text-amber-800">
                  <strong>Setup Instructions:</strong><br/>
                  1. Get API key from Google Cloud Console<br/>
                  2. Create Custom Search Engine at cse.google.com<br/>
                  3. Configure it to search the entire web<br/>
                  4. Copy both credentials here
                </p>
              </div>
            </div>
          ) : (
            // Standard single API key input for other sources
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={config.id === 'BASE' ? 'IP whitelisting required' : 'Enter API key'}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={config.id === 'BASE'}
              />
              {config.id !== 'BASE' && (
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKey ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.542 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  )}
                </button>
              )}
            </div>
          )}

          {config.id === 'BASE' && (
            <p className="text-xs text-gray-500 mt-2">
              BASE requires IP address whitelisting. Please register your IP address at their website.
            </p>
          )}

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              Your API key is stored locally in your browser and never sent to our servers.
            </p>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || (isGoogleSearch ? (!apiKey.trim() || !searchEngineId.trim()) : !apiKey.trim())}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {saving ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </>
            ) : saved ? (
              <>
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Saved!
              </>
            ) : (
              'Save API Keys'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiKeyModal;
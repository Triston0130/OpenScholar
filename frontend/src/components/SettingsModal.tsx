import React, { useState, useEffect } from 'react';
import { getProxySettings, saveProxySettings, ProxySettings, validateProxyUrl, suggestProxyUrl, getAlternativeProxyPatterns } from '../utils/proxy';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [proxyUrl, setProxyUrl] = useState('');
  const [institutionName, setInstitutionName] = useState('');
  const [isEnabled, setIsEnabled] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [suggestedUrl, setSuggestedUrl] = useState<string | null>(null);
  const [alternativeUrls, setAlternativeUrls] = useState<string[]>([]);
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    if (isOpen) {
      const settings = getProxySettings();
      setProxyUrl(settings.proxyUrl || '');
      setInstitutionName(settings.institutionName || '');
      setIsEnabled(settings.enabled || false);
    }
  }, [isOpen]);

  const handleProxyUrlChange = (newUrl: string) => {
    setProxyUrl(newUrl);
    setValidationError(null);
    
    if (newUrl.trim()) {
      const validation = validateProxyUrl(newUrl);
      if (!validation.isValid) {
        setValidationError(validation.error || 'Invalid URL');
      } else if (validation.corrected) {
        // Auto-correct the URL
        setProxyUrl(validation.corrected);
      }
    }
  };

  const handleEmailChange = (email: string) => {
    setUserEmail(email);
    const suggestion = suggestProxyUrl(email);
    setSuggestedUrl(suggestion);
    
    // Get alternative URLs for this domain
    if (email.includes('@')) {
      const domain = email.split('@')[1];
      const alternatives = getAlternativeProxyPatterns(domain);
      setAlternativeUrls(alternatives);
    } else {
      setAlternativeUrls([]);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    
    // Final validation
    if (isEnabled && proxyUrl.trim()) {
      const validation = validateProxyUrl(proxyUrl);
      if (!validation.isValid) {
        setValidationError(validation.error || 'Invalid URL');
        setIsSaving(false);
        return;
      }
    }
    
    const settings: ProxySettings = {
      proxyUrl: proxyUrl.trim(),
      institutionName: institutionName.trim(),
      enabled: isEnabled && proxyUrl.trim().length > 0
    };
    
    saveProxySettings(settings);
    
    // Simulate save delay
    await new Promise(resolve => setTimeout(resolve, 300));
    setIsSaving(false);
    onClose();
  };

  const handleClose = () => {
    // Reset form to saved values
    const settings = getProxySettings();
    setProxyUrl(settings.proxyUrl || '');
    setInstitutionName(settings.institutionName || '');
    setIsEnabled(settings.enabled || false);
    setValidationError(null);
    setSuggestedUrl(null);
    setAlternativeUrls([]);
    setUserEmail('');
    onClose();
  };

  const commonProxyExamples = [
    { name: 'EZproxy Standard', url: 'https://your-library.ezproxy.org/login?url=' },
    { name: 'LibProxy', url: 'https://libproxy.university.edu/login?url=' },
    { name: 'Proxy with Port', url: 'https://proxy.university.edu:2048/login?url=' }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            University Access Settings
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Enable Toggle */}
            <div className="flex items-center">
              <input
                id="enableProxy"
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => setIsEnabled(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="enableProxy" className="ml-3 text-sm font-medium text-gray-700">
                Enable university proxy access
              </label>
            </div>

            {/* Institution Name */}
            <div>
              <label htmlFor="institutionName" className="block text-sm font-medium text-gray-700 mb-2">
                Institution Name (Optional)
              </label>
              <input
                id="institutionName"
                type="text"
                value={institutionName}
                onChange={(e) => setInstitutionName(e.target.value)}
                placeholder="e.g., University of California, Sacramento"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Email for Auto-Detection */}
            <div>
              <label htmlFor="userEmail" className="block text-sm font-medium text-gray-700 mb-2">
                University Email (Optional - for auto-detection)
              </label>
              <input
                id="userEmail"
                type="email"
                value={userEmail}
                onChange={(e) => handleEmailChange(e.target.value)}
                placeholder="e.g., student@university.edu"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
              {suggestedUrl && (
                <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-sm text-green-800 font-medium">Suggested proxy URL:</p>
                  <p className="text-xs text-green-700 font-mono mt-1">{suggestedUrl}</p>
                  <button
                    onClick={() => handleProxyUrlChange(suggestedUrl)}
                    className="text-xs text-green-600 hover:text-green-800 font-medium mt-1"
                  >
                    Use This URL
                  </button>
                </div>
              )}
              
              {alternativeUrls.length > 0 && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-800 font-medium">Alternative proxy URLs for your institution:</p>
                  <div className="mt-2 space-y-1">
                    {alternativeUrls.map((url, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <p className="text-xs text-yellow-700 font-mono">{url}</p>
                        <button
                          onClick={() => handleProxyUrlChange(url)}
                          className="text-xs text-yellow-600 hover:text-yellow-800 font-medium ml-2"
                        >
                          Try This
                        </button>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-yellow-600 mt-2">
                    💡 Try different URLs if one doesn't work. Contact your library if none work.
                  </p>
                </div>
              )}
            </div>

            {/* Proxy URL */}
            <div>
              <label htmlFor="proxyUrl" className="block text-sm font-medium text-gray-700 mb-2">
                EZproxy URL <span className="text-red-500">*</span>
              </label>
              <input
                id="proxyUrl"
                type="url"
                value={proxyUrl}
                onChange={(e) => handleProxyUrlChange(e.target.value)}
                placeholder="https://libproxy.university.edu/login?url="
                className={`w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 ${
                  validationError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'
                }`}
              />
              {validationError ? (
                <p className="mt-1 text-xs text-red-600">{validationError}</p>
              ) : (
                <p className="mt-1 text-xs text-gray-500">
                  This URL should end with "login?url=" or similar parameter for the target URL
                </p>
              )}
            </div>

            {/* Common Examples */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Common EZproxy URL formats:</h4>
              <div className="space-y-2">
                {commonProxyExamples.map((example, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{example.name}</div>
                      <div className="text-xs text-gray-500 font-mono">{example.url}</div>
                    </div>
                    <button
                      onClick={() => handleProxyUrlChange(example.url)}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Use This
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Help Text */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-blue-900 mb-2">How to find your proxy URL:</h4>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Visit your university library's website</li>
                <li>Look for "Off-campus access" or "Remote access" links</li>
                <li>The URL usually contains "ezproxy", "libproxy", or "idm"</li>
                <li>Contact your library's IT support if you need help</li>
              </ol>
            </div>

            {/* Troubleshooting for CSUS */}
            <div className="bg-orange-50 border border-orange-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-orange-900 mb-2">🔧 Troubleshooting Common Issues:</h4>
              <div className="text-sm text-orange-800 space-y-2">
                <p><strong>For CSU Sacramento students:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Try: <code className="bg-orange-100 px-1 rounded">https://csus.idm.oclc.org/login?url=</code></li>
                  <li>Alternative: <code className="bg-orange-100 px-1 rounded">https://libproxy.csus.edu/login?url=</code></li>
                  <li>If neither works, check the CSUS Library website for current proxy instructions</li>
                </ul>
                <p className="mt-2"><strong>If you get "can't find server" errors:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Make sure you're connected to the internet</li>
                  <li>Try accessing the proxy URL directly in your browser first</li>
                  <li>Some proxies only work from on-campus or VPN connections</li>
                  <li>Contact your library's IT support for current proxy information</li>
                </ul>
              </div>
            </div>

            {/* Preview */}
            {proxyUrl && (
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Preview:</h4>
                <div className="text-xs text-gray-600 font-mono break-all">
                  {proxyUrl}https://doi.org/10.1016/j.example.2024.001
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || (isEnabled && !proxyUrl.trim()) || !!validationError}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
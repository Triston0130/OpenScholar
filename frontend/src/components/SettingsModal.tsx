import React, { useState, useEffect } from 'react';
import { getProxySettings, saveProxySettings, ProxySettings } from '../utils/proxy';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [proxyUrl, setProxyUrl] = useState('');
  const [institutionName, setInstitutionName] = useState('');
  const [isEnabled, setIsEnabled] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const settings = getProxySettings();
      setProxyUrl(settings.proxyUrl || '');
      setInstitutionName(settings.institutionName || '');
      setIsEnabled(settings.enabled || false);
    }
  }, [isOpen]);

  const handleSave = async () => {
    setIsSaving(true);
    
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

            {/* Proxy URL */}
            <div>
              <label htmlFor="proxyUrl" className="block text-sm font-medium text-gray-700 mb-2">
                EZproxy URL <span className="text-red-500">*</span>
              </label>
              <input
                id="proxyUrl"
                type="url"
                value={proxyUrl}
                onChange={(e) => setProxyUrl(e.target.value)}
                placeholder="https://libproxy.university.edu/login?url="
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                This URL should end with "login?url=" or similar parameter for the target URL
              </p>
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
                      onClick={() => setProxyUrl(example.url)}
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
                <li>The URL usually contains "ezproxy" or "libproxy"</li>
                <li>Contact your library's IT support if you need help</li>
              </ol>
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
            disabled={isSaving || (isEnabled && !proxyUrl.trim())}
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
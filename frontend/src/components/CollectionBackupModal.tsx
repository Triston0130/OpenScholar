import React, { useState, useEffect } from 'react';
import { 
  listBackups, 
  restoreFromBackup, 
  exportCollections, 
  importCollections,
  validateCollections,
  createBackup
} from '../utils/collectionBackup';
import toast from 'react-hot-toast';

interface BackupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRestore?: () => void;
}

const CollectionBackupModal: React.FC<BackupModalProps> = ({
  isOpen,
  onClose,
  onRestore
}) => {
  const [backups, setBackups] = useState<Array<{ key: string; metadata: any }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [validation, setValidation] = useState<{ isValid: boolean; issues: string[] } | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadBackups();
      checkValidation();
    }
  }, [isOpen]);

  const loadBackups = () => {
    const availableBackups = listBackups();
    setBackups(availableBackups);
  };

  const checkValidation = () => {
    const result = validateCollections();
    setValidation(result);
  };

  const handleRestore = async (backupKey: string) => {
    if (!window.confirm('This will replace your current collections. Are you sure?')) {
      return;
    }

    setIsLoading(true);
    try {
      const success = restoreFromBackup(backupKey);
      if (success) {
        toast.success('Collections restored successfully!');
        onRestore?.();
        onClose();
      } else {
        toast.error('Failed to restore backup');
      }
    } catch (error) {
      toast.error('Error restoring backup');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = (format: 'json' | 'readable') => {
    try {
      exportCollections(format);
      toast.success(`Collections exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export collections');
    }
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!window.confirm('This will replace your current collections. Are you sure?')) {
      return;
    }

    setIsLoading(true);
    importCollections(file)
      .then(success => {
        if (success) {
          toast.success('Collections imported successfully!');
          loadBackups();
          checkValidation();
          onRestore?.();
        } else {
          toast.error('Failed to import collections');
        }
      })
      .finally(() => setIsLoading(false));
  };

  const handleCreateBackup = () => {
    setIsLoading(true);
    try {
      const backupKey = createBackup();
      if (backupKey) {
        toast.success('Backup created successfully!');
        loadBackups();
      } else {
        toast.error('Failed to create backup');
      }
    } catch (error) {
      toast.error('Error creating backup');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Collection Backup & Recovery
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {/* Validation Status */}
          {validation && (
            <div className={`mb-6 p-4 rounded-lg ${
              validation.isValid 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <h4 className={`font-medium ${
                validation.isValid ? 'text-green-800' : 'text-yellow-800'
              }`}>
                {validation.isValid ? '✅ Collections are healthy' : '⚠️ Collection issues detected'}
              </h4>
              {!validation.isValid && (
                <ul className="mt-2 text-sm text-yellow-700">
                  {validation.issues.map((issue, index) => (
                    <li key={index}>• {issue}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Backup Actions</h4>
              <button
                onClick={handleCreateBackup}
                disabled={isLoading}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
              >
                Create Backup Now
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Export/Import</h4>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleExport('json')}
                  className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Export JSON
                </button>
                <button
                  onClick={() => handleExport('readable')}
                  className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Export MD
                </button>
              </div>
              <div>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImport}
                  className="hidden"
                  id="import-file"
                />
                <label
                  htmlFor="import-file"
                  className="w-full inline-block px-4 py-2 text-sm font-medium text-center text-white bg-green-600 rounded-md hover:bg-green-700 cursor-pointer transition-colors"
                >
                  Import Collections
                </label>
              </div>
            </div>
          </div>

          {/* Available Backups */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-medium text-gray-900">Available Backups ({backups.length})</h4>
              <button
                onClick={loadBackups}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Refresh
              </button>
            </div>

            {backups.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p>No backups available</p>
                <p className="text-sm mt-1">Backups are created automatically every 30 minutes</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {backups.map((backup) => (
                  <div
                    key={backup.key}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {new Date(backup.metadata.timestamp).toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">
                            {backup.metadata.totalCollections} collections, {backup.metadata.totalPapers} papers
                          </p>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRestore(backup.key)}
                      disabled={isLoading}
                      className="px-3 py-1 text-sm font-medium text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 disabled:opacity-50 transition-colors"
                    >
                      Restore
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h5 className="font-medium text-blue-900 mb-2">Automatic Protection</h5>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Backups are created automatically every 30 minutes</li>
              <li>• Additional backups are created when you make changes</li>
              <li>• Up to 5 recent backups are kept</li>
              <li>• Export your collections regularly for extra safety</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CollectionBackupModal;
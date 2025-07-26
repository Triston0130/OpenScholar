import React, { useState, useEffect } from 'react';
import { Collection } from '../utils/collections';

interface ShareCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  collection: Collection;
  onShare: (shareData: ShareData) => void;
}

interface ShareData {
  email?: string;
  role: 'viewer' | 'commenter' | 'editor' | 'admin';
  canReshare: boolean;
  message?: string;
  expiresIn?: number; // days
  shareType: 'user' | 'link';
}

interface SharedUser {
  id: string;
  email: string;
  name?: string;
  role: string;
  sharedAt: Date;
  accepted: boolean;
}

const ShareCollectionModal: React.FC<ShareCollectionModalProps> = ({
  isOpen,
  onClose,
  collection,
  onShare
}) => {
  const [shareType, setShareType] = useState<'user' | 'link'>('user');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'viewer' | 'commenter' | 'editor' | 'admin'>('viewer');
  const [canReshare, setCanReshare] = useState(false);
  const [message, setMessage] = useState('');
  const [expiresIn, setExpiresIn] = useState<number | undefined>(undefined);
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const [shareLink, setShareLink] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSharedUsers();
    }
  }, [isOpen]);

  const loadSharedUsers = async () => {
    // TODO: Fetch from backend
    // const response = await fetch(`/api/collections/${collection.id}/shares`);
    // const data = await response.json();
    // setSharedUsers(data);
    
    // Mock data for now
    setSharedUsers([
      {
        id: '1',
        email: 'colleague@university.edu',
        name: 'Dr. Jane Smith',
        role: 'editor',
        sharedAt: new Date('2024-01-15'),
        accepted: true
      }
    ]);
  };

  const handleShare = async () => {
    setIsLoading(true);
    try {
      if (shareType === 'user' && !email) {
        alert('Please enter an email address');
        return;
      }

      const shareData: ShareData = {
        email: shareType === 'user' ? email : undefined,
        role,
        canReshare,
        message,
        expiresIn,
        shareType
      };

      // TODO: Call backend API
      await onShare(shareData);

      if (shareType === 'link') {
        // Generate share link
        const link = `${window.location.origin}/shared/${collection.id}/${generateShareToken()}`;
        setShareLink(link);
      } else {
        // Reset form
        setEmail('');
        setMessage('');
        loadSharedUsers();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const generateShareToken = () => {
    return Math.random().toString(36).substring(2, 15);
  };

  const removeShare = async (userId: string) => {
    if (window.confirm('Remove access for this user?')) {
      // TODO: Call backend API
      setSharedUsers(sharedUsers.filter(u => u.id !== userId));
    }
  };

  const copyShareLink = () => {
    navigator.clipboard.writeText(shareLink);
    // Could add a toast notification here
  };

  const roleDescriptions = {
    viewer: 'Can view papers and annotations',
    commenter: 'Can view and add comments',
    editor: 'Can add/remove papers and edit metadata',
    admin: 'Full control including sharing settings'
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Share "{collection.name}"
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Share Type Tabs */}
          <div className="flex space-x-1 mb-6">
            <button
              onClick={() => setShareType('user')}
              className={`px-4 py-2 rounded-lg font-medium ${
                shareType === 'user'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Share with People
            </button>
            <button
              onClick={() => setShareType('link')}
              className={`px-4 py-2 rounded-lg font-medium ${
                shareType === 'link'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Get Shareable Link
            </button>
          </div>

          {shareType === 'user' ? (
            <>
              {/* Email Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="colleague@university.edu"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              {/* Role Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Permission level
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="viewer">Viewer - {roleDescriptions.viewer}</option>
                  <option value="commenter">Commenter - {roleDescriptions.commenter}</option>
                  <option value="editor">Editor - {roleDescriptions.editor}</option>
                  <option value="admin">Admin - {roleDescriptions.admin}</option>
                </select>
              </div>

              {/* Message */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message (optional)
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Here's the research collection we discussed..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>

              {/* Current Shares */}
              {sharedUsers.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    People with access
                  </h3>
                  <div className="space-y-2">
                    {sharedUsers.map(user => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                            {user.name ? user.name[0].toUpperCase() : user.email[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">
                              {user.name || user.email}
                            </p>
                            <p className="text-sm text-gray-500">
                              {user.role} • {user.accepted ? 'Accepted' : 'Pending'}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => removeShare(user.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Link Sharing */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Anyone with this link can access
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="viewer">View only</option>
                  <option value="commenter">View and comment</option>
                </select>
              </div>

              {/* Expiration */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Link expires in
                </label>
                <select
                  value={expiresIn || ''}
                  onChange={(e) => setExpiresIn(e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="">Never</option>
                  <option value="1">1 day</option>
                  <option value="7">7 days</option>
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                </select>
              </div>

              {shareLink && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-blue-900 mb-2">
                    Share link created!
                  </p>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={shareLink}
                      readOnly
                      className="flex-1 px-3 py-2 bg-white border border-blue-200 rounded-md text-sm"
                    />
                    <button
                      onClick={copyShareLink}
                      className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Additional Options */}
          <div className="mt-6 space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={canReshare}
                onChange={(e) => setCanReshare(e.target.checked)}
                className="h-4 w-4 text-blue-600 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                Allow recipients to reshare
              </span>
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleShare}
            disabled={isLoading || (shareType === 'user' && !email)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300"
          >
            {isLoading ? 'Sharing...' : shareType === 'user' ? 'Send Invite' : 'Generate Link'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareCollectionModal;
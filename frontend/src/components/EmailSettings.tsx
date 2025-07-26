import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface EmailSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  from_email: string;
  from_name: string;
  is_configured: boolean;
  is_verified: boolean;
}

interface NotificationPreferences {
  share_invitations: boolean;
  share_acceptances: boolean;
  annotation_replies: boolean;
  collection_updates: boolean;
}

const EmailSettings: React.FC = () => {
  const { user } = useAuth();
  const [emailSettings, setEmailSettings] = useState<EmailSettings>({
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
    from_email: '',
    from_name: 'OpenScholar User',
    is_configured: false,
    is_verified: false
  });
  
  const [notifications, setNotifications] = useState<NotificationPreferences>({
    share_invitations: true,
    share_acceptances: true,
    annotation_replies: true,
    collection_updates: true
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  
  // Common email providers
  const emailProviders = [
    { name: 'Gmail', host: 'smtp.gmail.com', port: 587, tls: true, ssl: false },
    { name: 'Outlook', host: 'smtp-mail.outlook.com', port: 587, tls: true, ssl: false },
    { name: 'Yahoo', host: 'smtp.mail.yahoo.com', port: 587, tls: true, ssl: false },
    { name: 'SendGrid', host: 'smtp.sendgrid.net', port: 587, tls: true, ssl: false },
    { name: 'Mailgun', host: 'smtp.mailgun.org', port: 587, tls: true, ssl: false },
    { name: 'Custom', host: '', port: 587, tls: true, ssl: false }
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const token = localStorage.getItem('openscholar_access_token');
      
      // Load email settings
      const emailRes = await fetch('/api/settings/email', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (emailRes.ok) {
        const data = await emailRes.json();
        setEmailSettings(prev => ({ ...prev, ...data }));
      }
      
      // Load notification preferences
      const notifRes = await fetch('/api/settings/notifications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (notifRes.ok) {
        const data = await notifRes.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSelect = (provider: typeof emailProviders[0]) => {
    setEmailSettings(prev => ({
      ...prev,
      smtp_host: provider.host,
      smtp_port: provider.port,
      smtp_use_tls: provider.tls,
      smtp_use_ssl: provider.ssl
    }));
  };

  const saveEmailSettings = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      const token = localStorage.getItem('openscholar_access_token');
      const response = await fetch('/api/settings/email', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          smtp_host: emailSettings.smtp_host,
          smtp_port: emailSettings.smtp_port,
          smtp_user: emailSettings.smtp_user,
          smtp_password: emailSettings.smtp_password,
          smtp_use_tls: emailSettings.smtp_use_tls,
          smtp_use_ssl: emailSettings.smtp_use_ssl,
          from_email: emailSettings.from_email || emailSettings.smtp_user,
          from_name: emailSettings.from_name
        })
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Email settings saved successfully' });
        setEmailSettings(prev => ({ ...prev, is_configured: true, is_verified: false }));
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to save settings' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const testEmailSettings = async () => {
    setTesting(true);
    setMessage(null);
    
    try {
      const token = localStorage.getItem('openscholar_access_token');
      const response = await fetch('/api/settings/email/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Test email sent successfully! Check your inbox.' });
        setEmailSettings(prev => ({ ...prev, is_verified: true }));
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to send test email' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to send test email' });
    } finally {
      setTesting(false);
    }
  };

  const saveNotificationPreferences = async () => {
    try {
      const token = localStorage.getItem('openscholar_access_token');
      const response = await fetch('/api/settings/notifications', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(notifications)
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Notification preferences saved' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save preferences' });
    }
  };

  if (loading) {
    return <div className="p-6">Loading settings...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Email Settings</h2>
      
      {message && (
        <div className={`mb-4 p-3 rounded ${
          message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      {/* Email Provider Selection */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Email Provider</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {emailProviders.map(provider => (
            <button
              key={provider.name}
              onClick={() => handleProviderSelect(provider)}
              className={`p-3 border rounded hover:bg-gray-50 ${
                emailSettings.smtp_host === provider.host 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300'
              }`}
            >
              {provider.name}
            </button>
          ))}
        </div>
      </div>

      {/* SMTP Configuration */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">SMTP Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SMTP Host
            </label>
            <input
              type="text"
              value={emailSettings.smtp_host}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_host: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="smtp.gmail.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SMTP Port
            </label>
            <input
              type="number"
              value={emailSettings.smtp_port}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_port: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={emailSettings.smtp_user}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_user: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="your-email@gmail.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              App Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={emailSettings.smtp_password}
                onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_password: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
                placeholder="App-specific password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              For Gmail, use an app-specific password. 
              <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline ml-1">
                Generate one here
              </a>
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Email (optional)
            </label>
            <input
              type="email"
              value={emailSettings.from_email}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, from_email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Defaults to email address"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Name
            </label>
            <input
              type="text"
              value={emailSettings.from_name}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, from_name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div className="mt-4 flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={emailSettings.smtp_use_tls}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_use_tls: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm">Use TLS</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={emailSettings.smtp_use_ssl}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, smtp_use_ssl: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm">Use SSL</span>
          </label>
        </div>
        
        <div className="mt-6 flex space-x-3">
          <button
            onClick={saveEmailSettings}
            disabled={saving || !emailSettings.smtp_host || !emailSettings.smtp_user || !emailSettings.smtp_password}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
          
          {emailSettings.is_configured && (
            <button
              onClick={testEmailSettings}
              disabled={testing}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {testing ? 'Sending...' : 'Send Test Email'}
            </button>
          )}
        </div>
        
        {emailSettings.is_verified && (
          <p className="mt-2 text-sm text-green-600">✓ Email settings verified</p>
        )}
      </div>

      {/* Notification Preferences */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Email Notifications</h3>
        
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={notifications.share_invitations}
              onChange={(e) => setNotifications(prev => ({ ...prev, share_invitations: e.target.checked }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium">Collection Share Invitations</div>
              <div className="text-sm text-gray-500">Receive emails when someone shares a collection with you</div>
            </div>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={notifications.share_acceptances}
              onChange={(e) => setNotifications(prev => ({ ...prev, share_acceptances: e.target.checked }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium">Share Acceptances</div>
              <div className="text-sm text-gray-500">Get notified when someone accepts your share invitation</div>
            </div>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={notifications.annotation_replies}
              onChange={(e) => setNotifications(prev => ({ ...prev, annotation_replies: e.target.checked }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium">Annotation Replies</div>
              <div className="text-sm text-gray-500">Receive emails when someone replies to your annotations</div>
            </div>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={notifications.collection_updates}
              onChange={(e) => setNotifications(prev => ({ ...prev, collection_updates: e.target.checked }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium">Collection Updates</div>
              <div className="text-sm text-gray-500">Get updates about shared collections you follow</div>
            </div>
          </label>
        </div>
        
        <button
          onClick={saveNotificationPreferences}
          className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Save Preferences
        </button>
      </div>
    </div>
  );
};

export default EmailSettings;
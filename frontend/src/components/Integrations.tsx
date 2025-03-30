
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { RotateCw, Link, X, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface Integration {
  id: string;
  type: string;
  status: string;
  lastSync?: string;
  config?: Record<string, unknown>;
}

interface IntegrationFormData {
  [key: string]: string;
}

interface FormField {
  name: string;
  label: string;
  placeholder: string;
}

export default function Integrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showConnectionForm, setShowConnectionForm] = useState<string | null>(null);
  const [formData, setFormData] = useState<IntegrationFormData>({});

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      setError(null);
      const data = await api.integrations.getStatus();
      setIntegrations(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch integrations');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (integrationType: string) => {
    try {
      setConnecting(integrationType);
      setError(null);
      setSuccessMessage(null);
      
      await api.integrations.connect(integrationType, formData);
      
      // Update the integration in the list
      setIntegrations(prevIntegrations => 
        prevIntegrations.map(integration => 
          integration.id === integrationType ? { ...integration, status: 'active' } : integration
        )
      );
      
      setSuccessMessage(`Successfully connected to ${integrationType}`);
      setShowConnectionForm(null);
      setFormData({});
      
      // Refresh the integrations list
      fetchIntegrations();
    } catch (err: any) {
      setError(err.message || `Failed to connect to ${integrationType}`);
    } finally {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (integrationId: string) => {
    try {
      setDisconnecting(integrationId);
      setError(null);
      setSuccessMessage(null);
      
      await api.integrations.disconnect(integrationId);
      
      // Update the integration in the list
      setIntegrations(prevIntegrations => 
        prevIntegrations.map(integration => 
          integration.id === integrationId ? { ...integration, status: 'inactive' } : integration
        )
      );
      
      setSuccessMessage(`Successfully disconnected from ${integrationId}`);
      
      // Refresh the integrations list
      fetchIntegrations();
    } catch (err: any) {
      setError(err.message || `Failed to disconnect from ${integrationId}`);
    } finally {
      setDisconnecting(null);
    }
  };

  const handleSync = async (integrationId: string) => {
    try {
      setSyncing(integrationId);
      setError(null);
      setSuccessMessage(null);
      
      await api.integrations.sync(integrationId);
      setSuccessMessage(`Successfully initiated sync for ${integrationId}`);
      
      // Refresh the integrations list
      fetchIntegrations();
    } catch (err: any) {
      setError(err.message || `Failed to sync ${integrationId}`);
    } finally {
      setSyncing(null);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const renderConfigForm = (integrationType: string) => {
    let formFields: FormField[] = [];

    if (integrationType === 'slack') {
      formFields = [
        { name: 'bot_token', label: 'Bot Token', placeholder: 'xoxb-...' },
        { name: 'channel_id', label: 'Channel ID', placeholder: 'C...' }
      ];
    } else if (integrationType === 'hubspot') {
      formFields = [
        { name: 'api_key', label: 'API Key', placeholder: 'hubspot_api_key' }
      ];
    } else if (integrationType === 'salesforce') {
      formFields = [
        { name: 'client_id', label: 'Client ID', placeholder: 'salesforce_client_id' },
        { name: 'client_secret', label: 'Client Secret', placeholder: 'salesforce_client_secret' },
        { name: 'instance_url', label: 'Instance URL', placeholder: 'https://yourinstance.salesforce.com' }
      ];
    } else if (integrationType === 'email') {
      formFields = [
        { name: 'email', label: 'Email Address', placeholder: 'your@email.com' },
        { name: 'password', label: 'App Password', placeholder: 'email_app_password' },
        { name: 'smtp_server', label: 'SMTP Server', placeholder: 'smtp.gmail.com' },
        { name: 'smtp_port', label: 'SMTP Port', placeholder: '587' }
      ];
    }

    return (
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="bg-blue-50 p-4 rounded-md mt-4"
      >
        <h4 className="font-medium mb-3">Connect {integrationType.charAt(0).toUpperCase() + integrationType.slice(1)}</h4>
        <form onSubmit={(e) => {
          e.preventDefault();
          handleConnect(integrationType);
        }}>
          {formFields.map((field, index) => (
            <div key={index} className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
              </label>
              <input
                type={field.name.includes('password') || field.name.includes('secret') ? 'password' : 'text'}
                name={field.name}
                value={formData[field.name] || ''}
                onChange={handleFormChange}
                placeholder={field.placeholder}
                className="w-full p-2 border border-gray-300 rounded text-sm"
                required
              />
            </div>
          ))}
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={() => setShowConnectionForm(null)}
              className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm flex items-center"
              disabled={connecting === integrationType}
            >
              {connecting === integrationType ? (
                <>
                  <RotateCw size={14} className="animate-spin mr-1" />
                  Connecting...
                </>
              ) : (
                <>
                  <Link size={14} className="mr-1" />
                  Connect
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    );
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Integrations</h2>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-100 text-red-700 p-4 rounded mb-4"
        >
          {error}
        </motion.div>
      )}

      {successMessage && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-100 text-green-700 p-4 rounded mb-4"
        >
          {successMessage}
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 flex justify-center items-center py-12">
            <RotateCw size={24} className="animate-spin mr-2 text-blue-500" />
            <span>Loading integrations...</span>
          </div>
        ) : (
          integrations.map((integration) => (
            <motion.div
              key={integration.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold">{integration.type.charAt(0).toUpperCase() + integration.type.slice(1)}</h3>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    integration.status === 'active' ? 'bg-green-500' :
                    integration.status === 'error' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`} />
                  <span className="text-gray-600 text-sm">
                    {integration.status.charAt(0).toUpperCase() + integration.status.slice(1)}
                  </span>
                </div>
              </div>
              
              {integration.lastSync && (
                <p className="text-sm text-gray-500 mb-4">
                  Last synced: {new Date(integration.lastSync).toLocaleDateString()}
                </p>
              )}

              {/* Integration Configuration Details */}
              {integration.config && Object.keys(integration.config).length > 0 && (
                <div className="mb-4 bg-gray-50 p-3 rounded text-sm">
                  {Object.entries(integration.config).map(([key, value]) => {
                    // Don't show empty arrays or sensitive information
                    if (Array.isArray(value) && value.length === 0) return null;
                    if (key.includes('token') || key.includes('password') || key.includes('secret')) {
                      return (
                        <div key={key} className="flex justify-between">
                          <span className="font-medium">{key}:</span>
                          <span>••••••••</span>
                        </div>
                      );
                    }
                    return (
                      <div key={key} className="flex justify-between">
                        <span className="font-medium">{key}:</span>
                        <span>{String(value)}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="flex justify-between mt-4">
                {integration.status === 'active' ? (
                  <>
                    <button
                      onClick={() => handleSync(integration.id)}
                      disabled={syncing === integration.id}
                      className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                    >
                      {syncing === integration.id ? (
                        <>
                          <RotateCw size={14} className="animate-spin mr-1" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          <RefreshCw size={14} className="mr-1" />
                          Sync Now
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleDisconnect(integration.id)}
                      disabled={disconnecting === integration.id}
                      className="text-red-600 hover:text-red-800 text-sm flex items-center"
                    >
                      {disconnecting === integration.id ? (
                        <>
                          <RotateCw size={14} className="animate-spin mr-1" />
                          Disconnecting...
                        </>
                      ) : (
                        <>
                          <X size={14} className="mr-1" />
                          Disconnect
                        </>
                      )}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setShowConnectionForm(integration.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                  >
                    <Link size={14} className="mr-1" />
                    Connect
                  </button>
                )}
              </div>

              {showConnectionForm === integration.id && renderConfigForm(integration.id)}
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}

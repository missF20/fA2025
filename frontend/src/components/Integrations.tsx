
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Database, 
  MessageSquare, 
  BarChart, 
  ShoppingBag, 
  Headphones,
  Link2,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  ExternalLink,
  RotateCw,
  RefreshCw,
  X,
  Link
} from 'lucide-react';
import { motion } from 'framer-motion';
import SlackDashboard from './SlackDashboard';
import { IntegrationGuide } from './IntegrationGuide';

interface Integration {
  id: string;
  type: string;
  status: string;
  lastSync?: string;
  config?: Record<string, unknown>;
  name?: string;
  description?: string;
  icon?: string;
  category?: string;
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
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showConnectionForm, setShowConnectionForm] = useState<string | null>(null);
  const [formData, setFormData] = useState<IntegrationFormData>({});
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);

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

  // Function to handle clicking on an integration card
  const handleIntegrationClick = (integration: Integration) => {
    if (integration.status === 'active' && integration.id === 'slack') {
      setSelectedIntegration('slack');
    }
  };

  // Function to go back to the main integrations view
  const handleBackToIntegrations = () => {
    setSelectedIntegration(null);
  };

  // If Slack dashboard is selected, show it
  if (selectedIntegration === 'slack') {
    return (
      <div className="p-6">
        <div className="flex items-center mb-6">
          <button 
            onClick={handleBackToIntegrations}
            className="mr-4 text-blue-600 hover:text-blue-800 text-sm"
          >
            ← Back to Integrations
          </button>
          <h2 className="text-2xl font-bold">Slack Integration</h2>
        </div>
        <SlackDashboard />
      </div>
    );
  }

  // Create a mapping of our API integration IDs to more user-friendly data
  const getDefaultIntegrations = () => {
    const staticIntegrations = [
      // CRM
      {
        id: 'salesforce',
        name: 'Salesforce',
        description: 'Connect your CRM data for enhanced customer insights',
        icon: 'database',
        status: 'disconnected',
        category: 'crm',
        type: 'salesforce' 
      },
      {
        id: 'hubspot',
        name: 'HubSpot',
        description: 'Integrate with your marketing automation platform',
        icon: 'database',
        status: 'disconnected',
        category: 'crm',
        type: 'hubspot'
      },
      // Communication
      {
        id: 'slack',
        name: 'Slack',
        description: 'Get notifications and manage responses through Slack',
        icon: 'message-square',
        status: 'disconnected',
        category: 'communication',
        type: 'slack'
      },
      // Analytics
      {
        id: 'google_analytics',
        name: 'Google Analytics',
        description: 'Track customer engagement and response metrics',
        icon: 'bar-chart',
        status: 'disconnected',
        category: 'analytics',
        type: 'google_analytics'
      },
      // E-commerce
      {
        id: 'shopify',
        name: 'Shopify',
        description: 'Integrate with your e-commerce platform',
        icon: 'shopping-bag',
        status: 'disconnected',
        category: 'ecommerce',
        type: 'shopify'
      },
      // Helpdesk
      {
        id: 'zendesk',
        name: 'Zendesk',
        description: 'Sync customer support tickets and history',
        icon: 'headphones',
        status: 'disconnected',
        category: 'helpdesk',
        type: 'zendesk'
      }
    ];

    return staticIntegrations;
  };

  // Merge the API data with the static metadata
  const mergeIntegrationData = () => {
    const defaultIntegrations = getDefaultIntegrations();
    
    if (integrations.length === 0) {
      return defaultIntegrations;
    }

    // Enhance API integrations with static metadata
    return defaultIntegrations.map(defaultInt => {
      const apiInt = integrations.find(i => i.id === defaultInt.id);
      if (apiInt) {
        return {
          ...defaultInt,
          status: apiInt.status,
          config: apiInt.config,
          lastSync: apiInt.lastSync
        };
      }
      return defaultInt;
    });
  };

  // Categories for filtering
  const categories = [
    { id: 'all', label: 'All Integrations' },
    { id: 'crm', label: 'CRM' },
    { id: 'communication', label: 'Communication' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'ecommerce', label: 'E-Commerce' },
    { id: 'helpdesk', label: 'Helpdesk' }
  ];

  // Get the icon component based on the icon type
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'database':
        return <Database size={20} />;
      case 'message-square':
        return <MessageSquare size={20} />;
      case 'bar-chart':
        return <BarChart size={20} />;
      case 'shopping-bag':
        return <ShoppingBag size={20} />;
      case 'headphones':
        return <Headphones size={20} />;
      default:
        return <Link2 size={20} />;
    }
  };

  // Filter integrations based on selected category
  const filteredIntegrations = activeCategory === 'all' 
    ? mergeIntegrationData() 
    : mergeIntegrationData().filter(integration => integration.category === activeCategory);

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* If Slack dashboard is selected, show it */}
        {selectedIntegration === 'slack' ? (
          <div>
            <div className="flex items-center gap-3 mb-8">
              <button 
                onClick={handleBackToIntegrations}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                ← Back to Integrations
              </button>
              <div className="p-2 bg-blue-50 rounded-lg">
                <MessageSquare className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Slack Integration</h1>
                <p className="text-gray-500">Manage your Slack connection</p>
              </div>
            </div>
            <SlackDashboard />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 mb-8">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Link2 className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
                <p className="text-gray-500">Connect your favorite tools with Dana AI</p>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
              <div className="flex flex-wrap gap-2">
                {categories.map(category => (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeCategory === category.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-100 rounded-lg p-4 mb-6 flex items-center text-red-700">
                <AlertCircle className="h-5 w-5 mr-2" />
                <p>{error}</p>
              </div>
            )}

            {successMessage && (
              <div className="bg-green-50 border border-green-100 rounded-lg p-4 mb-6 flex items-center text-green-700">
                <CheckCircle className="h-5 w-5 mr-2" />
                <p>{successMessage}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {loading ? (
                <div className="col-span-3 flex justify-center items-center py-12">
                  <RotateCw size={24} className="animate-spin mr-2 text-blue-500" />
                  <span>Loading integrations...</span>
                </div>
              ) : (
                filteredIntegrations.map((integration) => (
                  <div
                    key={integration.id}
                    className={`bg-white rounded-xl p-6 shadow-sm border border-gray-100 ${
                      integration.status === 'active' && integration.id === 'slack' 
                        ? 'cursor-pointer hover:bg-gray-50' 
                        : ''
                    }`}
                    onClick={() => integration.status === 'active' && integration.id === 'slack' ? handleIntegrationClick(integration) : null}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                          {getIcon(integration.icon)}
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                      </div>
                      {integration.status === 'active' ? (
                        <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                          <CheckCircle size={12} className="mr-1" />
                          Connected
                        </span>
                      ) : (
                        <span className="flex items-center text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded-full">
                          <XCircle size={12} className="mr-1" />
                          Disconnected
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-4">{integration.description}</p>
                    
                    {integration.lastSync && (
                      <p className="text-xs text-gray-500 mb-4">
                        Last synced: {new Date(integration.lastSync).toLocaleDateString()}
                      </p>
                    )}

                    {/* Integration Configuration Details */}
                    {integration.config && Object.keys(integration.config).length > 0 && (
                      <div className="mb-4 bg-gray-50 p-3 rounded text-xs">
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

                    <div onClick={(e) => e.stopPropagation()}>
                      {integration.status === 'active' ? (
                        <div className="flex gap-2 mt-4">
                          <button
                            onClick={() => handleSync(integration.id)}
                            disabled={syncing === integration.id}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                          >
                            {syncing === integration.id ? (
                              <>
                                <Loader2 size={16} className="animate-spin" />
                                Syncing...
                              </>
                            ) : (
                              <>
                                <RefreshCw size={16} />
                                Sync
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleDisconnect(integration.id)}
                            disabled={disconnecting === integration.id}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
                          >
                            {disconnecting === integration.id ? (
                              <>
                                <Loader2 size={16} className="animate-spin" />
                                Disconnecting...
                              </>
                            ) : (
                              <>
                                <X size={16} />
                                Disconnect
                              </>
                            )}
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setShowConnectionForm(integration.id)}
                          disabled={connecting === integration.id}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                        >
                          {connecting === integration.id ? (
                            <>
                              <Loader2 size={16} className="animate-spin" />
                              Connecting...
                            </>
                          ) : (
                            <>
                              <Link2 size={16} />
                              Connect
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {showConnectionForm === integration.id && (
                      <div onClick={(e) => e.stopPropagation()}>
                        {renderConfigForm(integration.id)}
                      </div>
                    )}

                    {integration.status === 'active' && integration.id === 'slack' && (
                      <div className="mt-4 text-sm text-center text-blue-600">
                        Click to access Slack dashboard
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="bg-blue-50 rounded-xl p-6 mt-8 border border-blue-100">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Need a custom integration?</h3>
              <p className="text-blue-700 mb-4">
                Don't see the tool you're looking for? We can build custom integrations for your specific needs.
              </p>
              <a 
                href="mailto:support@hartford-tech.com" 
                className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
              >
                Contact us for custom integrations
                <ExternalLink size={16} className="ml-1" />
              </a>
            </div>

            <IntegrationGuide />
          </>
        )}
      </div>
    </div>
  );
}

import React, { useState } from 'react';
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
  ExternalLink
} from 'lucide-react';

export function Integrations() {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [connecting, setConnecting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const integrations = [
    // CRM
    {
      id: '1',
      name: 'Salesforce',
      description: 'Connect your CRM data for enhanced customer insights',
      icon: 'database',
      status: 'disconnected',
      category: 'crm'
    },
    {
      id: '2',
      name: 'HubSpot',
      description: 'Integrate with your marketing automation platform',
      icon: 'database',
      status: 'disconnected',
      category: 'crm'
    },
    // Communication
    {
      id: '3',
      name: 'Slack',
      description: 'Get notifications and manage responses through Slack',
      icon: 'message-square',
      status: 'disconnected',
      category: 'communication'
    },
    // Analytics
    {
      id: '4',
      name: 'Google Analytics',
      description: 'Track customer engagement and response metrics',
      icon: 'bar-chart',
      status: 'disconnected',
      category: 'analytics'
    },
    // E-commerce
    {
      id: '5',
      name: 'Shopify',
      description: 'Integrate with your e-commerce platform',
      icon: 'shopping-bag',
      status: 'disconnected',
      category: 'ecommerce'
    },
    // Helpdesk
    {
      id: '6',
      name: 'Zendesk',
      description: 'Sync customer support tickets and history',
      icon: 'headphones',
      status: 'disconnected',
      category: 'helpdesk'
    }
  ];

  const categories = [
    { id: 'all', label: 'All Integrations' },
    { id: 'crm', label: 'CRM' },
    { id: 'communication', label: 'Communication' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'ecommerce', label: 'E-Commerce' },
    { id: 'helpdesk', label: 'Helpdesk' }
  ];

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

  const handleConnect = async (integration: any) => {
    setConnecting(integration.id);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Open OAuth window based on integration
      switch (integration.name.toLowerCase()) {
        case 'salesforce':
          window.open('https://login.salesforce.com/services/oauth2/authorize', '_blank');
          break;
        case 'hubspot':
          window.open('https://app.hubspot.com/oauth/authorize', '_blank');
          break;
        case 'slack':
          window.open('https://slack.com/oauth/v2/authorize', '_blank');
          break;
        case 'google analytics':
          window.open('https://accounts.google.com/o/oauth2/v2/auth', '_blank');
          break;
        case 'shopify':
          window.open('https://your-store.myshopify.com/admin/oauth/authorize', '_blank');
          break;
        case 'zendesk':
          window.open('https://your-domain.zendesk.com/oauth/authorizations/new', '_blank');
          break;
      }
    } catch (err) {
      setError('Failed to connect integration');
    } finally {
      setConnecting(null);
    }
  };

  const filteredIntegrations = activeCategory === 'all' 
    ? integrations 
    : integrations.filter(integration => integration.category === activeCategory);

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIntegrations.map(integration => (
            <div
              key={integration.id}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                    {getIcon(integration.icon)}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                </div>
                {integration.status === 'connected' ? (
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
              
              <button
                onClick={() => handleConnect(integration)}
                disabled={connecting === integration.id}
                className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  integration.status === 'connected'
                    ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {connecting === integration.id ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Connecting...
                  </>
                ) : integration.status === 'connected' ? (
                  'Manage Connection'
                ) : (
                  <>
                    <Link2 size={16} />
                    Connect
                  </>
                )}
              </button>
            </div>
          ))}
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
      </div>
    </div>
  );
}
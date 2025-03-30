import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import IntegrationStatus from './IntegrationStatus';
import { MessageSquare, Database, BarChart, Mail, Headphones } from 'react-feather';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: React.ReactElement;
  status: 'active' | 'inactive' | 'pending' | 'error' | 'not_configured';
  category: string;
  type: string;
}

const INTEGRATION_TYPES = {
  SLACK: 'slack',
  EMAIL: 'email',
  DATABASE_POSTGRESQL: 'database_postgresql',
  DATABASE_MYSQL: 'database_mysql',
  DATABASE_MONGODB: 'database_mongodb',
  DATABASE_SQLSERVER: 'database_sqlserver',
  HUBSPOT: 'hubspot',
  SALESFORCE: 'salesforce',
  GOOGLE_ANALYTICS: 'google_analytics',
  ZENDESK: 'zendesk'
};

export default function Integrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await fetch('/api/integrations/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch integrations');

      const data = await response.json();

      // Map backend data to frontend format
      const mappedIntegrations = data.dashboard.integrations.map((integration: any) => ({
        id: integration.integration_type,
        name: getIntegrationName(integration.integration_type),
        description: getIntegrationDescription(integration.integration_type),
        icon: getIntegrationIcon(integration.integration_type),
        status: integration.status,
        category: getIntegrationCategory(integration.integration_type),
        type: integration.integration_type
      }));

      setIntegrations(mappedIntegrations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getIntegrationName = (type: string): string => {
    const names: Record<string, string> = {
      [INTEGRATION_TYPES.SLACK]: 'Slack',
      [INTEGRATION_TYPES.EMAIL]: 'Email',
      [INTEGRATION_TYPES.DATABASE_POSTGRESQL]: 'PostgreSQL',
      [INTEGRATION_TYPES.DATABASE_MYSQL]: 'MySQL',
      [INTEGRATION_TYPES.DATABASE_MONGODB]: 'MongoDB',
      [INTEGRATION_TYPES.DATABASE_SQLSERVER]: 'SQL Server',
      [INTEGRATION_TYPES.HUBSPOT]: 'HubSpot',
      [INTEGRATION_TYPES.SALESFORCE]: 'Salesforce',
      [INTEGRATION_TYPES.GOOGLE_ANALYTICS]: 'Google Analytics',
      [INTEGRATION_TYPES.ZENDESK]: 'Zendesk'
    };
    return names[type] || type;
  };

  const getIntegrationDescription = (type: string): string => {
    const descriptions: Record<string, string> = {
      [INTEGRATION_TYPES.SLACK]: 'Get notifications and manage responses through Slack',
      [INTEGRATION_TYPES.EMAIL]: 'Send and receive emails through the platform',
      [INTEGRATION_TYPES.DATABASE_POSTGRESQL]: 'Connect to PostgreSQL databases',
      [INTEGRATION_TYPES.DATABASE_MYSQL]: 'Connect to MySQL databases',
      [INTEGRATION_TYPES.DATABASE_MONGODB]: 'Connect to MongoDB databases',
      [INTEGRATION_TYPES.DATABASE_SQLSERVER]: 'Connect to SQL Server databases',
      [INTEGRATION_TYPES.HUBSPOT]: 'Integrate with your marketing automation platform',
      [INTEGRATION_TYPES.SALESFORCE]: 'Connect your CRM data',
      [INTEGRATION_TYPES.GOOGLE_ANALYTICS]: 'Track customer engagement metrics',
      [INTEGRATION_TYPES.ZENDESK]: 'Sync customer support tickets'
    };
    return descriptions[type] || 'Integration description not available';
  };

  const getIntegrationCategory = (type: string): string => {
    if (type.includes('database')) return 'database';
    if (type === INTEGRATION_TYPES.SLACK || type === INTEGRATION_TYPES.EMAIL) return 'communication';
    if (type === INTEGRATION_TYPES.GOOGLE_ANALYTICS) return 'analytics';
    if (type === INTEGRATION_TYPES.HUBSPOT || type === INTEGRATION_TYPES.SALESFORCE) return 'crm';
    if (type === INTEGRATION_TYPES.ZENDESK) return 'helpdesk';
    return 'other';
  };

  const getIntegrationIcon = (type: string): React.ReactElement => {
    if (type === INTEGRATION_TYPES.SLACK || type === INTEGRATION_TYPES.EMAIL) {
      return <MessageSquare className="w-5 h-5" />;
    }
    if (type.includes('database')) {
      return <Database className="w-5 h-5" />;
    }
    if (type === INTEGRATION_TYPES.GOOGLE_ANALYTICS) {
      return <BarChart className="w-5 h-5" />;
    }
    if (type === INTEGRATION_TYPES.ZENDESK) {
      return <Headphones className="w-5 h-5" />;
    }
    return <Database className="w-5 h-5" />;
  };

  const handleConnect = async (integration: Integration) => {
    try {
      // Fetch integration schema first
      const schemaResponse = await fetch(`/api/integrations/schema/${integration.type}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!schemaResponse.ok) throw new Error('Failed to fetch integration schema');

      const schemaData = await schemaResponse.json();

      // TODO: Open configuration modal with schema
      console.log('Integration schema:', schemaData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect integration');
    }
  };

  if (loading) return <div className="p-6">Loading integrations...</div>;
  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Integrations</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map(integration => (
          <div
            key={integration.id}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  {integration.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
              </div>
              <IntegrationStatus status={integration.status} />
            </div>

            <p className="text-sm text-gray-600 mb-4">{integration.description}</p>

            <button
              onClick={() => handleConnect(integration)}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Configure
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function IntegrationStatus({status}: {status: string}) {
  switch (status) {
    case 'active':
      return <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
        <CheckCircle className="h-4 w-4 mr-1" />
        Active
      </span>
    case 'inactive':
      return <span className="flex items-center text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded-full">
      <XCircle className="h-4 w-4 mr-1"/>
        Inactive
      </span>
    case 'pending':
      return <span className="flex items-center text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">
      <Loader2 className="h-4 w-4 mr-1 animate-spin"/>
        Pending
      </span>
    case 'error':
      return <span className="flex items-center text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">
      <AlertCircle className="h-4 w-4 mr-1"/>
        Error
      </span>
    case 'not_configured':
      return <span className="flex items-center text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded-full">
      <XCircle className="h-4 w-4 mr-1"/>
        Not Configured
      </span>
    default:
      return <></>;
  }
}
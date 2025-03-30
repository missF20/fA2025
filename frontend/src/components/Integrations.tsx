
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface Integration {
  id: string;
  type: string;
  status: string;
  lastSync?: string;
}

export default function Integrations() {
  const { user } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await fetch('/api/integrations/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setIntegrations(data.integrations);
    } catch (err) {
      setError('Failed to fetch integrations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Integrations</h2>

      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div>Loading integrations...</div>
        ) : (
          integrations.map((integration) => (
            <div
              key={integration.id}
              className="bg-white rounded-lg shadow p-6"
            >
              <h3 className="text-lg font-semibold mb-2">{integration.type}</h3>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  integration.status === 'active' ? 'bg-green-500' :
                  integration.status === 'error' ? 'bg-red-500' :
                  'bg-yellow-500'
                }`} />
                <span className="text-gray-600">
                  {integration.status.charAt(0).toUpperCase() + integration.status.slice(1)}
                </span>
              </div>
              {integration.lastSync && (
                <p className="text-sm text-gray-500 mt-2">
                  Last synced: {new Date(integration.lastSync).toLocaleDateString()}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

import React from 'react';
import { Check, X, AlertCircle } from 'lucide-react';

export function IntegrationStatus({status}: {status: string}) {
  switch (status) {
    case 'active':
      return <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
        <Check size={12} className="mr-1" />Active
      </span>;
    case 'error':
      return <span className="flex items-center text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">
        <X size={12} className="mr-1" />Error
      </span>;
    default:
      return <span className="flex items-center text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">
        <AlertCircle size={12} className="mr-1" />Pending
      </span>;
  }
}

export function Integrations() {
  const integrations = [
    { id: 1, name: 'Slack', status: 'active' },
    { id: 2, name: 'Email', status: 'pending' },
    { id: 3, name: 'API', status: 'error' }
  ];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Integrations</h2>

      <div className="grid gap-4">
        {integrations.map(integration => (
          <div key={integration.id} className="bg-white p-4 rounded-xl flex justify-between items-center">
            <div>
              <h3 className="font-medium">{integration.name}</h3>
            </div>
            <IntegrationStatus status={integration.status} />
          </div>
        ))}
      </div>
    </div>
  );
}
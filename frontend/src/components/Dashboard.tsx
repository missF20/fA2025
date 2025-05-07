
import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { useAuth } from '../hooks/useAuth';
import { AdvancedAnalytics } from './AdvancedAnalytics';

// Define User type to include company property
interface User {
  id: string;
  email: string;
  company?: string;
}

export const Dashboard = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAnalytics, setShowAnalytics] = useState(false);

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await api.get('/conversations');
        setConversations(response.data.conversations);
        
        // Check if user has any social media integrations connected
        // We'll show analytics if data is available
        try {
          const integrationsResponse = await api.get('/api/integrations/status');
          const socialIntegrations = integrationsResponse.data.filter(
            (integration: any) => 
              ['facebook', 'instagram', 'whatsapp'].includes(integration.type.toLowerCase()) && 
              integration.status === 'active'
          );
          
          setShowAnalytics(socialIntegrations.length > 0);
        } catch (err) {
          console.error('Failed to check integrations status:', err);
          setShowAnalytics(false);
        }
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );

  return (
    <div className="dashboard">
      <div className="bg-gray-100 p-6 rounded-lg mb-6">
        <h1 className="text-2xl font-bold mb-2">Welcome, {user?.company || 'User'}</h1>
        <p className="text-gray-600">
          Here's your Dana AI platform overview. Connect your social media accounts in the Socials section 
          to see detailed analytics.
        </p>
      </div>
      
      {/* Show advanced analytics if available */}
      {showAnalytics && (
        <div className="mb-6">
          <AdvancedAnalytics />
        </div>
      )}
      
      {/* Always show conversations section */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Recent Conversations</h2>
        {conversations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conversations.map((conv: any) => (
              <div key={conv.id} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 className="font-medium text-lg">{conv.client_name}</h3>
                <div className="mt-2 text-sm text-gray-600">
                  <p>Platform: {conv.platform}</p>
                  <p>Status: <span className={`${conv.status === 'active' ? 'text-green-600' : 'text-orange-600'}`}>{conv.status}</span></p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-gray-700">
              No recent conversations found. Start engaging with your audience through connected platforms.
            </p>
          </div>
        )}
      </div>
      
      {/* Show connect social prompt if no analytics available */}
      {!showAnalytics && (
        <div className="mt-6 p-6 bg-yellow-50 rounded-lg border border-yellow-100">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">Connect Your Social Media Accounts</h3>
          <p className="text-gray-700 mb-4">
            To see detailed analytics about your social media performance, connect your accounts in the Socials section.
          </p>
          <p className="text-gray-600">
            Once connected, you'll see metrics on engagement, audience growth, message volume, and response times across all your platforms.
          </p>
        </div>
      )}
    </div>
  );
};

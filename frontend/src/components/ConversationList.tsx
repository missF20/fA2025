
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface Conversation {
  id: string;
  platform: string;
  client_name: string;
  client_company: string;
  status: string;
  date_created: string;
}

export default function ConversationList() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await fetch('/api/conversations', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setConversations(data.conversations);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  if (loading) {
    return <div className="p-6">Loading conversations...</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Conversations</h2>
      
      <div className="grid gap-4">
        {conversations.map((conversation) => (
          <div key={conversation.id} className="border rounded-lg p-4 hover:bg-gray-50">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-lg">{conversation.client_name}</h3>
                {conversation.client_company && (
                  <p className="text-gray-600">{conversation.client_company}</p>
                )}
              </div>
              <span className={`px-2 py-1 rounded-full text-sm ${getStatusColor(conversation.status)}`}>
                {conversation.status}
              </span>
            </div>
            
            <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
              <span>{conversation.platform}</span>
              <span>•</span>
              <span>{new Date(conversation.date_created).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

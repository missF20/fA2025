
import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { useAuth } from '../hooks/useAuth';

export const Dashboard = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await api.get('/conversations');
        setConversations(response.data.conversations);
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>Welcome, {user?.company}</h1>
      <div className="conversations">
        <h2>Recent Conversations</h2>
        {conversations.map((conv: any) => (
          <div key={conv.id} className="conversation-card">
            <h3>{conv.client_name}</h3>
            <p>Platform: {conv.platform}</p>
            <p>Status: {conv.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

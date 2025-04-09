import React, { useState, useEffect } from 'react';
import { Loader2, Check, MessageSquare, AlertCircle, RefreshCw, Send } from 'lucide-react';
import IntegrationStatus from './IntegrationStatus';

interface SlackMessage {
  text: string;
  timestamp: string;
  user: string;
  thread_ts?: string;
  reply_count?: number;
}

interface SlackStatus {
  valid: boolean;
  channel_id: string | null;
  missing: string[];
}

export default function SlackDashboard() {
  const [status, setStatus] = useState<SlackStatus | null>(null);
  const [messages, setMessages] = useState<SlackMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [messageText, setMessageText] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    fetchSlackStatus();
    fetchSlackMessages();
  }, []);
  
  async function fetchSlackStatus() {
    try {
      const response = await fetch('/api/slack/status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError('Failed to fetch Slack integration status');
    }
  }
  
  async function fetchSlackMessages() {
    setIsLoading(true);
    try {
      const response = await fetch('/api/slack/history?limit=10');
      const data = await response.json();
      
      if (data.success) {
        setMessages(data.messages || []);
        setError('');
      } else {
        setError(data.message || 'Failed to fetch messages');
        setMessages([]);
      }
    } catch (err) {
      setError('Error fetching messages from Slack');
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }
  
  async function refreshMessages() {
    setRefreshing(true);
    try {
      await fetchSlackMessages();
      setSuccess('Messages refreshed successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to refresh messages');
    } finally {
      setRefreshing(false);
    }
  }
  
  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!messageText.trim()) return;
    
    setSendingMessage(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await fetch('/api/slack/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: messageText })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuccess('Message sent successfully');
        setMessageText('');
        // Refresh messages to show the new one
        fetchSlackMessages();
      } else {
        setError(data.message || 'Failed to send message');
      }
    } catch (err) {
      setError('Error sending message to Slack');
    } finally {
      setSendingMessage(false);
    }
  }
  
  const getStatusMessage = () => {
    if (!status) return 'Checking Slack status...';
    
    if (status.valid) {
      return `Connected to Slack channel: ${status.channel_id || 'Unknown'}`;
    } else {
      const missingItems = Array.isArray(status.missing) ? status.missing.join(', ') : 'configuration';
      return `Slack integration not properly configured. Missing: ${missingItems}`;
    }
  };
  
  return (
    <div className="p-6">
      <div className="bg-white p-4 rounded-xl shadow-sm mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-medium text-lg">Status</h3>
            <p className="text-sm text-gray-600 mt-1">{getStatusMessage()}</p>
          </div>
          <IntegrationStatus status={status?.valid ? 'active' : 'error'} />
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 flex items-center">
          <AlertCircle size={16} className="mr-2" />
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 text-green-600 p-3 rounded-lg mb-4 flex items-center">
          <Check size={16} className="mr-2" />
          {success}
        </div>
      )}
      
      <div className="bg-white rounded-xl shadow-sm mb-6">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <h3 className="font-medium text-lg">Send Message</h3>
        </div>
        <div className="p-4">
          <form onSubmit={sendMessage} className="flex flex-col space-y-3">
            <textarea
              rows={3}
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Type your message here..."
              className="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!status?.valid || sendingMessage}
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!status?.valid || sendingMessage || !messageText.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendingMessage ? (
                  <>
                    <Loader2 size={16} className="animate-spin mr-2" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send size={16} className="mr-2" />
                    Send
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <h3 className="font-medium text-lg">Recent Messages</h3>
          <button
            onClick={refreshMessages}
            disabled={refreshing}
            className="text-blue-600 hover:text-blue-800 flex items-center disabled:opacity-50"
          >
            {refreshing ? (
              <Loader2 size={16} className="animate-spin mr-1" />
            ) : (
              <RefreshCw size={16} className="mr-1" />
            )}
            Refresh
          </button>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-blue-500" />
          </div>
        ) : messages.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            <MessageSquare className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p>No messages found</p>
            {!status?.valid && (
              <p className="mt-1 text-sm">Configure Slack integration to see messages</p>
            )}
          </div>
        ) : (
          <div className="divide-y">
            {messages.map((msg, index) => (
              <div key={`${msg.timestamp}-${index}`} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="text-sm font-semibold text-gray-600">
                    {msg.user || 'Unknown user'}
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(msg.timestamp).toLocaleString()}
                  </div>
                </div>
                <div className="mt-1 whitespace-pre-line">{msg.text}</div>
                {msg.reply_count && msg.reply_count > 0 && (
                  <div className="mt-2 text-xs text-blue-600">
                    {msg.reply_count} {msg.reply_count === 1 ? 'reply' : 'replies'}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
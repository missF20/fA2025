import React, { useState, useRef, FormEvent } from 'react';
import { MessageSquare, Facebook, Instagram, MessageCircle, ChevronDown, ChevronUp, Send, Slack } from 'lucide-react';
import type { Conversation, Message } from '../types';
import { supabase } from '../lib/supabase';

interface ConversationsListProps {
  conversations: Conversation[];
}

export function ConversationsList({ conversations }: ConversationsListProps) {
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [messageInput, setMessageInput] = useState<string>('');
  const messageEndRef = useRef<HTMLDivElement>(null);
  const [conversationsData, setConversationsData] = useState<Conversation[]>(conversations);

  const getPlatformIcon = (platform: Conversation['platform']) => {
    switch (platform) {
      case 'facebook':
        return <Facebook size={16} className="text-blue-600" />;
      case 'instagram':
        return <Instagram size={16} className="text-pink-600" />;
      case 'whatsapp':
        return <MessageCircle size={16} className="text-green-600" />;
      case 'slack':
        return <Slack size={16} className="text-purple-600" />;
      default:
        return <MessageSquare size={16} className="text-gray-600" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: FormEvent, conversationId: string) => {
    e.preventDefault();
    
    if (!messageInput.trim() || loading) return;
    
    try {
      setLoading(true);
      
      // Prepare the message data
      const newMessage = {
        conversation_id: conversationId,
        content: messageInput.trim(),
        sender_type: 'user',
      };
      
      // Get the current conversation
      const currentConversation = conversationsData.find(conv => conv.id === conversationId);
      if (!currentConversation) {
        throw new Error('Conversation not found');
      }
      
      // Insert the message into Supabase
      const { data: insertedMessage, error } = await supabase
        .from('messages')
        .insert(newMessage)
        .select()
        .single();
      
      if (error) {
        throw error;
      }
      
      // If this is a Slack conversation, also send message to Slack
      if (currentConversation.platform === 'slack') {
        try {
          // Call API to post to Slack
          const slackResponse = await fetch('/api/integrations/slack/message', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              message: messageInput.trim(),
              conversation_id: conversationId,
            }),
          });
          
          if (!slackResponse.ok) {
            console.warn('Message saved to database but failed to send to Slack');
          }
        } catch (slackError) {
          console.warn('Error sending message to Slack:', slackError);
          // We don't throw here since the message was saved in Supabase
          // Just log a warning instead
        }
      }
      
      // Clear input field after successful send
      setMessageInput('');
      
      // Optimistically update the UI
      // Add the message to the current conversation's messages array
      const updatedConversations = conversationsData.map(conv => {
        if (conv.id === conversationId) {
          const updatedMessages = [...(conv.messages || []), insertedMessage as Message];
          return { ...conv, messages: updatedMessages };
        }
        return conv;
      });
      
      setConversationsData(updatedConversations);
      
      // Scroll to the bottom of the messages
      setTimeout(scrollToBottom, 100);
      
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-6">
        <MessageSquare className="text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Recent Conversations</h3>
      </div>

      <div className="space-y-4">
        {conversationsData.map((conversation) => (
          <div
            key={conversation.id}
            className="border border-gray-100 rounded-lg overflow-hidden"
          >
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedConversation(
                expandedConversation === conversation.id ? null : conversation.id
              )}
            >
              <div className="flex items-center gap-3">
                {getPlatformIcon(conversation.platform)}
                <div>
                  <h4 className="font-medium text-gray-900">{conversation.client_name}</h4>
                  <p className="text-sm text-gray-500">{conversation.client_company}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-400">
                  {formatDate(conversation.created_at)}
                </span>
                {expandedConversation === conversation.id ? (
                  <ChevronUp size={16} className="text-gray-400" />
                ) : (
                  <ChevronDown size={16} className="text-gray-400" />
                )}
              </div>
            </div>

            {expandedConversation === conversation.id && (
              <>
                <div className="border-t border-gray-100 p-4 space-y-3 max-h-[400px] overflow-y-auto">
                  {conversation.messages && conversation.messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.sender_type === 'ai' || message.sender_type === 'client' 
                          ? 'justify-start' 
                          : 'justify-end'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.sender_type === 'ai'
                            ? 'bg-purple-100 text-gray-900'
                            : message.sender_type === 'client'
                            ? 'bg-gray-100 text-gray-900'
                            : 'bg-blue-600 text-white'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <div className="flex justify-between items-center mt-1">
                          <span className="text-xs opacity-70 block">
                            {formatDate(message.created_at)}
                          </span>
                          <span className="text-xs font-medium ml-2 opacity-70">
                            {message.sender_type === 'ai' ? 'Dana AI' : 
                             message.sender_type === 'client' ? 'Client' : 'You'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={messageEndRef} />
                </div>
                
                {/* Message Input Area */}
                <div className="border-t border-gray-100 p-3">
                  <form 
                    className="flex items-center space-x-2" 
                    onSubmit={(e) => handleSendMessage(e, conversation.id)}
                  >
                    <input
                      type="text"
                      className="flex-1 border border-gray-200 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Type your message..."
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      disabled={loading}
                    />
                    <button
                      type="submit"
                      className="bg-blue-600 text-white rounded-md p-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                      disabled={loading || !messageInput.trim()}
                    >
                      <Send size={16} />
                    </button>
                  </form>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
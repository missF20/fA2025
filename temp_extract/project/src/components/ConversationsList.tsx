import React, { useState } from 'react';
import { MessageSquare, Facebook, Instagram, MessageCircle, ChevronDown, ChevronUp } from 'lucide-react';
import type { Conversation } from '../types';

interface ConversationsListProps {
  conversations: Conversation[];
}

export function ConversationsList({ conversations }: ConversationsListProps) {
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);

  const getPlatformIcon = (platform: Conversation['platform']) => {
    switch (platform) {
      case 'facebook':
        return <Facebook size={16} className="text-blue-600" />;
      case 'instagram':
        return <Instagram size={16} className="text-pink-600" />;
      case 'whatsapp':
        return <MessageCircle size={16} className="text-green-600" />;
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

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-6">
        <MessageSquare className="text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Recent Conversations</h3>
      </div>

      <div className="space-y-4">
        {conversations.map((conversation) => (
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
              <div className="border-t border-gray-100 p-4 space-y-3">
                {conversation.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.sender_type === 'ai' ? 'justify-start' : 'justify-end'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.sender_type === 'ai'
                          ? 'bg-gray-100 text-gray-900'
                          : 'bg-blue-600 text-white'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <span className="text-xs opacity-70 mt-1 block">
                        {formatDate(message.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
import React from 'react';
import { BarChart2 } from 'lucide-react';
import TokenUsageWidget from './TokenUsageWidget';

/**
 * Token Usage Card Component
 * 
 * A card container for the token usage widget to be displayed below conversations.
 * Styled to match the ConversationsList component.
 */
const TokenUsageCard: React.FC = () => {
  return (
    <div className="mt-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 size={20} className="text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Token Usage Summary</h3>
        </div>
        
        <TokenUsageWidget />
      </div>
    </div>
  );
};

export default TokenUsageCard;
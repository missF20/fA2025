import React from 'react';
import TokenUsageWidget from './TokenUsageWidget';
import { motion } from 'framer-motion';

interface ConversationHeaderProps {
  title?: string;
}

/**
 * Header component for conversations dashboard that includes token usage widget
 */
const ConversationHeader: React.FC<ConversationHeaderProps> = ({ title = 'Conversations' }) => {
  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
      <motion.h1 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-gray-900 mb-4 md:mb-0"
      >
        {title}
      </motion.h1>
      <div className="w-full md:w-1/3 lg:w-1/4">
        <TokenUsageWidget />
      </div>
    </div>
  );
};

export default ConversationHeader;
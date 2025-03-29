import React from 'react';
import { 
  Home,
  MessageSquare,
  Star,
  HelpCircle,
  Share2,
  LogOut,
  FileText,
  BrainCircuit,
  CreditCard
} from 'lucide-react';
import { motion } from 'framer-motion';
import { supabase } from '../lib/supabase';

interface SidebarProps {
  currentSection: string;
  onSectionChange: (section: string) => void;
}

export function Sidebar({ currentSection, onSectionChange }: SidebarProps) {
  const menuItems = [
    { id: 'home', icon: <Home size={20} />, label: 'Home' },
    { id: 'conversations', icon: <MessageSquare size={20} />, label: 'Conversations' },
    { id: 'knowledge', icon: <FileText size={20} />, label: 'Knowledge Base' },
  ];

  const bottomMenuItems = [
    { id: 'rate', icon: <Star size={20} />, label: 'Rate Us' },
    { id: 'support', icon: <HelpCircle size={20} />, label: 'Support' },
    { id: 'subscriptions', icon: <CreditCard size={20} />, label: 'Subscriptions' },
    { id: 'integrations', icon: <Share2 size={20} />, label: 'Integrations' },
  ];

  return (
    <motion.div 
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      className="h-screen w-64 bg-white/90 backdrop-blur-sm border-r border-gray-200/50 flex flex-col fixed left-0 top-0"
    >
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-b border-gray-200/50"
      >
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ scale: 1.1, rotate: 360 }}
            transition={{ duration: 0.5 }}
          >
            <BrainCircuit className="text-blue-600" size={32} />
          </motion.div>
          <div>
            <h2 className="font-semibold text-gray-900">DANA AI</h2>
            <p className="text-sm text-gray-500">Dashboard</p>
          </div>
        </div>
      </motion.div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item, index) => (
            <motion.li 
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <motion.button
                onClick={() => onSectionChange(item.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  currentSection === item.id
                    ? 'bg-blue-50/80 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-50/80'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </motion.button>
            </motion.li>
          ))}
        </ul>
      </nav>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-t border-gray-200/50"
      >
        <ul className="space-y-2">
          {bottomMenuItems.map((item, index) => (
            <motion.li 
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
            >
              <motion.button
                onClick={() => onSectionChange(item.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  currentSection === item.id
                    ? 'bg-blue-50/80 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-50/80'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </motion.button>
            </motion.li>
          ))}
          <motion.li
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
          >
            <motion.button
              onClick={() => {
                supabase.auth.signOut();
                if (localStorage.getItem('dana_email')) {
                  localStorage.removeItem('dana_email');
                }
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-red-600 hover:bg-red-50/80 transition-colors"
            >
              <LogOut size={20} />
              <span>Sign Out</span>
            </motion.button>
          </motion.li>
        </ul>
      </motion.div>
    </motion.div>
  );
}
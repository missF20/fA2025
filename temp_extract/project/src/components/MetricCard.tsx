import React, { useState } from 'react';
import type { MetricCardType, PendingTask, Interaction, EscalatedTask } from '../types';
import { TrendingDown, TrendingUp, ChevronDown, ChevronUp, Facebook, Instagram, MessageCircle, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ExtendedMetricCardProps extends MetricCardType {
  pendingTasks?: PendingTask[];
  escalatedTasks?: EscalatedTask[];
  interactions?: Interaction[];
  breakdown?: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
}

export function MetricCard({ 
  title, 
  value, 
  icon, 
  description, 
  trend, 
  pendingTasks,
  escalatedTasks,
  interactions,
  breakdown
}: ExtendedMetricCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const renderBreakdown = () => {
    if (!breakdown) return null;

    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4 grid grid-cols-3 gap-2"
      >
        <motion.div 
          whileHover={{ scale: 1.05 }}
          className="flex items-center space-x-2 bg-blue-50/80 backdrop-blur-sm p-2 rounded-lg hover:bg-blue-100/80 transition-colors"
        >
          <Facebook size={16} className="text-blue-600" />
          <span className="text-sm text-blue-700">{breakdown.facebook}</span>
        </motion.div>
        <motion.div 
          whileHover={{ scale: 1.05 }}
          className="flex items-center space-x-2 bg-pink-50/80 backdrop-blur-sm p-2 rounded-lg hover:bg-pink-100/80 transition-colors"
        >
          <Instagram size={16} className="text-pink-600" />
          <span className="text-sm text-pink-700">{breakdown.instagram}</span>
        </motion.div>
        <motion.div 
          whileHover={{ scale: 1.05 }}
          className="flex items-center space-x-2 bg-green-50/80 backdrop-blur-sm p-2 rounded-lg hover:bg-green-100/80 transition-colors"
        >
          <MessageCircle size={16} className="text-green-600" />
          <span className="text-sm text-green-700">{breakdown.whatsapp}</span>
        </motion.div>
      </motion.div>
    );
  };

  const renderDetails = () => {
    if (pendingTasks) {
      return (
        <motion.div 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 space-y-3"
        >
          {pendingTasks.map((task) => (
            <motion.div
              key={task.id}
              whileHover={{ scale: 1.02 }}
              className="bg-gray-50/80 backdrop-blur-sm p-3 rounded-lg hover:bg-gray-100/80 transition-all"
            >
              <div className="text-sm font-medium text-gray-900">{task.task}</div>
              <div className="text-xs text-gray-500 mt-1">
                <span className="font-medium">{task.client.name}</span> from {task.client.company}
              </div>
              <div className="text-xs text-gray-400 mt-1">{task.timestamp}</div>
            </motion.div>
          ))}
        </motion.div>
      );
    }

    if (escalatedTasks) {
      return (
        <motion.div 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 space-y-3"
        >
          <h4 className="text-sm font-semibold text-gray-700 flex items-center">
            <AlertTriangle size={14} className="text-amber-500 mr-1" />
            Escalated Tasks
          </h4>
          {escalatedTasks.map((task) => (
            <motion.div
              key={task.id}
              whileHover={{ scale: 1.02 }}
              className="p-3 rounded-lg border bg-white/50 backdrop-blur-sm hover:bg-white/80 transition-all"
            >
              <div className="flex justify-between items-start">
                <div className="text-sm font-medium">{task.task}</div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  task.priority === 'high' ? 'bg-red-100 text-red-800' : 
                  task.priority === 'medium' ? 'bg-orange-100 text-orange-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {task.priority}
                </span>
              </div>
              <div className="text-xs mt-1">
                <span className="font-medium">{task.client.name}</span> from {task.client.company}
              </div>
              <div className="text-xs opacity-70 mt-1">{new Date(task.timestamp).toLocaleString()}</div>
            </motion.div>
          ))}
        </motion.div>
      );
    }

    if (interactions) {
      return (
        <motion.div 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 space-y-3"
        >
          {interactions.map((interaction) => (
            <motion.div
              key={interaction.id}
              whileHover={{ scale: 1.02 }}
              className="bg-gray-50/80 backdrop-blur-sm p-3 rounded-lg hover:bg-gray-100/80 transition-all"
            >
              <div className="text-sm font-medium text-gray-900">{interaction.name}</div>
              <div className="text-xs text-gray-500 mt-1">{interaction.company}</div>
              <div className="text-xs text-gray-400 mt-1">
                {interaction.type} • {interaction.timestamp}
              </div>
            </motion.div>
          ))}
        </motion.div>
      );
    }

    return null;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className="bg-white/90 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50 hover:shadow-xl transition-all"
    >
      <motion.div 
        animate={isHovered ? { y: -2 } : { y: 0 }}
        className="flex items-center justify-between mb-4"
      >
        <div className="text-gray-500">{icon}</div>
        {trend && (
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex items-center ${trend.isPositive ? 'text-green-500' : 'text-red-500'}`}
          >
            {trend.isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span className="ml-1 text-sm">{trend.value}%</span>
          </motion.div>
        )}
      </motion.div>

      <motion.h3 
        animate={isHovered ? { scale: 1.05 } : { scale: 1 }}
        className="text-2xl font-bold text-gray-900 mb-1"
      >
        {value.toLocaleString()}
      </motion.h3>
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <p className="text-xs text-gray-400 mt-2">{description}</p>
      
      {breakdown && renderBreakdown()}
      
      {(pendingTasks || interactions || escalatedTasks) && (
        <>
          <motion.button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center text-blue-500 text-sm mt-4 hover:text-blue-600 transition-colors"
            whileHover={{ scale: 1.05 }}
          >
            {isExpanded ? (
              <>
                <ChevronUp size={16} className="mr-1" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown size={16} className="mr-1" />
                Show details
              </>
            )}
          </motion.button>
          <AnimatePresence>
            {isExpanded && renderDetails()}
          </AnimatePresence>
        </>
      )}
    </motion.div>
  );
}
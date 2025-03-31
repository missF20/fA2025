import React from 'react';
import type { ChatMetrics } from '../types';
import { Facebook, Instagram, MessageCircle } from 'lucide-react';

interface InteractionChartProps {
  data: ChatMetrics['interactionsByType'];
}

export function InteractionChart({ data }: InteractionChartProps) {
  // Handle empty or undefined data
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Interactions by Platform</h3>
        <p className="text-gray-500 text-center">No interaction data available</p>
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.count, 0);
  let currentAngle = 0;

  // Updated color palette for social media platforms
  const colors = {
    Facebook: {
      fill: 'fill-blue-500',
      bg: 'bg-blue-500',
      icon: <Facebook size={16} className="text-blue-500" />
    },
    Instagram: {
      fill: 'fill-pink-500',
      bg: 'bg-pink-500',
      icon: <Instagram size={16} className="text-pink-500" />
    },
    WhatsApp: {
      fill: 'fill-green-500',
      bg: 'bg-green-500',
      icon: <MessageCircle size={16} className="text-green-500" />
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Interactions by Platform</h3>
      <div className="flex items-center justify-between">
        <div className="relative w-[200px] h-[200px]">
          <svg viewBox="0 0 100 100" className="transform -rotate-90">
            {data.map((item) => {
              const percentage = (item.count / total) * 100;
              const angle = (percentage / 100) * 360;
              
              const startAngle = currentAngle;
              currentAngle += angle;
              
              const x1 = 50 + 40 * Math.cos((Math.PI * startAngle) / 180);
              const y1 = 50 + 40 * Math.sin((Math.PI * startAngle) / 180);
              const x2 = 50 + 40 * Math.cos((Math.PI * currentAngle) / 180);
              const y2 = 50 + 40 * Math.sin((Math.PI * currentAngle) / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              
              const platformKey = item.type as keyof typeof colors;
              const colorClass = colors[platformKey]?.fill || 'fill-gray-300';
              
              return (
                <path
                  key={item.type}
                  d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
                  className={`${colorClass} opacity-80`}
                />
              );
            })}
          </svg>
        </div>
        <div className="flex flex-col space-y-3">
          {data.map((item) => {
            const platformKey = item.type as keyof typeof colors;
            const platformIcon = colors[platformKey]?.icon;
            
            return (
              <div key={item.type} className="flex items-center">
                {platformIcon}
                <span className="text-sm text-gray-600 ml-2">
                  {item.type}: {item.count} ({((item.count / total) * 100).toFixed(1)}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
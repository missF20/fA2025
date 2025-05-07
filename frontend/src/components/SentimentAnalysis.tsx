import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Smile, Meh, Frown, Info, HelpCircle, BarChart, PieChart } from 'lucide-react';
import { SentimentData } from '../types';

interface SentimentAnalysisProps {
  data: SentimentData[];
}

export function SentimentAnalysis({ data }: SentimentAnalysisProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [chartType, setChartType] = useState<'pie' | 'donut'>('donut');
  const [tooltipVisible, setTooltipVisible] = useState<boolean>(false);

  // Check if data is available
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Analysis</h3>
        <div className="flex flex-col items-center justify-center h-48">
          <div className="bg-gray-100 p-4 rounded-full mb-4">
            <Meh size={32} className="text-gray-400" />
          </div>
          <p className="text-gray-500 text-center">No sentiment data available</p>
        </div>
      </div>
    );
  }

  // Colors for sentiment types
  const sentimentColors = {
    positive: '#22c55e', // green-500
    neutral: '#94a3b8', // slate-400
    negative: '#ef4444', // red-500
  };

  // Sentiment icons
  const sentimentIcons = {
    positive: <Smile size={20} className="text-green-500" />,
    neutral: <Meh size={20} className="text-slate-400" />,
    negative: <Frown size={20} className="text-red-500" />,
  };

  // We're using a pure SVG implementation instead of recharts due to TypeScript compatibility issues

  // Get trend icon based on sentiment trend value
  const getTrendIcon = (trend: number) => {
    if (trend > 0) {
      return <span className="text-green-500 text-xs">+{trend}%</span>;
    } else if (trend < 0) {
      return <span className="text-red-500 text-xs">{trend}%</span>;
    }
    return <span className="text-gray-400 text-xs">0%</span>;
  };

  // Calculate total messages for additional insights
  const totalMessages = data.reduce((sum, item) => sum + item.count, 0);
  const positivePercentage = data.find(item => item.type === 'positive')?.percentage || 0;
  const negativePercentage = data.find(item => item.type === 'negative')?.percentage || 0;
  
  // Determine overall sentiment
  let overallSentiment = 'neutral';
  let sentimentMessage = 'Neutral overall sentiment';
  
  if (positivePercentage > negativePercentage + 20) {
    overallSentiment = 'positive';
    sentimentMessage = 'Positive overall sentiment';
  } else if (negativePercentage > positivePercentage + 10) {
    overallSentiment = 'negative';
    sentimentMessage = 'Negative overall sentiment';
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Sentiment Analysis</h3>
        
        <div className="flex space-x-2">
          {/* Chart type toggle */}
          <div className="flex bg-gray-100 p-1 rounded-md">
            <button
              onClick={() => setChartType('donut')}
              className={`p-1 rounded ${chartType === 'donut' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Donut Chart"
            >
              <PieChart size={16} />
            </button>
            <button
              onClick={() => setChartType('pie')}
              className={`p-1 rounded ${chartType === 'pie' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Pie Chart"
            >
              <BarChart size={16} />
            </button>
          </div>
          
          {/* Help tooltip */}
          <div className="relative">
            <button
              onMouseEnter={() => setTooltipVisible(true)}
              onMouseLeave={() => setTooltipVisible(false)}
              className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            >
              <HelpCircle size={16} />
            </button>
            <AnimatePresence>
              {tooltipVisible && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute right-0 w-48 bg-black text-white text-xs rounded py-1 px-2 z-10"
                >
                  Shows the sentiment distribution of customer interactions based on AI analysis
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Chart visualization - fallback manual chart when recharts has TS issues */}
        <div className="lg:w-1/2 h-48 flex items-center justify-center">
          {/* Manual SVG donut/pie chart as fallback */}
          <svg width="150" height="150" viewBox="0 0 150 150">
            <g transform="translate(75, 75)">
              {/* Draw pie segments manually */}
              {data.map((item, index) => {
                // Simplified pie/donut chart logic
                const total = data.reduce((sum, d) => sum + d.count, 0);
                const percentage = item.count / total;
                
                // Calculate start and end angles for each segment
                const startAngle = index === 0 ? 0 : 
                  data.slice(0, index).reduce((sum, d) => sum + (d.count / total) * Math.PI * 2, 0);
                const endAngle = startAngle + percentage * Math.PI * 2;
                
                // Calculate pie segment coordinates
                const startX = Math.cos(startAngle) * (chartType === 'pie' ? 0 : 40);
                const startY = Math.sin(startAngle) * (chartType === 'pie' ? 0 : 40);
                const endX = Math.cos(endAngle) * (chartType === 'pie' ? 0 : 40);
                const endY = Math.sin(endAngle) * (chartType === 'pie' ? 0 : 40);
                
                const outerStartX = Math.cos(startAngle) * 70;
                const outerStartY = Math.sin(startAngle) * 70;
                const outerEndX = Math.cos(endAngle) * 70;
                const outerEndY = Math.sin(endAngle) * 70;
                
                // Calculate arc flags
                const largeArcFlag = percentage > 0.5 ? 1 : 0;
                
                // Create pie segment path
                const path = [
                  `M ${startX} ${startY}`,
                  `L ${outerStartX} ${outerStartY}`,
                  `A 70 70 0 ${largeArcFlag} 1 ${outerEndX} ${outerEndY}`,
                  `L ${endX} ${endY}`,
                  chartType === 'pie' ? 'Z' : `A 40 40 0 ${largeArcFlag} 0 ${startX} ${startY}`
                ].join(' ');
                
                // Handle active state
                const isActive = activeIndex === index;
                const stroke = isActive ? "#fff" : "none";
                const strokeWidth = isActive ? 2 : 0;
                
                return (
                  <path 
                    key={`pie-segment-${index}`} 
                    d={path} 
                    fill={sentimentColors[item.type]} 
                    stroke={stroke}
                    strokeWidth={strokeWidth}
                    onMouseEnter={() => setActiveIndex(index)}
                    onMouseLeave={() => setActiveIndex(null)}
                  />
                );
              })}
              
              {/* Display active segment text */}
              {activeIndex !== null && (
                <>
                  <text 
                    x="0" 
                    y="0" 
                    textAnchor="middle" 
                    fill="#374151" 
                    fontSize="12"
                    fontWeight="500"
                  >
                    {data[activeIndex].type}
                  </text>
                  <text 
                    x="0" 
                    y="16" 
                    textAnchor="middle" 
                    fill="#6B7280" 
                    fontSize="10"
                  >
                    {data[activeIndex].percentage.toFixed(1)}%
                  </text>
                </>
              )}
            </g>
          </svg>
        </div>

        {/* Details and insights */}
        <div className="lg:w-1/2 mt-4 lg:mt-0">
          <div className="space-y-3">
            {data.map((item) => (
              <div 
                key={item.id}
                className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                onMouseEnter={() => setActiveIndex(data.findIndex(d => d.id === item.id))}
                onMouseLeave={() => setActiveIndex(null)}
              >
                <div className="flex items-center">
                  {sentimentIcons[item.type]}
                  <span className="ml-2 text-sm capitalize">{item.type}</span>
                </div>
                <div className="flex items-center space-x-3">
                  {getTrendIcon(item.trend)}
                  <span className="font-medium text-sm">
                    {item.count} <span className="text-gray-400">({item.percentage.toFixed(0)}%)</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Insights */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center">
              <div 
                className={`p-1.5 rounded-full mr-2 ${
                  overallSentiment === 'positive' 
                    ? 'bg-green-100' 
                    : overallSentiment === 'negative' 
                      ? 'bg-red-100' 
                      : 'bg-gray-100'
                }`}
              >
                {
                  overallSentiment === 'positive' 
                    ? <Smile size={16} className="text-green-500" />
                    : overallSentiment === 'negative' 
                      ? <Frown size={16} className="text-red-500" />
                      : <Meh size={16} className="text-gray-400" />
                }
              </div>
              <span className="text-sm text-gray-700">{sentimentMessage}</span>
            </div>
            
            <div className="mt-2 pt-2 flex items-center">
              <Info size={14} className="text-blue-500 mr-1" />
              <span className="text-xs text-gray-500">
                Based on {totalMessages} analyzed messages
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
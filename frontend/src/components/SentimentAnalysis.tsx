import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Smile, Meh, Frown, Info, HelpCircle, BarChart, PieChart } from 'lucide-react';
// Import recharts with explicit types
import { 
  Cell, 
  Pie, 
  PieChart as RechartsPieChart, 
  ResponsiveContainer, 
  Sector, 
  PieLabelRenderProps 
} from 'recharts';

interface SentimentData {
  id: string;
  type: 'positive' | 'neutral' | 'negative';
  count: number;
  trend: number;
  percentage: number;
}

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

  // Format data for pie/donut chart
  const chartData = data.map(item => ({
    name: item.type,
    value: item.count,
    color: sentimentColors[item.type],
    percentage: item.percentage,
    trend: item.trend,
  }));

  // TypeScript interface for active shape props from recharts
  interface ActiveShapeProps {
    cx: number;
    cy: number;
    innerRadius: number;
    outerRadius: number;
    startAngle: number;
    endAngle: number;
    fill: string;
    payload: {
      name: string;
      value: number;
      color: string;
      percentage: number;
      trend: number;
    };
    percent: number;
    value: number;
  }

  // Custom active shape for donut/pie chart with proper typing
  const renderActiveShape = (props: ActiveShapeProps) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props;
    
    // Use recharts components directly as function calls to avoid JSX typing issues
    return (
      <g>
        <text x={cx} y={cy} dy={0} textAnchor="middle" fill="#374151" fontSize={12} fontWeight="medium">
          {payload.name}
        </text>
        <text x={cx} y={cy + 16} dy={0} textAnchor="middle" fill="#6B7280" fontSize={10}>
          {`${(percent * 100).toFixed(1)}%`}
        </text>
        {Sector({
          cx,
          cy,
          innerRadius,
          outerRadius: outerRadius + 5,
          startAngle,
          endAngle,
          fill
        })}
        {Sector({
          cx,
          cy,
          startAngle,
          endAngle,
          innerRadius: outerRadius + 6,
          outerRadius: outerRadius + 8,
          fill
        })}
      </g>
    );
  };

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
        {/* Chart visualization */}
        <div className="lg:w-1/2 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                activeIndex={activeIndex !== null ? activeIndex : undefined}
                activeShape={renderActiveShape}
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={chartType === 'donut' ? 50 : 0}
                outerRadius={70}
                fill="#8884d8"
                dataKey="value"
                onMouseEnter={(_, index) => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    stroke="#fff"
                    strokeWidth={1}
                  />
                ))}
              </Pie>
            </RechartsPieChart>
          </ResponsiveContainer>
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
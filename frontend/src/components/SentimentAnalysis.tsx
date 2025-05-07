import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Smile, Meh, Frown, Info, HelpCircle, RefreshCcw, 
  PieChart, TrendingUp, MessageSquare, Download, Users, ChevronRight 
} from 'lucide-react';
import { SentimentData } from '../types';

interface SentimentAnalysisProps {
  data: SentimentData[];
}

export function SentimentAnalysis({ data }: SentimentAnalysisProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [chartType, setChartType] = useState<'donut' | 'gauge'>('donut');
  const [tooltipVisible, setTooltipVisible] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [hoverSegment, setHoverSegment] = useState<string | null>(null);

  // Simulate data loading when time range changes
  useEffect(() => {
    if (timeRange) {
      setLoading(true);
      const timer = setTimeout(() => {
        setLoading(false);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [timeRange]);

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

  // Colors for sentiment types with expanded palette
  const sentimentColors = {
    positive: {
      main: '#22c55e', // green-500
      light: '#dcfce7', // green-100
      dark: '#16a34a', // green-600
      text: 'text-green-500',
      bg: 'bg-green-500', 
      bgLight: 'bg-green-100',
      hover: 'hover:bg-green-50',
      border: 'border-green-200'
    },
    neutral: {
      main: '#94a3b8', // slate-400
      light: '#f1f5f9', // slate-100
      dark: '#64748b', // slate-500
      text: 'text-slate-400',
      bg: 'bg-slate-400',
      bgLight: 'bg-slate-100',
      hover: 'hover:bg-slate-50',
      border: 'border-slate-200'
    },
    negative: {
      main: '#ef4444', // red-500
      light: '#fee2e2', // red-100
      dark: '#dc2626', // red-600
      text: 'text-red-500',
      bg: 'bg-red-500',
      bgLight: 'bg-red-100',
      hover: 'hover:bg-red-50',
      border: 'border-red-200'
    }
  };

  // Sentiment icons with enhanced design
  const sentimentIcons = {
    positive: <Smile size={18} className="text-green-500" />,
    neutral: <Meh size={18} className="text-slate-400" />,
    negative: <Frown size={18} className="text-red-500" />,
  };

  // Get trend icon based on sentiment trend value with enhanced visuals
  const getTrendIcon = (trend: number, type: string) => {
    const sentimentType = type as keyof typeof sentimentColors;
    if (trend > 10) {
      return (
        <div className={`flex items-center ${sentimentColors[sentimentType].text} font-medium`}>
          <TrendingUp size={12} className="mr-0.5" />
          <span>+{trend}%</span>
        </div>
      );
    } else if (trend > 0) {
      return <span className={`${sentimentColors[sentimentType].text}`}>+{trend}%</span>;
    } else if (trend < 0) {
      return <span className="text-red-500">{trend}%</span>;
    }
    return <span className="text-gray-400">0%</span>;
  };

  // Calculate total messages for additional insights
  const totalMessages = data.reduce((sum, item) => sum + item.count, 0);
  const positiveData = data.find(item => item.type === 'positive') || { count: 0, percentage: 0, trend: 0 };
  const neutralData = data.find(item => item.type === 'neutral') || { count: 0, percentage: 0, trend: 0 };
  const negativeData = data.find(item => item.type === 'negative') || { count: 0, percentage: 0, trend: 0 };
  
  const positivePercentage = positiveData?.percentage || 0;
  const negativePercentage = negativeData?.percentage || 0;
  
  // Determine overall sentiment with more nuanced thresholds
  let overallSentiment = 'neutral';
  let sentimentMessage = 'Neutral customer sentiment';
  let sentimentDescription = 'Customer feedback is balanced between positive and negative experiences.';
  
  if (positivePercentage > negativePercentage + 20) {
    overallSentiment = 'positive';
    sentimentMessage = 'Positive customer sentiment';
    sentimentDescription = 'Most customers are having positive experiences with your products and services.';
  } else if (negativePercentage > positivePercentage + 10) {
    overallSentiment = 'negative';
    sentimentMessage = 'Negative customer sentiment';
    sentimentDescription = 'A significant number of customers are reporting negative experiences that need attention.';
  } else if (positivePercentage > negativePercentage + 5) {
    overallSentiment = 'positive';
    sentimentMessage = 'Slightly positive sentiment';
    sentimentDescription = 'Customer feedback is trending positive, but there's room for improvement.';
  } else if (negativePercentage > positivePercentage + 5) {
    overallSentiment = 'negative';
    sentimentMessage = 'Slightly negative sentiment';
    sentimentDescription = 'Customer feedback shows some concerning patterns that should be addressed.';
  }

  // Build category-specific insights
  const categoryInsights = {
    product: [
      { sentiment: 'positive', text: 'Product durability is frequently praised' },
      { sentiment: 'negative', text: 'Some users report issues with product packaging' }
    ],
    service: [
      { sentiment: 'positive', text: 'Customer service response time is well-received' },
      { sentiment: 'negative', text: 'Weekend support availability is a common complaint' }
    ],
    pricing: [
      { sentiment: 'neutral', text: 'Price point is considered fair for the value provided' },
      { sentiment: 'negative', text: 'Subscription pricing model causes some confusion' }
    ]
  };

  // Generate actionable recommendations based on sentiment
  const getRecommendations = () => {
    if (overallSentiment === 'positive') {
      return [
        'Highlight positive customer testimonials in marketing materials',
        'Analyze what's working well to replicate across other areas'
      ];
    } else if (overallSentiment === 'negative') {
      return [
        'Investigate common themes in negative feedback',
        'Establish a customer recovery program for dissatisfied customers'
      ];
    }
    return [
      'Balance resources between addressing pain points and enhancing strengths',
      'Conduct targeted surveys to gather more specific feedback'
    ];
  };

  // Function to handle csv download
  const downloadCSV = () => {
    const headers = ['Type', 'Count', 'Percentage', 'Trend'];
    const csvData = data.map(item => 
      [item.type, item.count, item.percentage, item.trend].join(',')
    );
    
    const csvContent = [
      headers.join(','),
      ...csvData
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `sentiment_analysis_${timeRange}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Animated donut chart component
  const renderDonutChart = () => {
    const radius = 70;
    const innerRadius = 45;
    const centerX = 75;
    const centerY = 75;
    
    return (
      <div className="relative w-[180px] h-[180px]">
        <svg width="180" height="180" viewBox="0 0 180 180" className="transform -rotate-90">
          <g transform={`translate(${centerX}, ${centerY})`}>
            {data.map((item, index) => {
              if (item.percentage === 0) return null;
              
              // Calculate segment dimensions
              const total = 100; // Using percentage directly
              const anglePerPercent = (Math.PI * 2) / total;
              const previousPercentages = data
                .slice(0, index)
                .reduce((sum, d) => sum + d.percentage, 0);
              
              const startAngle = anglePerPercent * previousPercentages;
              const endAngle = startAngle + (anglePerPercent * item.percentage);
              
              // Calculate path coordinates
              const startOuterX = Math.cos(startAngle) * radius;
              const startOuterY = Math.sin(startAngle) * radius;
              const endOuterX = Math.cos(endAngle) * radius;
              const endOuterY = Math.sin(endAngle) * radius;
              
              const startInnerX = Math.cos(startAngle) * innerRadius;
              const startInnerY = Math.sin(startAngle) * innerRadius;
              const endInnerX = Math.cos(endAngle) * innerRadius;
              const endInnerY = Math.sin(endAngle) * innerRadius;
              
              // Determine if we need to draw a large arc (more than 180 degrees)
              const largeArcFlag = item.percentage > 50 ? 1 : 0;
              
              // Create SVG path for the donut segment
              const path = [
                `M ${startOuterX} ${startOuterY}`, // Move to start of outer arc
                `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endOuterX} ${endOuterY}`, // Draw outer arc
                `L ${endInnerX} ${endInnerY}`, // Line to inner arc end
                `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${startInnerX} ${startInnerY}`, // Draw inner arc
                'Z' // Close path
              ].join(' ');
              
              const isHovered = hoverSegment === item.type;
              
              // Apply animations and interactions
              return (
                <g 
                  key={`segment-${item.type}`}
                  onMouseEnter={() => {
                    setHoverSegment(item.type);
                    setActiveIndex(index);
                  }}
                  onMouseLeave={() => {
                    setHoverSegment(null);
                    setActiveIndex(null);
                  }}
                  className="cursor-pointer"
                >
                  <motion.path
                    d={path}
                    fill={sentimentColors[item.type].main}
                    initial={{ opacity: 0 }}
                    animate={{ 
                      opacity: hoverSegment === null || isHovered ? 1 : 0.7,
                      scale: isHovered ? 1.05 : 1
                    }}
                    transition={{ duration: 0.3 }}
                    transform={isHovered ? `translate(${Math.cos((startAngle + endAngle) / 2) * 3}, ${Math.sin((startAngle + endAngle) / 2) * 3})` : ''}
                  />
                  
                  {/* Segment dividers/separators */}
                  <line
                    x1={startInnerX}
                    y1={startInnerY}
                    x2={startOuterX}
                    y2={startOuterY}
                    stroke="#ffffff"
                    strokeWidth="1"
                  />
                </g>
              );
            })}

            {/* Inner circle with overall sentiment icon */}
            <circle
              cx="0"
              cy="0"
              r={innerRadius - 5}
              fill="#ffffff"
              stroke="#f1f5f9"
              strokeWidth="1"
            />
          </g>
        </svg>
        
        {/* Center text overlay (displayed in the normal/non-rotated orientation) */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {activeIndex !== null ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center"
            >
              <span className={`text-sm font-medium capitalize ${sentimentColors[data[activeIndex].type].text}`}>
                {data[activeIndex].type}
              </span>
              <span className="text-2xl font-bold">
                {data[activeIndex].percentage.toFixed(0)}%
              </span>
              <span className="text-xs text-gray-500">
                {data[activeIndex].count} messages
              </span>
            </motion.div>
          ) : (
            <div className="flex flex-col items-center">
              <div className={`p-2 rounded-full ${sentimentColors[overallSentiment].bgLight} mb-1`}>
                {overallSentiment === 'positive' ? (
                  <Smile size={20} className="text-green-500" />
                ) : overallSentiment === 'negative' ? (
                  <Frown size={20} className="text-red-500" />
                ) : (
                  <Meh size={20} className="text-slate-400" />
                )}
              </div>
              <span className="text-xs font-medium text-gray-600 text-center whitespace-nowrap">
                {overallSentiment === 'positive' ? 'Mostly Positive' : 
                 overallSentiment === 'negative' ? 'Needs Attention' : 'Neutral'}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Gauge chart for sentiment visualization
  const renderGaugeChart = () => {
    // Calculate sentiment score (0-100) where 0 is negative, 50 is neutral, 100 is positive
    const sentimentScore = Math.min(100, Math.max(0, 50 + (positivePercentage - negativePercentage)));
    // Convert to angle for gauge (0 = -90deg, 100 = 90deg)
    const angle = -90 + (sentimentScore * 1.8); // 180 degrees total range
    
    return (
      <div className="relative w-[180px] h-[180px]">
        {/* Background track */}
        <svg width="180" height="180" viewBox="0 0 180 180" className="absolute">
          <g transform="translate(90, 90)">
            {/* Gray background arc */}
            <path 
              d="M -80 0 A 80 80 0 0 1 80 0" 
              fill="none" 
              stroke="#e5e7eb" 
              strokeWidth="15" 
              strokeLinecap="round"
            />
            
            {/* Colored segments of the arc */}
            <path 
              d="M -80 0 A 80 80 0 0 1 -28 -75" 
              fill="none" 
              stroke="#ef4444" 
              strokeWidth="15" 
              strokeLinecap="round"
            />
            <path 
              d="M -28 -75 A 80 80 0 0 1 28 -75" 
              fill="none" 
              stroke="#94a3b8" 
              strokeWidth="15" 
              strokeLinecap="round"
            />
            <path 
              d="M 28 -75 A 80 80 0 0 1 80 0" 
              fill="none" 
              stroke="#22c55e" 
              strokeWidth="15" 
              strokeLinecap="round"
            />
            
            {/* Tick marks */}
            {[0, 25, 50, 75, 100].map(tick => {
              const tickAngle = -90 + (tick * 1.8);
              const x = Math.cos(tickAngle * Math.PI / 180) * 80;
              const y = Math.sin(tickAngle * Math.PI / 180) * 80;
              const innerX = Math.cos(tickAngle * Math.PI / 180) * 70;
              const innerY = Math.sin(tickAngle * Math.PI / 180) * 70;
              
              return (
                <g key={`tick-${tick}`}>
                  <line
                    x1={innerX}
                    y1={innerY}
                    x2={x}
                    y2={y}
                    stroke="#ffffff"
                    strokeWidth="2"
                  />
                  <text
                    x={Math.cos(tickAngle * Math.PI / 180) * 58}
                    y={Math.sin(tickAngle * Math.PI / 180) * 58}
                    fontSize="10"
                    fill="#6b7280"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    {tick === 0 ? 'Neg' : tick === 50 ? 'Neu' : tick === 100 ? 'Pos' : ''}
                  </text>
                </g>
              );
            })}
            
            {/* Needle */}
            <motion.g
              initial={{ rotate: -90 }}
              animate={{ rotate: angle }}
              transition={{ type: 'spring', stiffness: 100, damping: 15 }}
            >
              <line x1="0" y1="0" x2="0" y2="-65" stroke="#1f2937" strokeWidth="2" />
              <circle cx="0" cy="0" r="10" fill="#1f2937" />
              <circle cx="0" cy="0" r="6" fill="#ffffff" />
            </motion.g>
          </g>
        </svg>
        
        {/* Score display */}
        <div className="absolute bottom-2 left-0 right-0 flex flex-col items-center justify-center">
          <div className="bg-white rounded-full px-3 py-1 shadow-sm border">
            <span className="text-sm font-medium">
              Score: 
              <span 
                className={`ml-1 ${
                  sentimentScore > 60 ? 'text-green-500' : 
                  sentimentScore < 40 ? 'text-red-500' : 
                  'text-slate-500'
                }`}
              >
                {sentimentScore.toFixed(0)}
              </span>
            </span>
          </div>
        </div>
      </div>
    );
  };

  // Render time period filter buttons
  const renderTimeFilters = () => (
    <div className="flex bg-gray-100 p-1 rounded-md text-xs">
      {['day', 'week', 'month'].map((period) => (
        <button
          key={period}
          onClick={() => setTimeRange(period as 'day' | 'week' | 'month')}
          className={`px-2 py-1 rounded ${
            timeRange === period 
              ? 'bg-white shadow-sm font-medium text-gray-800' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {period.charAt(0).toUpperCase() + period.slice(1)}
        </button>
      ))}
    </div>
  );

  // Main render method
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full overflow-hidden">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Customer Sentiment Analysis</h3>
        
        <div className="flex flex-wrap gap-2 mt-2 sm:mt-0">
          {/* Time filter */}
          {renderTimeFilters()}
          
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
              onClick={() => setChartType('gauge')}
              className={`p-1 rounded ${chartType === 'gauge' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Gauge Chart"
            >
              <RefreshCcw size={16} />
            </button>
          </div>
          
          {/* Download button */}
          <button
            onClick={downloadCSV}
            className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            title="Download data as CSV"
          >
            <Download size={16} />
          </button>
          
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
                  className="absolute right-0 w-64 bg-black text-white text-xs rounded py-1.5 px-2.5 z-10"
                >
                  AI-powered sentiment analysis of customer interactions across all channels. Updated in real-time.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10 rounded-xl">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="mt-2 text-sm text-gray-500">Loading sentiment data...</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left side: Chart visualization */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center">
          {chartType === 'donut' && renderDonutChart()}
          {chartType === 'gauge' && renderGaugeChart()}
          
          {/* Overall sentiment indicator */}
          <div 
            className={`mt-2 px-3 py-1.5 rounded-full flex items-center 
            ${sentimentColors[overallSentiment].bgLight} 
            ${sentimentColors[overallSentiment].border} border`}
          >
            {sentimentIcons[overallSentiment]}
            <span className={`ml-1.5 text-sm font-medium ${sentimentColors[overallSentiment].text}`}>
              {sentimentMessage}
            </span>
          </div>
          
          <p className="text-xs text-gray-500 text-center mt-2 max-w-[250px]">
            {sentimentDescription}
          </p>
        </div>

        {/* Right side: Details and insights */}
        <div className="lg:col-span-7 flex flex-col">
          {/* Detailed sentiment metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Positive', type: 'positive', data: positiveData },
              { label: 'Neutral', type: 'neutral', data: neutralData },
              { label: 'Negative', type: 'negative', data: negativeData }
            ].map(category => (
              <motion.div
                key={category.type}
                className={`rounded-lg border px-3 py-2 ${
                  selectedCategory === category.type 
                    ? sentimentColors[category.type].border + ' ' + sentimentColors[category.type].bgLight 
                    : 'border-gray-200 hover:border-gray-300'
                } cursor-pointer`}
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedCategory(
                  selectedCategory === category.type ? null : category.type
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {sentimentIcons[category.type]}
                    <span className="ml-1.5 text-sm font-medium">{category.label}</span>
                  </div>
                  {getTrendIcon(category.data.trend, category.type)}
                </div>
                <div className="flex justify-between items-end mt-1">
                  <div className="flex items-baseline">
                    <span className="text-xl font-bold">{category.data.percentage.toFixed(0)}%</span>
                    <span className="text-xs text-gray-500 ml-1">of total</span>
                  </div>
                  <span className="text-sm text-gray-500">{category.data.count} messages</span>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Message volume by source */}
          <div className="border rounded-lg p-3 mb-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-sm font-medium flex items-center">
                <MessageSquare size={14} className="text-blue-500 mr-1.5" />
                Message Sources
              </h4>
              <span className="text-xs text-gray-500">{totalMessages} total messages</span>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              {[
                { source: 'Email', count: Math.round(totalMessages * 0.35), icon: '📧', color: 'bg-blue-100' },
                { source: 'Facebook', count: Math.round(totalMessages * 0.25), icon: '👤', color: 'bg-indigo-100' },
                { source: 'Chat', count: Math.round(totalMessages * 0.15), icon: '💬', color: 'bg-green-100' },
                { source: 'Twitter', count: Math.round(totalMessages * 0.25), icon: '🐦', color: 'bg-sky-100' }
              ].map(source => (
                <div key={source.source} className="flex items-center">
                  <div className={`w-6 h-6 rounded-full ${source.color} flex items-center justify-center mr-2`}>
                    <span className="text-xs">{source.icon}</span>
                  </div>
                  <div>
                    <div className="text-xs font-medium">{source.source}</div>
                    <div className="text-xs text-gray-500">{source.count} messages</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Recommendations */}
          <div className="border rounded-lg p-3">
            <h4 className="text-sm font-medium flex items-center mb-2">
              <Users size={14} className="text-violet-500 mr-1.5" />
              Recommended Actions
            </h4>
            
            <ul className="space-y-1.5">
              {getRecommendations().map((recommendation, index) => (
                <li key={index} className="text-xs flex items-start">
                  <div 
                    className={`${sentimentColors[overallSentiment].bgLight} rounded-full w-4 h-4 flex items-center justify-center mt-0.5 mr-2 flex-shrink-0`}
                  >
                    <span className="text-[8px] font-medium">{index + 1}</span>
                  </div>
                  <span className="text-gray-600">{recommendation}</span>
                </li>
              ))}
            </ul>
            
            <button className="mt-3 text-xs text-blue-600 flex items-center hover:underline">
              View detailed analysis
              <ChevronRight size={12} className="ml-0.5" />
            </button>
          </div>
          
          <div className="mt-auto pt-4 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center">
              <Info size={12} className="text-blue-500 mr-1" />
              <span>AI sentiment analysis based on {totalMessages} messages from the past {timeRange}</span>
            </div>
            <button className="text-blue-600 hover:underline">
              Customize
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
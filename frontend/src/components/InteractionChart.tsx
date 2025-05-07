import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Facebook, 
  Instagram, 
  MessageCircle, 
  Mail, 
  Slack, 
  PieChart, 
  BarChart, 
  LineChart,
  Eye, 
  EyeOff,
  Download,
  HelpCircle
} from 'lucide-react';
import type { ChatMetrics } from '../types';

interface InteractionChartProps {
  data: ChatMetrics['interactionsByType'];
}

interface ExtendedInteraction {
  type: string;
  count: number;
  trend?: number;
  color: string;
  icon: React.ReactNode;
  hidden?: boolean;
}

export function InteractionChart({ data }: InteractionChartProps) {
  const [chartType, setChartType] = useState<'pie' | 'bar' | 'line'>('pie');
  const [highlightedPlatform, setHighlightedPlatform] = useState<string | null>(null);
  const [hiddenPlatforms, setHiddenPlatforms] = useState<string[]>([]);
  const [showTooltip, setShowTooltip] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  
  // Color palette for all platforms
  const platformColors = {
    Facebook: {
      fill: 'fill-blue-500',
      bg: 'bg-blue-500',
      stroke: 'stroke-blue-500',
      text: 'text-blue-500',
      color: '#3b82f6',
      icon: <Facebook size={16} className="text-blue-500" />
    },
    Instagram: {
      fill: 'fill-pink-500',
      bg: 'bg-pink-500',
      stroke: 'stroke-pink-500',
      text: 'text-pink-500',
      color: '#ec4899',
      icon: <Instagram size={16} className="text-pink-500" />
    },
    Whatsapp: {
      fill: 'fill-green-500',
      bg: 'bg-green-500',
      stroke: 'stroke-green-500',
      text: 'text-green-500',
      color: '#22c55e',
      icon: <MessageCircle size={16} className="text-green-500" />
    },
    Slack: {
      fill: 'fill-purple-500',
      bg: 'bg-purple-500',
      stroke: 'stroke-purple-500',
      text: 'text-purple-500',
      color: '#a855f7',
      icon: <Slack size={16} className="text-purple-500" />
    },
    Email: {
      fill: 'fill-cyan-500',
      bg: 'bg-cyan-500',
      stroke: 'stroke-cyan-500',
      text: 'text-cyan-500',
      color: '#06b6d4',
      icon: <Mail size={16} className="text-cyan-500" />
    }
  };
  
  // Handle empty or undefined data
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <h3 className="text-lg font-semibold text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">Interactions by Platform</h3>
        </div>
        <div className="flex flex-col items-center justify-center h-48">
          <PieChart size={48} className="text-gray-300 mb-4" />
          <p className="text-gray-500 text-center">No interaction data available</p>
        </div>
      </div>
    );
  }
  
  // Process and enhance data with additional properties
  const enhancedData: ExtendedInteraction[] = data.map(item => {
    const platformKey = item.type as keyof typeof platformColors;
    return {
      ...item,
      // Add random trend data (in a real app, this would come from the API)
      trend: Math.floor(Math.random() * 20) - 10,
      color: platformColors[platformKey]?.color || '#94a3b8',
      icon: platformColors[platformKey]?.icon || null,
      hidden: hiddenPlatforms.includes(item.type)
    };
  }).sort((a, b) => b.count - a.count); // Sort by count descending
  
  const visibleData = enhancedData.filter(item => !item.hidden);
  const total = visibleData.reduce((sum, item) => sum + item.count, 0);
  
  // Toggle visibility of a platform
  const togglePlatformVisibility = (platform: string) => {
    if (hiddenPlatforms.includes(platform)) {
      setHiddenPlatforms(prev => prev.filter(p => p !== platform));
    } else {
      setHiddenPlatforms(prev => [...prev, platform]);
    }
  };
  
  // Download chart data as CSV
  const downloadCSV = () => {
    const headers = ["Platform", "Count", "Percentage"];
    const csvData = enhancedData.map(item => [
      item.type,
      item.count.toString(),
      ((item.count / total) * 100).toFixed(1) + "%"
    ]);
    
    const csvContent = [
      headers.join(","),
      ...csvData.map(row => row.join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "platform_interactions.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Render Pie Chart
  const renderPieChart = () => {
    let currentAngle = 0;
    
    return (
      <div className="relative w-full flex justify-center">
        <svg 
          viewBox="0 0 100 100" 
          className="transform -rotate-90 max-w-[250px]"
          onMouseLeave={() => setShowTooltip(null)}
        >
          <circle
            cx="50"
            cy="50"
            r="42"
            className="fill-gray-50 stroke-gray-100"
            strokeWidth="1"
          />
          {visibleData.map((item) => {
            const percentage = (item.count / total) * 100;
            const angle = (percentage / 100) * 360;
            
            const startAngle = currentAngle;
            currentAngle += angle;
            
            const x1 = 50 + 40 * Math.cos((Math.PI * startAngle) / 180);
            const y1 = 50 + 40 * Math.sin((Math.PI * startAngle) / 180);
            const x2 = 50 + 40 * Math.cos((Math.PI * currentAngle) / 180);
            const y2 = 50 + 40 * Math.sin((Math.PI * currentAngle) / 180);
            
            const largeArcFlag = angle > 180 ? 1 : 0;
            
            const platformKey = item.type as keyof typeof platformColors;
            const colorClass = platformColors[platformKey]?.fill || 'fill-gray-300';
            
            // Calculate middle point for label
            const midAngle = startAngle + (angle / 2);
            const labelRadius = 30; // Slightly inside the pie
            const labelX = 50 + labelRadius * Math.cos((Math.PI * midAngle) / 180);
            const labelY = 50 + labelRadius * Math.sin((Math.PI * midAngle) / 180);
            
            return (
              <g key={item.type}>
                <motion.path
                  initial={{ opacity: 0 }}
                  animate={{ 
                    opacity: highlightedPlatform === item.type || !highlightedPlatform ? 1 : 0.3,
                    scale: highlightedPlatform === item.type ? 1.05 : 1,
                    transformOrigin: '50px 50px'
                  }}
                  transition={{ duration: 0.3 }}
                  d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
                  className={`${colorClass} cursor-pointer`}
                  onMouseEnter={(e) => {
                    setHighlightedPlatform(item.type);
                    setShowTooltip(item.type);
                    setTooltipPosition({ 
                      x: e.clientX, 
                      y: e.clientY 
                    });
                  }}
                  onMouseLeave={() => {
                    setHighlightedPlatform(null);
                    setShowTooltip(null);
                  }}
                />
                
                {percentage > 10 && (
                  <text
                    x={labelX}
                    y={labelY}
                    className="text-[8px] font-medium fill-white text-center"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    transform={`rotate(${midAngle + 90}, ${labelX}, ${labelY})`}
                  >
                    {Math.round(percentage)}%
                  </text>
                )}
              </g>
            );
          })}
          
          {/* Center circle with total count */}
          <circle
            cx="50"
            cy="50"
            r="20"
            className="fill-white stroke-gray-100"
            strokeWidth="1"
          />
          <text
            x="50"
            y="46"
            className="text-[10px] font-bold fill-gray-700 text-center"
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {total}
          </text>
          <text
            x="50"
            y="54"
            className="text-[6px] fill-gray-400 text-center"
            textAnchor="middle"
            dominantBaseline="middle"
          >
            Total
          </text>
        </svg>
        
        {/* Floating tooltip */}
        <AnimatePresence>
          {showTooltip && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute z-10 bg-black bg-opacity-80 text-white rounded px-2 py-1 text-xs"
              style={{ 
                left: `${tooltipPosition.x}px`, 
                top: `${tooltipPosition.y - 40}px`,
                transform: 'translate(-50%, -100%)',
                pointerEvents: 'none'
              }}
            >
              {enhancedData.find(d => d.type === showTooltip)?.type}: {' '}
              {enhancedData.find(d => d.type === showTooltip)?.count} ({' '}
              {((enhancedData.find(d => d.type === showTooltip)?.count || 0) / total * 100).toFixed(1)}%
              )
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };
  
  // Render Bar Chart
  const renderBarChart = () => {
    const maxValue = Math.max(...visibleData.map(item => item.count));
    
    return (
      <div className="h-[250px] w-full">
        <div className="flex h-full items-end">
          {visibleData.map((item, index) => {
            const height = (item.count / maxValue) * 100;
            const platformKey = item.type as keyof typeof platformColors;
            const bgClass = platformColors[platformKey]?.bg || 'bg-gray-300';
            
            return (
              <div 
                key={item.type}
                className="flex flex-col items-center flex-1 mx-1 relative group"
                onMouseEnter={() => setHighlightedPlatform(item.type)}
                onMouseLeave={() => setHighlightedPlatform(null)}
              >
                <div className="text-xs text-gray-500 mb-1 whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
                  {item.count}
                </div>
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ 
                    height: `${height}%`,
                    opacity: highlightedPlatform === item.type || !highlightedPlatform ? 1 : 0.4
                  }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className={`w-full ${bgClass} rounded-t relative cursor-pointer`}
                >
                  <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity rounded-t"></div>
                </motion.div>
                <div className="text-[10px] mt-1 capitalize whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
                  {item.type}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  
  // Render Line Chart for trends
  const renderLineChart = () => {
    const chartHeight = 200;
    const chartWidth = 300;
    const padding = { top: 20, right: 10, bottom: 30, left: 40 };
    
    const maxCount = Math.max(...visibleData.map(item => item.count));
    
    const getY = (count: number) => {
      return padding.top + ((chartHeight - padding.top - padding.bottom) * (1 - count / maxCount));
    };
    
    return (
      <div className="w-full flex justify-center">
        <svg
          width={chartWidth}
          height={chartHeight}
          className="overflow-visible"
        >
          {/* Y-axis */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={chartHeight - padding.bottom}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
          
          {/* X-axis */}
          <line
            x1={padding.left}
            y1={chartHeight - padding.bottom}
            x2={chartWidth - padding.right}
            y2={chartHeight - padding.bottom}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
          
          {/* Y-axis ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
            const y = getY(maxCount * tick);
            return (
              <g key={`y-tick-${tick}`}>
                <line
                  x1={padding.left - 5}
                  y1={y}
                  x2={padding.left}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 10}
                  y={y}
                  textAnchor="end"
                  dominantBaseline="middle"
                  className="text-[8px] fill-gray-500"
                >
                  {Math.round(maxCount * tick)}
                </text>
              </g>
            );
          })}
          
          {/* Data lines */}
          {visibleData.map((item, index) => {
            const platformKey = item.type as keyof typeof platformColors;
            const strokeClass = platformColors[platformKey]?.stroke || 'stroke-gray-300';
            const x = padding.left + ((chartWidth - padding.left - padding.right) * ((index + 0.5) / visibleData.length));
            const y = getY(item.count);
            
            // Draw connector lines between points
            return (
              <g key={item.type}>
                {index > 0 && (
                  <line
                    x1={padding.left + ((chartWidth - padding.left - padding.right) * ((index - 0.5) / visibleData.length))}
                    y1={getY(visibleData[index - 1].count)}
                    x2={x}
                    y2={y}
                    className={strokeClass}
                    strokeWidth="2"
                    strokeOpacity={highlightedPlatform === item.type || !highlightedPlatform ? 1 : 0.3}
                  />
                )}
                
                <motion.circle
                  cx={x}
                  cy={y}
                  r={highlightedPlatform === item.type ? 6 : 4}
                  className={`${platformColors[platformKey]?.fill || 'fill-gray-300'} cursor-pointer`}
                  whileHover={{ r: 6 }}
                  onMouseEnter={() => setHighlightedPlatform(item.type)}
                  onMouseLeave={() => setHighlightedPlatform(null)}
                  opacity={highlightedPlatform === item.type || !highlightedPlatform ? 1 : 0.3}
                />
                
                {/* X-axis labels */}
                <text
                  x={x}
                  y={chartHeight - padding.bottom + 15}
                  textAnchor="middle"
                  className="text-[8px] fill-gray-500 capitalize"
                >
                  {item.type}
                </text>
                
                {/* Data labels */}
                <text
                  x={x}
                  y={y - 10}
                  textAnchor="middle"
                  className={`text-[8px] ${platformColors[platformKey]?.text || 'fill-gray-500'}`}
                  opacity={highlightedPlatform === item.type ? 1 : 0}
                >
                  {item.count}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    );
  };
  
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
        <h3 className="text-lg font-semibold text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">Interactions by Platform</h3>
        
        <div className="flex space-x-2 self-end sm:self-auto">
          {/* Chart Type Toggle */}
          <div className="flex bg-gray-100 p-1 rounded-md">
            <button
              onClick={() => setChartType('pie')}
              className={`p-1 rounded ${chartType === 'pie' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Pie Chart"
            >
              <PieChart size={16} />
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`p-1 rounded ${chartType === 'bar' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Bar Chart"
            >
              <BarChart size={16} />
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`p-1 rounded ${chartType === 'line' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              title="Line Chart"
            >
              <LineChart size={16} />
            </button>
          </div>
          
          {/* Download Data Button */}
          <button
            onClick={downloadCSV}
            className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            title="Download data as CSV"
          >
            <Download size={16} />
          </button>
          
          {/* Info Button */}
          <div className="relative group">
            <button className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
              <HelpCircle size={16} />
            </button>
            <div className="absolute right-0 w-48 bg-black text-white text-xs rounded py-1 px-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              Shows the distribution of interactions across different platforms
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="md:col-span-3">
          {chartType === 'pie' && renderPieChart()}
          {chartType === 'bar' && renderBarChart()}
          {chartType === 'line' && renderLineChart()}
        </div>
        
        <div className="md:col-span-2">
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Platforms</h4>
            
            {enhancedData.map((item) => {
              const platformKey = item.type as keyof typeof platformColors;
              const platformIcon = platformColors[platformKey]?.icon;
              const isHidden = hiddenPlatforms.includes(item.type);
              
              return (
                <motion.div 
                  key={item.type}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer ${
                    highlightedPlatform === item.type ? 'bg-gray-50' : ''
                  } ${isHidden ? 'opacity-60' : ''}`}
                  whileHover={{ backgroundColor: '#f9fafb' }}
                  onMouseEnter={() => setHighlightedPlatform(item.type)}
                  onMouseLeave={() => setHighlightedPlatform(null)}
                >
                  <div className="flex items-center">
                    <div className="mr-3">
                      <button
                        onClick={() => togglePlatformVisibility(item.type)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {isHidden ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    
                    <div className="flex items-center">
                      {platformIcon}
                      <span className={`text-sm ${isHidden ? 'text-gray-400' : 'text-gray-600'} ml-2 capitalize`}>
                        {item.type}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <span className={`text-sm ${isHidden ? 'text-gray-400' : 'text-gray-900'} font-medium mr-2`}>
                      {item.count}
                    </span>
                    
                    <div className={`text-xs ${item.trend && item.trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {item.trend && item.trend > 0 ? '+' : ''}{item.trend}%
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
          
          <div className="mt-6 pt-4 border-t border-gray-100">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Total Interactions</span>
              <span className="font-medium">{total}</span>
            </div>
            
            <div className="mt-4">
              <button className="text-blue-600 text-sm hover:underline">
                View detailed breakdown →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
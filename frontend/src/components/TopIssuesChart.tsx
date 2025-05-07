import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, HelpCircle, ChevronRight, BarChart3 } from 'lucide-react';

// Create a combined interface for chart issues
interface ChartIssue {
  id?: string;
  name?: string; // From standard TopIssue
  issue?: string; // From previous implementation
  count: number;
  trend: number;
  percentage: number;
  platform?: string;
}

interface TopIssuesChartProps {
  issues: ChartIssue[];
}

export function TopIssuesChart({ issues }: TopIssuesChartProps) {
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);
  const [chartType, setChartType] = useState<'bar' | 'progress'>('progress');
  const [tooltipVisible, setTooltipVisible] = useState<string | null>(null);

  // If no issues data, show empty state
  if (!issues || issues.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col items-center justify-center h-full">
        <BarChart3 size={48} className="text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Issues Data</h3>
        <p className="text-gray-500 text-center text-sm">
          No top issues data is available for the selected time period
        </p>
      </div>
    );
  }

  // Get colors based on issue severity (using percentage as severity)
  const getIssueColor = (percentage: number) => {
    if (percentage > 70) return 'bg-red-500';
    if (percentage > 40) return 'bg-orange-500';
    return 'bg-blue-500';
  };

  // Get trend color and icon based on whether trend is positive or negative
  const getTrendComponent = (trend: number) => {
    const isPositive = trend < 0; // For issues, negative trend is positive (fewer issues)
    return (
      <span className={`flex items-center ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
        {isPositive ? <TrendingDown size={14} /> : <TrendingUp size={14} />}
        <span className="ml-1 text-xs">{Math.abs(trend)}%</span>
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Top Issues</h3>
        <div className="flex space-x-4 items-center">
          {/* Chart type toggle */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-md">
            <button
              onClick={() => setChartType('progress')}
              className={`px-2 py-1 text-xs rounded ${
                chartType === 'progress' ? 'bg-white shadow-sm' : 'text-gray-500'
              }`}
            >
              Progress
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`px-2 py-1 text-xs rounded ${
                chartType === 'bar' ? 'bg-white shadow-sm' : 'text-gray-500'
              }`}
            >
              Bar
            </button>
          </div>

          {/* Help tooltip */}
          <div className="relative">
            <button 
              onMouseEnter={() => setTooltipVisible('help')}
              onMouseLeave={() => setTooltipVisible(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <HelpCircle size={16} />
            </button>
            <AnimatePresence>
              {tooltipVisible === 'help' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="absolute right-0 w-48 bg-black text-white text-xs rounded py-1 px-2 z-10"
                >
                  Shows the most common issues reported by users, with frequency and trend data
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {issues.map((issue) => {
          // Use whichever is available, issue or name, or fallback to a default string
          const issueLabel = issue.issue || issue.name || `Issue #${issue.id || ''}`;
          
          return (
            <motion.div 
              key={issueLabel}
              whileHover={{ scale: 1.01 }}
              onClick={() => setSelectedIssue(selectedIssue === issueLabel ? null : issueLabel || null)}
              className="cursor-pointer"
            >
              <div className="flex justify-between text-sm mb-1">
                <div className="flex items-center">
                  <ChevronRight 
                    size={14} 
                    className={`mr-1 transform transition-transform ${
                      selectedIssue === issueLabel ? 'rotate-90' : ''
                    }`} 
                  />
                  <span className="text-gray-600">{issueLabel}</span>
                </div>
                <div className="flex items-center space-x-2">
                  {getTrendComponent(issue.trend)}
                  <span className="text-gray-900 font-medium">{issue.count}</span>
                </div>
              </div>

              {/* Progress bar or bar chart based on selected chart type */}
              {chartType === 'progress' ? (
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${issue.percentage}%` }}
                    transition={{ duration: 0.5 }}
                    className={`${getIssueColor(issue.percentage)} h-3 rounded-full relative`}
                  >
                    {/* Show percentage on hover */}
                    <div 
                      className="absolute right-0 -top-6 bg-gray-800 text-white text-xs px-1 py-0.5 rounded opacity-0 hover:opacity-100"
                    >
                      {Math.round(issue.percentage)}%
                    </div>
                  </motion.div>
                </div>
              ) : (
                <div className="h-20 w-full flex items-end space-x-1">
                  {/* Generate a simple bar chart visualization */}
                  {Array.from({ length: Math.min(10, Math.ceil(issue.percentage / 10)) }).map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ height: 0 }}
                      animate={{ height: `${Math.min(100, (i + 1) * 10)}%` }}
                      transition={{ duration: 0.5, delay: i * 0.05 }}
                      className={`flex-1 ${getIssueColor(issue.percentage)} rounded-t`}
                    />
                  ))}
                </div>
              )}

              {/* Expanded details for selected issue */}
              <AnimatePresence>
                {selectedIssue === issueLabel && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 text-xs bg-gray-50 p-3 rounded"
                  >
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <div className="text-gray-500">Frequency</div>
                        <div className="text-gray-900 font-medium">{issue.count} instances</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Trend</div>
                        <div className="text-gray-900 font-medium flex items-center">
                          {getTrendComponent(issue.trend)}
                          <span className="ml-1">from last period</span>
                        </div>
                      </div>
                      {issue.platform && (
                        <div>
                          <div className="text-gray-500">Platform</div>
                          <div className="text-gray-900 font-medium capitalize">{issue.platform}</div>
                        </div>
                      )}
                      <div>
                        <div className="text-gray-500">Percentage</div>
                        <div className="text-gray-900 font-medium">{Math.round(issue.percentage)}% of all issues</div>
                      </div>
                    </div>
                    
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <span className="text-blue-600">View related conversations →</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })
      </div>
    </div>
  );
}
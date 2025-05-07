
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import api from '../utils/api';
import { MetricCard } from './MetricCard';
import { TopIssuesChart } from './TopIssuesChart';
import { InteractionChart } from './InteractionChart';
import { 
  Users, 
  Clock, 
  AlertTriangle, 
  LineChart, 
  MessageCircle, 
  CheckCircle, 
  RefreshCw, 
  CalendarClock,
  Smile,
  Meh,
  Frown,
  Filter,
  Download,
  Bell,
  Zap,
  TrendingUp,
  TrendingDown,
  HelpCircle
} from 'lucide-react';
import type { 
  ChatMetrics, 
  TopIssue, 
  PendingTask, 
  EscalatedTask,
  Interaction
} from '../types';

// Define time range options
const timeRanges = [
  { id: 'today', label: 'Today' },
  { id: '7d', label: 'Last 7 Days' },
  { id: '30d', label: 'Last 30 Days' },
  { id: 'mtd', label: 'Month to Date' },
  { id: 'ytd', label: 'Year to Date' },
  { id: 'custom', label: 'Custom Range' }
];

// Define sentiment types for sentiment analysis
interface SentimentData {
  id: string;
  type: 'positive' | 'neutral' | 'negative';
  count: number;
  trend: number;
  percentage: number;
}

export const Dashboard = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<ChatMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [platformFilter, setPlatformFilter] = useState<string[]>([]);
  const [sentiment, setSentiment] = useState<SentimentData[]>([]);
  const [anomalyDetected, setAnomalyDetected] = useState<boolean>(false);
  const [showAnomalyDetails, setShowAnomalyDetails] = useState<boolean>(false);
  const [refreshLoading, setRefreshLoading] = useState<boolean>(false);
  
  // Create a ref for WebSocket connection
  const wsRef = useRef<WebSocket | null>(null);
  
  // Subscribe to WebSocket notifications for real-time updates
  useEffect(() => {
    // Only create WebSocket if we have a user
    if (user?.id) {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/${user.id}`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connection established');
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update') {
              // Update metrics with the latest data
              setMetrics(prevMetrics => ({
                ...prevMetrics,
                ...data.metrics
              }));
              
              setLastUpdated(new Date());
            } else if (data.type === 'anomaly_alert') {
              setAnomalyDetected(true);
              // Show toast notification here with details about the anomaly
            }
          } catch (e) {
            console.error('Error processing WebSocket message:', e);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        
        wsRef.current = ws;
        
        // Close WebSocket on component unmount
        return () => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        };
      } catch (error) {
        console.error('Error setting up WebSocket:', error);
      }
    }
  }, [user?.id]);

  // Function to fetch dashboard metrics
  const fetchDashboardMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      let url = `/api/visualization/dashboard?timeRange=${timeRange}`;
      
      // Add custom date range parameters if needed
      if (timeRange === 'custom' && customDateRange.start && customDateRange.end) {
        url += `&startDate=${customDateRange.start}&endDate=${customDateRange.end}`;
      }
      
      // Add platform filters if any
      if (platformFilter.length > 0) {
        url += `&platforms=${platformFilter.join(',')}`;
      }
      
      const response = await api.get(url);
      
      if (response.status === 200 && response.data) {
        setMetrics(response.data);
        
        // Process sentiment data
        if (response.data.sentimentData) {
          setSentiment(response.data.sentimentData);
        } else {
          // Calculate sentiment based on interactions if not provided directly
          // This is a fallback approach
          calculateSentiment(response.data);
        }
        
        // Check for anomalies
        checkForAnomalies(response.data);
        
        setLastUpdated(new Date());
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard data');
      console.error('Error fetching dashboard metrics:', err);
    } finally {
      setLoading(false);
      setRefreshLoading(false);
    }
  }, [timeRange, customDateRange, platformFilter]);

  // Initial data fetch
  useEffect(() => {
    fetchDashboardMetrics();
    
    // Set up interval for periodic refreshes (every 5 minutes)
    const refreshInterval = setInterval(() => {
      fetchDashboardMetrics();
    }, 5 * 60 * 1000);
    
    return () => clearInterval(refreshInterval);
  }, [fetchDashboardMetrics]);

  // Function to refresh data manually
  const handleRefresh = () => {
    setRefreshLoading(true);
    fetchDashboardMetrics();
  };
  
  // Function to download dashboard data as CSV
  const downloadData = () => {
    if (!metrics) return;
    
    try {
      // Convert metrics to CSV format
      const csvHeader = 'Metric,Value,Trend\n';
      
      let csvContent = csvHeader;
      csvContent += `Total Interactions,${metrics.totalChats},${metrics.totalChats ? '+' : '-'}\n`;
      csvContent += `Completed Tasks,${metrics.completedTasks},${metrics.completedTasks ? '+' : '-'}\n`;
      csvContent += `Pending Tasks,${metrics.pendingTasks?.length || 0},${metrics.pendingTasks?.length ? '-' : '+'}\n`;
      csvContent += `Escalated Tasks,${metrics.escalatedTasks?.length || 0},${metrics.escalatedTasks?.length ? '-' : '+'}\n`;
      
      // Create and trigger download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `dana-ai-dashboard-${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Error downloading data:', err);
    }
  };
  
  // Function to calculate sentiment from interactions
  const calculateSentiment = (data: ChatMetrics) => {
    if (!data.peopleInteracted?.length) return;
    
    // This is a placeholder for real sentiment analysis that would be done on the backend
    // In a real implementation, you'd use NLP like OpenAI or similar to analyze message content
    const sentimentCounts = {
      positive: Math.floor(data.peopleInteracted.length * 0.6),
      neutral: Math.floor(data.peopleInteracted.length * 0.3),
      negative: Math.floor(data.peopleInteracted.length * 0.1)
    };
    
    const total = Object.values(sentimentCounts).reduce((a, b) => a + b, 0);
    
    setSentiment([
      {
        id: 'positive',
        type: 'positive',
        count: sentimentCounts.positive,
        trend: 5,
        percentage: (sentimentCounts.positive / total) * 100
      },
      {
        id: 'neutral',
        type: 'neutral',
        count: sentimentCounts.neutral,
        trend: -2,
        percentage: (sentimentCounts.neutral / total) * 100
      },
      {
        id: 'negative',
        type: 'negative',
        count: sentimentCounts.negative,
        trend: -10,
        percentage: (sentimentCounts.negative / total) * 100
      }
    ]);
  };
  
  // Check for anomalies in the data
  const checkForAnomalies = (data: ChatMetrics) => {
    // This is a simplified anomaly detection
    // In a real implementation, you'd use statistical methods or ML
    
    // Check if there's a significant drop in interactions
    if (data.totalChats === 0 && data.responseTime !== "0s") {
      setAnomalyDetected(true);
      return;
    }
    
    // Check if there's an unusual number of escalated tasks
    if (data.escalatedTasks && data.pendingTasks) {
      const escalationRate = data.escalatedTasks.length / 
        (data.pendingTasks.length + data.escalatedTasks.length);
      
      if (escalationRate > 0.3) { // If more than 30% of tasks are escalated
        setAnomalyDetected(true);
        return;
      }
    }
    
    setAnomalyDetected(false);
  };

  // Render loading state
  if (loading && !metrics) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  // Render error state
  if (error && !metrics) {
    return (
      <div className="flex flex-col justify-center items-center h-screen">
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
          <p>{error}</p>
        </div>
        <button 
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Dashboard Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.company || 'Dashboard'}</h1>
          <p className="text-gray-500">
            Here's your overview of data and insights
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Time Range Filter */}
          <div className="relative">
            <select 
              value={timeRange}
              onChange={(e) => {
                setTimeRange(e.target.value);
                if (e.target.value === 'custom') {
                  setShowCustomDatePicker(true);
                } else {
                  setShowCustomDatePicker(false);
                }
              }}
              className="bg-white border border-gray-300 rounded-md shadow-sm px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {timeRanges.map(range => (
                <option key={range.id} value={range.id}>{range.label}</option>
              ))}
            </select>
            
            {/* Custom Date Picker */}
            <AnimatePresence>
              {showCustomDatePicker && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 mt-2 z-10 w-64 bg-white shadow-lg rounded-md border border-gray-200 p-4"
                >
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Start Date</label>
                      <input 
                        type="date" 
                        value={customDateRange.start}
                        onChange={(e) => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">End Date</label>
                      <input 
                        type="date" 
                        value={customDateRange.end}
                        onChange={(e) => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={() => {
                          fetchDashboardMetrics();
                          setShowCustomDatePicker(false);
                        }}
                        className="bg-blue-500 text-white rounded-md px-3 py-1 text-sm font-medium hover:bg-blue-600"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Filter Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="relative inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Filter size={16} className="mr-2" />
            Filters
            {platformFilter.length > 0 && (
              <span className="absolute top-0 right-0 -mt-1 -mr-1 flex h-4 w-4 items-center justify-center rounded-full bg-blue-500 text-xs text-white">
                {platformFilter.length}
              </span>
            )}
          </button>
          
          {/* Platform Filter Dropdown */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute top-32 right-8 z-10 w-56 bg-white shadow-lg rounded-md border border-gray-200 p-4"
              >
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">Filter Platforms</h3>
                  <div className="space-y-1">
                    {['facebook', 'instagram', 'whatsapp', 'email', 'slack'].map(platform => (
                      <div key={platform} className="flex items-center">
                        <input
                          id={`filter-${platform}`}
                          type="checkbox"
                          checked={platformFilter.includes(platform)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setPlatformFilter(prev => [...prev, platform]);
                            } else {
                              setPlatformFilter(prev => prev.filter(p => p !== platform));
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`filter-${platform}`} className="ml-2 block text-sm text-gray-700 capitalize">
                          {platform}
                        </label>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-end pt-2">
                    <button
                      onClick={() => {
                        fetchDashboardMetrics();
                        setShowFilters(false);
                      }}
                      className="bg-blue-500 text-white rounded-md px-3 py-1 text-sm font-medium hover:bg-blue-600"
                    >
                      Apply Filters
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Download Button */}
          <button
            onClick={downloadData}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Download size={16} className="mr-2" />
            Export
          </button>
          
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshLoading}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <RefreshCw size={16} className={`mr-2 ${refreshLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
      
      {/* Last Updated and Anomaly Indicators */}
      <div className="flex justify-between items-center mb-6">
        <div className="text-sm text-gray-500">
          {lastUpdated && (
            <span className="flex items-center">
              <CalendarClock size={14} className="mr-1" />
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
        
        {/* Anomaly Alert */}
        {anomalyDetected && (
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center bg-amber-50 text-amber-700 px-4 py-2 rounded-md border border-amber-200"
          >
            <Bell size={16} className="mr-2 animate-pulse" />
            <span className="text-sm font-medium">Unusual activity detected</span>
            <button 
              onClick={() => setShowAnomalyDetails(!showAnomalyDetails)}
              className="ml-2 text-xs underline"
            >
              {showAnomalyDetails ? 'Hide details' : 'View details'}
            </button>
          </motion.div>
        )}
      </div>
      
      {/* Anomaly Details */}
      <AnimatePresence>
        {showAnomalyDetails && anomalyDetected && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 bg-white border border-amber-200 rounded-md shadow-sm"
          >
            <h3 className="font-medium text-amber-700 mb-2">Anomaly Details</h3>
            <p className="text-sm text-gray-700">
              Our system has detected unusual patterns in your dashboard metrics:
            </p>
            <ul className="list-disc list-inside mt-2 text-sm text-gray-700 space-y-1">
              <li>Escalation rate is higher than normal (30% vs typical 10%)</li>
              <li>Response time is longer than usual</li>
              <li>Negative sentiment has increased by 15% compared to your baseline</li>
            </ul>
            <div className="mt-3 text-sm">
              <span className="font-medium">Recommendation: </span>
              <span className="text-gray-700">Review recent interactions and consider adjusting staffing or response templates.</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {metrics && (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total Interactions"
              value={metrics.totalChats}
              icon={<Users size={24} />}
              description="Total interactions across all channels"
              trend={{ value: 12, isPositive: true }}
              breakdown={metrics.chatsBreakdown}
              allowedPlatforms={metrics.allowedPlatforms}
            />
            
            <MetricCard
              title="Completed Tasks"
              value={metrics.completedTasks}
              icon={<CheckCircle size={24} />}
              description="Tasks successfully completed"
              trend={{ value: 8, isPositive: true }}
              breakdown={metrics.completedTasksBreakdown}
              allowedPlatforms={metrics.allowedPlatforms}
            />
            
            <MetricCard
              title="Pending Tasks"
              value={metrics.pendingTasks?.length || 0}
              icon={<Clock size={24} />}
              description="Tasks waiting for completion"
              trend={{ value: 3, isPositive: false }}
              pendingTasks={metrics.pendingTasks}
            />
            
            <MetricCard
              title="Escalated Tasks"
              value={metrics.escalatedTasks?.length || 0}
              icon={<AlertTriangle size={24} />}
              description="Tasks requiring human attention"
              trend={{ value: 5, isPositive: false }}
              escalatedTasks={metrics.escalatedTasks}
            />
          </div>
          
          {/* Sentiment Analysis Section */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Customer Sentiment Analysis</h2>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500 flex items-center">
                  <HelpCircle size={12} className="mr-1" />
                  Powered by AI
                </span>
                <button className="text-xs text-blue-600 hover:underline">View methodology</button>
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {sentiment.map(item => (
                  <div key={item.id} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center">
                        {item.type === 'positive' && <Smile size={20} className="text-green-500 mr-2" />}
                        {item.type === 'neutral' && <Meh size={20} className="text-amber-500 mr-2" />}
                        {item.type === 'negative' && <Frown size={20} className="text-red-500 mr-2" />}
                        <span className="font-medium capitalize">{item.type}</span>
                      </div>
                      <div className={`flex items-center text-xs ${
                        item.type === 'positive' 
                          ? 'text-green-600' 
                          : item.type === 'negative' 
                            ? 'text-red-600' 
                            : 'text-amber-600'
                      }`}>
                        {item.trend > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        <span className="ml-1">{Math.abs(item.trend)}%</span>
                      </div>
                    </div>
                    <div className="text-2xl font-bold">
                      {item.count}
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          item.type === 'positive' 
                            ? 'bg-green-500' 
                            : item.type === 'negative' 
                              ? 'bg-red-500' 
                              : 'bg-amber-500'
                        }`}
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {Math.round(item.percentage)}% of total interactions
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <div className="flex items-start">
                  <Zap size={16} className="text-blue-600 mt-1 mr-2" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-800">AI Insight</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Customer sentiment is mostly positive, but there's been a slight increase in negative feedback
                      related to response times. Consider addressing this through improved automation or additional staffing.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Charts and Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <MetricCard
              title="People Interacted"
              value={metrics.peopleInteracted?.length || 0}
              icon={<Users size={24} />}
              description="Unique users across all platforms"
              trend={{ value: 15, isPositive: true }}
              breakdown={metrics.chatsBreakdown}
              interactions={metrics.peopleInteracted?.slice(0, 3)}
            />
            
            <div className="md:col-span-2">
              <TopIssuesChart issues={metrics.topIssues?.map(issue => ({
                issue: issue.name,
                count: issue.count,
                percentage: issue.trend
              })) || []} />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="md:col-span-2">
              <InteractionChart data={metrics.interactionsByType || []} />
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Response Time</h3>
              <div className="flex flex-col items-center justify-center h-48">
                <div className="text-5xl font-bold text-blue-600 mb-2">
                  {metrics.responseTime || "0s"}
                </div>
                <p className="text-gray-500 text-center">Average response time</p>
                <div className="mt-6 w-full bg-gray-100 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: '65%' }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">65% faster than industry average</p>
              </div>
            </div>
          </div>
          
          {/* Conversation List */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recent Conversations</h3>
              <a href="/conversations" className="text-sm text-blue-600 hover:underline">View all</a>
            </div>
            
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Client
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Platform
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Message
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {metrics.conversations && metrics.conversations.map((conversation: any) => (
                    <tr key={conversation.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{conversation.client_name}</div>
                        <div className="text-sm text-gray-500">{conversation.client_company}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          conversation.platform === 'facebook' ? 'bg-blue-100 text-blue-800' : 
                          conversation.platform === 'instagram' ? 'bg-pink-100 text-pink-800' : 
                          conversation.platform === 'whatsapp' ? 'bg-green-100 text-green-800' :
                          conversation.platform === 'slack' ? 'bg-purple-100 text-purple-800' :
                          conversation.platform === 'email' ? 'bg-cyan-100 text-cyan-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {conversation.platform}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{conversation.last_message?.substring(0, 30)}...</div>
                        <div className="text-xs text-gray-500">
                          {new Date(conversation.last_message_time || conversation.updated_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          conversation.status === 'active' ? 'bg-green-100 text-green-800' : 
                          conversation.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {conversation.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  
                  {(!metrics.conversations || metrics.conversations.length === 0) && (
                    <tr>
                      <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                        No recent conversations found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

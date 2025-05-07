import React, { useState, useEffect } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale,
  Filler
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import api from '../utils/api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Define analytics data types
interface PlatformData {
  name: string;
  messages: number;
  users: number;
  interactions: number;
  color: string;
}

interface AnalyticsData {
  messageCounts: {
    labels: string[];
    values: number[];
  };
  responseTime: {
    labels: string[];
    values: number[];
  };
  platformBreakdown: PlatformData[];
  sentimentAnalysis: {
    positive: number;
    neutral: number;
    negative: number;
  };
  userActivity: {
    labels: string[];
    values: number[];
  };
  conversionRate: {
    labels: string[];
    values: number[];
  };
}

export const AdvancedAnalytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/analytics/data?range=${timeRange}`);
        setAnalyticsData(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analytics data');
        console.error('Analytics error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-medium">Error loading analytics</h3>
        <p className="text-red-600">{error}</p>
        <p className="mt-2 text-gray-600">
          We're working on connecting to your social media platforms to provide accurate analytics.
          Connect your platforms in the Socials section to see real-time data.
        </p>
      </div>
    );
  }

  // If we don't have data yet, but also no error, show a placeholder with instructions
  if (!analyticsData) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Social Media Analytics Dashboard</h2>
        <div className="p-6 bg-blue-50 rounded-lg border border-blue-100">
          <h3 className="text-lg font-medium text-blue-800 mb-2">Connect Your Social Media Accounts</h3>
          <p className="text-gray-700 mb-4">
            To see detailed analytics about your social media performance, connect your accounts in the Socials section.
          </p>
          <p className="text-gray-600">
            Once connected, you'll see metrics on engagement, audience growth, message volume, and response times across all your platforms.
          </p>
        </div>
      </div>
    );
  }

  // Prepare chart data from analyticsData
  const messageCountData = {
    labels: analyticsData.messageCounts.labels,
    datasets: [
      {
        label: 'Message Volume',
        data: analyticsData.messageCounts.values,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const responseTimeData = {
    labels: analyticsData.responseTime.labels,
    datasets: [
      {
        label: 'Average Response Time (minutes)',
        data: analyticsData.responseTime.values,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const platformData = {
    labels: analyticsData.platformBreakdown.map(p => p.name),
    datasets: [
      {
        label: 'Messages',
        data: analyticsData.platformBreakdown.map(p => p.messages),
        backgroundColor: analyticsData.platformBreakdown.map(p => p.color),
      },
    ],
  };

  const sentimentData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [
          analyticsData.sentimentAnalysis.positive,
          analyticsData.sentimentAnalysis.neutral,
          analyticsData.sentimentAnalysis.negative,
        ],
        backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(59, 130, 246, 0.8)', 'rgba(239, 68, 68, 0.8)'],
      },
    ],
  };

  const userActivityData = {
    labels: analyticsData.userActivity.labels,
    datasets: [
      {
        label: 'Active Users',
        data: analyticsData.userActivity.values,
        backgroundColor: 'rgba(139, 92, 246, 0.8)',
      },
    ],
  };

  const conversionRateData = {
    labels: analyticsData.conversionRate.labels,
    datasets: [
      {
        label: 'Conversion Rate (%)',
        data: analyticsData.conversionRate.values,
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">Social Media Analytics Dashboard</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-3 py-1 rounded ${
              timeRange === '7d'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-3 py-1 rounded ${
              timeRange === '30d'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => setTimeRange('90d')}
            className={`px-3 py-1 rounded ${
              timeRange === '90d'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            90 Days
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">Message Volume</h3>
          <div className="h-64">
            <Line 
              data={messageCountData} 
              options={{ 
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Number of Messages'
                    }
                  },
                  x: {
                    title: {
                      display: true,
                      text: 'Date'
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">Response Time</h3>
          <div className="h-64">
            <Line 
              data={responseTimeData} 
              options={{ 
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Minutes'
                    }
                  },
                  x: {
                    title: {
                      display: true,
                      text: 'Date'
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">Platform Breakdown</h3>
          <div className="h-64 flex items-center justify-center">
            <Doughnut 
              data={platformData} 
              options={{ 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                  }
                }
              }} 
            />
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">Sentiment Analysis</h3>
          <div className="h-64 flex items-center justify-center">
            <Pie 
              data={sentimentData} 
              options={{ 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                  }
                }
              }} 
            />
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">User Activity</h3>
          <div className="h-64">
            <Bar 
              data={userActivityData} 
              options={{ 
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Active Users'
                    }
                  },
                  x: {
                    title: {
                      display: true,
                      text: 'Time'
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
        <h3 className="text-lg font-medium mb-4">Conversion Rate</h3>
        <div className="h-64">
          <Line 
            data={conversionRateData} 
            options={{ 
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: 'Conversion Rate (%)'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: 'Date'
                  }
                }
              }
            }} 
          />
        </div>
      </div>
    </div>
  );
};
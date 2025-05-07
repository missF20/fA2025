import { 
  ArrowDown, 
  ArrowUp, 
  BarChart2, 
  Calendar, 
  ChevronRight, 
  Download, 
  Filter, 
  Info, 
  PieChart, 
  Sliders, 
  TrendingDown, 
  TrendingUp 
} from 'lucide-react';
import { useState } from 'react';
import { 
  ResponsiveContainer, 
  PieChart as PieChartComponent, 
  Pie, 
  Cell, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  BarChart, 
  Bar
} from 'recharts';
import { SentimentAnalysis } from './SentimentAnalysis';
import { TopIssuesChart } from './TopIssuesChart';
import { InteractionChart } from './InteractionChart';

// Mock data for the analytics components
const sentimentData = [
  { 
    type: 'positive', 
    count: 425, 
    percentage: 56, 
    trend: 12 
  },
  { 
    type: 'neutral', 
    count: 210, 
    percentage: 28, 
    trend: -3 
  },
  { 
    type: 'negative', 
    count: 120, 
    percentage: 16, 
    trend: -9 
  }
];

const topIssuesData = [
  { 
    issue: "Content clarity", 
    percentage: 38, 
    count: 152, 
    trend: 5 
  },
  { 
    issue: "Response time", 
    percentage: 24, 
    count: 96, 
    trend: -8 
  },
  { 
    issue: "Information accuracy", 
    percentage: 21, 
    count: 84, 
    trend: 2 
  },
  { 
    issue: "Documentation gaps", 
    percentage: 17, 
    count: 68, 
    trend: -3 
  },
];

const interactionData = [
  { 
    name: 'Jan', 
    conversations: 240, 
    messages: 1200, 
    positive: 140, 
    negative: 30, 
    neutral: 70 
  },
  { 
    name: 'Feb', 
    conversations: 300, 
    messages: 1800, 
    positive: 180, 
    negative: 40, 
    neutral: 80 
  },
  { 
    name: 'Mar', 
    conversations: 280, 
    messages: 1600, 
    positive: 160, 
    negative: 30, 
    neutral: 90 
  },
  { 
    name: 'Apr', 
    conversations: 320, 
    messages: 2000, 
    positive: 190, 
    negative: 35, 
    neutral: 95 
  },
  { 
    name: 'May', 
    conversations: 400, 
    messages: 2200, 
    positive: 220, 
    negative: 40, 
    neutral: 140 
  }
];

const usageData = [
  { name: 'Jan', tokens: 12500 },
  { name: 'Feb', tokens: 18000 },
  { name: 'Mar', tokens: 16000 },
  { name: 'Apr', tokens: 19500 },
  { name: 'May', tokens: 22000 }
];

const documentData = [
  { name: 'Product Manuals', count: 24, percentage: 28 },
  { name: 'Technical Guides', count: 18, percentage: 21 },
  { name: 'FAQs', count: 32, percentage: 38 },
  { name: 'Policies', count: 11, percentage: 13 }
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [expandedSection, setExpandedSection] = useState<string | null>('sentiment');

  // Function to toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-semibold">Knowledge Base Analytics</h1>
        <div className="flex space-x-3">
          <div className="flex items-center space-x-1 bg-gray-50 rounded-md px-3 py-1.5">
            <Calendar size={14} className="text-gray-500" />
            <select 
              className="bg-transparent border-none text-sm focus:outline-none"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as '7d' | '30d' | '90d')}
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
          <button className="flex items-center space-x-1 bg-gray-50 rounded-md px-3 py-1.5">
            <Download size={14} className="text-gray-500" />
            <span className="text-sm">Export</span>
          </button>
          <button className="flex items-center space-x-1 bg-gray-50 rounded-md px-3 py-1.5">
            <Filter size={14} className="text-gray-500" />
            <span className="text-sm">Filter</span>
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-500">Knowledge Base Queries</p>
              <h3 className="text-2xl font-bold mt-1">2,458</h3>
            </div>
            <div className="p-2 bg-blue-100 rounded-md">
              <BarChart2 size={20} className="text-blue-600" />
            </div>
          </div>
          <div className="flex items-center mt-2">
            <span className="text-xs flex items-center text-green-600">
              <TrendingUp size={12} className="mr-1" />
              12.5%
            </span>
            <span className="text-xs text-gray-500 ml-1">vs last period</span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-500">Avg. Response Time</p>
              <h3 className="text-2xl font-bold mt-1">1.2s</h3>
            </div>
            <div className="p-2 bg-green-100 rounded-md">
              <TrendingDown size={20} className="text-green-600" />
            </div>
          </div>
          <div className="flex items-center mt-2">
            <span className="text-xs flex items-center text-green-600">
              <ArrowDown size={12} className="mr-1" />
              8.3%
            </span>
            <span className="text-xs text-gray-500 ml-1">vs last period</span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-500">Document Count</p>
              <h3 className="text-2xl font-bold mt-1">85</h3>
            </div>
            <div className="p-2 bg-indigo-100 rounded-md">
              <PieChart size={20} className="text-indigo-600" />
            </div>
          </div>
          <div className="flex items-center mt-2">
            <span className="text-xs flex items-center text-green-600">
              <TrendingUp size={12} className="mr-1" />
              5.2%
            </span>
            <span className="text-xs text-gray-500 ml-1">vs last period</span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-500">Token Usage</p>
              <h3 className="text-2xl font-bold mt-1">22K</h3>
            </div>
            <div className="p-2 bg-amber-100 rounded-md">
              <Sliders size={20} className="text-amber-600" />
            </div>
          </div>
          <div className="flex items-center mt-2">
            <span className="text-xs flex items-center text-red-600">
              <ArrowUp size={12} className="mr-1" />
              15.7%
            </span>
            <span className="text-xs text-gray-500 ml-1">vs last period</span>
          </div>
        </div>
      </div>

      {/* Analytics Sections */}
      <div className="space-y-6">
        {/* Sentiment Analysis Section */}
        <div className="border rounded-lg overflow-hidden">
          <div 
            className={`flex justify-between items-center p-4 cursor-pointer ${expandedSection === 'sentiment' ? 'bg-gray-50' : 'bg-white'}`}
            onClick={() => toggleSection('sentiment')}
          >
            <h3 className="font-semibold flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
              Sentiment Analysis
            </h3>
            <ChevronRight 
              size={20} 
              className={`text-gray-400 transform transition-transform ${expandedSection === 'sentiment' ? 'rotate-90' : ''}`} 
            />
          </div>
          {expandedSection === 'sentiment' && (
            <div className="p-4 bg-white">
              <SentimentAnalysis data={sentimentData} />
            </div>
          )}
        </div>

        {/* Top Issues Section */}
        <div className="border rounded-lg overflow-hidden">
          <div 
            className={`flex justify-between items-center p-4 cursor-pointer ${expandedSection === 'issues' ? 'bg-gray-50' : 'bg-white'}`}
            onClick={() => toggleSection('issues')}
          >
            <h3 className="font-semibold flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span>
              Top Issues
            </h3>
            <ChevronRight 
              size={20} 
              className={`text-gray-400 transform transition-transform ${expandedSection === 'issues' ? 'rotate-90' : ''}`} 
            />
          </div>
          {expandedSection === 'issues' && (
            <div className="p-4 bg-white">
              <TopIssuesChart data={topIssuesData} />
            </div>
          )}
        </div>

        {/* Interaction Trends Section */}
        <div className="border rounded-lg overflow-hidden">
          <div 
            className={`flex justify-between items-center p-4 cursor-pointer ${expandedSection === 'interactions' ? 'bg-gray-50' : 'bg-white'}`}
            onClick={() => toggleSection('interactions')}
          >
            <h3 className="font-semibold flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-2"></span>
              Interaction Trends
            </h3>
            <ChevronRight 
              size={20} 
              className={`text-gray-400 transform transition-transform ${expandedSection === 'interactions' ? 'rotate-90' : ''}`} 
            />
          </div>
          {expandedSection === 'interactions' && (
            <div className="p-4 bg-white">
              <InteractionChart data={interactionData} />
            </div>
          )}
        </div>

        {/* Token Usage Section */}
        <div className="border rounded-lg overflow-hidden">
          <div 
            className={`flex justify-between items-center p-4 cursor-pointer ${expandedSection === 'usage' ? 'bg-gray-50' : 'bg-white'}`}
            onClick={() => toggleSection('usage')}
          >
            <h3 className="font-semibold flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-amber-500 mr-2"></span>
              Token Usage
            </h3>
            <ChevronRight 
              size={20} 
              className={`text-gray-400 transform transition-transform ${expandedSection === 'usage' ? 'rotate-90' : ''}`} 
            />
          </div>
          {expandedSection === 'usage' && (
            <div className="p-4 bg-white">
              <div className="mb-4 flex justify-between items-center">
                <h4 className="text-sm font-medium">Token Usage Over Time</h4>
                <div className="flex space-x-2">
                  <button className="text-xs bg-gray-100 px-2 py-1 rounded">Monthly</button>
                  <button className="text-xs text-gray-500">Weekly</button>
                  <button className="text-xs text-gray-500">Daily</button>
                </div>
              </div>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={usageData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="tokens" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-500">Average Daily Usage</p>
                  <p className="text-lg font-semibold">745 tokens</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-500">Peak Usage Day</p>
                  <p className="text-lg font-semibold">May 12 (1,243)</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-500">Monthly Projection</p>
                  <p className="text-lg font-semibold">~25K tokens</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Document Distribution Section */}
        <div className="border rounded-lg overflow-hidden">
          <div 
            className={`flex justify-between items-center p-4 cursor-pointer ${expandedSection === 'documents' ? 'bg-gray-50' : 'bg-white'}`}
            onClick={() => toggleSection('documents')}
          >
            <h3 className="font-semibold flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-indigo-500 mr-2"></span>
              Document Distribution
            </h3>
            <ChevronRight 
              size={20} 
              className={`text-gray-400 transform transition-transform ${expandedSection === 'documents' ? 'rotate-90' : ''}`} 
            />
          </div>
          {expandedSection === 'documents' && (
            <div className="p-4 bg-white">
              <div className="mb-4 flex justify-between items-center">
                <h4 className="text-sm font-medium">Document Types</h4>
                <button className="text-xs text-blue-600">View all documents</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChartComponent>
                      <Pie
                        data={documentData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="count"
                        label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {documentData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChartComponent>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Document Activity</h4>
                  <div className="space-y-3">
                    {documentData.map((doc, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded-lg">
                        <div className="flex justify-between mb-1">
                          <p className="text-sm font-medium">{doc.name}</p>
                          <p className="text-sm">{doc.count} files</p>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full" 
                            style={{ 
                              width: `${doc.percentage}%`, 
                              backgroundColor: COLORS[index % COLORS.length] 
                            }} 
                          />
                        </div>
                        <div className="flex justify-between mt-1">
                          <p className="text-xs text-gray-500">{doc.percentage}% of total</p>
                          <p className="text-xs text-gray-500">Last updated: 2 days ago</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 text-xs text-gray-500 flex items-center">
        <Info size={12} className="text-blue-500 mr-1" />
        <span>Analytics data is updated every 24 hours. Last updated: May 7, 2025</span>
      </div>
    </div>
  );
}
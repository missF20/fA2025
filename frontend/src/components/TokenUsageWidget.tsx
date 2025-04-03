import React, { useState, useEffect } from 'react';
import { Settings, AlertTriangle, BarChart2, Server, Info } from 'lucide-react';

// Define interfaces for token usage data
interface TokenUsage {
  used: number;
  limit: number;
  percentage: number;
}

interface TokenUsageByModel {
  [key: string]: TokenUsage;
}

/**
 * TokenUsageWidget Component
 * 
 * A component that displays token usage statistics and allows
 * configuration of token limits. Styled with Tailwind CSS to match
 * the ConversationsList component.
 */
const TokenUsageWidget: React.FC = () => {
  const [totalUsage, setTotalUsage] = useState<TokenUsage>({
    used: 0,
    limit: 1000000,
    percentage: 0
  });
  
  const [modelUsage, setModelUsage] = useState<TokenUsageByModel>({
    'gpt-4': {
      used: 0,
      limit: 500000,
      percentage: 0
    },
    'gpt-3.5-turbo': {
      used: 0,
      limit: 500000,
      percentage: 0
    }
  });
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState('total');
  const [newLimit, setNewLimit] = useState('1000000');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch token usage data from API
  useEffect(() => {
    const fetchTokenUsage = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/usage/tokens');
        
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data) {
          // Update total usage
          const total = {
            used: data.total_tokens_used || 0,
            limit: data.total_tokens_limit || 1000000,
            percentage: data.total_tokens_used 
              ? Math.min(100, (data.total_tokens_used / data.total_tokens_limit) * 100)
              : 0
          };
          setTotalUsage(total);
          
          // Update model-specific usage
          const models: TokenUsageByModel = {};
          if (data.models) {
            Object.keys(data.models).forEach(model => {
              const modelData = data.models[model];
              models[model] = {
                used: modelData.tokens_used || 0,
                limit: modelData.tokens_limit || 500000,
                percentage: modelData.tokens_used
                  ? Math.min(100, (modelData.tokens_used / modelData.tokens_limit) * 100)
                  : 0
              };
            });
            setModelUsage(models);
          }
        }
      } catch (error) {
        console.error('Error fetching token usage:', error);
        setError('Failed to load token usage data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTokenUsage();
    // Refresh every 5 minutes
    const interval = setInterval(fetchTokenUsage, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  const handleSaveLimit = async () => {
    try {
      const limitValue = parseInt(newLimit);
      if (isNaN(limitValue) || limitValue <= 0) {
        return;
      }
      
      setLoading(true);
      const response = await fetch('/api/usage/limits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: selectedModel === 'total' ? null : selectedModel,
          token_limit: limitValue
        })
      });
      
      if (response.ok) {
        // Update the UI with new limit
        if (selectedModel === 'total') {
          setTotalUsage(prev => {
            const percentage = (prev.used / limitValue) * 100;
            return {
              ...prev,
              limit: limitValue,
              percentage: percentage
            };
          });
        } else {
          setModelUsage(prev => {
            const modelData = prev[selectedModel] || { used: 0, limit: 0, percentage: 0 };
            const percentage = typeof modelData.used === 'number' ? (modelData.used / limitValue) * 100 : 0;
            return {
              ...prev,
              [selectedModel]: {
                ...modelData,
                limit: limitValue,
                percentage: percentage
              }
            };
          });
        }
        setShowConfigModal(false);
      } else {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error saving token limit:', error);
      setError('Failed to update token limit');
    } finally {
      setLoading(false);
    }
  };
  
  // Get color for progress bar based on percentage
  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  // Get color for status badge based on percentage
  const getStatusColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-100 text-red-800';
    if (percentage >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };
  
  // Helper function to format large numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };
  
  if (loading && Object.keys(modelUsage).length === 0) {
    return (
      <div className="flex justify-center items-center p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mr-3"></div>
        <p className="text-gray-500">Loading token usage data...</p>
      </div>
    );
  }
  
  if (error && Object.keys(modelUsage).length === 0) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center">
        <AlertTriangle size={16} className="mr-2" />
        <span>{error}</span>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2">
            <BarChart2 size={18} className="text-blue-600" />
            <h4 className="font-medium text-gray-900">Monthly Token Usage</h4>
          </div>
          <p className="text-sm text-gray-500">Current billing period</p>
        </div>
        <button 
          className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50 flex items-center gap-1"
          onClick={() => {
            setSelectedModel('total');
            setNewLimit(totalUsage.limit.toString());
            setShowConfigModal(true);
          }}
          disabled={loading}
        >
          <Settings size={14} />
          <span>Configure</span>
        </button>
      </div>
      
      {/* Total Usage Card */}
      <div className="border border-gray-100 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <h5 className="font-medium text-gray-900">Total Usage</h5>
          <div className="flex items-center">
            <span className={`px-2 py-0.5 rounded-full text-xs ${getStatusColor(totalUsage.percentage)} mr-2`}>
              {Math.round(totalUsage.percentage)}%
            </span>
            <span className="font-medium">
              {formatNumber(totalUsage.used)} / {formatNumber(totalUsage.limit)}
            </span>
            <div className="ml-2 text-gray-400 cursor-pointer" title={`${totalUsage.percentage.toFixed(1)}% of your total allocation used`}>
              <Info size={14} />
            </div>
          </div>
        </div>
        
        <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div 
            className={`h-full ${getProgressColor(totalUsage.percentage)} ${totalUsage.percentage > 90 ? 'animate-pulse' : ''}`}
            style={{ width: `${totalUsage.percentage}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">0</span>
          <span className="text-xs text-gray-500">{formatNumber(totalUsage.limit)}</span>
        </div>
      </div>
      
      {/* Model-specific Usage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.keys(modelUsage).map(model => (
          <div key={model} className="border border-gray-100 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center gap-2">
                <Server size={16} className="text-gray-600" />
                <h5 className="font-medium text-gray-900">{model}</h5>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-xs ${getStatusColor(modelUsage[model].percentage)}`}>
                {Math.round(modelUsage[model].percentage)}%
              </span>
            </div>
            
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{formatNumber(modelUsage[model].used)} used</span>
              <span>{formatNumber(modelUsage[model].limit)} limit</span>
            </div>
            
            <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
              <div 
                className={`h-full ${getProgressColor(modelUsage[model].percentage)} ${modelUsage[model].percentage > 90 ? 'animate-pulse' : ''}`}
                style={{ width: `${modelUsage[model].percentage}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex justify-center items-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Settings className="mr-2 text-blue-600" size={20} />
                Configure Token Limits
              </h3>
              <button
                className="text-gray-400 hover:text-gray-500"
                onClick={() => setShowConfigModal(false)}
                disabled={loading}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Model
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedModel}
                onChange={(e) => {
                  const model = e.target.value;
                  setSelectedModel(model);
                  if (model === 'total') {
                    setNewLimit(totalUsage.limit.toString());
                  } else {
                    setNewLimit(modelUsage[model]?.limit.toString() || '500000');
                  }
                }}
              >
                <option value="total">Total (All Models)</option>
                {Object.keys(modelUsage).map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
              <p className="mt-1 text-sm text-gray-500">
                Configure limits for specific models or set an overall total
              </p>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Token Limit
              </label>
              <input
                type="number"
                min="1000"
                value={newLimit}
                onChange={(e) => setNewLimit(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Set the maximum number of tokens that can be used
              </p>
            </div>
            
            {selectedModel === 'total' && (
              <div className="bg-blue-50 text-blue-700 p-3 rounded-md flex items-start mb-4">
                <Info size={16} className="mr-2 mt-0.5 flex-shrink-0" />
                <p className="text-sm">
                  Setting a total limit helps control overall usage across all AI models
                </p>
              </div>
            )}
            
            <div className="flex justify-end gap-3">
              <button
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                onClick={() => setShowConfigModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                onClick={handleSaveLimit}
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                    <span>Saving...</span>
                  </div>
                ) : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenUsageWidget;
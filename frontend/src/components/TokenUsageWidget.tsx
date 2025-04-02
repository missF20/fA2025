import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api } from '../utils/fetchApi';

// Optional import to avoid errors when outside AuthProvider
let useAuth: any;
try {
  useAuth = require('../contexts/AuthContext').useAuth;
} catch (error) {
  console.warn('AuthContext not available, using mock auth data');
  useAuth = () => ({ user: null, token: null });
}

interface TokenUsageData {
  limit: number;
  used: number;
  remaining: number;
  percentage: number;
}

interface TokenLimits {
  responseLimit: number;
  dailyLimit: number;
  monthlyLimit: number;
}

interface ApiTokenUsageResponse {
  limit: number;
  usage?: {
    total_tokens: number;
  };
  remaining: number;
  percentage_used: number;
}

interface ApiTokenLimitsResponse {
  response_token_limit: number;
  daily_token_limit: number;
  monthly_token_limit: number;
}

const DEFAULT_TOKEN_USAGE: TokenUsageData = {
  limit: 50000,
  used: 0,
  remaining: 50000,
  percentage: 0
};

const DEFAULT_TOKEN_LIMITS: TokenLimits = {
  responseLimit: 1000,
  dailyLimit: 10000,
  monthlyLimit: 50000
};

/**
 * Token Usage Widget Component
 * 
 * Displays the current token usage with a progress bar and settings modal
 */
const TokenUsageWidget: React.FC = () => {
  const { user, token } = useAuth();
  const [tokenUsage, setTokenUsage] = useState<TokenUsageData>(DEFAULT_TOKEN_USAGE);
  const [tokenLimits, setTokenLimits] = useState<TokenLimits>(DEFAULT_TOKEN_LIMITS);
  const [showSettings, setShowSettings] = useState(false);
  const [responseLimit, setResponseLimit] = useState(1000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (user && token) {
      fetchUsageData();
    }
  }, [user, token]);
  
  const fetchUsageData = async () => {
    if (!token) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch token usage
      const data = await api.get<ApiTokenUsageResponse>('/api/usage/tokens?period=month');
      
      setTokenUsage({
        limit: data.limit || DEFAULT_TOKEN_USAGE.limit,
        used: data.usage?.total_tokens || 0,
        remaining: data.remaining || DEFAULT_TOKEN_USAGE.limit,
        percentage: data.percentage_used || 0
      });
      
      // Fetch token limits
      const limitsData = await api.get<ApiTokenLimitsResponse>('/api/usage/limits');
      
      setTokenLimits({
        responseLimit: limitsData.response_token_limit || DEFAULT_TOKEN_LIMITS.responseLimit,
        dailyLimit: limitsData.daily_token_limit || DEFAULT_TOKEN_LIMITS.dailyLimit,
        monthlyLimit: limitsData.monthly_token_limit || DEFAULT_TOKEN_LIMITS.monthlyLimit
      });
      
      setResponseLimit(limitsData.response_token_limit || DEFAULT_TOKEN_LIMITS.responseLimit);
      
    } catch (err) {
      console.error('Error fetching token usage data:', err);
      setError('Failed to load token usage data');
    } finally {
      setLoading(false);
    }
  };
  
  const updateResponseLimit = async () => {
    if (!token) return;
    
    try {
      await api.post('/api/usage/limits/response', { limit: responseLimit });
      
      setTokenLimits(prev => ({
        ...prev,
        responseLimit
      }));
      
      setShowSettings(false);
      
      // Save to local storage as well for persistence
      localStorage.setItem('responseTokenLimit', responseLimit.toString());
      
    } catch (err) {
      console.error('Error updating response token limit:', err);
      setError('Failed to update response token limit');
    }
  };
  
  // Determine progress bar color based on usage
  const getProgressColor = (percentage: number) => {
    if (percentage > 90) return 'bg-red-500';
    if (percentage > 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  // Format large numbers with commas
  const formatNumber = (num: number) => {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
  
  // Render a placeholder if not authenticated
  if (!user || !token) {
    return (
      <div className="token-usage-widget">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex justify-between items-center mb-2">
            <h6 className="text-sm font-semibold text-gray-700 m-0">Token Usage</h6>
          </div>
          <div className="text-xs text-gray-500 text-center py-2">
            Sign in to view token usage
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="token-usage-widget">
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex justify-between items-center mb-2">
          <h6 className="text-sm font-semibold text-gray-700 m-0">Token Usage</h6>
          <button 
            className="text-gray-500 hover:text-gray-700 transition-colors p-0 bg-transparent border-0"
            onClick={() => setShowSettings(true)}
            aria-label="Token settings"
          >
            <span className="text-sm">⚙️</span>
          </button>
        </div>
        
        {error ? (
          <div className="p-2 text-xs text-red-600 bg-red-50 rounded mb-2">
            Error loading token data. Please try again.
          </div>
        ) : loading ? (
          <div className="animate-pulse mb-2">
            <div className="h-4 bg-gray-200 rounded mb-1"></div>
            <div className="h-2 bg-gray-200 rounded mb-3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ) : (
          <>
            <div className="mb-2">
              <div className="flex justify-between mb-1">
                <div>
                  <span className="text-xs text-gray-600">{formatNumber(tokenUsage.used)} / {formatNumber(tokenUsage.limit)}</span>
                </div>
                <div>
                  <span className="text-xs text-gray-600">{tokenUsage.percentage.toFixed(1)}%</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`${getProgressColor(tokenUsage.percentage)} h-1.5 rounded-full`}
                  style={{ width: `${tokenUsage.percentage}%` }}
                ></div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">
                Remaining: {formatNumber(tokenUsage.remaining)}
              </span>
              <div className="relative group">
                <span className="text-gray-500 cursor-pointer">
                  <span className="text-sm">ℹ️</span>
                </span>
                <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded p-2 w-44">
                  Response Limit: {formatNumber(tokenLimits.responseLimit)} tokens
                </div>
              </div>
            </div>
          </>
        )}
      </div>
      
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
          >
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold">Token Settings</h3>
              <button 
                className="text-gray-500 hover:text-gray-700"
                onClick={() => setShowSettings(false)}
              >
                &times;
              </button>
            </div>
            <div className="p-4">
              <p className="mb-4">Adjust your token usage settings to optimize AI responses.</p>
              
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Response Token Limit
                </label>
                <select 
                  className="block w-full p-2 border border-gray-300 rounded-md"
                  value={responseLimit}
                  onChange={(e) => setResponseLimit(parseInt(e.target.value))}
                >
                  <option value="500">500 tokens - Very concise responses</option>
                  <option value="1000">1000 tokens - Standard responses</option>
                  <option value="2000">2000 tokens - Detailed responses</option>
                  <option value="4000">4000 tokens - Comprehensive responses</option>
                  <option value="8000">8000 tokens - Maximum detail (high token usage)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Controls the maximum size of AI responses. Higher limits allow for more detailed 
                  responses but consume more tokens from your quota.
                </p>
              </div>
              
              <div className="mb-4">
                <h6 className="text-sm font-semibold mb-2">Current Limits</h6>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  <li>Response Limit: {formatNumber(tokenLimits.responseLimit)} tokens</li>
                  <li>Daily Limit: {formatNumber(tokenLimits.dailyLimit)} tokens</li>
                  <li>Monthly Limit: {formatNumber(tokenLimits.monthlyLimit)} tokens</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">
                  To increase your monthly token limits, please upgrade your subscription.
                </p>
              </div>
            </div>
            <div className="flex justify-end p-4 border-t">
              <button 
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md mr-2 hover:bg-gray-300 transition-colors"
                onClick={() => setShowSettings(false)}
              >
                Cancel
              </button>
              <button 
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                onClick={updateResponseLimit}
              >
                Save Changes
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default TokenUsageWidget;
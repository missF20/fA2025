import { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/fetch';
import { useAuth } from '../contexts/AuthContext';

interface TokenUsage {
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

interface UsageStatsReturn {
  tokenUsage: TokenUsage | null;
  tokenLimits: TokenLimits | null;
  setResponseTokenLimit: (limit: number) => void;
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

const DEFAULT_TOKEN_USAGE: TokenUsage = {
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
 * Hook to manage token usage statistics
 */
export const useUsageStats = (): UsageStatsReturn => {
  const { user, token } = useAuth();
  const [tokenUsage, setTokenUsage] = useState<TokenUsage | null>(null);
  const [tokenLimits, setTokenLimits] = useState<TokenLimits | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch usage data
  const fetchUsageData = async () => {
    if (!user || !token) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch token usage
      const usageData = await fetchWithAuth('/api/usage/tokens?period=month', token);
      
      setTokenUsage({
        limit: usageData.limit || DEFAULT_TOKEN_USAGE.limit,
        used: usageData.usage?.total_tokens || 0,
        remaining: usageData.remaining || DEFAULT_TOKEN_USAGE.limit,
        percentage: usageData.percentage_used || 0
      });

      // Fetch token limits
      const limitsData = await fetchWithAuth('/api/usage/limits', token);
      
      setTokenLimits({
        responseLimit: limitsData.response_token_limit || DEFAULT_TOKEN_LIMITS.responseLimit,
        dailyLimit: limitsData.daily_token_limit || DEFAULT_TOKEN_LIMITS.dailyLimit,
        monthlyLimit: limitsData.monthly_token_limit || DEFAULT_TOKEN_LIMITS.monthlyLimit
      });
    } catch (err: any) {
      console.error('Error fetching token usage data:', err);
      setError(err.message || 'Failed to load token usage data');
      
      // Use defaults if fetching fails
      if (!tokenUsage) setTokenUsage(DEFAULT_TOKEN_USAGE);
      if (!tokenLimits) setTokenLimits(DEFAULT_TOKEN_LIMITS);
    } finally {
      setLoading(false);
    }
  };

  // Set response token limit
  const setResponseTokenLimit = async (limit: number) => {
    if (!user || !token) return;
    
    try {
      await fetchWithAuth('/api/usage/limits/response', token, {
        method: 'POST',
        body: { limit }
      });
      
      setTokenLimits(prev => prev ? { ...prev, responseLimit: limit } : DEFAULT_TOKEN_LIMITS);
      
      // Save to local storage as well for persistence
      localStorage.setItem('responseTokenLimit', limit.toString());
    } catch (err) {
      console.error('Error setting response token limit:', err);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchUsageData();
    
    // Get saved response token limit from local storage
    const savedLimit = localStorage.getItem('responseTokenLimit');
    if (savedLimit && tokenLimits) {
      setTokenLimits({
        ...tokenLimits,
        responseLimit: parseInt(savedLimit, 10)
      });
    }
  }, [user, token]);

  return {
    tokenUsage,
    tokenLimits,
    setResponseTokenLimit,
    loading,
    error,
    refreshData: fetchUsageData
  };
};
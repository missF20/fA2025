import { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/fetch';

interface TokenUsage {
  request_tokens: number;
  response_tokens: number;
  total_tokens: number;
  request_count: number;
}

interface UsageStats {
  usage: TokenUsage;
  tier: string;
  limit: number;
  remaining: number;
  percentage_used: number;
  period: string;
}

interface RateLimit {
  current_rate: number;
  limit: number;
  remaining: number;
  tier: string;
}

interface TokenLimit {
  current_usage: number;
  limit: number;
  remaining: number;
  percentage_used: number;
  tier: string;
}

interface UsageLimits {
  token_usage: TokenLimit;
  rate_limit: RateLimit;
}

interface TierLimits {
  token_limits: Record<string, number>;
  rate_limits: Record<string, number>;
}

interface UsageStatsHook {
  usageStats: UsageStats | null;
  usageLimits: UsageLimits | null;
  tierLimits: TierLimits | null;
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  setPeriod: (period: string) => void;
}

export const useUsageStats = (): UsageStatsHook => {
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null);
  const [tierLimits, setTierLimits] = useState<TierLimits | null>(null);
  const [period, setPeriod] = useState<string>('month');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsageStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetchWithAuth(`/api/usage/tokens?period=${period}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch usage stats: ${response.statusText}`);
      }
      
      const data = await response.json();
      setUsageStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error fetching usage stats:', err);
    }
  };

  const fetchUsageLimits = async () => {
    try {
      const response = await fetchWithAuth('/api/usage/limits');
      if (!response.ok) {
        throw new Error(`Failed to fetch usage limits: ${response.statusText}`);
      }
      
      const data = await response.json();
      setUsageLimits(data);
    } catch (err) {
      console.error('Error fetching usage limits:', err);
    }
  };

  const fetchTierLimits = async () => {
    try {
      const response = await fetchWithAuth('/api/usage/tiers');
      if (!response.ok) {
        throw new Error(`Failed to fetch tier limits: ${response.statusText}`);
      }
      
      const data = await response.json();
      setTierLimits(data);
    } catch (err) {
      console.error('Error fetching tier limits:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    await Promise.all([
      fetchUsageStats(),
      fetchUsageLimits(),
      fetchTierLimits()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    refreshData();
  }, [period]);

  return {
    usageStats,
    usageLimits,
    tierLimits,
    loading,
    error,
    refreshData,
    setPeriod
  };
};

export default useUsageStats;
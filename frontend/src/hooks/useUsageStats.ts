import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import type { TokenUsageStats, UserTokenUsage } from '../types';
import { useAuth } from '../contexts/AuthContext';

// Add these types to your types.ts file
export interface UsageStatsResult {
  stats: TokenUsageStats | null;
  loading: boolean;
  error: string | null;
  allUserStats?: UserTokenUsage[];
}

export function useUsageStats(userId?: string, fetchAllUsers = false): UsageStatsResult {
  const { token } = useAuth();
  const [stats, setStats] = useState<TokenUsageStats | null>(null);
  const [allUserStats, setAllUserStats] = useState<UserTokenUsage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    async function fetchUsageStats() {
      try {
        setLoading(true);
        setError(null);
        
        console.log('Token available in useUsageStats:', !!token);
        console.log('User ID provided:', userId);
        
        // If fetchAllUsers is true, we fetch stats for all users (admin only)
        if (fetchAllUsers && token) {
          console.log('Fetching all user stats...');
          const response = await fetch('/api/admin/usage/all-users', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              // Include authorization token from Supabase
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (!response.ok) {
            throw new Error(`Error fetching all user stats: ${response.statusText}`);
          }
          
          const data = await response.json();
          console.log('All user stats response:', data);
          if (isMounted) {
            setAllUserStats(data.users || []);
          }
        }
        
        // If userId is provided, fetch individual user stats
        if (userId && token) {
          console.log(`Fetching usage stats for user: ${userId}`);
          const response = await fetch(`/api/usage/stats?user_id=${userId}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              // Include authorization token from context
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (!response.ok) {
            throw new Error(`Error fetching usage stats: ${response.statusText}`);
          }
          
          const data = await response.json();
          console.log('User stats response:', data);
          
          if (isMounted) {
            setStats({
              totals: {
                total_tokens: data.total_tokens || 0,
                request_count: data.request_count || 0,
                prompt_tokens: data.prompt_tokens || 0,
                completion_tokens: data.completion_tokens || 0
              },
              limits: {
                limit: data.token_limit || 100000,
                used: data.total_tokens || 0,
                remaining: (data.token_limit || 100000) - (data.total_tokens || 0),
                unlimited: data.unlimited || false,
                exceeded: data.total_tokens > data.token_limit && !data.unlimited
              },
              period: {
                start: data.period_start || new Date(new Date().setDate(new Date().getDate() - 30)).toISOString(),
                end: data.period_end || new Date(new Date().setDate(new Date().getDate() + 30)).toISOString()
              },
              models: data.models || []
            });
          }
        }
      } catch (err: any) {
        console.error('Error fetching usage stats:', err);
        if (isMounted) {
          setError(err.message || 'Failed to load usage statistics');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    
    if (userId || fetchAllUsers) {
      fetchUsageStats();
    } else {
      setLoading(false);
    }
    
    return () => {
      isMounted = false;
    };
  }, [userId, fetchAllUsers, token]);
  
  return { stats, loading, error, allUserStats };
}
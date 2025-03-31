import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import type { ChatMetrics, Integration } from '../types';
import { v4 as uuidv4 } from 'uuid';

// Function to extract and analyze top issues from messages and interactions
function extractTopIssues(messages: any[], interactions: any[], conversations: any[], platforms: string[]) {
  // If no data, return empty array
  if (!messages?.length && !interactions?.length) return [];
  
  // Common issues/keywords to look for
  const commonIssuesKeywords = {
    'billing': ['billing', 'payment', 'invoice', 'charge', 'subscription', 'cost', 'price', 'fee'],
    'account access': ['login', 'password', 'access', 'account', 'forgot', 'reset', 'sign in', 'cannot login'],
    'technical problem': ['error', 'bug', 'crash', 'not working', 'problem', 'issue', 'broken', 'fails'],
    'product inquiry': ['product', 'service', 'feature', 'how to', 'available', 'when', 'release'],
    'shipping': ['shipping', 'delivery', 'track', 'package', 'order status', 'delayed', 'arrive'],
    'returns': ['return', 'refund', 'exchange', 'money back', 'cancel order'],
    'support': ['help', 'support', 'assistance', 'guidance', 'talk to', 'representative', 'agent']
  };
  
  // Count occurrences of each issue
  const issueCounts: Record<string, { count: number, platforms: Record<string, number> }> = {};
  
  // Process messages for issue detection
  messages?.forEach(message => {
    const content = message.content?.toLowerCase() || '';
    const conversation = conversations?.find(c => c.id === message.conversation_id);
    const platform = conversation?.platform || 'unknown';
    
    // Only process if the platform is allowed
    if (!platforms.includes(platform)) return;
    
    Object.entries(commonIssuesKeywords).forEach(([issue, keywords]) => {
      if (keywords.some(keyword => content.includes(keyword.toLowerCase()))) {
        if (!issueCounts[issue]) {
          issueCounts[issue] = { count: 0, platforms: {} };
        }
        issueCounts[issue].count += 1;
        
        if (!issueCounts[issue].platforms[platform]) {
          issueCounts[issue].platforms[platform] = 0;
        }
        issueCounts[issue].platforms[platform] += 1;
      }
    });
  });
  
  // Sort issues by count and take top 5
  const topIssues = Object.entries(issueCounts)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 5)
    .map(([issue, data]) => {
      // Find the most common platform for this issue
      const topPlatform = Object.entries(data.platforms)
        .sort((a, b) => b[1] - a[1])[0]?.[0] || undefined;
      
      // Generate a random trend between -15 and +20
      const trend = Math.floor(Math.random() * 35) - 15;
      
      return {
        id: uuidv4(),
        name: issue.charAt(0).toUpperCase() + issue.slice(1),
        count: data.count,
        trend: trend,
        platform: topPlatform
      };
    });
  
  return topIssues;
}

export function useMetrics(session: any) {
  const [metrics, setMetrics] = useState<ChatMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allowedPlatforms, setAllowedPlatforms] = useState<string[]>([]);
  
  // Make allowedPlatforms available to components
  const exportedMetrics = metrics ? { 
    ...metrics, 
    allowedPlatforms,
    // Fix the type for integrations
    integrations: metrics.integrations as unknown as Integration[]
  } : null;

  useEffect(() => {
    if (!session?.user?.id) {
      setLoading(false);
      return;
    }

    async function fetchAllowedPlatforms() {
      try {
        const { data: profileData, error: profileError } = await supabase
          .from('profiles')
          .select(`
            subscription_tier_id,
            subscription_tiers (
              platforms
            )
          `)
          .eq('id', session.user.id)
          .single();

        if (profileError) {
          console.error('Error fetching subscription tier:', profileError);
          return ['facebook', 'instagram', 'whatsapp', 'slack', 'email']; // Default to all platforms if error
        }

        if (profileData?.subscription_tiers && 'platforms' in profileData.subscription_tiers) {
          return profileData.subscription_tiers.platforms as string[];
        }

        // Default to all platforms if no subscription is set
        return ['facebook', 'instagram', 'whatsapp', 'slack', 'email'];
      } catch (err) {
        console.error('Error fetching subscription tier:', err);
        return ['facebook', 'instagram', 'whatsapp', 'slack', 'email']; // Default to all platforms if error
      }
    }

    async function fetchMetrics() {
      try {
        // Fetch allowed platforms first
        const platforms = await fetchAllowedPlatforms();
        setAllowedPlatforms(platforms);

        // Only fetch data for allowed platforms
        const [
          { data: responses, error: responsesError },
          { data: tasks, error: tasksError },
          { data: interactions, error: interactionsError },
          { data: conversations, error: conversationsError },
          { data: messages, error: messagesError }
        ] = await Promise.all([
          supabase
            .from('responses')
            .select('*')
            .eq('user_id', session.user.id)
            .in('platform', platforms),
          supabase
            .from('tasks')
            .select('*')
            .eq('user_id', session.user.id)
            .in('platform', platforms),
          supabase
            .from('interactions')
            .select('*')
            .eq('user_id', session.user.id)
            .in('platform', platforms),
          supabase
            .from('conversations')
            .select('*')
            .eq('user_id', session.user.id)
            .in('platform', platforms)
            .order('created_at', { ascending: false }),
          supabase
            .from('messages')
            .select('*')
            .order('created_at', { ascending: true })
        ]);

        if (responsesError || tasksError || interactionsError || conversationsError || messagesError) {
          throw new Error('Error fetching data');
        }

        // Group messages by conversation
        const conversationsWithMessages = conversations?.map(conversation => ({
          ...conversation,
          messages: messages?.filter(message => message.conversation_id === conversation.id) || []
        })) || [];

        // Create metrics object with filtered data
        const metrics: ChatMetrics = {
          totalResponses: responses?.length || 0,
          responsesBreakdown: {
            facebook: responses?.filter(r => r.platform === 'facebook').length || 0,
            instagram: responses?.filter(r => r.platform === 'instagram').length || 0,
            whatsapp: responses?.filter(r => r.platform === 'whatsapp').length || 0,
            slack: responses?.filter(r => r.platform === 'slack').length || 0,
            email: responses?.filter(r => r.platform === 'email').length || 0
          },
          completedTasks: tasks?.filter(t => t.status === 'completed').length || 0,
          completedTasksBreakdown: {
            facebook: tasks?.filter(t => t.status === 'completed' && t.platform === 'facebook').length || 0,
            instagram: tasks?.filter(t => t.status === 'completed' && t.platform === 'instagram').length || 0,
            whatsapp: tasks?.filter(t => t.status === 'completed' && t.platform === 'whatsapp').length || 0,
            slack: tasks?.filter(t => t.status === 'completed' && t.platform === 'slack').length || 0,
            email: tasks?.filter(t => t.status === 'completed' && t.platform === 'email').length || 0
          },
          pendingTasks: tasks?.filter(t => t.status === 'pending').map(t => ({
            id: t.id,
            task: t.description,
            client: {
              name: t.client_name,
              company: t.client_company
            },
            timestamp: t.created_at,
            platform: t.platform,
            priority: t.priority || 'medium'
          })) || [],
          escalatedTasks: tasks?.filter(t => t.priority === 'high' && t.status !== 'completed').map(t => ({
            id: t.id,
            task: t.description,
            client: {
              name: t.client_name,
              company: t.client_company
            },
            timestamp: t.created_at,
            platform: t.platform,
            priority: t.priority || 'high',
            reason: t.escalation_reason || 'High priority task'
          })) || [],
          totalChats: interactions?.length || 0,
          chatsBreakdown: {
            facebook: interactions?.filter(i => i.platform === 'facebook').length || 0,
            instagram: interactions?.filter(i => i.platform === 'instagram').length || 0,
            whatsapp: interactions?.filter(i => i.platform === 'whatsapp').length || 0,
            slack: interactions?.filter(i => i.platform === 'slack').length || 0,
            email: interactions?.filter(i => i.platform === 'email').length || 0
          },
          peopleInteracted: interactions?.map(i => ({
            id: i.id,
            name: i.client_name,
            company: i.client_company,
            timestamp: i.created_at,
            platform: i.platform
          })) || [],
          responseTime: '1m 30s',
          topIssues: messages ? extractTopIssues(messages, interactions || [], conversations || [], platforms) : [],
          // Include all available platforms in the chart, even if they have 0 interactions
          interactionsByType: ['facebook', 'instagram', 'whatsapp', 'slack', 'email']
            .filter(platform => platforms.includes(platform))
            .map(platform => ({
              type: platform.charAt(0).toUpperCase() + platform.slice(1),
              count: interactions?.filter(i => i.platform === platform).length || 0
            })),
          conversations: conversationsWithMessages,
          integrations: []
        };

        setMetrics(metrics);
        setLoading(false);
      } catch (err) {
        console.error('Error loading metrics:', err);
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    }

    fetchMetrics();

    // Set up real-time subscription for changes
    const subscription = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
        },
        () => {
          fetchMetrics();
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [session]);

  return { metrics: exportedMetrics, loading, error, allowedPlatforms };
}
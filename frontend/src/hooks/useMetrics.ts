import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import type { ChatMetrics } from '../types';

export function useMetrics(session: any) {
  const [metrics, setMetrics] = useState<ChatMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allowedPlatforms, setAllowedPlatforms] = useState<string[]>([]);

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
          return ['facebook', 'instagram', 'whatsapp']; // Default to all platforms if error
        }

        if (profileData?.subscription_tiers?.platforms) {
          return profileData.subscription_tiers.platforms;
        }

        // Default to all platforms if no subscription is set
        return ['facebook', 'instagram', 'whatsapp'];
      } catch (err) {
        console.error('Error fetching subscription tier:', err);
        return ['facebook', 'instagram', 'whatsapp']; // Default to all platforms if error
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
            whatsapp: responses?.filter(r => r.platform === 'whatsapp').length || 0
          },
          completedTasks: tasks?.filter(t => t.status === 'completed').length || 0,
          completedTasksBreakdown: {
            facebook: tasks?.filter(t => t.status === 'completed' && t.platform === 'facebook').length || 0,
            instagram: tasks?.filter(t => t.status === 'completed' && t.platform === 'instagram').length || 0,
            whatsapp: tasks?.filter(t => t.status === 'completed' && t.platform === 'whatsapp').length || 0
          },
          pendingTasks: tasks?.filter(t => t.status === 'pending').map(t => ({
            id: t.id,
            task: t.description,
            client: {
              name: t.client_name,
              company: t.client_company
            },
            timestamp: t.created_at
          })) || [],
          escalatedTasks: [],
          totalChats: interactions?.length || 0,
          chatsBreakdown: {
            facebook: interactions?.filter(i => i.platform === 'facebook').length || 0,
            instagram: interactions?.filter(i => i.platform === 'instagram').length || 0,
            whatsapp: interactions?.filter(i => i.platform === 'whatsapp').length || 0
          },
          peopleInteracted: interactions?.map(i => ({
            id: i.id,
            name: i.client_name,
            company: i.client_company,
            timestamp: i.created_at,
            type: i.platform
          })) || [],
          responseTime: '1m 30s',
          topIssues: [],
          interactionsByType: platforms.map(platform => ({
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

  return { metrics, loading, error };
}
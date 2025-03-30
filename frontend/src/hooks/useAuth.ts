import { useCallback, useEffect, useState } from 'react';
import { useQueryClient } from 'react-query';
import * as Sentry from '@sentry/react';
import { supabase } from '../services/api';
import type { AuthError, User } from '@supabase/supabase-js';

interface UseAuthReturn {
  user: User | null;
  loading: boolean;
  error: AuthError | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, company: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AuthError | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);

        if (event === 'SIGNED_IN') {
          Sentry.setUser({ id: session?.user?.id });
        } else if (event === 'SIGNED_OUT') {
          Sentry.setUser(null);
          queryClient.clear();
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [queryClient]);

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      setError(null);
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
    } catch (err) {
      setError(err as AuthError);
      throw err;
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string, company: string) => {
    try {
      setError(null);
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { company } },
      });
      if (error) throw error;
    } catch (err) {
      setError(err as AuthError);
      throw err;
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      setError(null);
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } catch (err) {
      setError(err as AuthError);
      throw err;
    }
  }, []);

  return { user, loading, error, signIn, signUp, signOut };
}
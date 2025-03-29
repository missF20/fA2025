import { supabase } from './api';
import { z } from 'zod';

const refreshTokenSchema = z.object({
  refresh_token: z.string(),
});

export const auth = {
  async refreshSession() {
    const { data: { session }, error } = await supabase.auth.getSession();
    
    if (error || !session) {
      throw new Error('No active session');
    }

    const { data, error: refreshError } = await supabase.auth.refreshSession();
    
    if (refreshError) {
      throw refreshError;
    }

    return data.session;
  },

  async getRole() {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.user) {
      return null;
    }

    const { data, error } = await supabase
      .from('admin_users')
      .select('role')
      .eq('user_id', session.user.id)
      .single();

    if (error) {
      return null;
    }

    return data.role;
  },

  persistSession(session: any) {
    localStorage.setItem('supabase.auth.token', JSON.stringify(session));
  },

  clearSession() {
    localStorage.removeItem('supabase.auth.token');
  }
};
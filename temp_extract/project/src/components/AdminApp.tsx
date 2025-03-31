import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { AdminLogin } from './AdminLogin';
import { AdminDashboard } from './AdminDashboard';

export function AdminApp() {
  const [session, setSession] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkSession() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
      
      if (data.session) {
        // Check if user is an admin
        const { data: adminData, error } = await supabase
          .from('admin_users')
          .select('*')
          .eq('user_id', data.session.user.id)
          .single();
        
        setIsAdmin(!error && adminData);
      }
      
      setLoading(false);
    }
    
    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      
      if (session) {
        // Check if user is an admin when auth state changes
        const checkAdmin = async () => {
          const { data: adminData, error } = await supabase
            .from('admin_users')
            .select('*')
            .eq('user_id', session.user.id)
            .single();
          
          setIsAdmin(!error && adminData);
        };
        
        checkAdmin();
      } else {
        setIsAdmin(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleAdminLogin = () => {
    setIsAdmin(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!session || !isAdmin) {
    return <AdminLogin onLogin={handleAdminLogin} />;
  }

  return <AdminDashboard />;
}
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '../services/api'; // Import the existing supabase client
import { ExtendedUser } from '../types';

interface AuthContextType {
  user: ExtendedUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ error: any | null }>;
  signup: (email: string, password: string, userData?: any) => Promise<{ error: any | null, user: ExtendedUser | null }>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: any | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Login function implementation
function performLogin(email: string, password: string) {
  return async () => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      
      return { error: null };
    } catch (error) {
      console.error('Login error:', error);
      return { error };
    }
  };
}

// Signup function implementation
function performSignup(email: string, password: string, userData: any = {}) {
  return async () => {
    try {
      // Register user
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            ...userData,
          },
        },
      });
      
      if (error) throw error;
      
      return { error: null, user: data.user };
    } catch (error) {
      console.error('Signup error:', error);
      return { error, user: null };
    }
  };
}

// Reset password implementation
function performResetPassword(email: string) {
  return async () => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      
      if (error) throw error;
      
      return { error: null };
    } catch (error) {
      console.error('Password reset error:', error);
      return { error };
    }
  };
}

// Define props type
interface AuthProviderProps {
  children: ReactNode;
}

// Main provider component using function declaration
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    async function checkSession() {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        setUser(session.user as ExtendedUser);
        setToken(session.access_token);
      }
      
      setIsLoading(false);
    }
    
    checkSession();
    
    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user as ExtendedUser || null);
        setToken(session?.access_token || null);
        setIsLoading(false);
      }
    );

    // Cleanup subscription when component unmounts
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Implementing the login function
  const login = async (email: string, password: string) => {
    return await performLogin(email, password)();
  };

  // Implementing the signup function
  const signup = async (email: string, password: string, userData: any = {}) => {
    return await performSignup(email, password, userData)();
  };

  // Implementing the logout function
  const logout = async () => {
    try {
      await supabase.auth.signOut();
      setUser(null);
      setToken(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Implementing the reset password function
  const resetPassword = async (email: string) => {
    return await performResetPassword(email)();
  };

  const contextValue = {
    user,
    token,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook for using the auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}
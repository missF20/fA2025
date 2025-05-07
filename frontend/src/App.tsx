import React, { useState, useEffect } from 'react';
import { supabase } from './lib/supabase';
import { AuthForm } from './components/AuthForm';
import { ForgotPasswordForm } from './components/ForgotPasswordForm';
import { ResetPassword } from './components/ResetPassword';
import { Sidebar } from './components/Sidebar';
import { MetricCard } from './components/MetricCard';
import { TopIssuesCard } from './components/TopIssuesCard';
import { InteractionChart } from './components/InteractionChart';
import { ConversationsList } from './components/ConversationsList';
import { RateUs } from './components/RateUs';
import { Support } from './components/Support';
import Integrations from './components/Integrations';
import { NewUserSetupPrompt } from './components/NewUserSetupPrompt';
import { KnowledgeBase } from './components/KnowledgeBase';
// SlackDashboard is now accessed through the Integrations component
import { SubscriptionTierSelector } from './components/SubscriptionTierSelector';
import { ProfileMenu } from './components/ProfileMenu';
import { Subscriptions } from './components/Subscriptions';
import { useMetrics } from './hooks/useMetrics';
import { MessageSquare, CheckCircle, Clock, Users, AlertTriangle, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AuthFormData } from './types';
import { TokenUsageCard } from './components/TokenUsageCard';
// Used to track the platforms the user is allowed to access based on their subscription

function App() {
  const [session, setSession] = useState<any>(null);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState('home');
  const [isLoading, setIsLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);
  const [showSetupPrompt, setShowSetupPrompt] = useState(false);
  const [accountSetupComplete, setAccountSetupComplete] = useState(true);
  const [showSubscriptionSelector, setShowSubscriptionSelector] = useState(false);
  const { metrics, loading, error, allowedPlatforms } = useMetrics(session);

  useEffect(() => {
    async function checkSession() {
      try {
        const { data: sessionData } = await supabase.auth.getSession();
        setSession(sessionData.session);

        if (sessionData.session) {
          // Check if profile exists
          const { data: profileData, error: profileError } = await supabase
            .from('profiles')
            .select('account_setup_complete, subscription_tier_id')
            .eq('id', sessionData.session.user.id)
            .single();

          if (profileError) {
            if (profileError.code === 'PGRST116') {
              // Profile doesn't exist, create it
              const { error: createError } = await supabase
                .from('profiles')
                .insert({
                  id: sessionData.session.user.id,
                  email: sessionData.session.user.email,
                  account_setup_complete: false,
                  welcome_email_sent: false,
                  onboarding_completed: false,
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                });

              if (createError) throw createError;

              setAccountSetupComplete(false);
              setShowSubscriptionSelector(true);
            } else {
              throw profileError;
            }
          } else if (profileData) {
            setAccountSetupComplete(profileData.account_setup_complete);
            setShowSubscriptionSelector(!profileData.subscription_tier_id);
          }
        }
      } catch (err) {
        console.error('Error checking profile:', err);
        setAuthError('Error loading profile. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }

    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    // Check if user is new (has just signed up)
    if (session && isNewUser) {
      setShowSubscriptionSelector(true);
      setAccountSetupComplete(false);

      // For now, we'll just mark it as sent in the database
      const markWelcomeEmailSent = async () => {
        await supabase
          .from('profiles')
          .update({ welcome_email_sent: true })
          .eq('id', session.user.id);
      };

      markWelcomeEmailSent();

      // Reset the new user flag
      setIsNewUser(false);
    }
  }, [session, isNewUser]);

  const handleAuth = async (formData: AuthFormData) => {
    setAuthError(null);
    try {
      if (authMode === 'signin') {
        // Use Remember Me setting to determine if we should persist the session
        const { data, error } = await supabase.auth.signInWithPassword({
          email: formData.email,
          password: formData.password,
        });
        
        // Configure session persistence based on Remember Me
        if (data.session) {
          // Store in localStorage if rememberMe is checked
          if (formData.rememberMe) {
            localStorage.setItem('supabase.auth.token', JSON.stringify({
              access_token: data.session.access_token,
              refresh_token: data.session.refresh_token,
              expires_at: data.session.expires_at,
              user: data.session.user
            }));
          } else {
            // Clear from localStorage if not checked, will rely on session cookies
            localStorage.removeItem('supabase.auth.token');
          }
        }
        if (error) throw error;
        setSession(data.session);

        // Check if account setup is complete
        if (data.session) {
          const { data: profileData, error: profileError } = await supabase
            .from('profiles')
            .select('account_setup_complete, subscription_tier_id')
            .eq('id', data.session.user.id)
            .single();

          if (profileError) {
            if (profileError.code === 'PGRST116') {
              // Profile doesn't exist, create it
              await supabase
                .from('profiles')
                .insert({
                  id: data.session.user.id,
                  email: data.session.user.email,
                  company: formData.company,
                  account_setup_complete: false,
                  welcome_email_sent: false,
                  onboarding_completed: false
                });
              setAccountSetupComplete(false);
              setShowSetupPrompt(true);
              setShowSubscriptionSelector(true);
            } else {
              throw profileError;
            }
          } else if (profileData) {
            setAccountSetupComplete(profileData.account_setup_complete);
            if (!profileData.account_setup_complete) {
              setShowSetupPrompt(true);
            }
            // Show subscription selector if no tier is selected
            setShowSubscriptionSelector(!profileData.subscription_tier_id);
          }
        }
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: formData.email,
          password: formData.password,
          options: {
            data: {
              company: formData.company,
            },
          },
        });
        if (error) throw error;
        // For sign up, we mark as a new user to show the setup prompt
        if (data.user) {
          setIsNewUser(true);
          setSession(data.session);
        }
      }
    } catch (error: any) {
      setAuthError(error.message);
    }
  };

  const handleForgotPassword = async (email: string) => {
    setAuthError(null);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password',
      });
      if (error) throw error;
    } catch (error: any) {
      setAuthError(error.message);
    }
  };

  const handleSubscriptionSelect = async (tierId: string) => {
    if (!session) return;

    try {
      // Update the user's profile with the selected subscription tier
      await supabase
        .from('profiles')
        .update({ subscription_tier_id: tierId })
        .eq('id', session.user.id);

      // Create a subscription record
      await supabase
        .from('user_subscriptions')
        .insert({
          user_id: session.user.id,
          subscription_tier_id: tierId,
          status: 'pending', // Will be activated by admin
          start_date: new Date().toISOString(),
          payment_status: 'unpaid'
        });

      setShowSubscriptionSelector(false);
      setShowSetupPrompt(true);
    } catch (error) {
      console.error('Error selecting subscription tier:', error);
      setAuthError('Error selecting subscription tier. Please try again.');
    }
  };

  const renderAuthForms = () => {
    if (showResetPassword) {
      return <ResetPassword />;
    }

    if (showForgotPassword) {
      return (
        <ForgotPasswordForm
          onSubmit={handleForgotPassword}
          onBack={() => setShowForgotPassword(false)}
          error={authError}
        />
      );
    }

    return (
      <AuthForm
        mode={authMode}
        onSubmit={handleAuth}
        error={authError}
        onToggleMode={() => {
          setAuthMode(authMode === 'signin' ? 'signup' : 'signin');
          setAuthError(null);
        }}
        onForgotPassword={() => setShowForgotPassword(true)}
      />
    );
  };

  const renderDashboard = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-screen">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"
          />
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 text-red-600 p-4 rounded-lg"
          >
            Error loading dashboard data: {error}
          </motion.div>
        </div>
      );
    }

    if (!metrics) {
      return (
        <div className="p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-yellow-50 text-yellow-600 p-4 rounded-lg"
          >
            No metrics data available. Please check your database connection.
          </motion.div>
        </div>
      );
    }

    const pageVariants = {
      initial: { opacity: 0, x: 20 },
      animate: { opacity: 1, x: 0 },
      exit: { opacity: 0, x: -20 }
    };

    return (
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSection}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: 0.3 }}
        >
          {currentSection === 'home' && (
            <div className="p-8">
              <motion.h1 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold text-gray-900 mb-6"
              >
                Dashboard Overview
              </motion.h1>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <MetricCard
                  title="Total Responses"
                  value={metrics.totalResponses}
                  icon={<MessageSquare size={24} />}
                  description="AI responses across all platforms"
                  trend={{ value: 12, isPositive: true }}
                  breakdown={metrics.responsesBreakdown}
                  allowedPlatforms={metrics.allowedPlatforms || allowedPlatforms}
                />

                <MetricCard
                  title="Completed Tasks"
                  value={metrics.completedTasks}
                  icon={<CheckCircle size={24} />}
                  description="Tasks successfully completed by AI"
                  trend={{ value: 8, isPositive: true }}
                  breakdown={metrics.completedTasksBreakdown}
                  allowedPlatforms={metrics.allowedPlatforms || allowedPlatforms}
                />

                <MetricCard
                  title="Pending Tasks"
                  value={metrics.pendingTasks.length}
                  icon={<Clock size={24} />}
                  description="Tasks waiting for completion"
                  trend={{ value: 3, isPositive: false }}
                  pendingTasks={metrics.pendingTasks.map(task => ({...task, allowedPlatforms: metrics.allowedPlatforms || allowedPlatforms}))}
                />

                <MetricCard
                  title="Escalated Tasks"
                  value={metrics.escalatedTasks.length}
                  icon={<AlertTriangle size={24} />}
                  description="Tasks requiring human attention"
                  trend={{ value: 5, isPositive: false }}
                  escalatedTasks={metrics.escalatedTasks.map(task => ({...task, allowedPlatforms: metrics.allowedPlatforms || allowedPlatforms}))}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <MetricCard
                  title="People Interacted"
                  value={metrics.totalChats}
                  icon={<Users size={24} />}
                  description="Unique users across all platforms"
                  trend={{ value: 15, isPositive: true }}
                  breakdown={metrics.chatsBreakdown}
                  interactions={metrics.peopleInteracted.slice(0, 3).map(interaction => ({...interaction, allowedPlatforms: metrics.allowedPlatforms || allowedPlatforms}))}
                  allowedPlatforms={metrics.allowedPlatforms || allowedPlatforms}
                />

                <TopIssuesCard issues={metrics.topIssues} />

                <InteractionChart data={metrics.interactionsByType} />
              </div>

              <ConversationsList conversations={metrics.conversations} />
            </div>
          )}

          {currentSection === 'conversations' && (
            <div className="p-8">
              <motion.h1 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold text-gray-900 mb-6"
              >
                Conversations
              </motion.h1>
              <ConversationsList conversations={metrics.conversations} />
              
              {/* Token Usage Card below conversations */}
              <div className="mt-8">
                {session?.user?.id && <TokenUsageCard userId={session.user.id} />}
              </div>
            </div>
          )}

          {currentSection === 'knowledge' && <KnowledgeBase />}
          {currentSection === 'rate' && <RateUs />}
          {currentSection === 'support' && <Support />}
          {currentSection === 'subscriptions' && <Subscriptions />}
          {currentSection === 'integrations' && <Integrations />}
          {currentSection === 'social-preview' && <SocialMediaPreview />}
        </motion.div>
      </AnimatePresence>
    );
  };

  // Show loading indicator while checking session
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"
        />
      </div>
    );
  }

  // If no session, show auth forms
  if (!session) {
    return renderAuthForms();
  }

  // If session exists, show dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex">
      <Sidebar currentSection={currentSection} onSectionChange={setCurrentSection} />
      <div className="flex-1 ml-64 bg-gray-50/50 backdrop-blur-sm">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-white/90 backdrop-blur-sm border-b border-gray-200/50 flex items-center justify-between"
        >
          <div className="flex items-center">
            <motion.div
              whileHover={{ scale: 1.1, rotate: 360 }}
              transition={{ duration: 0.5 }}
            >
              <Activity className="text-blue-600 h-6 w-6 mr-2" />
            </motion.div>
            <h1 className="text-xl font-bold text-gray-900">DANA AI by Hartford Tech</h1>
          </div>
          <ProfileMenu onSectionChange={setCurrentSection} />
        </motion.div>
        {renderDashboard()}
        {!accountSetupComplete && <NewUserSetupPrompt onDismiss={() => setShowSetupPrompt(false)} />}
        {showSubscriptionSelector && (
          <SubscriptionTierSelector 
            onComplete={handleSubscriptionSelect} 
            onSkip={() => setShowSubscriptionSelector(false)} 
          />
        )}
      </div>
    </div>
  );
}

export default App;
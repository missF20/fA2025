-- Enhanced Row Level Security Policies for Dana AI Platform
-- This migration adds comprehensive row-level security to all tables

-- Enable Row Level Security on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations_config ENABLE ROW LEVEL SECURITY;

-- Remove any existing policies
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can view own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can insert own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can update own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can delete own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can view own messages" ON messages;
DROP POLICY IF EXISTS "Users can insert own messages" ON messages;
DROP POLICY IF EXISTS "Users can view own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can insert own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can update own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can delete own tasks" ON tasks;
DROP POLICY IF EXISTS "Users can view own interactions" ON interactions;
DROP POLICY IF EXISTS "Users can insert own interactions" ON interactions;
DROP POLICY IF EXISTS "Users can update own interactions" ON interactions;
DROP POLICY IF EXISTS "Users can view own knowledge files" ON knowledge_files;
DROP POLICY IF EXISTS "Users can insert own knowledge files" ON knowledge_files;
DROP POLICY IF EXISTS "Users can update own knowledge files" ON knowledge_files;
DROP POLICY IF EXISTS "Users can delete own knowledge files" ON knowledge_files;
DROP POLICY IF EXISTS "Users can view own subscriptions" ON user_subscriptions;
DROP POLICY IF EXISTS "Users can view own invoices" ON subscription_invoices;
DROP POLICY IF EXISTS "Users can view own integrations" ON integrations_config;
DROP POLICY IF EXISTS "Users can update own integrations" ON integrations_config;

-- Create helper function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin(user_id uuid)
RETURNS boolean AS $$
DECLARE
  user_email text;
  admin_emails text;
BEGIN
  -- Get user email from auth.users
  SELECT email INTO user_email FROM auth.users WHERE id = user_id;
  
  -- Get admin emails from config
  SELECT COALESCE(current_setting('app.admin_emails', true), 'admin@dana-ai.com') INTO admin_emails;
  
  -- Check if user email is in the admin emails list
  RETURN position(user_email in admin_emails) > 0;
EXCEPTION WHEN OTHERS THEN
  RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON profiles
  FOR SELECT USING (is_admin(auth.uid()));

CREATE POLICY "Admins can update all profiles" ON profiles
  FOR UPDATE USING (is_admin(auth.uid()));

-- Conversations policies
CREATE POLICY "Users can view own conversations" ON conversations
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own conversations" ON conversations
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own conversations" ON conversations
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own conversations" ON conversations
  FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can view all conversations" ON conversations
  FOR ALL USING (is_admin(auth.uid()));

-- Messages policies
CREATE POLICY "Users can view own messages" ON messages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM conversations 
      WHERE conversations.id = messages.conversation_id 
      AND conversations.user_id::text = auth.uid()::text
    )
  );

CREATE POLICY "Users can insert own messages" ON messages
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations 
      WHERE conversations.id = messages.conversation_id 
      AND conversations.user_id::text = auth.uid()::text
    )
  );

CREATE POLICY "Admins can view all messages" ON messages
  FOR ALL USING (is_admin(auth.uid()));

-- Tasks policies
CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own tasks" ON tasks
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own tasks" ON tasks
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own tasks" ON tasks
  FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all tasks" ON tasks
  FOR ALL USING (is_admin(auth.uid()));

-- Interactions policies
CREATE POLICY "Users can view own interactions" ON interactions
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own interactions" ON interactions
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own interactions" ON interactions
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all interactions" ON interactions
  FOR ALL USING (is_admin(auth.uid()));

-- Knowledge files policies
CREATE POLICY "Users can view own knowledge files" ON knowledge_files
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own knowledge files" ON knowledge_files
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own knowledge files" ON knowledge_files
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own knowledge files" ON knowledge_files
  FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all knowledge files" ON knowledge_files
  FOR ALL USING (is_admin(auth.uid()));

-- User subscriptions policies
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own subscriptions" ON user_subscriptions
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all subscriptions" ON user_subscriptions
  FOR ALL USING (is_admin(auth.uid()));

-- Subscription tiers policies (all users can view)
CREATE POLICY "Anyone can view subscription tiers" ON subscription_tiers
  FOR SELECT USING (true);

CREATE POLICY "Admins can manage subscription tiers" ON subscription_tiers
  FOR ALL USING (is_admin(auth.uid()));

-- Subscription features policies (all users can view)
CREATE POLICY "Anyone can view subscription features" ON subscription_features
  FOR SELECT USING (true);

CREATE POLICY "Admins can manage subscription features" ON subscription_features
  FOR ALL USING (is_admin(auth.uid()));

-- Subscription invoices policies
CREATE POLICY "Users can view own invoices" ON subscription_invoices
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all invoices" ON subscription_invoices
  FOR ALL USING (is_admin(auth.uid()));

-- Integrations config policies
CREATE POLICY "Users can view own integrations" ON integrations_config
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own integrations" ON integrations_config
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own integrations" ON integrations_config
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own integrations" ON integrations_config
  FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage all integrations" ON integrations_config
  FOR ALL USING (is_admin(auth.uid()));

-- Create trigger to automatically set user_id if not provided
CREATE OR REPLACE FUNCTION set_auth_user_id()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.user_id IS NULL THEN
    NEW.user_id = auth.uid();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply user_id trigger to relevant tables
DROP TRIGGER IF EXISTS set_conversations_user_id ON conversations;
CREATE TRIGGER set_conversations_user_id
  BEFORE INSERT ON conversations
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();

DROP TRIGGER IF EXISTS set_tasks_user_id ON tasks;
CREATE TRIGGER set_tasks_user_id
  BEFORE INSERT ON tasks
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();

DROP TRIGGER IF EXISTS set_interactions_user_id ON interactions;
CREATE TRIGGER set_interactions_user_id
  BEFORE INSERT ON interactions
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();

DROP TRIGGER IF EXISTS set_knowledge_files_user_id ON knowledge_files;
CREATE TRIGGER set_knowledge_files_user_id
  BEFORE INSERT ON knowledge_files
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();

DROP TRIGGER IF EXISTS set_integrations_config_user_id ON integrations_config;
CREATE TRIGGER set_integrations_config_user_id
  BEFORE INSERT ON integrations_config
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();
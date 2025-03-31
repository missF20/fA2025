/*
  # Dana AI Complete Database Schema

  1. New Tables
    - profiles: User profiles and settings
    - conversations: Chat conversations across platforms
    - messages: Individual messages within conversations
    - responses: AI responses to user queries
    - tasks: Tasks generated from conversations
    - interactions: User interaction tracking
    - knowledge_files: Knowledge base documents
    - subscription_tiers: Available subscription plans
    - user_subscriptions: User subscription management
    - admin_users: Admin user management
    - integrations_config: Platform integration settings

  2. Security
    - RLS enabled on all tables
    - Policies for user data access
    - Admin-specific policies
    
  3. Relationships
    - Foreign key constraints
    - Indexes for performance
*/

-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id),
  email text NOT NULL UNIQUE,
  company text,
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  status text DEFAULT 'active' CHECK (status IN ('active', 'archived', 'pending')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_platform ON conversations(platform);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
  content text NOT NULL,
  sender_type text NOT NULL CHECK (sender_type IN ('ai', 'client', 'user')),
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Responses table
CREATE TABLE IF NOT EXISTS responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  content text NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  description text NOT NULL,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
  priority text DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Interactions table
CREATE TABLE IF NOT EXISTS interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  interaction_type text NOT NULL CHECK (interaction_type IN ('message', 'query', 'task', 'response')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_platform ON interactions(platform);

-- Knowledge files table
CREATE TABLE IF NOT EXISTS knowledge_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  file_name text NOT NULL,
  file_size bigint NOT NULL,
  file_type text NOT NULL,
  content text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_files_user_id ON knowledge_files(user_id);

-- Subscription tiers table
CREATE TABLE IF NOT EXISTS subscription_tiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  description text NOT NULL,
  price decimal(10,2) NOT NULL,
  features jsonb NOT NULL DEFAULT '[]',
  platforms text[] NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  subscription_tier_id uuid REFERENCES subscription_tiers(id) NOT NULL,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'cancelled', 'expired')),
  start_date timestamptz NOT NULL,
  end_date timestamptz,
  payment_status text DEFAULT 'unpaid' CHECK (payment_status IN ('paid', 'unpaid', 'overdue')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

-- Admin users table
CREATE TABLE IF NOT EXISTS admin_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) UNIQUE NOT NULL,
  email text NOT NULL UNIQUE,
  username text NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);

-- Integrations config table
CREATE TABLE IF NOT EXISTS integrations_config (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  integration_type text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}',
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'connected', 'disconnected', 'error')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, integration_type)
);

CREATE INDEX IF NOT EXISTS idx_integrations_config_user_id ON integrations_config(user_id);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations_config ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Profiles
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Conversations
CREATE POLICY "Users can view own conversations"
  ON conversations FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create conversations"
  ON conversations FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Messages
CREATE POLICY "Users can view messages from own conversations"
  ON messages FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations c
      WHERE c.id = conversation_id
      AND c.user_id = auth.uid()
    )
  );

-- Responses
CREATE POLICY "Users can view own responses"
  ON responses FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Tasks
CREATE POLICY "Users can view own tasks"
  ON tasks FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own tasks"
  ON tasks FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

-- Interactions
CREATE POLICY "Users can view own interactions"
  ON interactions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Knowledge files
CREATE POLICY "Users can view own knowledge files"
  ON knowledge_files FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own knowledge files"
  ON knowledge_files FOR ALL
  TO authenticated
  USING (auth.uid() = user_id);

-- Subscription tiers
CREATE POLICY "Anyone can view subscription tiers"
  ON subscription_tiers FOR SELECT
  TO authenticated
  USING (true);

-- User subscriptions
CREATE POLICY "Users can view own subscriptions"
  ON user_subscriptions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Admin users
CREATE POLICY "Admin users can view admin data"
  ON admin_users FOR SELECT
  TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users au 
    WHERE au.user_id = auth.uid()
  ));

-- Integrations config
CREATE POLICY "Users can manage own integrations"
  ON integrations_config FOR ALL
  TO authenticated
  USING (auth.uid() = user_id);

-- Insert initial subscription tiers
INSERT INTO subscription_tiers (name, description, price, features, platforms)
VALUES
  (
    'Starter Package',
    'Perfect for small businesses starting with social media automation',
    79.99,
    '["AI-powered responses", "Basic analytics", "Single platform support"]',
    '{facebook}'
  ),
  (
    'Professional Package',
    'Ideal for growing businesses with multiple social channels',
    149.99,
    '["AI-powered responses", "Advanced analytics", "Multi-platform support", "Priority support"]',
    '{facebook,instagram}'
  ),
  (
    'Enterprise Package',
    'Complete solution for businesses requiring full social media automation',
    299.99,
    '["AI-powered responses", "Enterprise analytics", "All platforms support", "24/7 Priority support", "Custom integrations"]',
    '{facebook,instagram,whatsapp}'
  )
ON CONFLICT (name) DO NOTHING;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
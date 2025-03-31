/*
  # Initial Database Schema Setup

  1. New Tables
    - profiles: User profiles and settings
    - conversations: Customer interactions across platforms
    - messages: Individual messages within conversations
    - tasks: Action items and escalations
    - responses: AI-generated responses
    - interactions: User interaction tracking
    - subscription_tiers: Available subscription plans
    - user_subscriptions: User subscription status
    - knowledge_files: Uploaded knowledge base documents
    - integrations_config: Platform integration settings
    - admin_users: Admin user management

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated access
    - Add policies for admin access

  3. Indexes
    - Optimize common query patterns
    - Support efficient filtering and sorting
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id),
  email text NOT NULL UNIQUE,
  company text,
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  subscription_tier_id uuid,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Subscription tiers table
CREATE TABLE IF NOT EXISTS subscription_tiers (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  description text,
  price decimal(10,2) NOT NULL,
  features jsonb NOT NULL DEFAULT '[]',
  platforms text[] NOT NULL DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  subscription_tier_id uuid REFERENCES subscription_tiers(id),
  status text NOT NULL CHECK (status IN ('active', 'inactive', 'pending', 'cancelled')),
  start_date timestamptz NOT NULL,
  end_date timestamptz,
  payment_status text NOT NULL CHECK (payment_status IN ('paid', 'unpaid', 'overdue')),
  last_payment_date timestamptz,
  next_payment_date timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'escalated')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id uuid REFERENCES conversations(id),
  content text NOT NULL,
  sender_type text NOT NULL CHECK (sender_type IN ('ai', 'client', 'human')),
  created_at timestamptz DEFAULT now()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  conversation_id uuid REFERENCES conversations(id),
  description text NOT NULL,
  status text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'escalated')),
  priority text NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  assigned_to uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Responses table
CREATE TABLE IF NOT EXISTS responses (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  conversation_id uuid REFERENCES conversations(id),
  content text NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  effectiveness_score int CHECK (effectiveness_score BETWEEN 1 AND 5),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Interactions table
CREATE TABLE IF NOT EXISTS interactions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text,
  interaction_type text NOT NULL CHECK (interaction_type IN ('message', 'task', 'escalation')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Knowledge files table
CREATE TABLE IF NOT EXISTS knowledge_files (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  file_name text NOT NULL,
  file_size bigint NOT NULL,
  file_type text NOT NULL,
  content text NOT NULL,
  status text NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'active', 'error')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Integrations config table
CREATE TABLE IF NOT EXISTS integrations_config (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  integration_type text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'connected', 'error')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Admin users table
CREATE TABLE IF NOT EXISTS admin_users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  email text NOT NULL UNIQUE,
  username text NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_platform ON conversations(platform);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_files_user_id ON knowledge_files(user_id);
CREATE INDEX IF NOT EXISTS idx_integrations_config_user_id ON integrations_config(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);

-- RLS Policies

-- Profiles policies
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Conversations policies
CREATE POLICY "Users can view own conversations"
  ON conversations FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can create conversations"
  ON conversations FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- Messages policies
CREATE POLICY "Users can view conversation messages"
  ON messages FOR SELECT
  TO authenticated
  USING (
    conversation_id IN (
      SELECT id FROM conversations WHERE user_id = auth.uid()
    )
  );

-- Tasks policies
CREATE POLICY "Users can view own tasks"
  ON tasks FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Responses policies
CREATE POLICY "Users can view own responses"
  ON responses FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Interactions policies
CREATE POLICY "Users can view own interactions"
  ON interactions FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Knowledge files policies
CREATE POLICY "Users can view own knowledge files"
  ON knowledge_files FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Integrations config policies
CREATE POLICY "Users can view own integrations"
  ON integrations_config FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Admin users policies
CREATE POLICY "Admin users can view admin data"
  ON admin_users FOR SELECT
  TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users au 
    WHERE au.user_id = auth.uid()
  ));

-- Insert initial subscription tiers
INSERT INTO subscription_tiers (name, description, price, features, platforms) VALUES
('Starter', 'Get started with basic AI support', 49.99, 
  '["24/7 AI Support", "Basic Analytics", "Email Support"]',
  '{facebook}'),
('Professional', 'Enhanced support for growing businesses', 99.99,
  '["24/7 AI Support", "Advanced Analytics", "Priority Support", "Custom Responses"]',
  '{facebook,instagram}'),
('Enterprise', 'Complete solution for large organizations', 199.99,
  '["24/7 AI Support", "Enterprise Analytics", "Dedicated Support", "Custom Integrations", "API Access"]',
  '{facebook,instagram,whatsapp}');

-- Create admin user function
CREATE OR REPLACE FUNCTION create_admin_user(
  p_email text,
  p_username text,
  p_password text,
  p_role text
) RETURNS uuid AS $$
DECLARE
  v_user_id uuid;
  v_existing_user_id uuid;
BEGIN
  -- Check if user already exists
  SELECT id INTO v_existing_user_id
  FROM auth.users
  WHERE email = p_email;

  IF v_existing_user_id IS NULL THEN
    -- Create auth user
    INSERT INTO auth.users (
      email,
      raw_user_meta_data,
      raw_app_meta_data,
      encrypted_password,
      email_confirmed_at,
      created_at,
      updated_at,
      role,
      is_super_admin
    )
    VALUES (
      p_email,
      jsonb_build_object('username', p_username),
      jsonb_build_object('provider', 'email', 'providers', ARRAY['email']),
      crypt(p_password, gen_salt('bf')),
      now(),
      now(),
      now(),
      'authenticated',
      false
    )
    RETURNING id INTO v_user_id;
  ELSE
    -- Update existing user's password
    UPDATE auth.users
    SET encrypted_password = crypt(p_password, gen_salt('bf'))
    WHERE id = v_existing_user_id;
    
    v_user_id := v_existing_user_id;
  END IF;

  -- Delete existing admin user if exists
  DELETE FROM admin_users WHERE user_id = v_user_id;

  -- Create admin user
  INSERT INTO admin_users (
    user_id,
    email,
    username,
    role
  )
  VALUES (
    v_user_id,
    p_email,
    p_username,
    p_role
  );

  -- Ensure profile exists with email
  INSERT INTO profiles (
    id,
    email,
    account_setup_complete,
    created_at,
    updated_at
  )
  VALUES (
    v_user_id,
    p_email,
    true,
    now(),
    now()
  )
  ON CONFLICT (id) DO UPDATE
  SET email = p_email,
      account_setup_complete = true,
      updated_at = now();

  RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create initial admin user
SELECT create_admin_user(
  '20HT20@admin.com',
  '20HT20',
  '20HT20HT',
  'admin'
);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
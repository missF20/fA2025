/*
  # Complete Database Schema Setup

  1. Core Tables
    - users (handled by Supabase Auth)
    - profiles (user profiles)
    - admin_users (admin access)
    - subscription_tiers (available plans)
    - user_subscriptions (user plan relationships)

  2. Communication Tables
    - conversations (customer interactions)
    - messages (individual messages)
    - responses (AI responses)
    - interactions (platform interactions)

  3. Task Management
    - tasks (customer tasks)
    - knowledge_files (uploaded documents)

  4. Security
    - RLS policies for all tables
    - Proper constraints and relationships
*/

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables in reverse order of dependencies
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.responses CASCADE;
DROP TABLE IF EXISTS public.tasks CASCADE;
DROP TABLE IF EXISTS public.interactions CASCADE;
DROP TABLE IF EXISTS public.knowledge_files CASCADE;
DROP TABLE IF EXISTS public.user_subscriptions CASCADE;
DROP TABLE IF EXISTS public.admin_users CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TABLE IF EXISTS public.subscription_tiers CASCADE;

-- Drop existing functions and triggers
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

-- Subscription Tiers
CREATE TABLE public.subscription_tiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  description text NOT NULL,
  price numeric(10,2) NOT NULL,
  features jsonb NOT NULL,
  platforms text[] NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Profiles
CREATE TABLE public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  subscription_tier_id uuid REFERENCES subscription_tiers(id),
  onboarding_completed boolean DEFAULT false
);

-- Admin Users
CREATE TABLE public.admin_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  role text CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- User Subscriptions
CREATE TABLE public.user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  subscription_tier_id uuid REFERENCES subscription_tiers(id),
  status text CHECK (status IN ('active', 'inactive', 'pending', 'cancelled')),
  start_date timestamptz NOT NULL,
  end_date timestamptz,
  payment_status text CHECK (payment_status IN ('paid', 'unpaid', 'overdue')),
  last_payment_date timestamptz,
  next_payment_date timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Conversations
CREATE TABLE public.conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  platform text CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Messages
CREATE TABLE public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE,
  content text NOT NULL,
  sender_type text CHECK (sender_type IN ('ai', 'client')),
  created_at timestamptz DEFAULT now()
);

-- Responses
CREATE TABLE public.responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  platform text CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Tasks
CREATE TABLE public.tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  description text NOT NULL,
  status text CHECK (status IN ('pending', 'completed')),
  platform text CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Interactions
CREATE TABLE public.interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform text CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Knowledge Files
CREATE TABLE public.knowledge_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_size integer CHECK (file_size <= 10485760),
  file_type text NOT NULL,
  content bytea NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
DO $$ BEGIN
  CREATE POLICY "Public can view subscription tiers" ON subscription_tiers
    FOR SELECT TO public USING (true);
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT TO authenticated USING (id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE TO authenticated USING (id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Admin access" ON admin_users
    FOR ALL TO authenticated USING (
      EXISTS (SELECT 1 FROM admin_users WHERE user_id = auth.uid())
    );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view messages from their conversations" ON messages
    FOR SELECT TO authenticated USING (
      EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = conversation_id
        AND conversations.user_id = auth.uid()
      )
    );
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own responses" ON responses
    FOR SELECT TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own tasks" ON tasks
    FOR SELECT TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can view own interactions" ON interactions
    FOR SELECT TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE POLICY "Users can manage own knowledge files" ON knowledge_files
    FOR ALL TO authenticated USING (user_id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_user_id ON admin_users(user_id);

-- Create handle_new_user function and trigger
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (
    id,
    email,
    company,
    account_setup_complete,
    welcome_email_sent,
    onboarding_completed,
    created_at,
    updated_at
  )
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'company',
    false,
    false,
    false,
    NOW(),
    NOW()
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Insert default subscription tiers
INSERT INTO subscription_tiers (name, description, price, features, platforms)
VALUES
  (
    'Starter',
    'Perfect for small businesses starting with social media',
    99.99,
    '["Single platform support", "Basic AI responses", "Email support"]',
    ARRAY['facebook']
  ),
  (
    'Professional',
    'Ideal for growing businesses with multiple platforms',
    199.99,
    '["Dual platform support", "Advanced AI responses", "Priority support", "Analytics dashboard"]',
    ARRAY['facebook', 'instagram']
  ),
  (
    'Enterprise',
    'Complete solution for businesses at scale',
    299.99,
    '["All platforms support", "Custom AI training", "24/7 priority support", "Advanced analytics", "Custom integrations"]',
    ARRAY['facebook', 'instagram', 'whatsapp']
  );
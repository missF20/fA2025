/*
  # Initial Database Schema Setup

  1. Core Tables
    - Create profiles table
    - Create responses table
    - Create tasks table
    - Create interactions table

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
*/

-- Create profiles table
CREATE TABLE profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  subscription_tier_id uuid,
  onboarding_completed boolean DEFAULT false
);

-- Create responses table
CREATE TABLE responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create tasks table
CREATE TABLE tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  description text NOT NULL,
  status text NOT NULL CHECK (status IN ('pending', 'completed')),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create interactions table
CREATE TABLE interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (id = auth.uid());
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (id = auth.uid());

CREATE POLICY "Users can view own responses" ON responses FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own responses" ON responses FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Users can view own tasks" ON tasks FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own tasks" ON tasks FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Users can view own interactions" ON interactions FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own interactions" ON interactions FOR ALL USING (user_id = auth.uid());
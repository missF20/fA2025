/*
  # Add Communication and Knowledge Base Features

  1. New Tables
    - conversations (customer interactions)
    - messages (individual messages)
    - knowledge_files (uploaded documents)
    - admin_users (admin access)

  2. Security
    - Enable RLS on all tables
    - Add appropriate policies
*/

-- Create conversations table
CREATE TABLE conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  platform text CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create messages table
CREATE TABLE messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE,
  content text NOT NULL,
  sender_type text CHECK (sender_type IN ('ai', 'client')),
  created_at timestamptz DEFAULT now()
);

-- Create knowledge_files table
CREATE TABLE knowledge_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_size integer CHECK (file_size <= 10485760),
  file_type text NOT NULL,
  content bytea NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create admin_users table
CREATE TABLE admin_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  role text CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own conversations" ON conversations FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own conversations" ON conversations FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Users can view messages from their conversations" ON messages
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM conversations
    WHERE conversations.id = conversation_id
    AND conversations.user_id = auth.uid()
  ));

CREATE POLICY "Users can manage own knowledge files" ON knowledge_files FOR ALL USING (user_id = auth.uid());

-- Admin policies
CREATE POLICY "Users can view own admin record" ON admin_users FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Admins can view all records" ON admin_users FOR SELECT
  USING (EXISTS (SELECT 1 FROM admin_users WHERE user_id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can manage records" ON admin_users FOR ALL
  USING (EXISTS (SELECT 1 FROM admin_users WHERE user_id = auth.uid() AND role = 'admin'));
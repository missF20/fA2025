/*
  # Create knowledge base tables

  1. New Tables
    - `knowledge_files`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references auth.users)
      - `file_name` (text)
      - `file_size` (integer)
      - `file_type` (text)
      - `content` (bytea)
      - `created_at` (timestamp)
      - `updated_at` (timestamp)
  2. Security
    - Enable RLS on `knowledge_files` table
    - Add policies for authenticated users to manage their own files
*/

CREATE TABLE IF NOT EXISTS knowledge_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  file_name text NOT NULL,
  file_size integer NOT NULL,
  file_type text NOT NULL,
  content bytea NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Add a constraint to limit file size to 10MB (10 * 1024 * 1024 bytes)
ALTER TABLE knowledge_files ADD CONSTRAINT file_size_limit CHECK (file_size <= 10485760);

-- Enable Row Level Security
ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;

-- Create policies for knowledge_files
CREATE POLICY "Users can view their own knowledge files" ON knowledge_files
  FOR SELECT TO authenticated
  USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert their own knowledge files" ON knowledge_files
  FOR INSERT TO authenticated
  WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "Users can update their own knowledge files" ON knowledge_files
  FOR UPDATE TO authenticated
  USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can delete their own knowledge files" ON knowledge_files
  FOR DELETE TO authenticated
  USING (user_id::text = auth.uid()::text);

-- Add account_setup field to profiles table
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS account_setup_complete boolean DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS welcome_email_sent boolean DEFAULT false;
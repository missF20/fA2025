/*
  # Complete database schema rebuild

  1. Tables
    - Drop existing tables to avoid conflicts
    - Create profiles table linked to auth.users
    - Create responses, tasks, and interactions tables with proper UUID handling
  2. Security
    - Enable RLS on all tables
    - Add policies with proper UUID type casting
  3. Automation
    - Add trigger for automatic profile creation
*/

-- Drop existing tables in reverse order of dependencies
DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS profiles;

-- Create profiles table for user data
CREATE TABLE profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id),
  company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create responses table
CREATE TABLE responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  user_id uuid REFERENCES auth.users(id),
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
  user_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create interactions table
CREATE TABLE interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform text NOT NULL CHECK (platform IN ('facebook', 'instagram', 'whatsapp')),
  client_name text NOT NULL,
  client_company text NOT NULL,
  user_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Create policies for profiles
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT TO authenticated
  USING (id::text = auth.uid()::text);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE TO authenticated
  USING (id::text = auth.uid()::text);

-- Create policies for responses
CREATE POLICY "Users can view own responses" ON responses
  FOR SELECT TO authenticated
  USING (user_id::text = auth.uid()::text);

-- Create policies for tasks
CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT TO authenticated
  USING (user_id::text = auth.uid()::text);

-- Create policies for interactions
CREATE POLICY "Users can view own interactions" ON interactions
  FOR SELECT TO authenticated
  USING (user_id::text = auth.uid()::text);

-- Create function to handle user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, company)
  VALUES (new.id, (new.raw_user_meta_data->>'company')::text);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user creation
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
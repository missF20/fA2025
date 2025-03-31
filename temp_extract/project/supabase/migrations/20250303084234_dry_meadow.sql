/*
  # Create subscription tiers and admin features

  1. New Tables
    - `subscription_tiers` - Stores available subscription plans
    - `user_subscriptions` - Links users to their selected subscription tier
    - `admin_users` - Identifies users with admin privileges
  
  2. Updates
    - Add subscription_tier_id to profiles table
    - Add onboarding_completed field to profiles
  
  3. Security
    - Enable RLS on all tables
    - Add appropriate policies for user and admin access
*/

-- Create subscription_tiers table
CREATE TABLE IF NOT EXISTS subscription_tiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text NOT NULL,
  price numeric(10, 2) NOT NULL,
  features jsonb NOT NULL,
  platforms text[] NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create user_subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  subscription_tier_id uuid REFERENCES subscription_tiers(id) NOT NULL,
  status text NOT NULL CHECK (status IN ('active', 'inactive', 'pending', 'cancelled')),
  start_date timestamptz NOT NULL,
  end_date timestamptz,
  payment_status text NOT NULL CHECK (status IN ('paid', 'unpaid', 'overdue')),
  last_payment_date timestamptz,
  next_payment_date timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  role text NOT NULL CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Add subscription_tier_id to profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subscription_tier_id uuid REFERENCES subscription_tiers(id);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_completed boolean DEFAULT false;

-- Enable Row Level Security
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Create policies for subscription_tiers
CREATE POLICY "Anyone can view subscription tiers" ON subscription_tiers
  FOR SELECT USING (true);

-- Create policies for user_subscriptions
CREATE POLICY "Users can view their own subscriptions" ON user_subscriptions
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());

-- Create policies for admin_users
CREATE POLICY "Admin users can view admin data" ON admin_users
  FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users
    WHERE user_id = auth.uid()
  ));

-- Insert default subscription tiers
INSERT INTO subscription_tiers (name, description, price, features, platforms)
VALUES
  ('Facebook + Instagram', 'Connect with customers on Facebook and Instagram', 49.99, 
   '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]', 
   ARRAY['facebook', 'instagram']),
  
  ('Facebook + WhatsApp', 'Connect with customers on Facebook and WhatsApp', 49.99, 
   '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]', 
   ARRAY['facebook', 'whatsapp']),
  
  ('Instagram + WhatsApp', 'Connect with customers on Instagram and WhatsApp', 49.99, 
   '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]', 
   ARRAY['instagram', 'whatsapp']),
  
  ('Complete Package', 'Connect with customers on all platforms', 79.99, 
   '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard", "Priority support", "Advanced analytics"]', 
   ARRAY['facebook', 'instagram', 'whatsapp']);

-- Create function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admin_users
    WHERE user_id = auth.uid()
  );
END;
$$;
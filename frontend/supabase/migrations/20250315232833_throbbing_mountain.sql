/*
  # Fix Subscription Tiers and Related Tables

  1. Changes
    - Drop and recreate subscription_tiers table with proper constraints
    - Update user_subscriptions table structure
    - Add proper RLS policies
    - Add proper indexes

  2. Security
    - Enable RLS
    - Add policies for public viewing of tiers
    - Add policies for user subscription management
*/

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS subscription_tiers CASCADE;

-- Create subscription_tiers table
CREATE TABLE subscription_tiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  description text NOT NULL,
  price numeric(10,2) NOT NULL,
  features jsonb NOT NULL,
  platforms text[] NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CONSTRAINT valid_platforms CHECK (
    platforms <@ ARRAY['facebook', 'instagram', 'whatsapp']::text[]
  )
);

-- Create user_subscriptions table
CREATE TABLE user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  subscription_tier_id uuid REFERENCES subscription_tiers(id),
  status text NOT NULL DEFAULT 'pending',
  start_date timestamptz NOT NULL DEFAULT now(),
  end_date timestamptz,
  payment_status text NOT NULL DEFAULT 'unpaid',
  last_payment_date timestamptz,
  next_payment_date timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'pending', 'cancelled')),
  CONSTRAINT valid_payment_status CHECK (payment_status IN ('paid', 'unpaid', 'overdue')),
  CONSTRAINT unique_active_subscription UNIQUE (user_id, subscription_tier_id)
);

-- Enable RLS
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Create policies for subscription_tiers
CREATE POLICY "Anyone can view subscription tiers"
  ON subscription_tiers
  FOR SELECT
  USING (true);

-- Create policies for user_subscriptions
CREATE POLICY "Users can view own subscriptions"
  ON user_subscriptions
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can manage own subscriptions"
  ON user_subscriptions
  FOR ALL
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Create indexes
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_tier_id ON user_subscriptions(subscription_tier_id);
CREATE INDEX idx_subscription_tiers_price ON subscription_tiers(price);

-- Insert default subscription tiers
INSERT INTO subscription_tiers (name, description, price, features, platforms)
VALUES
  (
    'Facebook + Instagram',
    'Connect with customers on Facebook and Instagram',
    49.99,
    '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]',
    ARRAY['facebook', 'instagram']
  ),
  (
    'Facebook + WhatsApp',
    'Connect with customers on Facebook and WhatsApp',
    49.99,
    '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]',
    ARRAY['facebook', 'whatsapp']
  ),
  (
    'Instagram + WhatsApp',
    'Connect with customers on Instagram and WhatsApp',
    49.99,
    '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard"]',
    ARRAY['instagram', 'whatsapp']
  ),
  (
    'Complete Package',
    'Connect with customers on all platforms',
    79.99,
    '["AI responses", "24/7 availability", "Custom knowledge base", "Analytics dashboard", "Priority support", "Advanced analytics"]',
    ARRAY['facebook', 'instagram', 'whatsapp']
  );

-- Add function to handle subscription updates
CREATE OR REPLACE FUNCTION handle_subscription_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Update profiles table subscription_tier_id
  UPDATE profiles
  SET subscription_tier_id = NEW.subscription_tier_id
  WHERE id = NEW.user_id;
  
  RETURN NEW;
END;
$$;

-- Create trigger for subscription updates
CREATE TRIGGER on_subscription_update
  AFTER INSERT OR UPDATE ON user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION handle_subscription_update();
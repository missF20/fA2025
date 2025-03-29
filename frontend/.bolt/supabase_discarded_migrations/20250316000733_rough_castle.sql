/*
  # Add Subscription System

  1. New Tables
    - subscription_tiers (available plans)
    - user_subscriptions (user subscriptions)

  2. Changes
    - Add subscription_tier_id to profiles
    - Add subscription handling function
*/

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
  CONSTRAINT valid_platforms CHECK (platforms <@ ARRAY['facebook', 'instagram', 'whatsapp']::text[])
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

-- Add subscription_tier_id foreign key to profiles
ALTER TABLE profiles
  ADD CONSTRAINT profiles_subscription_tier_id_fkey
  FOREIGN KEY (subscription_tier_id)
  REFERENCES subscription_tiers(id)
  ON DELETE SET NULL;

-- Enable RLS
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can view subscription tiers" ON subscription_tiers FOR SELECT USING (true);

CREATE POLICY "Users can view own subscriptions" ON user_subscriptions FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own subscriptions" ON user_subscriptions FOR ALL USING (user_id = auth.uid());

-- Create subscription update handler
CREATE OR REPLACE FUNCTION handle_subscription_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE profiles
  SET subscription_tier_id = NEW.subscription_tier_id,
      updated_at = now()
  WHERE id = NEW.user_id;
  RETURN NEW;
END;
$$;

-- Create trigger for subscription updates
CREATE TRIGGER on_subscription_update
  AFTER INSERT OR UPDATE ON user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION handle_subscription_update();

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
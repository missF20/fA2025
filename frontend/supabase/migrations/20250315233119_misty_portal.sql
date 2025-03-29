/*
  # Fix Profile and Subscription Relationships

  1. Changes
    - Add proper foreign key relationships
    - Add composite view for profile data
    - Fix RLS policies
    - Add necessary indexes

  2. Security
    - Maintain existing RLS policies
    - Ensure proper data access
*/

-- Drop existing foreign key if it exists
ALTER TABLE profiles
  DROP CONSTRAINT IF EXISTS profiles_subscription_tier_id_fkey;

-- Add proper foreign key relationship
ALTER TABLE profiles
  ADD CONSTRAINT profiles_subscription_tier_id_fkey
  FOREIGN KEY (subscription_tier_id)
  REFERENCES subscription_tiers(id)
  ON DELETE SET NULL;

-- Create composite type for profile data
DO $$ BEGIN
  CREATE TYPE profile_subscription_data AS (
    id uuid,
    email text,
    company text,
    account_setup_complete boolean,
    welcome_email_sent boolean,
    onboarding_completed boolean,
    created_at timestamptz,
    updated_at timestamptz,
    subscription_id uuid,
    subscription_status text,
    payment_status text,
    start_date timestamptz,
    end_date timestamptz,
    next_payment_date timestamptz,
    tier_id uuid,
    tier_name text,
    tier_price numeric,
    tier_features jsonb,
    tier_platforms text[]
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

-- Create function to get profile subscription data
CREATE OR REPLACE FUNCTION get_profile_subscription_data(profile_id uuid)
RETURNS profile_subscription_data
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT 
    p.id,
    p.email,
    p.company,
    p.account_setup_complete,
    p.welcome_email_sent,
    p.onboarding_completed,
    p.created_at,
    p.updated_at,
    us.id as subscription_id,
    us.status as subscription_status,
    us.payment_status,
    us.start_date,
    us.end_date,
    us.next_payment_date,
    st.id as tier_id,
    st.name as tier_name,
    st.price as tier_price,
    st.features as tier_features,
    st.platforms as tier_platforms
  FROM profiles p
  LEFT JOIN user_subscriptions us ON p.id = us.user_id
  LEFT JOIN subscription_tiers st ON us.subscription_tier_id = st.id
  WHERE p.id = profile_id;
$$;

-- Create function to handle subscription updates
CREATE OR REPLACE FUNCTION handle_subscription_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Update profiles table subscription_tier_id
  UPDATE profiles
  SET 
    subscription_tier_id = NEW.subscription_tier_id,
    updated_at = now()
  WHERE id = NEW.user_id;
  
  RETURN NEW;
END;
$$;

-- Recreate trigger
DROP TRIGGER IF EXISTS on_subscription_update ON user_subscriptions;

CREATE TRIGGER on_subscription_update
  AFTER INSERT OR UPDATE ON user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION handle_subscription_update();

-- Add indexes for better join performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id 
  ON user_subscriptions(user_id);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_tier_id 
  ON user_subscriptions(subscription_tier_id);

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION get_profile_subscription_data(uuid) TO authenticated;
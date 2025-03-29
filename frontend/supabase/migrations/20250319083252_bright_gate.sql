/*
  # Fix Profile and Subscription Tier Relationship

  1. Changes
    - Add proper foreign key relationship between profiles and subscription_tiers
    - Update existing data to maintain consistency
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

-- Create index for better join performance
CREATE INDEX IF NOT EXISTS idx_profiles_subscription_tier_id 
  ON profiles(subscription_tier_id);
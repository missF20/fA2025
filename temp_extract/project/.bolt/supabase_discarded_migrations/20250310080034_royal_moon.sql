/*
  # Create Initial Users

  1. New Users
    - Regular user (hartfordtech2020@gmail.com)
    - Admin user (hartfordtech2020@gmail.com)
  
  2. Security
    - Admin role assignment
    - Profile creation
    - Default subscription tier
*/

-- Create admin user in admin_users table
INSERT INTO admin_users (user_id, role)
SELECT id, 'admin'
FROM auth.users
WHERE email = 'hartfordtech2020@gmail.com'
ON CONFLICT DO NOTHING;

-- Set up profile with subscription
UPDATE profiles
SET 
  account_setup_complete = true,
  onboarding_completed = true,
  subscription_tier_id = (
    SELECT id FROM subscription_tiers 
    WHERE name = 'Enterprise' 
    LIMIT 1
  )
WHERE email = 'hartfordtech2020@gmail.com';

-- Create subscription record
INSERT INTO user_subscriptions (
  user_id,
  subscription_tier_id,
  status,
  start_date,
  payment_status
)
SELECT 
  p.id,
  p.subscription_tier_id,
  'active',
  NOW(),
  'paid'
FROM profiles p
WHERE p.email = 'hartfordtech2020@gmail.com'
AND NOT EXISTS (
  SELECT 1 FROM user_subscriptions us 
  WHERE us.user_id = p.id
);
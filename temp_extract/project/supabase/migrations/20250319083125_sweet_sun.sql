/*
  # Assign Default Subscription

  1. Changes
    - Find user by email
    - Assign Facebook + Instagram subscription tier
    - Create user subscription record
    - Update profile with subscription tier

  2. Security
    - Use proper variable naming to avoid ambiguity
    - Maintain existing RLS policies
*/

DO $$
DECLARE
  target_user_id uuid;
  selected_tier_id uuid;
BEGIN
  -- Get user ID
  SELECT id INTO target_user_id
  FROM auth.users
  WHERE email = 'hartfordtech2020@gmail.com';

  IF target_user_id IS NULL THEN
    RAISE EXCEPTION 'User not found';
  END IF;

  -- Get Facebook + Instagram subscription tier
  SELECT id INTO selected_tier_id
  FROM subscription_tiers
  WHERE name = 'Facebook + Instagram'
  LIMIT 1;

  IF selected_tier_id IS NULL THEN
    RAISE EXCEPTION 'Subscription tier not found';
  END IF;

  -- Create user subscription with explicit column references
  INSERT INTO user_subscriptions (
    user_id,
    subscription_tier_id,
    status,
    start_date,
    payment_status
  )
  VALUES (
    target_user_id,
    selected_tier_id,
    'active',
    NOW(),
    'paid'
  )
  ON CONFLICT ON CONSTRAINT unique_active_subscription
  DO UPDATE SET
    status = EXCLUDED.status,
    payment_status = EXCLUDED.payment_status,
    updated_at = NOW();

  -- Update profile with explicit id reference
  UPDATE profiles
  SET 
    subscription_tier_id = selected_tier_id,
    updated_at = NOW()
  WHERE id = target_user_id;

END $$;
/*
  # Create Initial Users with Retry Logic

  1. New Users
    - Regular user (hartfordtech2020@gmail.com)
    - Admin user (hartfordtech2020@gmail.com)
  
  2. Security
    - Admin role assignment
    - Profile creation
    - Default subscription tier
*/

DO $$
BEGIN
  -- Create admin user in admin_users table with retry logic
  FOR i IN 1..3 LOOP
    BEGIN
      INSERT INTO admin_users (id, user_id, role, created_at, updated_at)
      SELECT 
        gen_random_uuid(),
        auth.uid(),
        'admin',
        NOW(),
        NOW()
      WHERE NOT EXISTS (
        SELECT 1 FROM admin_users 
        WHERE user_id = auth.uid()
      );
      EXIT; -- Exit loop if successful
    EXCEPTION WHEN OTHERS THEN
      IF i = 3 THEN RAISE; END IF; -- Re-raise on final attempt
      PERFORM pg_sleep(1); -- Wait 1 second before retry
    END;
  END LOOP;

  -- Set up profile
  FOR i IN 1..3 LOOP
    BEGIN
      INSERT INTO profiles (
        id,
        email,
        company,
        created_at,
        updated_at,
        account_setup_complete,
        welcome_email_sent,
        onboarding_completed
      )
      VALUES (
        auth.uid(),
        'hartfordtech2020@gmail.com',
        'Hartford Tech',
        NOW(),
        NOW(),
        true,
        true,
        true
      )
      ON CONFLICT (id) DO UPDATE
      SET 
        account_setup_complete = EXCLUDED.account_setup_complete,
        welcome_email_sent = EXCLUDED.welcome_email_sent,
        onboarding_completed = EXCLUDED.onboarding_completed;
      EXIT;
    EXCEPTION WHEN OTHERS THEN
      IF i = 3 THEN RAISE; END IF;
      PERFORM pg_sleep(1);
    END;
  END LOOP;

  -- Create subscription record with retry
  FOR i IN 1..3 LOOP
    BEGIN
      INSERT INTO user_subscriptions (
        id,
        user_id,
        subscription_tier_id,
        status,
        start_date,
        payment_status,
        created_at,
        updated_at
      )
      SELECT
        gen_random_uuid(),
        auth.uid(),
        st.id,
        'active',
        NOW(),
        'paid',
        NOW(),
        NOW()
      FROM subscription_tiers st
      WHERE st.name = 'Enterprise'
      AND NOT EXISTS (
        SELECT 1 FROM user_subscriptions us 
        WHERE us.user_id = auth.uid()
      );
      EXIT;
    EXCEPTION WHEN OTHERS THEN
      IF i = 3 THEN RAISE; END IF;
      PERFORM pg_sleep(1);
    END;
  END LOOP;
END $$;
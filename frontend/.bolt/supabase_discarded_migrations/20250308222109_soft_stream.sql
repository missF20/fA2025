/*
  # Update Admin User Creation Function

  1. Changes
    - Update create_admin_user function to handle email in profiles
    - Ensure proper email synchronization between auth.users and profiles
*/

-- Update the admin user creation function
CREATE OR REPLACE FUNCTION create_admin_user(
  p_email text,
  p_username text,
  p_password text,
  p_role text
) RETURNS uuid AS $$
DECLARE
  v_user_id uuid;
  v_existing_user_id uuid;
BEGIN
  -- Check if user already exists
  SELECT id INTO v_existing_user_id
  FROM auth.users
  WHERE email = p_email;

  IF v_existing_user_id IS NULL THEN
    -- Create auth user
    INSERT INTO auth.users (
      email,
      raw_user_meta_data,
      raw_app_meta_data,
      encrypted_password,
      email_confirmed_at,
      created_at,
      updated_at,
      role,
      is_super_admin
    )
    VALUES (
      p_email,
      jsonb_build_object('username', p_username),
      jsonb_build_object('provider', 'email', 'providers', ARRAY['email']),
      crypt(p_password, gen_salt('bf')),
      now(),
      now(),
      now(),
      'authenticated',
      false
    )
    RETURNING id INTO v_user_id;
  ELSE
    -- Update existing user's password
    UPDATE auth.users
    SET encrypted_password = crypt(p_password, gen_salt('bf'))
    WHERE id = v_existing_user_id;
    
    v_user_id := v_existing_user_id;
  END IF;

  -- Delete existing admin user if exists
  DELETE FROM admin_users WHERE user_id = v_user_id;

  -- Create admin user
  INSERT INTO admin_users (
    user_id,
    email,
    username,
    role
  )
  VALUES (
    v_user_id,
    p_email,
    p_username,
    p_role
  );

  -- Ensure profile exists with email
  INSERT INTO profiles (
    id,
    email,
    account_setup_complete,
    created_at,
    updated_at
  )
  VALUES (
    v_user_id,
    p_email,
    true,
    now(),
    now()
  )
  ON CONFLICT (id) DO UPDATE
  SET email = p_email,
      account_setup_complete = true,
      updated_at = now();

  RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recreate the admin user to ensure everything is properly set up
SELECT create_admin_user(
  '20HT20@admin.com',
  '20HT20',
  '20HT20HT',
  'admin'
);
/*
  # Create Admin User

  1. Changes
    - Create admin user with proper authentication
    - Create corresponding profile
    - Add admin role
    - Handle existing user cases

  2. Security
    - Use proper password hashing
    - Set up correct permissions
*/

-- Create admin user
DO $$
DECLARE
  admin_user_id uuid := '00000000-0000-0000-0000-000000000001';
  admin_email text := 'admin@hartford-tech.com';
BEGIN
  -- Insert admin user with a fixed UUID
  INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role,
    confirmation_token
  )
  VALUES (
    admin_user_id,
    '00000000-0000-0000-0000-000000000000',
    admin_email,
    crypt('ht20ht20', gen_salt('bf')),
    now(),
    now(),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"admin"}',
    false,
    'authenticated',
    encode(gen_random_bytes(32), 'hex')
  );

  -- Create profile for admin user
  INSERT INTO public.profiles (
    id,
    email,
    company,
    account_setup_complete,
    welcome_email_sent,
    onboarding_completed,
    created_at,
    updated_at
  )
  VALUES (
    admin_user_id,
    admin_email,
    'Hartford Tech',
    true,
    true,
    true,
    now(),
    now()
  );

  -- Create admin role
  INSERT INTO public.admin_users (
    id,
    user_id,
    role,
    created_at,
    updated_at
  )
  VALUES (
    gen_random_uuid(),
    admin_user_id,
    'admin',
    now(),
    now()
  );

EXCEPTION
  WHEN unique_violation THEN
    -- If user already exists, get their ID and ensure they have admin role
    SELECT id INTO admin_user_id
    FROM auth.users
    WHERE email = admin_email;

    IF admin_user_id IS NOT NULL THEN
      INSERT INTO public.admin_users (id, user_id, role)
      VALUES (gen_random_uuid(), admin_user_id, 'admin')
      ON CONFLICT DO NOTHING;
    END IF;
END $$;
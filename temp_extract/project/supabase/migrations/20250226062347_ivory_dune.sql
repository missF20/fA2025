/*
  # Add mock data for Hartford Tech

  1. Mock Data
    - Add sample conversations and messages
    - Add sample tasks and interactions
    - Add sample responses

  2. Data Structure
    - Realistic conversation flows
    - Various platforms (Facebook, Instagram, WhatsApp)
    - Different timestamps for temporal distribution
*/

-- Create function to get the first user ID
CREATE OR REPLACE FUNCTION get_first_user_id()
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
  first_user_id uuid;
BEGIN
  SELECT id INTO first_user_id FROM auth.users LIMIT 1;
  RETURN first_user_id;
END;
$$;

-- Insert mock conversations
DO $$
DECLARE
  user_id uuid;
BEGIN
  user_id := get_first_user_id();
  
  INSERT INTO conversations (id, user_id, platform, client_name, client_company, created_at)
  VALUES
    ('11111111-1111-1111-1111-111111111111', user_id, 'facebook', 'John Smith', 'TechCorp Solutions', NOW() - INTERVAL '2 hours'),
    ('22222222-2222-2222-2222-222222222222', user_id, 'instagram', 'Sarah Johnson', 'Digital Innovators', NOW() - INTERVAL '1 day'),
    ('33333333-3333-3333-3333-333333333333', user_id, 'whatsapp', 'Michael Brown', 'Cloud Systems Inc', NOW() - INTERVAL '3 hours'),
    ('44444444-4444-4444-4444-444444444444', user_id, 'facebook', 'Emma Davis', 'WebTech Solutions', NOW() - INTERVAL '30 minutes'),
    ('55555555-5555-5555-5555-555555555555', user_id, 'instagram', 'David Wilson', 'AI Dynamics', NOW() - INTERVAL '4 hours');

  -- Insert mock messages
  INSERT INTO messages (conversation_id, content, sender_type, created_at)
  VALUES
    -- John Smith conversation
    ('11111111-1111-1111-1111-111111111111', 'Hi, I need help with integrating the API', 'client', NOW() - INTERVAL '2 hours'),
    ('11111111-1111-1111-1111-111111111111', 'I''d be happy to help you with the API integration. Could you please specify which API you''re working with?', 'ai', NOW() - INTERVAL '2 hours'),
    ('11111111-1111-1111-1111-111111111111', 'We''re trying to integrate the payment processing API', 'client', NOW() - INTERVAL '2 hours'),
    ('11111111-1111-1111-1111-111111111111', 'I understand. Let me guide you through the payment API integration process step by step.', 'ai', NOW() - INTERVAL '2 hours'),

    -- Sarah Johnson conversation
    ('22222222-2222-2222-2222-222222222222', 'Having issues with the dashboard loading', 'client', NOW() - INTERVAL '1 day'),
    ('22222222-2222-2222-2222-222222222222', 'I''ll help you troubleshoot the dashboard issue. Are you seeing any specific error messages?', 'ai', NOW() - INTERVAL '1 day'),
    ('22222222-2222-2222-2222-222222222222', 'Yes, it says "Failed to fetch data"', 'client', NOW() - INTERVAL '1 day'),
    ('22222222-2222-2222-2222-222222222222', 'That error typically occurs when there''s a connection issue. Let''s check your network settings first.', 'ai', NOW() - INTERVAL '1 day'),

    -- Michael Brown conversation
    ('33333333-3333-3333-3333-333333333333', 'Need help with user authentication setup', 'client', NOW() - INTERVAL '3 hours'),
    ('33333333-3333-3333-3333-333333333333', 'I can help you set up user authentication. Are you using any specific authentication provider?', 'ai', NOW() - INTERVAL '3 hours'),
    ('33333333-3333-3333-3333-333333333333', 'We want to use OAuth with Google', 'client', NOW() - INTERVAL '3 hours'),
    ('33333333-3333-3333-3333-333333333333', 'Perfect choice! I''ll guide you through the Google OAuth implementation.', 'ai', NOW() - INTERVAL '3 hours'),

    -- Emma Davis conversation
    ('44444444-4444-4444-4444-444444444444', 'How do I deploy my React application?', 'client', NOW() - INTERVAL '30 minutes'),
    ('44444444-4444-4444-4444-444444444444', 'I''ll help you deploy your React application. Which hosting platform would you prefer to use?', 'ai', NOW() - INTERVAL '30 minutes'),
    ('44444444-4444-4444-4444-444444444444', 'We''re considering Netlify', 'client', NOW() - INTERVAL '30 minutes'),
    ('44444444-4444-4444-4444-444444444444', 'Excellent choice! Netlify is great for React applications. Let me walk you through the deployment process.', 'ai', NOW() - INTERVAL '30 minutes'),

    -- David Wilson conversation
    ('55555555-5555-5555-5555-555555555555', 'Need assistance with database optimization', 'client', NOW() - INTERVAL '4 hours'),
    ('55555555-5555-5555-5555-555555555555', 'I''ll help you optimize your database. What specific performance issues are you experiencing?', 'ai', NOW() - INTERVAL '4 hours'),
    ('55555555-5555-5555-5555-555555555555', 'Slow query performance on large datasets', 'client', NOW() - INTERVAL '4 hours'),
    ('55555555-5555-5555-5555-555555555555', 'Let''s analyze your queries and implement some optimization strategies.', 'ai', NOW() - INTERVAL '4 hours');

  -- Insert mock tasks
  INSERT INTO tasks (description, status, platform, client_name, client_company, user_id, created_at)
  VALUES
    ('Implement payment API integration', 'pending', 'facebook', 'John Smith', 'TechCorp Solutions', user_id, NOW() - INTERVAL '2 hours'),
    ('Resolve dashboard loading issue', 'completed', 'instagram', 'Sarah Johnson', 'Digital Innovators', user_id, NOW() - INTERVAL '1 day'),
    ('Setup Google OAuth authentication', 'pending', 'whatsapp', 'Michael Brown', 'Cloud Systems Inc', user_id, NOW() - INTERVAL '3 hours'),
    ('Guide React deployment process', 'completed', 'facebook', 'Emma Davis', 'WebTech Solutions', user_id, NOW() - INTERVAL '30 minutes'),
    ('Optimize database queries', 'pending', 'instagram', 'David Wilson', 'AI Dynamics', user_id, NOW() - INTERVAL '4 hours');

  -- Insert mock interactions
  INSERT INTO interactions (platform, client_name, client_company, user_id, created_at)
  VALUES
    ('facebook', 'John Smith', 'TechCorp Solutions', user_id, NOW() - INTERVAL '2 hours'),
    ('instagram', 'Sarah Johnson', 'Digital Innovators', user_id, NOW() - INTERVAL '1 day'),
    ('whatsapp', 'Michael Brown', 'Cloud Systems Inc', user_id, NOW() - INTERVAL '3 hours'),
    ('facebook', 'Emma Davis', 'WebTech Solutions', user_id, NOW() - INTERVAL '30 minutes'),
    ('instagram', 'David Wilson', 'AI Dynamics', user_id, NOW() - INTERVAL '4 hours');

  -- Insert mock responses
  INSERT INTO responses (content, platform, user_id, created_at)
  VALUES
    ('I''ll help you with the API integration. Could you please specify which API you''re working with?', 'facebook', user_id, NOW() - INTERVAL '2 hours'),
    ('Let''s troubleshoot the dashboard issue. Are you seeing any specific error messages?', 'instagram', user_id, NOW() - INTERVAL '1 day'),
    ('I can help you set up user authentication. Are you using any specific authentication provider?', 'whatsapp', user_id, NOW() - INTERVAL '3 hours'),
    ('I''ll help you deploy your React application. Which hosting platform would you prefer to use?', 'facebook', user_id, NOW() - INTERVAL '30 minutes'),
    ('I''ll help you optimize your database. What specific performance issues are you experiencing?', 'instagram', user_id, NOW() - INTERVAL '4 hours');
END $$;
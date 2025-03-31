/*
  # Add Mock Data for User Dashboard

  1. New Data
    - Add sample conversations across platforms
    - Add sample messages for each conversation
    - Add sample tasks and interactions
    - Add sample responses
    - Link all data to hartfordtech2020@gmail.com user

  2. Structure
    - Realistic conversation flows
    - Various platforms (Facebook, Instagram, WhatsApp)
    - Different timestamps for temporal distribution
*/

DO $$
DECLARE
  user_id uuid;
  conversation_id_1 uuid := gen_random_uuid();
  conversation_id_2 uuid := gen_random_uuid();
  conversation_id_3 uuid := gen_random_uuid();
BEGIN
  -- Get user ID
  SELECT id INTO user_id
  FROM auth.users
  WHERE email = 'hartfordtech2020@gmail.com';

  IF user_id IS NULL THEN
    RAISE EXCEPTION 'User not found';
  END IF;

  -- Insert conversations
  INSERT INTO conversations (id, user_id, platform, client_name, client_company, created_at)
  VALUES
    (conversation_id_1, user_id, 'facebook', 'Emily Chen', 'TechStart Solutions', NOW() - INTERVAL '2 hours'),
    (conversation_id_2, user_id, 'instagram', 'Marcus Rodriguez', 'Digital Innovate Co', NOW() - INTERVAL '1 day'),
    (conversation_id_3, user_id, 'whatsapp', 'Sarah Thompson', 'Cloud Systems Pro', NOW() - INTERVAL '30 minutes');

  -- Insert messages for each conversation
  -- Conversation 1: Technical Support Issue
  INSERT INTO messages (conversation_id, content, sender_type, created_at)
  VALUES
    (conversation_id_1, 'Hi, we''re having trouble integrating your API with our system. Can you help?', 'client', NOW() - INTERVAL '2 hours'),
    (conversation_id_1, 'Of course! I''d be happy to help. Could you please specify which integration endpoint you''re having issues with?', 'ai', NOW() - INTERVAL '1 hour 58 minutes'),
    (conversation_id_1, 'It''s the /users/sync endpoint. We''re getting a 403 error.', 'client', NOW() - INTERVAL '1 hour 55 minutes'),
    (conversation_id_1, 'I see the issue. You''ll need to include the API key in the Authorization header. Let me show you the correct format.', 'ai', NOW() - INTERVAL '1 hour 53 minutes'),
    (conversation_id_1, 'Here''s an example of the correct header format: Authorization: Bearer your-api-key', 'ai', NOW() - INTERVAL '1 hour 52 minutes'),
    (conversation_id_1, 'Thank you! That worked perfectly.', 'client', NOW() - INTERVAL '1 hour 45 minutes');

  -- Conversation 2: Feature Request Discussion
  INSERT INTO messages (conversation_id, content, sender_type, created_at)
  VALUES
    (conversation_id_2, 'Hello! Is there a way to export analytics data in CSV format?', 'client', NOW() - INTERVAL '1 day'),
    (conversation_id_2, 'Currently, we support PDF and JSON exports. CSV export is on our roadmap for next quarter. Would you like me to notify you when it''s available?', 'ai', NOW() - INTERVAL '23 hours'),
    (conversation_id_2, 'Yes, please! That would be very helpful. Any temporary workaround available?', 'client', NOW() - INTERVAL '22 hours'),
    (conversation_id_2, 'You can use our JSON export and convert it to CSV using our open-source conversion tool. Would you like me to share the link?', 'ai', NOW() - INTERVAL '21 hours'),
    (conversation_id_2, 'That would be perfect, thank you!', 'client', NOW() - INTERVAL '20 hours'),
    (conversation_id_2, 'Here''s the link to our conversion tool: https://github.com/example/json-to-csv. Let me know if you need help setting it up.', 'ai', NOW() - INTERVAL '19 hours');

  -- Conversation 3: Onboarding Support
  INSERT INTO messages (conversation_id, content, sender_type, created_at)
  VALUES
    (conversation_id_3, 'Hi, we just signed up for the enterprise plan. How do we get started?', 'client', NOW() - INTERVAL '30 minutes'),
    (conversation_id_3, 'Welcome to our platform! I''ll guide you through the setup process. First, let''s configure your team members and permissions.', 'ai', NOW() - INTERVAL '28 minutes'),
    (conversation_id_3, 'Great, we have a team of 5 people who need access.', 'client', NOW() - INTERVAL '25 minutes'),
    (conversation_id_3, 'Perfect! I''ll help you set up role-based access control. Would you like to schedule a quick onboarding call with our implementation team?', 'ai', NOW() - INTERVAL '23 minutes'),
    (conversation_id_3, 'Yes, that would be helpful. What times are available?', 'client', NOW() - INTERVAL '20 minutes'),
    (conversation_id_3, 'I''ve checked our calendar. We have slots available tomorrow at 10 AM or 2 PM EST. Which works better for you?', 'ai', NOW() - INTERVAL '18 minutes');

  -- Insert tasks
  INSERT INTO tasks (description, status, platform, client_name, client_company, user_id, created_at)
  VALUES
    ('Follow up on API integration success', 'pending', 'facebook', 'Emily Chen', 'TechStart Solutions', user_id, NOW() - INTERVAL '1 hour 45 minutes'),
    ('Schedule CSV export feature demo', 'completed', 'instagram', 'Marcus Rodriguez', 'Digital Innovate Co', user_id, NOW() - INTERVAL '19 hours'),
    ('Complete enterprise onboarding setup', 'pending', 'whatsapp', 'Sarah Thompson', 'Cloud Systems Pro', user_id, NOW() - INTERVAL '18 minutes'),
    ('Review security requirements', 'pending', 'facebook', 'Emily Chen', 'TechStart Solutions', user_id, NOW() - INTERVAL '1 hour'),
    ('Prepare custom integration documentation', 'completed', 'whatsapp', 'Sarah Thompson', 'Cloud Systems Pro', user_id, NOW() - INTERVAL '15 minutes');

  -- Insert interactions
  INSERT INTO interactions (platform, client_name, client_company, user_id, created_at)
  VALUES
    ('facebook', 'Emily Chen', 'TechStart Solutions', user_id, NOW() - INTERVAL '2 hours'),
    ('instagram', 'Marcus Rodriguez', 'Digital Innovate Co', user_id, NOW() - INTERVAL '1 day'),
    ('whatsapp', 'Sarah Thompson', 'Cloud Systems Pro', user_id, NOW() - INTERVAL '30 minutes'),
    ('facebook', 'Emily Chen', 'TechStart Solutions', user_id, NOW() - INTERVAL '1 hour'),
    ('whatsapp', 'Sarah Thompson', 'Cloud Systems Pro', user_id, NOW() - INTERVAL '15 minutes');

  -- Insert responses
  INSERT INTO responses (content, platform, user_id, created_at)
  VALUES
    ('I''d be happy to help with your API integration. Could you please specify which endpoint you''re having issues with?', 'facebook', user_id, NOW() - INTERVAL '1 hour 58 minutes'),
    ('Currently, we support PDF and JSON exports. CSV export is on our roadmap for next quarter. Would you like me to notify you when it''s available?', 'instagram', user_id, NOW() - INTERVAL '23 hours'),
    ('Welcome to our platform! I''ll guide you through the setup process. First, let''s configure your team members and permissions.', 'whatsapp', user_id, NOW() - INTERVAL '28 minutes'),
    ('Here''s the link to our conversion tool: https://github.com/example/json-to-csv. Let me know if you need help setting it up.', 'instagram', user_id, NOW() - INTERVAL '19 hours'),
    ('I''ve checked our calendar. We have slots available tomorrow at 10 AM or 2 PM EST. Which works better for you?', 'whatsapp', user_id, NOW() - INTERVAL '18 minutes');

END $$;
/*
  # Update subscription tiers

  1. Changes
    - Update subscription tier options
    - Add single platform and dual platform combinations
    - Set default prices for all tiers
*/

-- Update subscription tiers
TRUNCATE TABLE subscription_tiers CASCADE;

INSERT INTO subscription_tiers (name, description, price, features, platforms)
VALUES
  (
    'Facebook',
    'Connect and manage your Facebook presence',
    49.99,
    '["AI responses", "24/7 availability", "Analytics dashboard"]',
    ARRAY['facebook']
  ),
  (
    'Instagram',
    'Connect and manage your Instagram presence',
    49.99,
    '["AI responses", "24/7 availability", "Analytics dashboard"]',
    ARRAY['instagram']
  ),
  (
    'WhatsApp',
    'Connect and manage your WhatsApp presence',
    49.99,
    '["AI responses", "24/7 availability", "Analytics dashboard"]',
    ARRAY['whatsapp']
  ),
  (
    'Facebook + Instagram',
    'Manage both Facebook and Instagram together',
    79.99,
    '["AI responses", "24/7 availability", "Analytics dashboard", "Cross-platform insights"]',
    ARRAY['facebook', 'instagram']
  ),
  (
    'Facebook + WhatsApp',
    'Manage both Facebook and WhatsApp together',
    79.99,
    '["AI responses", "24/7 availability", "Analytics dashboard", "Cross-platform insights"]',
    ARRAY['facebook', 'whatsapp']
  ),
  (
    'Instagram + WhatsApp',
    'Manage both Instagram and WhatsApp together',
    79.99,
    '["AI responses", "24/7 availability", "Analytics dashboard", "Cross-platform insights"]',
    ARRAY['instagram', 'whatsapp']
  ),
  (
    'Enterprise',
    'Complete solution with all platforms',
    129.99,
    '["AI responses", "24/7 availability", "Analytics dashboard", "Cross-platform insights", "Priority support", "Custom integrations"]',
    ARRAY['facebook', 'instagram', 'whatsapp']
  );
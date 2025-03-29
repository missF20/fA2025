/*
  # Add Performance Indexes

  1. Changes
    - Add indexes for frequently queried columns
    - Add composite indexes for common query patterns
    - Add indexes for foreign key columns

  2. Performance
    - Improve query performance
    - Optimize join operations
    - Speed up sorting and filtering
*/

-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_company ON profiles(company);
CREATE INDEX IF NOT EXISTS idx_profiles_subscription_tier ON profiles(subscription_tier_id);

CREATE INDEX IF NOT EXISTS idx_conversations_platform ON conversations(platform);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_client_name ON conversations(client_name);

CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_sender_type ON messages(sender_type);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_platform ON tasks(platform);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_interactions_platform ON interactions(platform);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);

CREATE INDEX IF NOT EXISTS idx_responses_platform ON responses(platform);
CREATE INDEX IF NOT EXISTS idx_responses_created_at ON responses(created_at);

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_conversations_user_platform ON conversations(user_id, platform);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_interactions_user_platform ON interactions(user_id, platform);

-- Add indexes for timestamp range queries
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_dates ON user_subscriptions(start_date, end_date);
// Types for Dana AI Platform

// Base types for various entities
export interface Profile {
  id: string;
  user_id: string;
  email: string;
  company: string | null;
  account_setup_complete: boolean;
  welcome_email_sent: boolean;
  created_at: string;
  subscription_tier_id?: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  content: string;
  sender_type: 'user' | 'client' | 'ai';
  created_at: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  user_id: string;
  platform: string;
  client_name: string;
  client_company?: string;
  status: 'active' | 'closed' | 'pending';
  created_at: string;
  updated_at: string;
  last_message?: string;
  last_message_time?: string;
  messages?: Message[];
}

export interface Task {
  id: string;
  user_id: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  platform: string;
  client_name: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
  assigned_to?: string;
}

export interface KnowledgeFile {
  id: string;
  user_id: string;
  file_name?: string;
  filename?: string; // Support for legacy field name
  file_size: number;
  file_type: string;
  content?: string;
  created_at: string;
  updated_at?: string;
  category?: string;
  tags?: string[] | string;
  metadata?: Record<string, any> | string;
  binary_data?: string; // Support for legacy binary data
}

export interface KnowledgeFileWithContent extends KnowledgeFile {
  content: string;
  parsed_metadata?: {
    author?: string;
    title?: string;
    created_date?: string;
    modified_date?: string;
    pages?: number;
    [key: string]: any;
  };
}

export interface KnowledgeSearchResult {
  id: string;
  file_name?: string;
  filename?: string; // Support for legacy field name
  file_type: string;
  category?: string;
  tags?: string[] | string;
  created_at: string;
  snippets?: string[];
  relevance?: number;
}

export interface KnowledgeCategory {
  name: string;
  count?: number;
}

export interface KnowledgeTag {
  name: string;
  count?: number;
}

export interface Integration {
  id: string;
  user_id: string;
  integration_type: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
  config?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  last_sync?: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  type: string;
}

export interface SubscriptionTier {
  id: string;
  name: string;
  description: string;
  price: number;
  monthly_price?: number;
  annual_price?: number;
  features: string[];
  platforms: string[];
  is_popular: boolean;
  trial_days: number;
  max_users?: number;
  is_active: boolean;
  feature_limits?: Record<string, number>;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  subscription_tier_id: string;
  status: 'active' | 'canceled' | 'expired' | 'pending';
  start_date: string;
  end_date?: string;
  payment_method_id?: string;
  billing_cycle?: string;
  auto_renew: boolean;
  trial_end_date?: string;
  last_billing_date?: string;
  next_billing_date?: string;
  cancellation_date?: string;
  cancellation_reason?: string;
}

// Utility types
export type Platform = 'facebook' | 'instagram' | 'whatsapp' | 'email' | 'website' | 'slack';

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface SearchResult<T> {
  query: string;
  filters?: Record<string, any>;
  results: T[];
  count: number;
  limit: number;
}

// Analytics and Dashboard Types
export interface Interaction {
  id: string;
  client_name?: string;
  name?: string; // Alternative property for client_name
  company?: string; // Alternative for client_company
  platform: Platform;
  content?: string;
  timestamp: string;
}

export interface PendingTask {
  id: string;
  description?: string;
  client_name?: string;
  task?: string; // Alternative property for description
  client?: {
    name: string;
    company?: string;
  };
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  platform: Platform;
  client_company?: string;
  timestamp?: string;
}

export interface EscalatedTask {
  id: string;
  description?: string;
  client_name?: string;
  task?: string; // Alternative property for description
  client?: {
    name: string;
    company?: string;
  };
  reason?: string;
  timestamp: string;
  platform: Platform;
  priority: 'low' | 'medium' | 'high';
  client_company?: string;
}

export interface TopIssue {
  id?: string;
  issue: string; // The main issue label
  name?: string; // Alternative for issue (for API compatibility)
  count: number; // Number of occurrences
  trend: number; // Percentage change from previous period
  percentage: number; // Percentage of total issues
  platform?: string; // Source platform of the issue
}

// Support and Feedback Types
export interface SupportTicket {
  id?: string;
  subject: string;
  message: string;
  status: 'open' | 'in_progress' | 'closed';
  user_id?: string;
  email?: string;
  created_at: string;
  updated_at?: string;
}

export interface Rating {
  id?: string;
  score: number;
  feedback: string;
  user_id?: string;
  email?: string;
  created_at: string;
}

// Auth and User Management
import { User as SupabaseUser } from '@supabase/supabase-js';

// Extended User interface that properly extends User from Supabase
export interface ExtendedUser extends Omit<SupabaseUser, 'user_metadata'> {
  user_metadata: {
    company?: string;
    [key: string]: any;
  }
}

export interface SignUpData {
  email: string;
  password: string;
  company?: string;
}

export interface LoginData {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface PasswordResetData {
  email: string;
}

export interface PasswordChangeData {
  token: string;
  new_password: string;
}

export interface AuthFormData {
  email: string;
  password: string;
  company?: string;
  rememberMe?: boolean;
}

// Dashboard metrics types
// Sentiment Analysis Types
export interface SentimentData {
  id: string;
  type: 'positive' | 'neutral' | 'negative';
  count: number;
  trend: number;
  percentage: number;
}

export interface ChatMetrics {
  totalResponses: number;
  responsesBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
    slack?: number;
    email?: number;
  };
  completedTasks: number;
  completedTasksBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
    slack?: number;
    email?: number;
  };
  pendingTasks: Array<{
    id: string;
    task: string;
    client: {
      name: string;
      company?: string;
    };
    timestamp: string;
    platform: Platform;
    priority: 'low' | 'medium' | 'high';
  }>;
  escalatedTasks: Array<{
    id: string;
    task: string;
    client: {
      name: string;
      company?: string;
    };
    timestamp: string;
    platform: Platform;
    priority: 'low' | 'medium' | 'high';
    reason: string;
  }>;
  totalChats: number;
  chatsBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
    slack?: number;
    email?: number;
  };
  peopleInteracted: Array<{
    id: string;
    name: string;
    company?: string;
    timestamp: string;
    platform: Platform;
  }>;
  responseTime: string;
  topIssues: Array<{
    id: string;
    name: string;
    count: number;
    trend: number;
    platform?: string;
  }>;
  interactionsByType: Array<{
    type: string;
    count: number;
  }>;
  conversations: Conversation[];
  integrations: Array<Integration>;
  // Platforms allowed in the user's subscription
  allowedPlatforms?: string[];
  // Sentiment analysis data
  sentimentData?: SentimentData[];
}
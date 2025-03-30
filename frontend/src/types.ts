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
  file_name: string;
  file_size: number;
  file_type: string;
  content?: string;
  created_at: string;
  updated_at?: string;
  category?: string;
  tags?: string[] | string;
  metadata?: Record<string, any> | string;
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
export type Platform = 'facebook' | 'instagram' | 'whatsapp' | 'email' | 'website';

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
  client_name: string;
  platform: Platform;
  content: string;
  timestamp: string;
}

export interface PendingTask {
  id: string;
  description: string;
  client_name: string;
  priority: 'low' | 'medium' | 'high';
  due_date: string;
}

export interface EscalatedTask {
  id: string;
  description: string;
  client_name: string;
  reason: string;
  timestamp: string;
}

// Auth and User Management
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
export interface MetricCard {
  title: string;
  value: number;
  icon: React.ReactNode;
  description: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  breakdown?: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
}

export interface TopIssue {
  issue: string;
  count: number;
  percentage: number;
}

export interface PendingTask {
  id: string;
  task: string;
  client: {
    name: string;
    company: string;
  };
  timestamp: string;
}

export interface EscalatedTask {
  id: string;
  task: string;
  client: {
    name: string;
    company: string;
  };
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
}

export interface Interaction {
  id: string;
  name: string;
  company: string;
  timestamp: string;
  type: string;
}

export interface Message {
  id: string;
  content: string;
  sender_type: 'ai' | 'client';
  created_at: string;
}

export interface Conversation {
  id: string;
  platform: 'facebook' | 'instagram' | 'whatsapp';
  client_name: string;
  client_company: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'connected' | 'disconnected';
  category: 'crm' | 'communication' | 'analytics' | 'ecommerce' | 'helpdesk';
}

export interface ChatMetrics {
  totalResponses: number;
  responsesBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
  completedTasks: number;
  completedTasksBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
  pendingTasks: PendingTask[];
  escalatedTasks: EscalatedTask[];
  totalChats: number;
  chatsBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
  peopleInteracted: Interaction[];
  responseTime: string;
  topIssues: TopIssue[];
  interactionsByType: {
    type: string;
    count: number;
  }[];
  conversations: Conversation[];
  integrations: Integration[];
}

export interface AuthFormData {
  email: string;
  password: string;
  company?: string;
  rememberMe?: boolean;
}

export interface SupportTicket {
  id?: string;
  subject: string;
  message: string;
  status?: 'open' | 'in-progress' | 'resolved';
  created_at?: string;
}

export interface Rating {
  id?: string;
  score: number;
  feedback?: string;
  created_at?: string;
}

export interface KnowledgeFile {
  id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionTier {
  id: string;
  name: string;
  description: string;
  price: number;
  features: string[];
  platforms: string[];
  created_at?: string;
  updated_at?: string;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  subscription_tier_id: string;
  status: 'active' | 'inactive' | 'pending' | 'cancelled';
  start_date: string;
  end_date?: string;
  payment_status: 'paid' | 'unpaid' | 'overdue';
  last_payment_date?: string;
  next_payment_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AdminClient {
  id: string;
  company: string;
  email: string;
  status: 'active' | 'inactive' | 'pending';
  subscription: string;
  platforms: string[];
  setupComplete: boolean;
  paymentStatus: 'paid' | 'unpaid' | 'overdue';
  nextPaymentDate: string | null;
  createdAt: string;
}

export interface AdminStats {
  totalClients: number;
  activeClients: number;
  pendingSetup: number;
  revenueThisMonth: number;
  overdueBilling: number;
  platformBreakdown: {
    facebook: number;
    instagram: number;
    whatsapp: number;
  };
}
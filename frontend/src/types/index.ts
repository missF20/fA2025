// Admin Types
export interface AdminClient {
  id: string;
  company: string;
  email: string;
  status: string;
  subscription: string;
  platforms: string[];
  setupComplete: boolean;
  paymentStatus: string;
  nextPaymentDate: string;
  createdAt: string;
}

export interface AdminStats {
  totalClients: number;
  activeClients: number;
  pendingSetup: number;
  revenueThisMonth: number;
  overdueBilling: number;
  platformBreakdown: {
    [key: string]: number;
  };
}

// Token Usage Types
export interface ModelUsage {
  model: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  request_count: number;
  first_request?: string;
  last_request?: string;
}

export interface TokenLimits {
  limit: number;
  used: number;
  remaining: number;
  exceeded: boolean;
  unlimited: boolean;
}

export interface TokenUsageStats {
  totals: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    request_count: number;
  };
  models: ModelUsage[];
  limits: TokenLimits;
  period: {
    start: string;
    end: string;
    days: number;
  };
}

export interface UserTokenUsage {
  userId: string;
  username?: string;
  email?: string;
  company?: string;
  stats: TokenUsageStats;
}
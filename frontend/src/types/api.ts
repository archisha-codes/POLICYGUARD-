// frontend/src/types/api.ts

export interface User {
  id: string; 
  email: string;
  role: "admin" | "compliance_officer" | "auditor" | "manager";
  user_metadata?: {
    display_name?: string;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    email: string;
    role: string;
  };
}

export interface ApiTransaction {
  transaction_id: string;
  customer_name: string;
  customer_id: string;
  amount: number;
  currency: string;
  transaction_type: string;
  description: string;
  status: string;
  risk_score: number;
  ai_explanation?: string;
  created_at: string;
  // ✅ Added fields to match backend update
  flagged_reasons?: string[];
  country?: string;
  merchant?: string;
  risk_breakdown?: Record<string, number>;
  source_account?: string;
  destination_account?: string;
}

export interface ApiAlert {
  id: string;
  severity: string;
  message: string;
  created_at: string;
  transaction_id: string;
  status: string;
}

export interface ApiAuditLog {
  id: string;
  action: string;
  entity: string;
  timestamp: string;
  details?: any;
}

export interface DashboardStats {
  transactions_today: number;
  compliance_rate: number;
  pending_reviews: number;
  active_alerts: number;
}

export interface AnalyzeRequest {
  transaction_id: string;
  amount: number;
  currency: string;
  customer_id: string;
  transaction_type: string;
  description?: string;
  metadata?: any;
  source_account?: string;
  destination_account?: string;
  simulation?: boolean;
}
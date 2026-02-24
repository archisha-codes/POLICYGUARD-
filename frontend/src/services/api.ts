// frontend/src/services/api.ts

import { AuthService } from './auth';
import { 
  ApiTransaction, 
  DashboardStats, 
  AuthResponse, 
  ApiAuditLog, 
  AnalyzeRequest 
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface AlertActionPayload {
  transaction_id: string;
  action: 'approve' | 'resolve' | 'email_user';
  notes?: string;
}

/* =========================
   API SERVICE CLASS
========================= */

class ApiService {
  private getHeaders(includeAuth: boolean = false): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = AuthService.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      if (response.status === 401) {
        AuthService.logout();
        window.location.href = '/auth';
        throw new Error('Authentication required');
      }
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // --- Auth ---
  async login(email: string, role: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({ email, role }),
    });
    return this.handleResponse(res);
  }

  // --- Dashboard Data ---
  async fetchStats(): Promise<DashboardStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`, {
        method: 'GET',
        headers: this.getHeaders(true),
      });
      return this.handleResponse<DashboardStats>(response);
    } catch (error) {
      console.error('Error fetching stats:', error);
      return {
        transactions_today: 0,
        compliance_rate: 100,
        pending_reviews: 0,
        active_alerts: 0
      };
    }
  }

  // --- Transactions ---
  async fetchTransactions(limit = 50, offset = 0): Promise<ApiTransaction[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/transactions?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: this.getHeaders(true),
      });
      return this.handleResponse<ApiTransaction[]>(response);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      throw error;
    }
  }

  // --- Alerts ---
  async fetchAlerts(): Promise<ApiTransaction[]> {
    const res = await fetch(`${API_BASE_URL}/api/alerts`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Audit Logs ---
  async fetchAuditLogs(): Promise<ApiAuditLog[]> {
    const res = await fetch(`${API_BASE_URL}/api/audit-logs`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Analysis ---
  async analyzeTransaction(payload: AnalyzeRequest): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(payload),
    });
    return this.handleResponse(res);
  }

  // --- Traffic Simulation ---
  async simulateTraffic(scenario: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulate/traffic`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ scenario }),
    });
    return this.handleResponse(res);
  }

  // --- Simulation Cases ---
  async fetchSimulationCases(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/cases`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  async simulateCase(caseId: number): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/simulate/${caseId}`, {
      method: 'POST',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  async fetchSimulationTransactions(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/transactions`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  async fetchSimulationAuditLogs(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/audit`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  async fetchSimulationBalance(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/balance`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Policy Drift ---
  async checkDrift(simulate: boolean = false): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/admin/check-drift?simulate=${simulate}`, {
      method: 'POST',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Policy Drift Updates ---
  async fetchPolicyUpdates(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/policy-drift/updates`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Policy Drift Affected Transactions ---
  async fetchAffectedTransactions(regId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/policy-drift/affected/${regId}`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Retry Gemini Analysis ---
  async retryAnalysis(transactionId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/analyze/retry/${transactionId}`, {
      method: 'POST',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(res);
  }

  // --- Alert Actions ---
  async logAlertAction(payload: AlertActionPayload): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/alerts/action`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(payload),
    });
    return this.handleResponse(res);
  }
}

export const api = new ApiService();

export const loginApi = (email: string, role: string) => api.login(email, role);
export const fetchStats = () => api.fetchStats();
export const fetchTransactions = (limit?: number, offset?: number) => api.fetchTransactions(limit, offset);
export const fetchAlerts = () => api.fetchAlerts();
export const fetchAuditLogs = () => api.fetchAuditLogs();
export const analyzeTransaction = (payload: AnalyzeRequest) => api.analyzeTransaction(payload);
export const simulateTraffic = (scenario: string) => api.simulateTraffic(scenario);
export const fetchSimulationCases = () => api.fetchSimulationCases();
export const simulateCase = (caseId: number) => api.simulateCase(caseId);
export const fetchSimulationTransactions = () => api.fetchSimulationTransactions();
export const fetchSimulationAuditLogs = () => api.fetchSimulationAuditLogs();
export const fetchSimulationBalance = () => api.fetchSimulationBalance();
export const checkDrift = (simulate: boolean) => api.checkDrift(simulate);
export const fetchPolicyUpdates = () => api.fetchPolicyUpdates();
export const fetchAffectedTransactions = (regId: string) => api.fetchAffectedTransactions(regId);
export const retryAnalysis = (transactionId: string) => api.retryAnalysis(transactionId);
export const logAlertAction = (payload: AlertActionPayload) => api.logAlertAction(payload);
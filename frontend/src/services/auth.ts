// frontend/src/services/auth.ts

import { AuthResponse, User } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "policyguard_token";
const USER_KEY = "policyguard_user";

export const AuthService = {
  async login(email: string, role: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, role }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }

    const data: AuthResponse = await res.json();
    
    // Persist session
    localStorage.setItem(TOKEN_KEY, data.access_token);
    // Store minimal user info for persistence
    localStorage.setItem(USER_KEY, JSON.stringify({ 
      email: data.user.email, 
      role: data.user.role 
    }));

    return data;
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUser(): User | null {
    const u = localStorage.getItem(USER_KEY);
    if (!u) return null;
    try {
      const parsed = JSON.parse(u);
      return {
        id: "me",
        email: parsed.email,
        role: parsed.role,
        // Fix: Populate metadata so Dashboard doesn't crash
        user_metadata: { display_name: parsed.email.split('@')[0] } 
      };
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return !!localStorage.getItem(TOKEN_KEY);
  },
};
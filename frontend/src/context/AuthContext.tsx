// frontend/src/context/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect } from "react";
import { AuthService } from "../services/auth";
import { User } from "../types/api";
import { useToast } from "@/components/ui/use-toast";

// Define the shape of our Auth Context
interface AuthContextType {
  user: User | null;
  role: string | null;
  loading: boolean;
  login: (email: string, role: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>(null!);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { toast } = useToast();

  useEffect(() => {
    // Restore session on mount
    const token = AuthService.getToken();
    const storedUser = AuthService.getUser();
    
    if (token && storedUser) {
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  const login = async (email: string, role: string) => {
    try {
      setLoading(true);
      const data = await AuthService.login(email, role);
      
      const newUser: User = {
        id: `user_${data.user.email.split("@")[0]}`,
        email: data.user.email,
        role: data.user.role as any,
        user_metadata: {
          display_name: data.user.email.split("@")[0]
        }
      };
      
      setUser(newUser);
      
      toast({
        title: "Welcome back",
        description: `Logged in as ${data.user.role}`,
      });
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Login Failed",
        description: error.message,
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    AuthService.logout();
    setUser(null);
    toast({ description: "You have been logged out." });
  };

  const role = user?.role || null;

  return (
    <AuthContext.Provider value={{ user, role, loading, login, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

// Export the hook
export const useAuth = () => useContext(AuthContext);
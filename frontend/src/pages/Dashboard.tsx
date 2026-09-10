// frontend/src/pages/Dashboard.tsx

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  Shield, Activity, AlertTriangle, CheckCircle, TrendingUp, 
  Users, FileText, Loader2, LogOut 
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { StatusChip } from "@/components/ui/StatusChip";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { PulsingIndicator } from "@/components/ui/PulsingIndicator";
import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { ChatWidget } from "@/components/chat/ChatWidget";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { api } from "@/services/api";
import { DashboardStats, ApiTransaction } from "@/types/api";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, role, loading, signOut } = useAuth();
  
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<ApiTransaction[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth");
    }
  }, [user, loading, navigate]);

  // Fetch Dashboard Data
  useEffect(() => {
    if (user) {
      const loadDashboardData = async () => {
        try {
          setIsLoadingData(true);
          const [statsData, txnsData] = await Promise.all([
            api.fetchStats(),
            api.fetchTransactions(5) // Fetch top 5 for recent activity
          ]);
          setStats(statsData);
          setRecentTransactions(txnsData);
        } catch (error) {
          console.error("Failed to load dashboard data", error);
        } finally {
          setIsLoadingData(false);
        }
      };
      loadDashboardData();
    }
  }, [user]);

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  if (loading || isLoadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Dashboard Statistics Configuration
  const statCards = [
    { 
      label: "Transactions Today", 
      value: stats?.transactions_today || 0, 
      icon: Activity, 
      color: "primary" 
    },
    { 
      label: "Compliance Rate", 
      value: stats?.compliance_rate || 0, 
      suffix: "%", 
      icon: CheckCircle, 
      color: "success" 
    },
    { 
      label: "Pending Reviews", 
      value: stats?.pending_reviews || 0, 
      icon: AlertTriangle, 
      color: "warning" 
    },
    { 
      label: "Active Alerts", 
      value: stats?.active_alerts || 0, 
      icon: Shield, 
      color: "destructive" 
    },
  ];

  // Helper to map backend status string to StatusChip type
  const getStatusType = (status: string) => {
    const s = status ? status.toLowerCase() : 'pending';
    if (s === 'compliant') return 'approved';
    if (s === 'non_compliant' || s === 'rejected') return 'rejected';
    if (s === 'flagged') return 'flagged';
    return 'pending';
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />
      
      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-card/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center shadow-[0_0_15px_hsl(var(--primary)/0.4)]">
              <Shield className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">PolicyGuard</h1>
              <PulsingIndicator status="online" size="sm" label="System Active" />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden md:block">
              <p className="text-sm font-medium text-foreground">
                {user.user_metadata?.display_name || user.email}
              </p>
            </div>
            <StatusChip 
              status="approved"
              size="sm"
              label={role || "Officer"}
            />
            <NeonButton variant="outline" size="sm" onClick={handleSignOut}>
              <LogOut className="h-4 w-4" />
            </NeonButton>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-3xl font-bold text-foreground mb-2">
            Dashboard Overview
          </h2>
          <p className="text-muted-foreground">
            Real-time compliance monitoring and risk assessment.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <GlassCard 
                  glowColor={stat.color as any}
                  className="p-5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn(
                      "h-10 w-10 rounded-lg flex items-center justify-center",
                      stat.color === "primary" && "bg-primary/20 text-primary",
                      stat.color === "success" && "bg-success/20 text-success",
                      stat.color === "warning" && "bg-warning/20 text-warning",
                      stat.color === "destructive" && "bg-destructive/20 text-destructive"
                    )}>
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-foreground">
                      <AnimatedCounter value={stat.value} duration={1.5} suffix={stat.suffix || ""} decimals={stat.suffix === "%" ? 1 : 0} />
                    </div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>

        {/* Recent Activity & Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Recent Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2"
          >
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentTransactions.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">No recent activity found.</p>
                ) : (
                  recentTransactions.map((txn, index) => {
                    const dateStr = txn.created_at.endsWith("Z") ? txn.created_at : `${txn.created_at}Z`;
                    const dateObj = new Date(dateStr);
                    const timeAgo = isNaN(dateObj.getTime()) ? "Just now" : formatDistanceToNow(dateObj) + " ago";

                    return (
                      <motion.div
                        key={txn.transaction_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + index * 0.1 }}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex flex-col gap-1">
                           <div className="flex items-center gap-2">
                             <span className="text-xs px-2 py-0.5 rounded-md bg-primary/10 text-primary font-mono border border-primary/20">
                               {txn.currency} {txn.amount.toLocaleString()}
                             </span>
                           </div>
                           <div className="flex items-center gap-2 text-xs text-muted-foreground">
                             <span className="uppercase tracking-wider">{txn.transaction_type}</span>
                             <span>•</span>
                             <span className={cn(
                               "font-medium",
                               txn.risk_score > 80 ? "text-destructive" : txn.risk_score > 50 ? "text-warning" : "text-success"
                             )}>
                               Risk Score: {Math.round(txn.risk_score)}
                             </span>
                           </div>
                        </div>
                        
                        <div className="flex flex-col items-end gap-1">
                          <StatusChip 
                            status={getStatusType(txn.status)} 
                            size="sm" 
                            label={txn.status.replace("_", " ").toUpperCase()} 
                          />
                          <span className="text-[10px] text-muted-foreground">
                            {timeAgo}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </div>
            </GlassCard>
          </motion.div>

          {/* Quick Actions Panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <GlassCard className="p-6" glowColor="secondary">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-secondary" />
                Quick Actions
              </h3>
              <div className="space-y-3">
                <NeonButton 
                  variant="outline" 
                  className="w-full justify-start hover:bg-secondary/10 hover:text-secondary" 
                  size="sm"
                  onClick={() => navigate("/transactions")}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Transaction Monitoring
                </NeonButton>
                <NeonButton 
                  variant="outline" 
                  className="w-full justify-start hover:bg-destructive/10 hover:text-destructive" 
                  size="sm" 
                  onClick={() => navigate("/alerts")}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  View Active Alerts
                </NeonButton>
                <NeonButton 
                  variant="outline" 
                  className="w-full justify-start" 
                  size="sm"
                >
                  <Users className="h-4 w-4 mr-2" />
                  Team Overview
                </NeonButton>
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </main>

      <ChatWidget />
    </div>
  );
}
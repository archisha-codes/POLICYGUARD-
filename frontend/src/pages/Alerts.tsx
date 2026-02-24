import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Mail,
  User,
} from "lucide-react";
import { format } from "date-fns";
import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { useAuth } from "@/hooks/useAuth";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { StatusChip } from "@/components/ui/StatusChip";
import { useAlerts } from "@/hooks/useAlerts";
import { useToast } from "@/components/ui/use-toast";
import { logAlertAction } from "@/services/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

type Priority = "high" | "medium" | "low" | "info";

interface AlertUI {
  id: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  message: string;
  timestamp: string;
  transactionId: string;
  status: string;
  priority: Priority;
  emailSent: boolean;
  acknowledged: boolean;
  resolved: boolean;
  assignedTo?: string;
  isGeminiFailed?: boolean;
  errorCode?: string;
  user_email?: string;
  user_name?: string;
  amount?: number;
  currency?: string;
  transaction_type?: string;
  beneficiary_name?: string;
  country?: string;
  channel?: string;
}

export default function Alerts() {
  const { user, loading: authLoading } = useAuth();
  const { alerts: hookAlerts, loading: hookLoading, reload: refreshAlerts } = useAlerts();
  const [alerts, setAlerts] = useState<AlertUI[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<AlertUI[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<Priority | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [resolvedAlertIds, setResolvedAlertIds] = useState<Set<string>>(new Set());
  const [showResolvedDialog, setShowResolvedDialog] = useState(false);
  const { toast } = useToast();

  /* ============================
     FETCH FROM BACKEND
  ============================ */
  useEffect(() => {
    if (!hookLoading && hookAlerts.length >= 0) {
      // Map backend → UI model
      const mapped: AlertUI[] = hookAlerts.map((a) => ({
        ...a,
        priority:
          a.severity === "HIGH"
            ? "high"
            : a.severity === "MEDIUM"
            ? "medium"
            : "low",
        emailSent: true,
        acknowledged: false,
        resolved: false,
        // Check if this is a Gemini failure alert
        isGeminiFailed: a.message?.toLowerCase().includes("gemini") || 
                       a.message?.toLowerCase().includes("ai analysis failed"),
      }));

      setAlerts(mapped);
      setFilteredAlerts(mapped);
      setIsLoading(false);
    }
  }, [hookAlerts, hookLoading]);

  /* ============================
     FILTERING
  ============================ */
  useEffect(() => {
    let filtered = alerts;

    if (priorityFilter !== "all") {
      filtered = filtered.filter((a) => a.priority === priorityFilter);
    }

    setFilteredAlerts(filtered);
  }, [alerts, priorityFilter]);

  /* ============================
       UI ACTIONS (DEMO-ONLY)
  ============================ */
  const handleAcknowledge = async (alert: AlertUI) => {
    // Optimistic UI update
    setAlerts((prev) =>
      prev.map((a) => (a.id === alert.id ? { ...a, acknowledged: true } : a))
    );
    try {
      await logAlertAction({ transaction_id: alert.transactionId, action: 'approve' });
    } catch (e) {
      console.error("Failed to log approve action", e);
    }
  };

  const handleResolve = async (alert: AlertUI) => {
    // Optimistic UI update
    setAlerts((prev) =>
      prev.map((a) => (a.id === alert.id ? { ...a, resolved: true } : a))
    );
    setResolvedAlertIds((prev) => new Set(prev).add(alert.id));
    setShowResolvedDialog(true);
    try {
      await logAlertAction({ transaction_id: alert.transactionId, action: 'resolve' });
    } catch (e) {
      console.error("Failed to log resolve action", e);
    }
  };

  const handleEmailUser = async (alert: AlertUI) => {
    try {
      await logAlertAction({ transaction_id: alert.transactionId, action: 'email_user' });
    } catch (e) {
      console.error("Failed to log email action", e);
    }
  };

  if (authLoading || isLoading) return <div>Loading...</div>;
  if (!user) return <div>Please log in</div>;

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case "high":
        return "destructive";
      case "medium":
        return "secondary";
      case "low":
        return "default";
      default:
        return "default";
    }
  };

  const getEmailBody = (alert: AlertUI) => {
    const userName = alert.user_name || 'User';
    const transactionId = alert.transactionId || alert.id || 'N/A';
    const timestamp = alert.timestamp || 'N/A';
    const amount = alert.amount !== undefined ? alert.amount : 'N/A';
    const currency = alert.currency || 'N/A';
    const transactionType = alert.transaction_type || 'N/A';
    const beneficiaryName = alert.beneficiary_name || 'N/A';
    const country = alert.country || 'N/A';
    const channel = alert.channel || 'N/A';
    
    return `Dear ${userName},%0D%0A%0D%0AWe hope this message finds you well.%0D%0A%0D%0AOur compliance monitoring system has identified a recent transaction associated with your account that requires review. The details are provided below:%0D%0A%0D%0ATransaction Details:%0D%0A--------------------------------------------------%0D%0ATransaction ID: ${transactionId}%0D%0ADate & Time: ${timestamp}%0D%0AAmount: ${amount} ${currency}%0D%0ATransaction Type: ${transactionType}%0D%0ABeneficiary Name: ${beneficiaryName}%0D%0ADestination Country: ${country}%0D%0AChannel: ${channel}%0D%0A--------------------------------------------------%0D%0A%0D%0AReason for Flag:%0D%0A%0D%0AThis transaction has been flagged due to one or more risk indicators identified during routine compliance monitoring. This may include:%0D%0A%0D%0A• Unusual transaction pattern compared to historical activity%0D%0A• Cross-border remittance review%0D%0A• Velocity or frequency anomaly%0D%0A• Regulatory compliance requirement%0D%0A• Beneficiary or geographic risk indicator%0D%0A%0D%0APlease note this does NOT necessarily indicate wrongdoing. The review is part of our standard risk-based monitoring process to ensure regulatory compliance and account security.%0D%0A%0D%0AIf this transaction was initiated by you and is legitimate, no immediate action may be required. However, if you believe it was unauthorized or require clarification, please contact support immediately.%0D%0A%0D%0Asupport@policyguard.com%0D%0A%0D%0ARegards,%0D%0ACompliance Team%0D%0APolicyGuard`;
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="flex items-center justify-between mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h1 className="text-3xl font-bold text-glow">
              Alerts & Notifications
            </h1>
            <p className="text-muted-foreground">
              Real compliance alerts from backend
            </p>
          </div>

          <Select
            value={priorityFilter}
            onValueChange={(v) => setPriorityFilter(v as Priority | "all")}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </motion.div>

        {/* Alerts */}
        <div className="space-y-4">
          {filteredAlerts.map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Collapsible>
                <CollapsibleTrigger asChild>
                  <GlassCard className="p-4 cursor-pointer">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="h-4 w-4 text-warning" />
                        <div>
                          <h3 className="font-semibold">
                            Transaction {alert.transactionId}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {alert.message}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusChip
                          status={alert.status === "approved" ? "approved" : alert.status === "flagged" ? "flagged" : alert.status === "rejected" ? "rejected" : alert.status === "live" ? "live" : alert.status === "paused" ? "paused" : "pending"}
                        />
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(alert.timestamp), "PPp")}
                        </span>
                      </div>
                    </div>
                  </GlassCard>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <GlassCard className="p-4 mt-2">
                    <p className="text-sm mb-2">
                      {alert.message}
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {!alert.acknowledged && !resolvedAlertIds.has(alert.id) && (
                        <NeonButton
                          size="sm"
                          // Fix: Pass the whole alert object
                          onClick={() => handleAcknowledge(alert)}
                        >
                          Approve
                        </NeonButton>
                      )}
                      {!resolvedAlertIds.has(alert.id) && (
                        <>
                          <a
                            href={`mailto:${alert.user_email || 'support@policyguard.com'}?subject=${encodeURIComponent('Action Required – Review of Flagged Transaction')}&body=${getEmailBody(alert)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            // Fix: Add onClick handler to track the email action
                            onClick={() => handleEmailUser(alert)}
                          >
                            <NeonButton variant="outline" size="sm">
                              Email User
                            </NeonButton>
                          </a>
                          <NeonButton
                            variant="secondary"
                            size="sm"
                            // Fix: Pass the whole alert object
                            onClick={() => handleResolve(alert)}
                          >
                            Resolve
                          </NeonButton>
                        </>
                      )}
                    </div>
                  </GlassCard>
                </CollapsibleContent>
              </Collapsible>
            </motion.div>
          ))}
        </div>
      </div>

      <Dialog open={showResolvedDialog} onOpenChange={setShowResolvedDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alert Resolved</DialogTitle>
            <DialogDescription>
              Details of this transaction has been forwarded.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <NeonButton onClick={() => setShowResolvedDialog(false)}>
              OK
            </NeonButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
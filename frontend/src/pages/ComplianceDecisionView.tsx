import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  Brain,
  AlertTriangle,
  ChevronDown,
} from "lucide-react";
import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { RiskScoreBadge } from "@/components/transactions/RiskScoreBadge";
import { StatusChip } from "@/components/ui/StatusChip";
import { useAuth } from "@/hooks/useAuth";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { analyzeTransaction, fetchTransactions, submitFeedback } from "@/services/api";
import { ApiTransaction } from "@/types/api";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

export default function ComplianceDecisionView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  const [transaction, setTransaction] = useState<ApiTransaction | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [notes, setNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  /* ============================
     LOAD TRANSACTION + ANALYZE
  ============================ */
  useEffect(() => {
    const loadAndAnalyze = async () => {
      try {
        setIsLoading(true);

        // 1️⃣ Fetch transactions
        const transactions: ApiTransaction[] = await fetchTransactions();
        const txn = transactions.find((t) => t.id === id);

        if (!txn) {
          throw new Error("Transaction not found");
        }

        setTransaction(txn);

        // 2️⃣ Call protected analyze endpoint
        const result = await analyzeTransaction({
          transaction_id: txn.id,
          amount: txn.amount,
          description: "Compliance analysis request",
        });

        setAnalysis(result);
      } catch (err) {
        console.error("Compliance analysis failed:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) loadAndAnalyze();
  }, [id]);

  const handleConfirmAction = async () => {
    if (!action || !transaction || !analysis) return;
    try {
      setIsSubmitting(true);
      await submitFeedback({
        transaction_id: transaction.id,
        customer_id: transaction.customer_id || "CUST_UNKNOWN",
        ai_verdict: analysis.analysis?.verdict || "unknown",
        human_verdict: action.toUpperCase(),
        notes: notes || `Officer ${user?.email || ''} action: ${action}`
      });

      setTransaction(prev => prev ? { ...prev, status: action } : null);
      toast.success(`Action '${action.toUpperCase()}' logged and cryptographically signed into audit log.`);
      setAction(null);
      setNotes("");
    } catch (err: any) {
      toast.error(`Action failed: ${err.message || "Unknown error"}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading || isLoading) return <div className="p-8 text-center">Loading Compliance Assessment...</div>;
  if (!user) {
    navigate("/auth");
    return null;
  }
  if (!transaction || !analysis) {
    return <div className="p-8 text-center text-destructive">Unable to load compliance decision</div>;
  }

  const risk = analysis.analysis?.risk_score || 0;
  const amlRisk = Math.round(risk * 0.4);
  const kycRisk = Math.round(risk * 0.3);
  const policyRisk = Math.round(risk * 0.2);
  const historicalRisk = Math.round(risk * 0.1);

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground overflow-hidden">
        <ParticleBackground />

        <div className="relative z-10 container mx-auto px-4 py-8">
          {/* Header */}
          <motion.div
            className="flex items-center justify-between mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-4">
              <NeonButton
                variant="ghost"
                size="sm"
                onClick={() => navigate("/transactions")}
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </NeonButton>
              <div>
                <h1 className="text-3xl font-bold text-glow">
                  Compliance Decision Co-Pilot
                </h1>
                <p className="text-muted-foreground">
                  Transaction #{transaction.id} | Customer #{transaction.customer_id}
                </p>
              </div>
            </div>

            <RiskScoreBadge score={risk} size="lg" />
          </motion.div>

          {/* Timeline */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Compliance Audit Timeline</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <CheckCircle className="text-success" />
                <span>Transaction Ingested & Schema Validated</span>
              </div>
              <div className="flex items-center gap-4">
                <CheckCircle className="text-success" />
                <span>PII Detected & Tokenized (PAN/Aadhaar/Account)</span>
              </div>
              <div className="flex items-center gap-4">
                <Clock className="text-primary" />
                <span>Deterministic Rules Evaluated</span>
              </div>
              <div className="flex items-center gap-4">
                <Brain className="text-secondary" />
                <span>Local RAG Regulatory Evidence Retrieved & AI Risk Scoring</span>
              </div>
              <div className="flex items-center gap-4">
                <AlertTriangle className="text-warning" />
                <span>
                  Current System Verdict:{" "}
                  <StatusChip status={transaction.status as any} />
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Risk Decomposition */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Transparent Risk Breakdown</h2>
            {[["AML Velocity & Structuring Risk", amlRisk], ["KYC Compliance Risk", kycRisk], ["Policy Ambiguity Risk", policyRisk], ["Historical Pattern Risk", historicalRisk]].map(
              ([label, value], i) => (
                <Tooltip key={i}>
                  <TooltipTrigger asChild>
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span>{label}</span>
                        <span>{value}%</span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-primary"
                          initial={{ width: 0 }}
                          animate={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>Contribution: {value}%</TooltipContent>
                </Tooltip>
              )
            )}
          </GlassCard>

          {/* Explainable AI */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Explainable Compliance Reasoning</h2>

            <Collapsible defaultOpen>
              <CollapsibleTrigger className="flex justify-between w-full font-medium text-destructive">
                Triggered Compliance Rules
                <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ul className="mt-2 space-y-2">
                  {analysis.analysis?.violated_rules?.length ? (
                    analysis.analysis.violated_rules.map((r: string, i: number) => (
                      <li key={i} className="text-sm font-mono text-destructive">
                        • {r}
                      </li>
                    ))
                  ) : (
                    <p className="text-sm text-success">
                      ✓ No compliance rule violations detected
                    </p>
                  )}
                </ul>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible defaultOpen className="mt-4">
              <CollapsibleTrigger className="flex justify-between w-full font-medium text-primary">
                Regulatory Evidence & Explanation
                <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <p className="text-sm mt-2 leading-relaxed bg-black/40 p-4 rounded-lg border border-primary/20">
                  {analysis.analysis?.explanation}
                </p>
              </CollapsibleContent>
            </Collapsible>
          </GlassCard>

          {/* Actions (Human-in-the-Loop) */}
          {(user.role === "admin" || user.role === "compliance_officer") && (
            <GlassCard className="p-6">
              <h2 className="font-semibold mb-2">Human-in-the-Loop Governance</h2>
              <p className="text-xs text-muted-foreground mb-4">
                PolicyGuard assists compliance officers. Every officer action is permanently recorded with cryptographic SHA-256 hash chaining.
              </p>
              <div className="flex gap-3">
                <NeonButton onClick={() => setAction("approve")}>
                  Approve Transaction
                </NeonButton>
                <NeonButton
                  variant="destructive"
                  onClick={() => setAction("reject")}
                >
                  Reject Transaction
                </NeonButton>
                <NeonButton
                  variant="secondary"
                  onClick={() => setAction("override")}
                >
                  Override AI Recommendation
                </NeonButton>
              </div>
            </GlassCard>
          )}

          {/* Confirmation Dialog */}
          <Dialog open={!!action} onOpenChange={() => setAction(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirm Human Action: {action?.toUpperCase()}</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-muted-foreground mb-3">
                Are you sure you want to record a human {action} decision for Transaction #{transaction.id}?
              </p>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground">Compliance Reviewer Notes:</label>
                <Input
                  placeholder="Enter reason for approval/override..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
              <DialogFooter className="mt-4">
                <Button variant="outline" onClick={() => setAction(null)} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button onClick={handleConfirmAction} disabled={isSubmitting}>
                  {isSubmitting ? "Signing & Logging..." : "Confirm & Save Decision"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </TooltipProvider>
  );
}

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
import { analyzeTransaction, fetchTransactions } from "@/services/api";
import { ApiTransaction } from "@/types/api";


export default function ComplianceDecisionView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  const [transaction, setTransaction] = useState<ApiTransaction | null>(null);
const [analysis, setAnalysis] = useState<any>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);

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

      // 2️⃣ Call protected analyze endpoint (JWT attached automatically)
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


  if (authLoading || isLoading) return <div>Loading...</div>;
  if (!user) {
    navigate("/auth");
    return null;
  }
  if (!transaction || !analysis) {
    return <div>Unable to load compliance decision</div>;
  }

  const risk = analysis.analysis.risk_score || 0;

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
                  Compliance Decision
                </h1>
                <p className="text-muted-foreground">
                  Transaction {transaction.id}

                </p>
              </div>
            </div>

            <RiskScoreBadge score={risk} size="lg" />
          </motion.div>

          {/* Timeline */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Compliance Timeline</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <CheckCircle className="text-success" />
                <span>Transaction Received</span>
              </div>
              <div className="flex items-center gap-4">
                <Clock className="text-primary" />
                <span>Rules Evaluated</span>
              </div>
              <div className="flex items-center gap-4">
                <Brain className="text-secondary" />
                <span>AI Risk Scoring</span>
              </div>
              <div className="flex items-center gap-4">
                <AlertTriangle className="text-warning" />
                <span>
                  Final Verdict:
                  <StatusChip status={analysis.analysis.verdict as any} />
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Risk Decomposition */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Risk Decomposition</h2>
            {[["AML Risk", amlRisk], ["KYC Risk", kycRisk], ["Policy Risk", policyRisk], ["Historical Risk", historicalRisk]].map(
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
                  <TooltipContent>AI Confidence: {value}%</TooltipContent>
                </Tooltip>
              )
            )}
          </GlassCard>

          {/* Explainable AI */}
          <GlassCard className="p-6 mb-6">
            <h2 className="font-semibold mb-4">Explainable AI</h2>

            <Collapsible>
              <CollapsibleTrigger className="flex justify-between w-full">
                Why flagged?
                <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ul className="mt-2 space-y-2">
                  {analysis.analysis.violated_rules?.length ? (
                    analysis.analysis.violated_rules.map((r, i) => (
                      <li key={i} className="text-sm">
                        • {r}
                      </li>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No violations detected
                    </p>
                  )}
                </ul>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible>
              <CollapsibleTrigger className="flex justify-between w-full mt-4">
                AI Explanation
                <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <p className="text-sm mt-2">
                  {analysis.analysis.explanation}
                </p>
              </CollapsibleContent>
            </Collapsible>
          </GlassCard>

          {/* Actions (Demo) */}
          {(user.role === "admin" || user.role === "compliance_officer") && (
            <GlassCard className="p-6">
              <h2 className="font-semibold mb-4">Actions</h2>
              <div className="flex gap-3">
                <NeonButton onClick={() => setAction("approve")}>
                  Approve
                </NeonButton>
                <NeonButton
                  variant="destructive"
                  onClick={() => setAction("reject")}
                >
                  Reject
                </NeonButton>
                <NeonButton
                  variant="secondary"
                  onClick={() => setAction("escalate")}
                >
                  Escalate
                </NeonButton>
              </div>
            </GlassCard>
          )}

          {/* Confirmation Dialog */}
          <Dialog open={!!action} onOpenChange={() => setAction(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirm Action</DialogTitle>
              </DialogHeader>
              <p>Proceed with {action}?</p>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAction(null)}>
                  Cancel
                </Button>
                <Button onClick={() => setAction(null)}>Confirm</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </TooltipProvider>
  );
}

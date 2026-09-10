import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Play,
  Pause,
  RefreshCw,
  Zap,
  FileText
} from "lucide-react";
import { format } from "date-fns";

import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { usePolicyDrift } from "@/hooks/usePolicyDrift";
import { PulsingIndicator } from "@/components/ui/PulsingIndicator";
import { StatusChip } from "@/components/ui/StatusChip";
import { fetchPolicyUpdates, fetchAffectedTransactions } from "@/services/api";
import { useToast } from "@/components/ui/use-toast";

export default function PolicyDrift() {
  const { user, loading: authLoading } = useAuth();
  const {
    driftEvents,
    isMonitoring,
    setIsMonitoring,
    reload,
    simulateDrift, 
    lastChecked,
  } = usePolicyDrift();
  const { toast } = useToast();

  const [isReloading, setIsReloading] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [policyUpdates, setPolicyUpdates] = useState<any[]>([]);
  const [affectedTransactions, setAffectedTransactions] = useState<Record<string, any[]>>({});
  const [loadingUpdates, setLoadingUpdates] = useState(false);

  // Fetch persistent policy updates on mount
  useEffect(() => {
    const loadUpdates = async () => {
      setLoadingUpdates(true);
      try {
        const data = await fetchPolicyUpdates();
        setPolicyUpdates(data.updates || []);
      } catch (error) {
        console.error("Failed to fetch policy updates:", error);
      } finally {
        setLoadingUpdates(false);
      }
    };
    loadUpdates();
  }, []);

  if (authLoading) return <div>Loading...</div>;
  if (!user) return <div>Please log in</div>;

  const handleManualRefresh = async () => {
    setIsReloading(true);
    await reload();
    setIsReloading(false);
  };
  
  const handleSimulation = async () => {
    setIsSimulating(true);
    await simulateDrift();
    setIsSimulating(false);
  };

  // Show affected transactions for a regulation
  const showAffectedTransactions = async (regId: string) => {
    if (affectedTransactions[regId]) {
      setAffectedTransactions(prev => {
        const newState = { ...prev };
        delete newState[regId];
        return newState;
      });
      return;
    }
    
    try {
      const data = await fetchAffectedTransactions(regId);
      setAffectedTransactions(prev => ({
        ...prev,
        [regId]: data.transactions || []
      }));
    } catch (error) {
      console.error("Failed to fetch affected transactions:", error);
      toast({
        title: "Error",
        description: "Could not fetch affected transactions",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-3xl font-bold text-glow">
            Policy Drift & Regulatory Updates
          </h1>
          <p className="text-muted-foreground text-sm">
            Live monitoring of regulatory amendments and knowledge base updates
          </p>
        </motion.div>

        {/* Controls */}
        <div className="flex justify-center gap-4 mb-8">
          <StatusChip
            status={isMonitoring ? "live" : "paused"}
            label={isMonitoring ? "Live Monitoring" : "Paused"}
            icon={isMonitoring ? <PulsingIndicator /> : <Pause className="h-4 w-4" />}
          />

          <NeonButton
            size="sm"
            variant={isMonitoring ? "secondary" : "primary"}
            onClick={() => setIsMonitoring(!isMonitoring)}
          >
            {isMonitoring ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            {isMonitoring ? "Pause" : "Resume"}
          </NeonButton>

          <NeonButton
            size="sm"
            variant="destructive"
            onClick={handleSimulation}
            disabled={isSimulating}
          >
            <Zap className={`h-4 w-4 mr-2 ${isSimulating ? "animate-pulse" : ""}`} />
            {isSimulating ? "Simulating..." : "Simulate Regulatory Update"}
          </NeonButton>

          <NeonButton
            size="sm"
            variant="ghost"
            onClick={handleManualRefresh}
            disabled={isReloading}
          >
            <RefreshCw className={`h-4 w-4 ${isReloading ? "animate-spin" : ""}`} />
          </NeonButton>
        </div>

        {/* Policy Updates from RAG */}
        {policyUpdates.length > 0 && (
          <GlassCard className="p-6 mb-8">
            <h2 className="text-lg font-semibold mb-4 text-primary flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Historical Regulatory Updates
            </h2>
            <div className="space-y-3">
              {policyUpdates.map((update) => (
                <div key={update.rag_doc_id} className="p-3 bg-muted/20 rounded-lg border border-primary/20">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm">{update.title}</p>
                      <p className="text-xs text-muted-foreground mt-1">{update.summary}</p>
                      {update.updated_at && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Updated: {format(new Date(update.updated_at), "PPp")}
                        </p>
                      )}
                    </div>
                    <NeonButton
                      size="sm"
                      variant="outline"
                      onClick={() => showAffectedTransactions(update.rag_doc_id)}
                    >
                      {affectedTransactions[update.rag_doc_id] ? "Hide Transactions" : "Show Affected Transactions"}
                    </NeonButton>
                  </div>
                  
                  {/* Affected Transactions Table */}
                  {affectedTransactions[update.rag_doc_id] && affectedTransactions[update.rag_doc_id].length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/30">
                      <p className="text-xs text-muted-foreground mb-2">
                        Affected Transactions ({affectedTransactions[update.rag_doc_id].length}):
                      </p>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-left text-muted-foreground">
                              <th className="pb-2">Transaction ID</th>
                              <th className="pb-2">Amount</th>
                              <th className="pb-2">Customer</th>
                              <th className="pb-2">Risk Tags</th>
                            </tr>
                          </thead>
                          <tbody>
                            {affectedTransactions[update.rag_doc_id].map((txn: any, idx: number) => (
                              <tr key={idx} className="border-t border-border/20">
                                <td className="py-1 font-mono">{txn.transaction_id}</td>
                                <td className="py-1">${txn.amount?.toLocaleString()}</td>
                                <td className="py-1">{txn.customer_id}</td>
                                <td className="py-1">
                                  {txn.risk_tags?.map((tag: string, i: number) => (
                                    <Badge key={i} variant="outline" className="mr-1 text-xs">
                                      {tag}
                                    </Badge>
                                  ))}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Live Drift Events Timeline */}
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-primary flex items-center gap-2 px-2">
            <Zap className="h-5 w-5" />
            Live Event Stream
          </h2>
          
          <AnimatePresence>
            {driftEvents.map((event) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 40 }}
              >
                <GlassCard className="p-6 border-l-4 border-l-destructive bg-destructive/5">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex gap-3 items-start">
                      <Shield className="h-5 w-5 text-destructive mt-1" />
                      <div>
                        <h3 className="font-semibold text-white">{event.description}</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {format(new Date(event.timestamp), "PPp")}
                        </p>
                        {event.details.content && (
                          <div className="mt-3 p-4 bg-black/60 rounded text-sm font-mono text-muted-foreground whitespace-pre-wrap border border-white/10">
                            {event.details.content as string}
                          </div>
                        )}
                      </div>
                    </div>
                    <Badge variant="destructive">
                      {event.severity.toUpperCase()}
                    </Badge>
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <StatusChip status="flagged" label="Auto-Indexed" size="sm" />
                    <span className="text-xs text-muted-foreground self-center">Knowledge Base Updated Successfully</span>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Empty State */}
          {driftEvents.length === 0 && (
            <div className="text-center py-12">
              <Shield className="h-12 w-12 mx-auto text-success mb-4" />
              <h3 className="text-lg font-semibold">
                No active policy drift detected
              </h3>
              <p className="text-muted-foreground">
                {isMonitoring
                  ? "Monitoring live backend behavior"
                  : "Monitoring paused"}
              </p>
              {lastChecked && (
                <p className="text-xs text-muted-foreground mt-2">
                  Last checked: {format(new Date(lastChecked), "PPp")}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
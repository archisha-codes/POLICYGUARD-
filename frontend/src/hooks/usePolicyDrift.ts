import { useState, useEffect, useCallback } from "react";
import { fetchTransactions, checkDrift } from "@/services/api";
import { useToast } from "@/components/ui/use-toast";

export interface DriftEvent {
  id: string;
  type: "regulatory_update";
  description: string;
  severity: "high" | "medium" | "low";
  timestamp: string;
  details: Record<string, unknown>;
}

export const usePolicyDrift = () => {
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [pollingInterval, setPollingInterval] = useState(10000); // 10 seconds
  const [lastChecked, setLastChecked] = useState<string>(new Date().toISOString());
  const [totalTransactionsAnalyzed, setTotalTransactionsAnalyzed] = useState<number>(0);
  
  const { toast } = useToast();

  // --- Backend Drift Check (Simulation or Real) ---
  const checkForRegulatoryUpdates = useCallback(async (simulate: boolean = false) => {
    try {
      setLastChecked(new Date().toISOString());
      const result = await checkDrift(simulate);
      
      // Handle the backend payload format based on policy_drift_detector.py
      if (result && (result.status === "active" || result.drift_detected)) {
        
        // Handle different possible backend response structures safely
        const driftId = result.drift_id || `reg-update-${Date.now()}`;
        
        // Prevent duplicate events
        setDriftEvents(prev => {
          if (prev.some(event => event.id === driftId)) return prev;

          const newEvent: DriftEvent = {
            id: driftId,
            type: "regulatory_update",
            description: result.message || "New Regulatory Amendment Detected",
            severity: "high",
            timestamp: new Date().toISOString(),
            details: {
              content: result.details || result.diff || "Detailed amendment content not provided.",
            }
          };
          return [newEvent, ...prev].slice(0, 50); // Keep last 50
        });
        
        if (simulate) {
          toast({
            title: "Simulation Complete",
            description: "Injected regulatory update from backend.",
          });
        }
      } else if (simulate) {
         toast({
            title: "No Drift Detected",
            description: "Backend policies are up to date.",
          });
      }

      // Update total transactions for the UI stats
      const txns = await fetchTransactions(1);
      if (txns && txns.length > 0) {
        // If your backend supports returning count, use it. Otherwise, this is a placeholder.
        setTotalTransactionsAnalyzed(prev => prev > 0 ? prev : 15000); 
      }

    } catch (error) {
      console.error("Failed to check drift:", error);
      if (simulate) {
        toast({
          title: "Simulation Failed",
          description: "Could not contact backend drift detector.",
          variant: "destructive"
        });
      }
    }
  }, [toast]);

  useEffect(() => {
    if (!isMonitoring) return;
    const interval = setInterval(() => checkForRegulatoryUpdates(false), pollingInterval);
    return () => clearInterval(interval);
  }, [checkForRegulatoryUpdates, isMonitoring, pollingInterval]);

  // Initial load
  useEffect(() => {
    checkForRegulatoryUpdates(false);
  }, [checkForRegulatoryUpdates]);

  return {
    driftEvents,
    isMonitoring,
    setIsMonitoring,
    pollingInterval,
    setPollingInterval,
    reload: () => checkForRegulatoryUpdates(false),
    simulateDrift: () => checkForRegulatoryUpdates(true), 
    lastChecked,
    totalTransactionsAnalyzed,
  };
};
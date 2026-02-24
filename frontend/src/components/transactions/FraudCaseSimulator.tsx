import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { NeonButton } from "@/components/ui/NeonButton";
import { Loader2, DollarSign, AlertTriangle, Shield } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  fetchTransactions, 
  analyzeTransaction,
} from "@/services/api";
import { ApiTransaction } from "@/types/api";

interface FraudCaseSimulatorProps {
  onSimulationComplete: () => void;
  onBalanceUpdate?: (balance: number) => void;
}

export function FraudCaseSimulator({ onSimulationComplete, onBalanceUpdate }: FraudCaseSimulatorProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cases, setCases] = useState<ApiTransaction[] | null>(null);
  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  
  const { toast } = useToast();
  const navigate = useNavigate();

  // Load cases when dialog opens
  useEffect(() => {
    if (open && !cases) {
      loadCases();
    }
  }, [open]);

  const loadCases = async () => {
    try {
      // Fetch recent transactions from the database to use as cases
      const data = await fetchTransactions(12, 0);
      setCases(data);
    } catch (error) {
      console.error("Failed to load cases:", error);
    }
  };

  const handleSimulate = async (txn: ApiTransaction) => {
    setLoading(true);
    setSelectedCase(txn.transaction_id);
    
    // Generate a new ID for the simulated event
    const simTxnId = `SIM_${Date.now()}_${txn.transaction_id.substring(0, 5)}`;
    
    try {
      // Send the transaction to the AI Analyze endpoint to simulate fraud analysis
      // Appending "LAUNDERING" triggers the deterministic rule engine to flag it
      const data = await analyzeTransaction({
        transaction_id: simTxnId,
        amount: txn.amount,
        currency: txn.currency,
        description: `SIMULATED LAUNDERING: ${txn.description || 'Routine Check'}`,
        transaction_type: txn.transaction_type || "transfer",
        customer_id: txn.customer_id || "sim_user",
        source_account: txn.source_account || "unknown",
        destination_account: txn.destination_account || "unknown",
        simulation: true
      });

      if (data && data.new_balance !== undefined) {
        if (onBalanceUpdate) {
          onBalanceUpdate(data.new_balance);
        }
      }

      toast({
        title: "Flagged Cases",
        description: `Simulated transaction: ${txn.description || 'Transaction processed'}`,
        variant: "default",
      });

      // Trigger parent refresh
      onSimulationComplete();
      setOpen(false);

      // Redirect to alerts page and focus the targeted transaction
      navigate(`/alerts?txnId=${simTxnId}`);
    } catch (error) {
      console.error("Simulation Error:", error);
      toast({
        title: "Simulation Failed",
        description: "Could not simulate the fraud case.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setSelectedCase(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <NeonButton variant="primary" size="sm" className="gap-2">
          <AlertTriangle className="h-4 w-4" />
          Flagged Cases
        </NeonButton>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl bg-black/95 border-primary/20 text-white backdrop-blur-xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-glow text-xl">Flagged Cases</DialogTitle>
        </DialogHeader>
        
        {!cases ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : cases.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No transactions found in the database to simulate.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 py-4">
            {cases.map((caseData) => {
              const isDebit = caseData.transaction_type?.toUpperCase() === "DEBIT" || caseData.transaction_type?.toLowerCase() === "withdrawal";
              
              return (
                <button 
                  key={caseData.transaction_id}
                  disabled={loading}
                  onClick={() => handleSimulate(caseData)}
                  className={`flex items-start gap-3 p-3 rounded-lg border transition-all group text-left ${
                    isDebit 
                      ? "border-red-500/30 bg-red-500/5 hover:bg-red-500/15" 
                      : "border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/15"
                  }`}
                >
                  <div className={`p-2 rounded-full flex-shrink-0 ${
                    isDebit ? "bg-red-500/20 text-red-500" : "bg-blue-500/20 text-blue-500"
                  }`}>
                    {loading && selectedCase === caseData.transaction_id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Shield className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <div className="flex justify-between items-start">
                      <h4 className="font-semibold text-white truncate pr-2">
                        {caseData.transaction_id.substring(0, 8)}...
                      </h4>
                      <span className={`text-xs px-2 py-0.5 rounded flex-shrink-0 ${
                        isDebit ? "bg-red-500/20 text-red-400" : "bg-blue-500/20 text-blue-400"
                      }`}>
                        {caseData.transaction_type?.toUpperCase() || "UNKNOWN"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                      {caseData.description || "No description"}
                    </p>
                    <div className="flex items-center gap-1 mt-2 text-sm font-medium">
                      <DollarSign className="h-3 w-3" />
                      <span>{caseData.amount.toLocaleString()} {caseData.currency || 'USD'}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
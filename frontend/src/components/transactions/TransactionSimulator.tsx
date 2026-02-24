import { useState } from "react";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { NeonButton } from "@/components/ui/NeonButton";
import { PlayCircle, ShieldCheck, AlertTriangle, Loader2, Eye, Skull } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { simulateTraffic } from "@/services/api";

interface TransactionSimulatorProps {
  onSimulationComplete: () => void;
}

// Define valid scenario types to match Backend TrafficGenerator
type SimulationScenario = "compliant" | "non_compliant" | "flagged" | "escalated";

export function TransactionSimulator({ onSimulationComplete }: TransactionSimulatorProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSimulate = async (scenario: SimulationScenario) => {
    setLoading(true);
    try {
      // Call traffic simulation via api service - now deterministic
      const data = await simulateTraffic(scenario);

      if (data) {
        toast({
          title: "Simulation Injected",
          description: `Generated a ${scenario.replace("_", " ")} transaction.`,
          variant: scenario === "compliant" ? "default" : "destructive",
        });
        onSimulationComplete();
        setOpen(false);
      } else {
        throw new Error("Simulation failed");
      }
    } catch (error) {
      console.error("Simulation Error:", error);
      toast({
        title: "Simulation Failed",
        description: "Could not inject transaction. Check authentication.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <NeonButton variant="primary" size="sm" className="gap-2">
          <PlayCircle className="h-4 w-4" />
          Simulate Traffic
        </NeonButton>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl bg-black/95 border-primary/20 text-white backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle className="text-glow text-xl">Traffic Simulator</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Inject synthetic transactions into the live database to test policy rules.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
          
          {/* 1. Compliant */}
          <button 
            disabled={loading}
            onClick={() => handleSimulate("compliant")}
            className="flex items-start gap-4 p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-green-500/10 hover:border-green-500/30 transition-all group"
          >
            <div className="p-3 rounded-full bg-green-500/20 text-green-500 group-hover:scale-110 transition-transform">
              {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : <ShieldCheck className="h-6 w-6" />}
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-white group-hover:text-green-400 transition-colors">
                Compliant
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Standard low-risk behavior (Salary, Rent, Groceries).
              </p>
            </div>
          </button>

          {/* 2. Flagged (Suspicious) */}
          <button 
            disabled={loading}
            onClick={() => handleSimulate("flagged")}
            className="flex items-start gap-4 p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-yellow-500/10 hover:border-yellow-500/30 transition-all group"
          >
            <div className="p-3 rounded-full bg-yellow-500/20 text-yellow-500 group-hover:scale-110 transition-transform">
              {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : <Eye className="h-6 w-6" />}
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-white group-hover:text-yellow-400 transition-colors">
                Suspicious (Flagged)
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Patterns like structuring (smurfing) or cash near limits.
              </p>
            </div>
          </button>

          {/* 3. Non-Compliant */}
          <button 
            disabled={loading}
            onClick={() => handleSimulate("non_compliant")}
            className="flex items-start gap-4 p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-orange-500/10 hover:border-orange-500/30 transition-all group"
          >
            <div className="p-3 rounded-full bg-orange-500/20 text-orange-500 group-hover:scale-110 transition-transform">
              {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : <AlertTriangle className="h-6 w-6" />}
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-white group-hover:text-orange-400 transition-colors">
                Non-Compliant
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Clear violations like Sanctions hits or specific blocked entities.
              </p>
            </div>
          </button>

          {/* 4. Escalated (Critical) */}
          <button 
            disabled={loading}
            onClick={() => handleSimulate("escalated")}
            className="flex items-start gap-4 p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-red-600/10 hover:border-red-600/30 transition-all group"
          >
            <div className="p-3 rounded-full bg-red-600/20 text-red-600 group-hover:scale-110 transition-transform">
              {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : <Skull className="h-6 w-6" />}
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-white group-hover:text-red-500 transition-colors">
                Critical (Escalated)
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Major threats: Terror financing, Dark web, Shell companies.
              </p>
            </div>
          </button>

        </div>
      </DialogContent>
    </Dialog>
  );
}

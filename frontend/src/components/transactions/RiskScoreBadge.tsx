import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface RiskScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function RiskScoreBadge({ score, size = "md", showLabel = true }: RiskScoreBadgeProps) {
  const getRiskLevel = (score: number) => {
    if (score >= 75) return { level: "Critical", color: "text-destructive", bg: "bg-destructive/20", border: "border-destructive/50", glow: "shadow-[0_0_10px_hsl(var(--destructive)/0.5)]" };
    if (score >= 50) return { level: "High", color: "text-warning", bg: "bg-warning/20", border: "border-warning/50", glow: "shadow-[0_0_10px_hsl(var(--warning)/0.5)]" };
    if (score >= 25) return { level: "Medium", color: "text-accent", bg: "bg-accent/20", border: "border-accent/50", glow: "shadow-[0_0_10px_hsl(var(--accent)/0.5)]" };
    return { level: "Low", color: "text-success", bg: "bg-success/20", border: "border-success/50", glow: "shadow-[0_0_10px_hsl(var(--success)/0.5)]" };
  };

  const risk = getRiskLevel(score);

  const sizeClasses = {
    sm: "w-10 h-10 text-xs",
    md: "w-14 h-14 text-sm",
    lg: "w-18 h-18 text-base",
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <motion.div
        className={cn(
          "relative rounded-full flex items-center justify-center font-bold border-2",
          sizeClasses[size],
          risk.bg,
          risk.border,
          risk.color,
          risk.glow
        )}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        {/* Animated ring */}
        <svg className="absolute inset-0 w-full h-full -rotate-90">
          <motion.circle
            cx="50%"
            cy="50%"
            r="45%"
            fill="none"
            strokeWidth="3"
            stroke="currentColor"
            strokeLinecap="round"
            strokeDasharray={`${score * 2.83} 283`}
            initial={{ strokeDasharray: "0 283" }}
            animate={{ strokeDasharray: `${score * 2.83} 283` }}
            transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
            className="opacity-60"
          />
        </svg>
        <span className="relative z-10">{score}</span>
      </motion.div>
      {showLabel && (
        <motion.span
          className={cn("text-xs font-medium", risk.color)}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          {risk.level}
        </motion.span>
      )}
    </div>
  );
}

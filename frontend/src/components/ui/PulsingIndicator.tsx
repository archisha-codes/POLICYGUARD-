import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface PulsingIndicatorProps {
  status?: "online" | "warning" | "error" | "idle";
  size?: "sm" | "md" | "lg";
  label?: string;
  className?: string;
}

const statusColors = {
  online: "bg-success",
  warning: "bg-warning",
  error: "bg-destructive",
  idle: "bg-muted-foreground",
};

const sizeStyles = {
  sm: "h-2 w-2",
  md: "h-3 w-3",
  lg: "h-4 w-4",
};

export function PulsingIndicator({
  status = "online",
  size = "md",
  label,
  className,
}: PulsingIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="relative flex">
        <motion.span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75",
            statusColors[status]
          )}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.75, 0, 0.75],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <span
          className={cn(
            "relative inline-flex rounded-full",
            statusColors[status],
            sizeStyles[size]
          )}
        />
      </span>
      {label && (
        <span className="text-sm text-muted-foreground">{label}</span>
      )}
    </div>
  );
}

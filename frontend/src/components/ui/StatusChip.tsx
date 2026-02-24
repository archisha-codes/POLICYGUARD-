import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { CheckCircle, AlertTriangle, Clock, XCircle, Play, Pause } from "lucide-react";
import React from "react";

type StatusType = "approved" | "flagged" | "pending" | "rejected" | "live" | "paused";

interface StatusChipProps {
  status: StatusType;
  label?: string;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  icon?: React.ReactNode; // Added to support custom icon overrides
}

const statusConfig = {
  approved: {
    className: "status-approved",
    icon: CheckCircle,
    label: "Approved",
  },
  flagged: {
    className: "status-flagged",
    icon: AlertTriangle,
    label: "Flagged",
  },
  pending: {
    className: "status-pending",
    icon: Clock,
    label: "Pending",
  },
  rejected: {
    className: "bg-destructive/20 text-destructive border border-destructive/30",
    icon: XCircle,
    label: "Rejected",
  },
  live: {
    className: "bg-green-500/20 text-green-400 border-green-500/30",
    icon: Play,
    label: "Live",
  },
  paused: {
    className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    icon: Pause,
    label: "Paused",
  },
};

const sizeConfig = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-1.5 text-base",
};

export function StatusChip({
  status,
  label,
  showIcon = true,
  size = "md",
  pulse = false,
  icon: customIcon,
}: StatusChipProps) {
  const config = statusConfig[status] || statusConfig["pending"];
  const Icon = config.icon;

  return (
    <motion.span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium",
        config.className,
        sizeConfig[size],
        pulse && "animate-pulse"
      )}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {showIcon && (
        customIcon ? (
          <span className={cn(
             "shrink-0 flex items-center justify-center",
             size === "sm" && "h-3 w-3",
             size === "md" && "h-4 w-4",
             size === "lg" && "h-5 w-5"
          )}>
            {customIcon}
          </span>
        ) : (
          <Icon className={cn(
            "shrink-0",
            size === "sm" && "h-3 w-3",
            size === "md" && "h-4 w-4",
            size === "lg" && "h-5 w-5"
          )} />
        )
      )}
      {label || config.label}
    </motion.span>
  );
}

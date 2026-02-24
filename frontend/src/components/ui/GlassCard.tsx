import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import { forwardRef } from "react";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  glowColor?: "primary" | "secondary" | "success" | "warning" | "destructive";
  hoverLift?: boolean;
  pulse?: boolean;
}

const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, glowColor = "primary", hoverLift = true, pulse = false, children, ...props }, ref) => {
    const glowStyles = {
      primary: "hover:shadow-[0_0_30px_-5px_hsl(var(--primary)/0.5)]",
      secondary: "hover:shadow-[0_0_30px_-5px_hsl(var(--secondary)/0.5)]",
      success: "hover:shadow-[0_0_30px_-5px_hsl(var(--success)/0.5)]",
      warning: "hover:shadow-[0_0_30px_-5px_hsl(var(--warning)/0.5)]",
      destructive: "hover:shadow-[0_0_30px_-5px_hsl(var(--destructive)/0.5)]",
    };

    return (
      <motion.div
        ref={ref}
        className={cn(
          "glass-card p-6 transition-all duration-300",
          hoverLift && "hover:-translate-y-1",
          glowStyles[glowColor],
          pulse && "animate-glow-pulse",
          className
        )}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

GlassCard.displayName = "GlassCard";

export { GlassCard };

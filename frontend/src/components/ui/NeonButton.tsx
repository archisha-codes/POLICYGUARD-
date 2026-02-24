import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { forwardRef, ReactNode } from "react";
import { Loader2 } from "lucide-react";

interface NeonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  glowIntensity?: "low" | "medium" | "high";
  loading?: boolean;
  children?: ReactNode;
}

const NeonButton = forwardRef<HTMLButtonElement, NeonButtonProps>(
  ({ 
    className, 
    variant = "primary", 
    size = "md", 
    glowIntensity = "medium",
    loading = false,
    children, 
    disabled,
    ...props 
  }, ref) => {
    const variants = {
      primary: cn(
        "bg-primary text-primary-foreground",
        "hover:bg-primary/90",
        glowIntensity === "low" && "hover:shadow-[0_0_15px_hsl(var(--primary)/0.3)]",
        glowIntensity === "medium" && "hover:shadow-[0_0_25px_hsl(var(--primary)/0.5)]",
        glowIntensity === "high" && "hover:shadow-[0_0_35px_hsl(var(--primary)/0.7)]"
      ),
      secondary: cn(
        "bg-secondary text-secondary-foreground",
        "hover:bg-secondary/90",
        glowIntensity === "low" && "hover:shadow-[0_0_15px_hsl(var(--secondary)/0.3)]",
        glowIntensity === "medium" && "hover:shadow-[0_0_25px_hsl(var(--secondary)/0.5)]",
        glowIntensity === "high" && "hover:shadow-[0_0_35px_hsl(var(--secondary)/0.7)]"
      ),
      outline: cn(
        "border-2 border-primary bg-transparent text-primary",
        "hover:bg-primary/10",
        glowIntensity === "low" && "hover:shadow-[0_0_15px_hsl(var(--primary)/0.2)]",
        glowIntensity === "medium" && "hover:shadow-[0_0_25px_hsl(var(--primary)/0.3)]",
        glowIntensity === "high" && "hover:shadow-[0_0_35px_hsl(var(--primary)/0.5)]"
      ),
      ghost: cn(
        "bg-transparent text-foreground",
        "hover:bg-muted/50 hover:text-primary"
      ),
      destructive: cn(
        "bg-destructive text-destructive-foreground",
        "hover:bg-destructive/90",
        glowIntensity === "low" && "hover:shadow-[0_0_15px_hsl(var(--destructive)/0.3)]",
        glowIntensity === "medium" && "hover:shadow-[0_0_25px_hsl(var(--destructive)/0.5)]",
        glowIntensity === "high" && "hover:shadow-[0_0_35px_hsl(var(--destructive)/0.7)]"
      ),
    };

    const sizes = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-5 py-2.5 text-base",
      lg: "px-7 py-3.5 text-lg",
    };

    return (
      <motion.button
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center gap-2 font-medium",
          "rounded-lg transition-all duration-300",
          "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none",
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled || loading}
        whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
        whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
        {...(props as any)}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </motion.button>
    );
  }
);

NeonButton.displayName = "NeonButton";

export { NeonButton };

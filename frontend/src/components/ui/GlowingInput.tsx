import { forwardRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Eye, EyeOff, AlertCircle, CheckCircle } from "lucide-react";

interface GlowingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  success?: boolean;
  showPasswordToggle?: boolean;
}

const GlowingInput = forwardRef<HTMLInputElement, GlowingInputProps>(
  ({ className, label, error, success, type, showPasswordToggle, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const inputType = showPasswordToggle && type === "password" 
      ? (showPassword ? "text" : "password") 
      : type;

    return (
      <div className="space-y-2">
        {label && (
          <motion.label 
            className={cn(
              "block text-sm font-medium transition-colors duration-200",
              isFocused ? "text-primary" : "text-muted-foreground",
              error && "text-destructive"
            )}
            animate={{ 
              color: error ? "hsl(var(--destructive))" : isFocused ? "hsl(var(--primary))" : "hsl(var(--muted-foreground))" 
            }}
          >
            {label}
          </motion.label>
        )}
        <div className="relative">
          <motion.div
            className={cn(
              "absolute inset-0 rounded-lg opacity-0 transition-opacity duration-300",
              error 
                ? "shadow-[0_0_20px_hsl(var(--destructive)/0.5)]" 
                : success 
                  ? "shadow-[0_0_20px_hsl(var(--success)/0.5)]"
                  : "shadow-[0_0_20px_hsl(var(--primary)/0.5)]"
            )}
            animate={{ 
              opacity: isFocused ? 1 : 0 
            }}
          />
          <input
            ref={ref}
            type={inputType}
            className={cn(
              "relative w-full rounded-lg border bg-input px-4 py-3",
              "text-foreground placeholder:text-muted-foreground",
              "transition-all duration-300",
              "focus:outline-none focus:ring-0",
              error 
                ? "border-destructive" 
                : success 
                  ? "border-success"
                  : isFocused 
                    ? "border-primary" 
                    : "border-border",
              showPasswordToggle && "pr-12",
              className
            )}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            {...props}
          />
          {showPasswordToggle && type === "password" && (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          )}
          {success && !error && (
            <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-success" />
          )}
        </div>
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: -10, height: 0 }}
              className="flex items-center gap-1.5 text-sm text-destructive"
            >
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

GlowingInput.displayName = "GlowingInput";

export { GlowingInput };

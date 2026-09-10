import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Check, X } from "lucide-react";

interface PasswordStrengthMeterProps {
  password: string;
}

interface PasswordRequirement {
  label: string;
  test: (password: string) => boolean;
}

const requirements: PasswordRequirement[] = [
  { label: "At least 8 characters", test: (p) => p.length >= 8 },
  { label: "One uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { label: "One lowercase letter", test: (p) => /[a-z]/.test(p) },
  { label: "One number", test: (p) => /[0-9]/.test(p) },
  { label: "One special character", test: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
];

export function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  const passedRequirements = requirements.filter((req) => req.test(password)).length;
  const strength = (passedRequirements / requirements.length) * 100;

  const getStrengthColor = () => {
    if (strength <= 20) return "bg-destructive";
    if (strength <= 40) return "bg-destructive/70";
    if (strength <= 60) return "bg-warning";
    if (strength <= 80) return "bg-warning/70";
    return "bg-success";
  };

  const getStrengthLabel = () => {
    if (strength <= 20) return "Very Weak";
    if (strength <= 40) return "Weak";
    if (strength <= 60) return "Fair";
    if (strength <= 80) return "Strong";
    return "Very Strong";
  };

  const getGlowColor = () => {
    if (strength <= 40) return "shadow-[0_0_10px_hsl(var(--destructive)/0.5)]";
    if (strength <= 60) return "shadow-[0_0_10px_hsl(var(--warning)/0.5)]";
    return "shadow-[0_0_10px_hsl(var(--success)/0.5)]";
  };

  return (
    <div className="space-y-3">
      {/* Strength Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">Password Strength</span>
          <motion.span
            key={getStrengthLabel()}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "font-medium",
              strength <= 40 && "text-destructive",
              strength > 40 && strength <= 60 && "text-warning",
              strength > 60 && "text-success"
            )}
          >
            {getStrengthLabel()}
          </motion.span>
        </div>
        <div className={cn("h-2 w-full rounded-full bg-muted overflow-hidden", getGlowColor())}>
          <motion.div
            className={cn("h-full rounded-full transition-colors", getStrengthColor())}
            initial={{ width: 0 }}
            animate={{ width: `${strength}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Requirements List */}
      <div className="grid grid-cols-1 gap-1.5">
        {requirements.map((req, index) => {
          const passed = req.test(password);
          return (
            <motion.div
              key={req.label}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "flex items-center gap-2 text-xs transition-colors",
                passed ? "text-success" : "text-muted-foreground"
              )}
            >
              <motion.div
                initial={false}
                animate={{ scale: passed ? [1.2, 1] : 1 }}
                transition={{ duration: 0.2 }}
              >
                {passed ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <X className="h-3.5 w-3.5" />
                )}
              </motion.div>
              <span>{req.label}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

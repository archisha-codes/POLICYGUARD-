import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Shield, Eye, Briefcase, Crown } from "lucide-react";

type AppRole = "admin" | "compliance_officer" | "auditor" | "manager";

interface RoleSelectorProps {
  value: AppRole;
  onChange: (role: AppRole) => void;
}

const roles: { value: AppRole; label: string; description: string; icon: typeof Shield }[] = [
  {
    value: "compliance_officer",
    label: "Compliance Officer",
    description: "Monitor transactions & enforce policies",
    icon: Shield,
  },
  {
    value: "auditor",
    label: "Auditor",
    description: "Review decisions & audit trails",
    icon: Eye,
  },
  {
    value: "manager",
    label: "Manager",
    description: "Oversee team & approve overrides",
    icon: Briefcase,
  },
  {
    value: "admin",
    label: "Admin",
    description: "Full system access & configuration",
    icon: Crown,
  },
];

export function RoleSelector({ value, onChange }: RoleSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-muted-foreground">
        Select Your Role
      </label>
      <div className="grid grid-cols-2 gap-3">
        {roles.map((role, index) => {
          const isSelected = value === role.value;
          const Icon = role.icon;
          
          return (
            <motion.button
              key={role.value}
              type="button"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onChange(role.value)}
              className={cn(
                "relative p-4 rounded-lg border text-left transition-all duration-300",
                "hover:border-primary/50",
                isSelected
                  ? "border-primary bg-primary/10 shadow-[0_0_15px_hsl(var(--primary)/0.3)]"
                  : "border-border bg-card/50"
              )}
            >
              {/* Selection indicator */}
              <motion.div
                className="absolute top-2 right-2 h-3 w-3 rounded-full bg-primary"
                initial={false}
                animate={{
                  scale: isSelected ? 1 : 0,
                  opacity: isSelected ? 1 : 0,
                }}
                transition={{ duration: 0.2 }}
              />

              <div className="flex flex-col gap-2">
                <div
                  className={cn(
                    "h-10 w-10 rounded-lg flex items-center justify-center transition-colors",
                    isSelected ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <h4
                    className={cn(
                      "font-medium text-sm transition-colors",
                      isSelected ? "text-primary" : "text-foreground"
                    )}
                  >
                    {role.label}
                  </h4>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                    {role.description}
                  </p>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

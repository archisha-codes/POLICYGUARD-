// frontend/src/pages/Auth.tsx

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { z } from "zod";
import { Shield, ArrowRight, Loader2, Sparkles } from "lucide-react";

import { GlowingInput } from "@/components/ui/GlowingInput";
import { NeonButton } from "@/components/ui/NeonButton";
import { PasswordStrengthMeter } from "@/components/auth/PasswordStrengthMeter";
import { RoleSelector } from "@/components/auth/RoleSelector";
import { ParticleBackground } from "@/components/layout/ParticleBackground";

// Since we fixed hooks/useAuth.tsx to export * from Context, this works:
import { useAuth } from "@/hooks/useAuth"; 
import { cn } from "@/lib/utils";

type AppRole = "admin" | "compliance_officer" | "auditor" | "manager";

/* =========================
   VALIDATION SCHEMAS
========================= */
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

const signupSchema = z
  .object({
    displayName: z.string().min(2),
    email: z.string().email(),
    password: z.string().min(8),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match",
  });

/* =========================
   COMPONENT
========================= */
export default function Auth() {
  const navigate = useNavigate();
  // 'login' is now recognized because AuthContextType includes it
  const { user, loading: authLoading, login } = useAuth();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shake, setShake] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<AppRole>("compliance_officer");

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!authLoading && user) {
      navigate("/dashboard");
    }
  }, [authLoading, user, navigate]);

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 400);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});

    const schema = mode === "login" ? loginSchema : signupSchema;
    const result = schema.safeParse(
      mode === "login"
        ? { email, password }
        : { displayName, email, password, confirmPassword }
    );

    if (!result.success) {
      const errs: Record<string, string> = {};
      result.error.errors.forEach((e) => {
        if (e.path[0]) errs[String(e.path[0])] = e.message;
      });
      setFieldErrors(errs);
      triggerShake();
      return;
    }

    try {
      setLoading(true);
      await login(email, role); 
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Authentication failed");
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <ParticleBackground />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{
          opacity: 1,
          y: 0,
          x: shake ? [0, -10, 10, -10, 10, 0] : 0,
        }}
        className="relative w-full max-w-md mx-4"
      >
        <div className="glass-card p-8">
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">PolicyGuard</h1>
              <p className="text-xs text-muted-foreground">
                AI Compliance Co-Pilot
              </p>
            </div>
          </div>

          <div className="flex bg-muted/50 p-1 rounded-lg mb-6">
            {["login", "signup"].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m as any)}
                className={cn(
                  "flex-1 py-2 text-sm rounded-md transition",
                  mode === m && "bg-primary text-primary-foreground"
                )}
              >
                {m === "login" ? "Sign In" : "Sign Up"}
              </button>
            ))}
          </div>

          <AnimatePresence>
            {error && (
              <div className="text-destructive text-sm mb-4">{error}</div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "signup" && (
              <GlowingInput
                label="Name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            )}
            
            <RoleSelector value={role} onChange={setRole} />

            <GlowingInput
              label="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <GlowingInput
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {mode === "signup" && (
              <>
                <GlowingInput
                  label="Confirm Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                <PasswordStrengthMeter password={password} />
              </>
            )}

            <NeonButton type="submit" loading={loading} className="w-full">
              {mode === "login" ? (
                <>
                  Sign In <ArrowRight className="h-4 w-4" />
                </>
              ) : (
                <>
                  Create Account <Sparkles className="h-4 w-4" />
                </>
              )}
            </NeonButton>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
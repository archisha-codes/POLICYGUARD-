import { motion } from "framer-motion";
import { NeonButton } from "@/components/ui/NeonButton";
import { Shield, Sparkles, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 py-20">
      {/* Animated gradient background */}
      <div className="absolute inset-0 animated-gradient opacity-50" />
      
      {/* Grid overlay */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto text-center">
        {/* Floating badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-8"
        >
          <Sparkles className="h-4 w-4 text-primary animate-pulse" />
          <span className="text-sm font-medium text-muted-foreground">
            AI-Powered Compliance Intelligence
          </span>
        </motion.div>

        {/* Main headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl md:text-6xl lg:text-7xl font-display font-bold mb-6 leading-tight"
        >
          <span className="text-foreground">Real-Time.</span>{" "}
          <span className="text-gradient-primary">Explainable.</span>
          <br />
          <span className="neon-text">Regulator-Ready</span>{" "}
          <span className="text-foreground">Compliance.</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
        >
          PolicyGuard uses advanced AI to monitor transactions, detect policy drift, 
          and provide crystal-clear audit trails—all in real-time.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <NeonButton
            size="lg"
            variant="primary"
            glowIntensity="high"
            onClick={() => navigate("/dashboard")}
          >
            <Shield className="h-5 w-5" />
            Launch Dashboard
            <ArrowRight className="h-5 w-5" />
          </NeonButton>
          <NeonButton
            size="lg"
            variant="outline"
            glowIntensity="medium"
            onClick={() => navigate("/auth")}
          >
            Request Demo
          </NeonButton>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="grid grid-cols-3 gap-8 mt-16 pt-8 border-t border-border/50"
        >
          {[
            { value: "99.9%", label: "Accuracy Rate" },
            { value: "<50ms", label: "Decision Latency" },
            { value: "500+", label: "Regulations Covered" },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-2xl md:text-4xl font-display font-bold text-primary mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Floating shield icon */}
      <motion.div
        className="absolute right-10 top-1/3 hidden lg:block"
        animate={{ y: [0, -20, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
          <Shield className="h-32 w-32 text-primary/30" />
        </div>
      </motion.div>
    </section>
  );
}

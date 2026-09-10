import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/GlassCard";
import { 
  Zap, 
  Brain, 
  AlertTriangle, 
  Users, 
  Lock, 
  Globe 
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Real-Time Monitoring",
    description: "Process thousands of transactions per second with instant compliance decisions and zero latency.",
    color: "primary" as const,
  },
  {
    icon: Brain,
    title: "Explainable AI",
    description: "Every decision comes with human-readable explanations, regulation citations, and confidence scores.",
    color: "secondary" as const,
  },
  {
    icon: AlertTriangle,
    title: "Policy Drift Detection",
    description: "Automatically detect when regulatory changes impact your compliance posture and get instant alerts.",
    color: "warning" as const,
  },
  {
    icon: Users,
    title: "Human-in-the-Loop",
    description: "AI augments your team with smart escalation paths and override capabilities for edge cases.",
    color: "success" as const,
  },
  {
    icon: Lock,
    title: "Privacy-First Design",
    description: "PII masking, zero-knowledge proofs, and bank-grade encryption protect sensitive data.",
    color: "primary" as const,
  },
  {
    icon: Globe,
    title: "Multi-Regulation Support",
    description: "RBI, AML, KYC, GDPR, and 500+ regulatory frameworks in a single unified platform.",
    color: "secondary" as const,
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

export function FeaturesSection() {
  return (
    <section className="relative py-24 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">
            Enterprise-Grade{" "}
            <span className="text-gradient-primary">AI Compliance</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Built for the world's most demanding financial institutions, 
            designed to make compliance seamless.
          </p>
        </motion.div>

        {/* Features grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div key={index} variants={itemVariants}>
              <GlassCard
                glowColor={feature.color}
                className="h-full"
              >
                <div className="flex flex-col h-full">
                  <div className={`
                    inline-flex items-center justify-center w-12 h-12 rounded-lg mb-4
                    ${feature.color === 'primary' ? 'bg-primary/20 text-primary' : ''}
                    ${feature.color === 'secondary' ? 'bg-secondary/20 text-secondary' : ''}
                    ${feature.color === 'warning' ? 'bg-warning/20 text-warning' : ''}
                    ${feature.color === 'success' ? 'bg-success/20 text-success' : ''}
                  `}>
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

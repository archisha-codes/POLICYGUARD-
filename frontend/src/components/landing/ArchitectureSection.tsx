import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/GlassCard";
import { 
  CreditCard, 
  FileText, 
  Brain, 
  ClipboardCheck, 
  Bell,
  ArrowRight
} from "lucide-react";

const steps = [
  {
    icon: CreditCard,
    title: "Transaction",
    description: "Real-time ingestion",
    color: "primary",
  },
  {
    icon: FileText,
    title: "Rules Engine",
    description: "Policy matching",
    color: "secondary",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    description: "Risk assessment",
    color: "primary",
  },
  {
    icon: ClipboardCheck,
    title: "Audit Trail",
    description: "Immutable logging",
    color: "success",
  },
  {
    icon: Bell,
    title: "Alerts",
    description: "Smart notifications",
    color: "warning",
  },
];

export function ArchitectureSection() {
  return (
    <section className="relative py-24 px-4 overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 blur-[120px] rounded-full" />
      
      <div className="relative max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">
            How{" "}
            <span className="text-gradient-primary">PolicyGuard</span>
            {" "}Works
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A seamless flow from transaction to decision, with full transparency at every step.
          </p>
        </motion.div>

        {/* Architecture flow */}
        <div className="relative">
          {/* Connection line */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-primary/50 via-secondary/50 to-primary/50 hidden lg:block" />

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 lg:gap-4">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                <GlassCard
                  glowColor={step.color as any}
                  className="text-center relative z-10"
                >
                  <motion.div
                    className={`
                      mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4
                      ${step.color === 'primary' ? 'bg-primary/20 text-primary' : ''}
                      ${step.color === 'secondary' ? 'bg-secondary/20 text-secondary' : ''}
                      ${step.color === 'success' ? 'bg-success/20 text-success' : ''}
                      ${step.color === 'warning' ? 'bg-warning/20 text-warning' : ''}
                    `}
                    animate={{ 
                      boxShadow: [
                        `0 0 20px hsl(var(--${step.color}) / 0.3)`,
                        `0 0 40px hsl(var(--${step.color}) / 0.5)`,
                        `0 0 20px hsl(var(--${step.color}) / 0.3)`,
                      ]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <step.icon className="h-8 w-8" />
                  </motion.div>
                  <h3 className="font-semibold mb-1">{step.title}</h3>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </GlassCard>

                {/* Arrow connector (hidden on last item and mobile) */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:flex absolute -right-2 top-1/2 -translate-y-1/2 z-20">
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <ArrowRight className="h-6 w-6 text-primary" />
                    </motion.div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

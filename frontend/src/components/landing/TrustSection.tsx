import { motion } from "framer-motion";
import { Shield, Eye, Lock, Server } from "lucide-react";

const badges = [
  {
    icon: Shield,
    title: "Real-Time Policy Drift Detection",
    description: "Fastest Ever",
  },
  {
    icon: Eye,
    title: "Zero-Knowledge",
    description: "AI never sees raw PII",
  },
  {
    icon: Lock,
    title: "End-to-End Encryption",
    description: "Bank-grade security",
  },
  {
    icon: Server,
    title: "Zero-Trust Architecture",
    description: "Every request verified",
  },
];

export function TrustSection() {
  return (
    <section className="relative py-24 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
            Built for{" "}
            <span className="text-gradient-primary">Enterprise Trust</span>
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Security and privacy aren't afterthoughts—they're foundational to everything we build.
          </p>
        </motion.div>

        {/* Trust badges */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {badges.map((badge, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="text-center"
            >
              <motion.div
                className="mx-auto w-16 h-16 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center mb-4"
                whileHover={{ 
                  scale: 1.1,
                  boxShadow: "0 0 30px hsl(var(--primary) / 0.5)",
                }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <badge.icon className="h-8 w-8 text-primary" />
              </motion.div>
              <h3 className="font-semibold mb-1">{badge.title}</h3>
              <p className="text-sm text-muted-foreground">{badge.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

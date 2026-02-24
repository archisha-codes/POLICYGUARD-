import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { HeroSection } from "@/components/landing/HeroSection";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { ArchitectureSection } from "@/components/landing/ArchitectureSection";
import { TrustSection } from "@/components/landing/TrustSection";
import { ChatWidget } from "@/components/chat/ChatWidget";

export default function Landing() {
  return (
    <div className="relative min-h-screen bg-background">
      <ParticleBackground />
      
      <main className="relative z-10">
        <HeroSection />
        <FeaturesSection />
        <ArchitectureSection />
        <TrustSection />
      </main>

      <ChatWidget />
    </div>
  );
}

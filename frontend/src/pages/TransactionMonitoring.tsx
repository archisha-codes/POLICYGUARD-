// frontend/src/pages/TransactionMonitoring.tsx

import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  RefreshCw,
} from "lucide-react";

import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { TransactionFilters } from "@/components/transactions/TransactionFilters";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { TransactionSimulator } from "@/components/transactions/TransactionSimulator";
import { FraudCaseSimulator } from "@/components/transactions/FraudCaseSimulator";

import { useAuth } from "@/hooks/useAuth";
import { useTransactions } from "@/hooks/useTransactions";

export default function TransactionMonitoring() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  /* =========================
     FILTER STATE
  ========================= */
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState<Date | undefined>();

  const [sortField, setSortField] = useState("created_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  /* =========================
     DATA FETCHING & LOGIC
     (Passed state to hook!)
  ========================= */
  const {
    transactions,
    isLoading,
    stats,
    reload,
  } = useTransactions({
    searchQuery,
    statusFilter,
    riskFilter,
    typeFilter,
    dateFilter,
    sortField,
    sortDirection
  });

  /* =========================
     AUTH GUARD
  ========================= */
  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/auth");
    }
  }, [authLoading, user, navigate]);

  /* =========================
     HANDLERS
  ========================= */
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setStatusFilter("all");
    setRiskFilter("all");
    setTypeFilter("all");
    setDateFilter(undefined);
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
    return `$${amount.toLocaleString()}`;
  };

  /* =========================
     RENDER
  ========================= */
  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-4">
            <NeonButton
              variant="ghost"
              size="sm"
              onClick={() => navigate("/dashboard")}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </NeonButton>

            <div>
              <h1 className="text-2xl md:text-3xl font-display font-bold text-glow">
                Transaction Monitoring
              </h1>
              <p className="text-muted-foreground text-sm">
                Real-time compliance monitoring and risk analysis
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <FraudCaseSimulator onSimulationComplete={reload} />
            <TransactionSimulator onSimulationComplete={reload} />
            <NeonButton
              variant="secondary"
              size="sm"
              className="gap-2"
              onClick={reload}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </NeonButton>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <GlassCard glowColor="primary" className="p-4">
            <div className="text-sm text-muted-foreground mb-1">Total Transactions</div>
            <AnimatedCounter value={stats.total} />
          </GlassCard>

          <GlassCard glowColor="warning" className="p-4">
            <div className="text-sm text-muted-foreground mb-1">Pending Review</div>
            <AnimatedCounter value={stats.pending} />
          </GlassCard>

          <GlassCard glowColor="destructive" className="p-4">
            <div className="text-sm text-muted-foreground mb-1">Flagged / Risky</div>
            <AnimatedCounter value={stats.flagged} />
          </GlassCard>

          <GlassCard glowColor="success" className="p-4">
            <div className="text-sm text-muted-foreground mb-1">Total Volume</div>
            <p className="text-xl font-bold text-success font-mono">
              {formatCurrency(stats.totalAmount)}
            </p>
          </GlassCard>
        </div>

        {/* Filters */}
        <TransactionFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          riskFilter={riskFilter}
          onRiskChange={setRiskFilter}
          typeFilter={typeFilter}
          onTypeChange={setTypeFilter}
          dateFilter={dateFilter}
          onDateChange={setDateFilter}
          onClearFilters={handleClearFilters}
        />

        {/* Table */}
        <div className="mt-6">
           <TransactionTable
            transactions={transactions} // Directly use data from hook
            isLoading={isLoading}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        </div>
      </div>
    </div>
  );
}
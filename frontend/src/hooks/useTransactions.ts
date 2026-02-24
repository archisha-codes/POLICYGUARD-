// frontend/src/hooks/useTransactions.ts

import { useState, useEffect, useCallback } from "react";
import { api } from "../services/api";
import { ApiTransaction, DashboardStats } from "@/types/api";
import { useToast } from "@/components/ui/use-toast";

// Export the interface so the component can use it if needed
export interface UseTransactionsProps {
  searchQuery?: string;
  statusFilter?: string;
  riskFilter?: string;
  typeFilter?: string;
  dateFilter?: Date;
  sortField?: string;
  sortDirection?: "asc" | "desc";
}

export function useTransactions(props: UseTransactionsProps = {}) {
  // Destructure with default values to prevent "undefined" errors
  const {
    searchQuery = "",
    statusFilter = "all",
    riskFilter = "all",
    typeFilter = "all",
    dateFilter,
    sortField = "created_at",
    sortDirection = "desc",
  } = props;

  const [allTransactions, setAllTransactions] = useState<ApiTransaction[]>([]);
  const [displayedTransactions, setDisplayedTransactions] = useState<ApiTransaction[]>([]);
  
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    flagged: 0,
    totalAmount: 0
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // 1. Fetch Data (Only once on mount or reload)
  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    try {
      const [txns, dashboardStats] = await Promise.all([
        api.fetchTransactions(100, 0), // Fetch latest 100
        api.fetchStats()
      ]);

      setAllTransactions(txns);

      // Initialize stats from API + local calculation
      const totalAmt = txns.reduce((sum, t) => sum + (t.amount || 0), 0);
      setStats({
        total: dashboardStats.transactions_today || txns.length,
        pending: dashboardStats.pending_reviews,
        flagged: dashboardStats.active_alerts,
        totalAmount: totalAmt
      });

    } catch (error) {
      console.error("Fetch error:", error);
      toast({
        title: "Error fetching transactions",
        description: "Could not load data from the server.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  // 2. Filter & Sort (Runs whenever filters change or data updates)
  useEffect(() => {
    let result = [...allTransactions];

    // -- Search --
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (t) =>
          t.transaction_id?.toLowerCase().includes(q) ||
          t.customer_name?.toLowerCase().includes(q) ||
          t.customer_id?.toLowerCase().includes(q) ||
          t.amount?.toString().includes(q)
      );
    }

    // -- Status --
    if (statusFilter !== "all") {
      result = result.filter((t) => {
        const s = t.status?.toLowerCase() || "";
        if (statusFilter === "approved") return s === "compliant" || s === "approved";
        if (statusFilter === "rejected") return s === "non_compliant" || s === "rejected";
        return s === statusFilter;
      });
    }

    // -- Risk --
    if (riskFilter !== "all") {
      result = result.filter((t) => {
        const score = t.risk_score || 0;
        if (riskFilter === "low") return score < 25;
        if (riskFilter === "medium") return score >= 25 && score < 50;
        if (riskFilter === "high") return score >= 50 && score < 75;
        if (riskFilter === "critical") return score >= 75;
        return true;
      });
    }

    // -- Type --
    if (typeFilter !== "all") {
      result = result.filter((t) => t.transaction_type?.toLowerCase() === typeFilter.toLowerCase());
    }

    // -- Date --
    if (dateFilter) {
      result = result.filter((t) => {
        const d = new Date(t.created_at);
        return (
          d.getDate() === dateFilter.getDate() &&
          d.getMonth() === dateFilter.getMonth() &&
          d.getFullYear() === dateFilter.getFullYear()
        );
      });
    }

    // -- Sorting --
    result.sort((a, b) => {
      // Cast to any to access dynamic properties safely
      let valA = (a as any)[sortField];
      let valB = (b as any)[sortField];

      // Handle dates specifically
      if (sortField === "created_at") {
        valA = new Date(valA || 0).getTime();
        valB = new Date(valB || 0).getTime();
      }

      // Handle undefined/null safety
      if (valA === undefined) valA = "";
      if (valB === undefined) valB = "";

      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    setDisplayedTransactions(result);

  }, [
    allTransactions, 
    searchQuery, 
    statusFilter, 
    riskFilter, 
    typeFilter, 
    dateFilter, 
    sortField, 
    sortDirection
  ]);

  // Initial fetch on mount
  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  return { 
    transactions: displayedTransactions, 
    isLoading, 
    stats, 
    reload: fetchTransactions 
  };
}
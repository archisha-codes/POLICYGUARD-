// frontend/src/components/transactions/TransactionTable.tsx

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, ArrowUpDown } from "lucide-react";
import { format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusChip } from "@/components/ui/StatusChip";
import { RiskScoreBadge } from "./RiskScoreBadge";
import { TransactionExpandedRow } from "./TransactionExpandedRow";
import { cn } from "@/lib/utils";
import { ApiTransaction } from "@/types/api";

interface TransactionTableProps {
  transactions: ApiTransaction[];
  isLoading: boolean;
  sortField: string;
  sortDirection: "asc" | "desc";
  onSort: (field: string) => void;
}

export function TransactionTable({
  transactions,
  isLoading,
  sortField,
  sortDirection,
  onSort,
}: TransactionTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(amount);
  };

  // Helper to map backend status to StatusChip props
  const getStatusVariant = (status: string): "approved" | "rejected" | "flagged" | "pending" => {
    const s = status ? status.toLowerCase() : '';
    if (s === 'compliant' || s === 'approved') return 'approved';
    if (s === 'non_compliant' || s === 'rejected') return 'rejected';
    if (s === 'flagged') return 'flagged';
    return 'pending';
  };

  const SortableHeader = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 hover:text-primary transition-colors"
    >
      {children}
      {sortField === field ? (
        sortDirection === "asc" ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )
      ) : (
        <ArrowUpDown className="h-3 w-3 opacity-50" />
      )}
    </button>
  );

  if (isLoading) {
    return (
      <div className="glass-card p-8">
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-muted/30" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-muted/30 rounded w-1/4" />
                <div className="h-3 bg-muted/20 rounded w-1/3" />
              </div>
              <div className="h-6 w-20 bg-muted/30 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <motion.div
        className="glass-card p-12 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <p className="text-muted-foreground">No transactions found matching your criteria.</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="glass-card overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Table>
        <TableHeader>
          <TableRow className="border-border/30 hover:bg-transparent">
            <TableHead className="w-[50px]" />
            <TableHead>
              <SortableHeader field="transaction_id">Transaction ID</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="customer_name">Customer</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="amount">Amount</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="transaction_type">Type</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="risk_score">Risk Score</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="status">Status</SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader field="created_at">Date</SortableHeader>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <AnimatePresence>
            {transactions.map((transaction, index) => (
              <React.Fragment key={transaction.transaction_id || `txn-fallback-${index}`}>
                <motion.tr
                  key={transaction.transaction_id || `txn-row-${index}`}
                  className={cn(
                    "border-border/30 cursor-pointer transition-colors",
                    expandedRows.has(transaction.transaction_id)
                      ? "bg-primary/5"
                      : "hover:bg-muted/30"
                  )}
                  onClick={() => toggleRow(transaction.transaction_id)}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  whileHover={{ x: 4 }}
                >
                  <TableCell>
                    <motion.div
                      animate={{ rotate: expandedRows.has(transaction.transaction_id) ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    </motion.div>
                  </TableCell>
                  <TableCell className="font-mono text-sm text-primary">
                    {transaction.transaction_id}
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium text-foreground">{transaction.customer_name || "Unknown"}</p>
                      <p className="text-xs text-muted-foreground">{transaction.customer_id}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className={cn(
                      "font-semibold",
                      transaction.amount >= 50000 ? "text-warning" : "text-foreground"
                    )}>
                      {formatCurrency(transaction.amount, transaction.currency)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground capitalize">{transaction.transaction_type}</span>
                  </TableCell>
                  <TableCell>
                    <RiskScoreBadge score={transaction.risk_score} size="sm" showLabel={false} />
                  </TableCell>
                  <TableCell>
                    <StatusChip 
                      status={getStatusVariant(transaction.status)} 
                      size="sm" 
                      label={transaction.status ? transaction.status.replace("_", " ").toUpperCase() : "PENDING"}
                    />
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {format(new Date(transaction.created_at), "MMM d, yyyy")}
                    </span>
                  </TableCell>
                </motion.tr>
                <TransactionExpandedRow
                  key={`${transaction.transaction_id || `txn-expand-${index}`}-expanded`}
                  transaction={transaction}
                  isExpanded={expandedRows.has(transaction.transaction_id)}
                />
              </React.Fragment>
            ))}
          </AnimatePresence>
        </TableBody>
      </Table>
    </motion.div>
  );
}
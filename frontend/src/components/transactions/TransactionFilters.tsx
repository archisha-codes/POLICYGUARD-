import { motion } from "framer-motion";
import { Search, Filter, X, Calendar } from "lucide-react";
import { GlowingInput } from "@/components/ui/GlowingInput";
import { NeonButton } from "@/components/ui/NeonButton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";
import { useState } from "react";

interface TransactionFiltersProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusChange: (value: string) => void;
  riskFilter: string;
  onRiskChange: (value: string) => void;
  typeFilter: string;
  onTypeChange: (value: string) => void;
  dateFilter: Date | undefined;
  onDateChange: (date: Date | undefined) => void;
  onClearFilters: () => void;
}

export function TransactionFilters({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  riskFilter,
  onRiskChange,
  typeFilter,
  onTypeChange,
  onClearFilters,
}: TransactionFiltersProps) {
  const hasActiveFilters = searchQuery || statusFilter !== "all" || riskFilter !== "all" || typeFilter !== "all";

  return (
    <motion.div
      className="glass-card p-4 space-y-4"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" />
          <input
            type="text"
            placeholder="Search by transaction ID, customer, or merchant..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full h-10 pl-10 pr-4 rounded-lg bg-card/50 border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
          />
        </div>

        {/* Status Filter */}
        <Select value={statusFilter} onValueChange={onStatusChange}>
          <SelectTrigger className="w-full lg:w-[160px] bg-card/50 border-border/50">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="flagged">Flagged</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>

        {/* Risk Level Filter */}
        <Select value={riskFilter} onValueChange={onRiskChange}>
          <SelectTrigger className="w-full lg:w-[160px] bg-card/50 border-border/50">
            <SelectValue placeholder="Risk Level" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Risk</SelectItem>
            <SelectItem value="low">Low (0-24)</SelectItem>
            <SelectItem value="medium">Medium (25-49)</SelectItem>
            <SelectItem value="high">High (50-74)</SelectItem>
            <SelectItem value="critical">Critical (75+)</SelectItem>
          </SelectContent>
        </Select>

        {/* Transaction Type Filter */}
        <Select value={typeFilter} onValueChange={onTypeChange}>
          <SelectTrigger className="w-full lg:w-[160px] bg-card/50 border-border/50">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="Wire Transfer">Wire Transfer</SelectItem>
            <SelectItem value="ACH Transfer">ACH Transfer</SelectItem>
            <SelectItem value="SWIFT Transfer">SWIFT Transfer</SelectItem>
            <SelectItem value="SEPA Transfer">SEPA Transfer</SelectItem>
            <SelectItem value="Card Payment">Card Payment</SelectItem>
          </SelectContent>
        </Select>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <NeonButton
              variant="ghost"
              size="sm"
              onClick={onClearFilters}
              className="gap-1"
            >
              <X className="h-4 w-4" />
              Clear
            </NeonButton>
          </motion.div>
        )}
      </div>

      {/* Active Filter Tags */}
      {hasActiveFilters && (
        <motion.div
          className="flex flex-wrap gap-2"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
        >
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Filter className="h-3 w-3" />
            Active filters:
          </div>
          {searchQuery && (
            <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-xs">
              "{searchQuery}"
            </span>
          )}
          {statusFilter !== "all" && (
            <span className="px-2 py-0.5 rounded-full bg-secondary/20 text-secondary text-xs capitalize">
              {statusFilter}
            </span>
          )}
          {riskFilter !== "all" && (
            <span className="px-2 py-0.5 rounded-full bg-warning/20 text-warning text-xs capitalize">
              {riskFilter} risk
            </span>
          )}
          {typeFilter !== "all" && (
            <span className="px-2 py-0.5 rounded-full bg-accent/20 text-accent text-xs">
              {typeFilter}
            </span>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}

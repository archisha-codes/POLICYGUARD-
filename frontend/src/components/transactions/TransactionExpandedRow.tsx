import { motion, AnimatePresence } from "framer-motion"
import { AlertTriangle, Brain, MapPin, Building, FileText, Clock, List, Globe } from "lucide-react"
import { format } from "date-fns"
import { UiTransaction } from "@/hooks/useTransactions"
import { Badge } from "@/components/ui/badge"
import { getReadableRiskReasons } from "@/utils/riskReasons"
import React, { useState } from "react"

// TransactionDescription component with Read more/Show less
const MAX_DESC_LEN = 140; // characters

function TransactionDescription({ text }: { text?: string }) {
  const [expanded, setExpanded] = useState(false);
  const safeText = text || ""; // backend may send '' or null
  const isLong = safeText.length > MAX_DESC_LEN;
  const displayText = expanded ? safeText : safeText.slice(0, MAX_DESC_LEN);

  return (
    <div>
      <p className="text-sm text-gray-300" aria-live="polite" style={{ whiteSpace: "pre-wrap" }}>
        {displayText}{!expanded && isLong ? "..." : ""}
      </p>

      {isLong && (
        <button
          aria-expanded={expanded}
          className="text-cyan-400 text-xs mt-1 hover:underline focus:outline-none"
          onClick={() => setExpanded(!expanded)}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setExpanded(!expanded); }}
        >
          {expanded ? "Show less" : "Read more"}
        </button>
      )}
    </div>
  );
}

interface TransactionExpandedRowProps {
  transaction: UiTransaction
  isExpanded: boolean
}

export function TransactionExpandedRow({ transaction, isExpanded }: TransactionExpandedRowProps) {
  return (
    <AnimatePresence>
      {isExpanded && (
        <motion.tr
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3 }}
        >
          <td colSpan={8} className="p-0">
            <motion.div
              className="p-6 bg-card/30 border-t border-b border-primary/20 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 1. Transaction Details */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-primary flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Transaction Details
                  </h4>
                  <div className="space-y-2 text-sm bg-background/40 p-3 rounded-md border border-border/40">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Transaction ID:</span>
                      <span className="font-mono text-xs">{transaction.transaction_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type:</span>
                      <span className="font-medium">{transaction.transaction_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Description:</span>
                      <span className="text-right max-w-[200px]">
                        <TransactionDescription text={transaction.description} />
                      </span>
                    </div>
                    <div className="flex justify-between items-center gap-2">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        Country:
                      </span>
                      <span>{transaction.country}</span>
                    </div>
                    <div className="flex justify-between items-center gap-2">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Building className="h-3 w-3" />
                        Merchant:
                      </span>
                      <span>{transaction.merchant}</span>
                    </div>
                  </div>
                </div>

                {/* 2. Risk Indicators */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-warning flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Risk Indicators
                  </h4>
                  
                  <div className="bg-background/40 p-3 rounded-md border border-border/40 min-h-[120px]">
                    {transaction.flagged_reasons && transaction.flagged_reasons.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {transaction.flagged_reasons.map((reason, idx) => {
                          const readableReason = getReadableRiskReasons([reason])[0];
                          return (
                            <Badge key={idx} variant="destructive" className="text-xs">
                              {readableReason}
                            </Badge>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic flex items-center gap-2">
                        <List className="h-3 w-3" /> No specific flags raised.
                      </p>
                    )}

                    {/* Risk Breakdown (if available) */}
                    {transaction.risk_breakdown && (
                      <div className="mt-4 pt-3 border-t border-border/30 grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(transaction.risk_breakdown).map(([key, val]) => (
                           <div key={key} className="flex justify-between">
                             <span className="capitalize text-muted-foreground">{key.replace('_', ' ')}:</span>
                             <span className={val > 0 ? "text-destructive font-bold" : "text-success"}>{val}%</span>
                           </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* 3. AI Analysis */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-primary flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    AI Analysis
                  </h4>
                  <div className="bg-background/40 p-3 rounded-md border border-border/40 min-h-[120px] flex flex-col justify-between">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {transaction.ai_explanation 
                        ? transaction.ai_explanation 
                        : "AI analysis pending or not available for this transaction."}
                    </p>

                    <div className="pt-3 border-t border-border/30 mt-2">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        Created: {format(new Date(transaction.created_at), "PPp")}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </td>
        </motion.tr>
      )}
    </AnimatePresence>
  )
}
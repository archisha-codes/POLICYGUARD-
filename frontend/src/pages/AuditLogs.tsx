import React, { useState, useMemo } from "react"
import { motion } from "framer-motion"
import {
  Lock,
  Download,
  ChevronDown,
  User,
  FileText,
  AlertTriangle,
} from "lucide-react"
import { format } from "date-fns"
import jsPDF from "jspdf"
import Papa from "papaparse"

import { ParticleBackground } from "@/components/layout/ParticleBackground"
import { GlassCard } from "@/components/ui/GlassCard"
import { NeonButton } from "@/components/ui/NeonButton"
import { useAuth } from "@/hooks/useAuth"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuditLogs, SimulationAuditLog } from "@/hooks/useAuditLogs"

// TransactionDescription component with Read more/Show less (same as in TransactionExpandedRow)
const MAX_DESC_LEN = 140;

function TransactionDescription({ text }: { text?: string }) {
  const [expanded, setExpanded] = useState(false);
  const safeText = text || "";
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

export default function AuditLogs() {
  const { user, loading: authLoading } = useAuth()
  const { logs, simulationLogs, loading } = useAuditLogs()

  const [userFilter, setUserFilter] = useState("all")
  const [entityFilter, setEntityFilter] = useState("all")
  const [logTab, setLogTab] = useState<"database" | "simulation">("database")

  /* =========================
     FILTERED DATA
  ========================= */
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (userFilter !== "all" && log.action !== userFilter) return false
      if (entityFilter !== "all" && log.entity !== entityFilter) return false
      return true
    })
  }, [logs, userFilter, entityFilter])

  /* =========================
     SORTED DATA (NEWEST FIRST)
  ========================= */
  const sortedLogs = useMemo(() => {
    return [...filteredLogs].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [filteredLogs]);

  /* =========================
     EXPORT HANDLERS
  ========================= */
  const exportCSV = () => {
    const dataToExport = logTab === "database" 
      ? filteredLogs.map((log) => ({
          ID: log.id,
          Action: log.action,
          Entity: log.entity,
          Timestamp: log.timestamp,
        }))
      : simulationLogs.map((log) => ({
          Case_ID: log.case_id,
          Type: log.type,
          Amount: log.amount,
          Timestamp: log.timestamp,
          Action: log.action,
        }))
    
    const csv = Papa.unparse(dataToExport)

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)

    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", "audit_logs.csv")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const exportPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(14)
    doc.text(logTab === "database" ? "Audit Logs Report" : "Simulation Audit Logs Report", 14, 15)

    let y = 25
    doc.setFontSize(10)

    const logsToExport = logTab === "database" 
      ? filteredLogs 
      : simulationLogs as unknown as Array<{action: string; entity?: string; case_id?: number; type?: string; amount?: number; timestamp: string}>
    
    logsToExport.forEach((log, index) => {
      let line = ""
      if (logTab === "database") {
        line = `${index + 1}. ${log.action} | ${log.entity} | ${format(new Date(log.timestamp), "PPp")}`
      } else {
        line = `${index + 1}. Case ${log.case_id} | ${log.type} | ${log.amount.toLocaleString()} | ${format(new Date(log.timestamp), "PPp")}`
      }
      doc.text(line, 14, y)
      y += 8
      if (y > 280) {
        doc.addPage()
        y = 20
      }
    })

    doc.save(logTab === "database" ? "audit_logs.pdf" : "simulation_audit_logs.pdf")
  }

  if (authLoading || loading) return <div>Loading...</div>
  if (!user) return <div>Please log in</div>

  const uniqueActions = [...new Set(logs.map((l) => l.action))]
  const uniqueEntities = [...new Set(logs.map((l) => l.entity))]

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="flex justify-between items-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h1 className="text-3xl font-bold text-glow">Audit Logs & Reports</h1>
            <p className="text-muted-foreground">
              Immutable audit trail from backend
            </p>
          </div>
          <div className="flex gap-2">
            <NeonButton 
              variant={logTab === "database" ? "primary" : "outline"} 
              size="sm" 
              onClick={() => setLogTab("database")}
            >
              Database Logs
            </NeonButton>
            <NeonButton 
              variant={logTab === "simulation" ? "primary" : "outline"} 
              size="sm" 
              onClick={() => setLogTab("simulation")}
              className="gap-2"
            >
              <AlertTriangle className="h-4 w-4" />
              Simulation Logs
            </NeonButton>
            <NeonButton variant="outline" size="sm" onClick={exportPDF}>
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </NeonButton>
            <NeonButton variant="outline" size="sm" onClick={exportCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </NeonButton>
          </div>
        </motion.div>

        {/* Filters */}
        {logTab === "database" && (
        <GlassCard className="p-4 mb-6">
          <div className="flex gap-4 flex-wrap">
            <Select value={userFilter} onValueChange={setUserFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {uniqueActions.map((a) => (
                  <SelectItem key={a} value={a}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={entityFilter} onValueChange={setEntityFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by Entity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entities</SelectItem>
                {uniqueEntities.map((e) => (
                  <SelectItem key={e} value={e}>
                    {e}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </GlassCard>
        )}

        {/* Timeline */}
        <div className="relative space-y-6">
          {logTab === "database" ? (
            sortedLogs.map((log, index) => (
              <motion.div
                key={log.id}
                className="relative flex gap-8"
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.04 }}
              >
                <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center shadow-lg">
                  <Lock className="h-3 w-3 text-primary-foreground" />
                </div>

                <div className="flex-1">
                  <Collapsible>
                    <CollapsibleTrigger asChild>
                      <GlassCard className="p-4 cursor-pointer">
                        <div className="flex justify-between items-center">
                          <div>
                            <h3 className="font-semibold">{log.action}</h3>
                            <div className="text-sm text-muted-foreground flex gap-4">
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                System
                              </span>
                              <span className="flex items-center gap-1">
                                <FileText className="h-3 w-3" />
                                {log.entity}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">
                              {format(new Date(log.timestamp), "PPp")}
                            </span>
                            <ChevronDown className="h-4 w-4" />
                          </div>
                        </div>
                      </GlassCard>
                    </CollapsibleTrigger>

                    <CollapsibleContent>
                      <GlassCard className="p-4 mt-2">
                        <p className="text-sm">
                          Action <strong>{log.action}</strong> was performed on{" "}
                          <strong>{log.entity}</strong>.
                        </p>
                        {/* Show explanation/description with Read more if available */}
                        {log.description && (
                          <div className="mt-3 pt-3 border-t border-border/30">
                            <TransactionDescription text={log.description} />
                          </div>
                        )}
                      </GlassCard>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              </motion.div>
            ))
          ) : (
            // Simulation logs
            <>
              {simulationLogs.map((log, index) => {
                // Use a combination of case_id and timestamp for unique key
                const logKey = log.case_id && log.timestamp ? `sim-${log.case_id}-${log.timestamp}` : `sim-${index}`;
                return (
                  <motion.div
                    key={logKey}
                    className="relative flex gap-8"
                    initial={{ opacity: 0, x: -40 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                  >
                    <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center shadow-lg">
                      <AlertTriangle className="h-3 w-3 text-white" />
                    </div>

                    <div className="flex-1">
                      <Collapsible>
                        <CollapsibleTrigger asChild>
                          <GlassCard className="p-4 cursor-pointer">
                            <div className="flex justify-between items-center">
                              <div>
                                <h3 className="font-semibold">Simulation Run - Case {log.case_id}</h3>
                                <div className="text-sm text-muted-foreground flex gap-4">
                                  <span className="flex items-center gap-1">
                                    <User className="h-3 w-3" />
                                    System
                                  </span>
                                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded ${
                                    log.type === "DEBIT" ? "bg-red-500/20 text-red-400" : "bg-blue-500/20 text-blue-400"
                                  }`}>
                                    {log.type}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <FileText className="h-3 w-3" />
                                    ${log.amount.toLocaleString()}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">
                                  {format(new Date(log.timestamp), "PPp")}
                                </span>
                                <ChevronDown className="h-4 w-4" />
                              </div>
                            </div>
                          </GlassCard>
                        </CollapsibleTrigger>

                        <CollapsibleContent>
                          <GlassCard className="p-4 mt-2">
                            <p className="text-sm">
                              Simulation executed for <strong>Case {log.case_id}</strong> with{" "}
                              transaction type <strong>{log.type}</strong> and amount{" "}
                              <strong>${log.amount.toLocaleString()}</strong>.
                            </p>
                          </GlassCard>
                        </CollapsibleContent>
                      </Collapsible>
                    </div>
                  </motion.div>
                );
              })}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

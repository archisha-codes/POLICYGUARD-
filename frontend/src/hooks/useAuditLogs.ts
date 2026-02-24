import { useEffect, useState, useCallback } from "react"
import { fetchAuditLogs, fetchSimulationAuditLogs } from "@/services/api"
import { ApiAuditLog } from "@/types/api"

/**
 * Shape consumed by AuditLogs UI
 */
export interface UiAuditLog {
  id: string
  action: string
  entity: string
  timestamp: string
}

/**
 * Simulation audit log shape
 */
export interface SimulationAuditLog {
  action: string
  case_id: number
  amount: number
  type: string
  timestamp: string
}

export const useAuditLogs = () => {
  const [logs, setLogs] = useState<UiAuditLog[]>([])
  const [simulationLogs, setSimulationLogs] = useState<SimulationAuditLog[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  const load = useCallback(async () => {
    try {
      setLoading(true)

      const data: ApiAuditLog[] = await fetchAuditLogs()

      const mapped: UiAuditLog[] = data.map((log) => ({
        id: log.id,
        action: log.action,
        entity: log.entity,
        timestamp: log.timestamp,
      }))

      setLogs(mapped)
      
      // Also fetch simulation audit logs
      try {
        const simData = await fetchSimulationAuditLogs()
        setSimulationLogs(simData)
      } catch (e) {
        console.error("Failed to load simulation audit logs:", e)
        setSimulationLogs([])
      }
    } catch (error) {
      console.error("Failed to load audit logs:", error)
      setLogs([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return {
    logs,
    simulationLogs,
    loading,
    reload: load,
  }
}

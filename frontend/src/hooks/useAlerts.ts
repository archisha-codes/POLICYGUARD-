import { useEffect, useState } from "react"
// ✅ Import ApiTransaction correctly from types
import { fetchAlerts } from "../services/api"
import { ApiTransaction } from "../types/api"

/**
 * Shape expected by Alerts UI components
 */
export interface UiAlert {
  id: string
  severity: "LOW" | "MEDIUM" | "HIGH"
  message: string
  timestamp: string
  transactionId: string
  status: string
}

export const useAlerts = () => {
  const [alerts, setAlerts] = useState<UiAlert[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      setLoading(true)

      // ✅ FIX: fetchAlerts returns ApiTransaction[] (High Risk Transactions)
      const data: ApiTransaction[] = await fetchAlerts()

      const mapped: UiAlert[] = data.map((tx) => ({
        id: tx.transaction_id, // Use transaction_id as alert ID
        severity: tx.risk_score > 80 ? "HIGH" : tx.risk_score > 50 ? "MEDIUM" : "LOW",
        message: tx.ai_explanation || tx.description || "Suspicious Activity Detected",
        timestamp: tx.created_at,
        transactionId: tx.transaction_id,
        status: "ACTIVE",
      }))

      setAlerts(mapped)
    } catch (error) {
      console.error("Failed to load alerts", error)
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return {
    alerts,
    loading,
    reload: load,
  }
}
// frontend/src/App.tsx

import { Toaster } from "@/components/ui/toaster"
import { Toaster as Sonner } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Routes, Route } from "react-router-dom"

import { AuthProvider } from "@/hooks/useAuth"

import Landing from "./pages/Landing"
import Auth from "./pages/Auth"
import Dashboard from "./pages/Dashboard"
import Profile from "./pages/Profile"
import TransactionMonitoring from "./pages/TransactionMonitoring"
import ComplianceDecisionView from "./pages/ComplianceDecisionView"
import Alerts from "./pages/Alerts"
import PolicyDrift from "./pages/PolicyDrift"
import AuditLogs from "./pages/AuditLogs"
import AdminPanel from "./pages/AdminPanel"
import NotFound from "./pages/NotFound"
import Layout from "./components/Layout"

// ------------------------------------------------------------------
// React Query Client
// ------------------------------------------------------------------
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// ------------------------------------------------------------------
// App Root
// ------------------------------------------------------------------
const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />

          <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/auth" element={<Auth />} />

              {/* Protected / App Routes */}
              <Route path="/" element={<Layout />}>
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="profile" element={<Profile />} />
                <Route path="transactions" element={<TransactionMonitoring />} />
                <Route
                  path="compliance-decision/:id"
                  element={<ComplianceDecisionView />}
                />
                <Route path="alerts" element={<Alerts />} />
                <Route path="policy-drift" element={<PolicyDrift />} />
                <Route path="audit-logs" element={<AuditLogs />} />
                <Route path="admin" element={<AdminPanel />} />
              </Route>

              {/* Catch-all */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App

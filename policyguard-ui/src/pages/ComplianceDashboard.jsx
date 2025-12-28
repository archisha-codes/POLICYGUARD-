import { useState } from "react";
import Sidebar from "../components/Sidebar";
import StatCard from "../components/StatCard";
import RiskMeter from "../components/RiskMeter";
import ComplianceBadge from "../components/ComplianceBadge";



export default function ComplianceDashboard() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <Sidebar open={open} setOpen={setOpen} />

      <main className="flex-1 p-8 md:ml-64">
        <h1 className="text-3xl font-bold mb-8 text-slate-800">
          Real-time Compliance Overview
        </h1>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <StatCard title="Policies Scanned" value="12"
            gradient="from-blue-500 to-indigo-600" />
          <StatCard title="Open Violations" value="5"
            gradient="from-red-500 to-rose-600" />
          <StatCard title="Compliance Rate" value="82%"
            gradient="from-green-500 to-emerald-600" />
        </div>

        {/* Risk + Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <RiskMeter risk={68} />

          <div className="bg-white rounded-2xl shadow-lg p-6
            hover:shadow-2xl transition">
            <p className="text-gray-500 mb-3">Current Status</p>
            <ComplianceBadge status="PARTIALLY" />

            <div className="mt-8 flex gap-4">
              <button
                className="px-5 py-2 rounded-xl bg-indigo-600 text-white
                hover:bg-indigo-700 hover:scale-105 transition shadow"
              >
                Run Compliance Check
              </button>

              <button
                className="px-5 py-2 rounded-xl bg-slate-200
                hover:bg-slate-300 hover:scale-105 transition"
              >
                Upload PDFs
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

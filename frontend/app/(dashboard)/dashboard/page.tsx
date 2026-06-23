"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Summary, Violation } from "@/lib/types";
import { useViolationFeed } from "@/lib/useWebSocket";
import KpiCard from "@/components/KpiCard";
import ViolationCard from "@/components/ViolationCard";
import MapplsMap from "@/components/MapplsMap";
import LiveCameraFeed from "@/components/LiveCameraFeed";

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [recent, setRecent] = useState<Violation[]>([]);
  const [flash, setFlash] = useState(0);

  async function refresh() {
    try {
      const [s, list] = await Promise.all([
        api.summary(),
        api.violations({ page_size: 12 }),
      ]);
      setSummary(s);
      setRecent(list.items);
    } catch { /* handled by api (redirect on 401) */ }
  }

  useEffect(() => { refresh(); }, []);

  const { connected } = useViolationFeed((e) => {
    if (e.type === "new_violation") {
      setFlash((f) => f + 1);
      refresh();
    }
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <span className={`flex items-center gap-2 text-xs ${connected ? "text-green-400" : "text-slate-500"}`}>
          <span className={`h-2 w-2 rounded-full ${connected ? "bg-green-400" : "bg-slate-500"}`} />
          {connected ? "Live" : "Disconnected"} {flash > 0 && `· ${flash} new`}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Total Today" value={summary?.total_today ?? "—"}
          sub={summary ? `${summary.pct_change_vs_yesterday > 0 ? "▲" : "▼"} ${Math.abs(summary.pct_change_vs_yesterday)}% vs yesterday` : ""}
          accent="blue" />
        <KpiCard title="Auto-Enforced" value={summary?.auto_enforced ?? "—"}
          sub={summary && summary.total_all_time ? `${((summary.auto_enforced / summary.total_all_time) * 100).toFixed(1)}%` : ""}
          accent="red" />
        <KpiCard title="Pending Review" value={summary?.pending_review ?? "—"}
          sub="awaiting officer" accent="amber" />
        <KpiCard title="Avg Latency" value={summary ? `${summary.avg_latency_ms.toFixed(1)}ms` : "—"}
          sub={summary && summary.avg_latency_ms < 40 ? "✅ < 40ms" : ""} accent="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <LiveCameraFeed />
        </div>
        <div>
          <h2 className="mb-3 mt-8 text-lg font-semibold text-white">Live Gridlock Hotspots</h2>
          <MapplsMap violations={recent} />
        </div>
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold text-white">Recent Violations</h2>
      {recent.length === 0 ? (
        <div className="card p-8 text-center text-slate-500">
          No violations yet. Start the ML pipeline to begin detection.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {recent.map((v) => <ViolationCard key={v.id} v={v} />)}
        </div>
      )}
    </div>
  );
}

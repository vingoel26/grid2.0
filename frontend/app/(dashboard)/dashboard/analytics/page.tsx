"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HeatmapPoint, HourlyPoint, Summary } from "@/lib/types";
import { HourlyChart, TypeBreakdown } from "@/components/AnalyticsChart";
import { rupee } from "@/lib/format";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [hourly, setHourly] = useState<HourlyPoint[]>([]);
  const [heat, setHeat] = useState<HeatmapPoint[]>([]);

  useEffect(() => {
    api.summary().then(setSummary).catch(() => {});
    api.hourly(24).then(setHourly).catch(() => {});
    api.heatmap().then(setHeat).catch(() => {});
  }, []);

  const maxCount = Math.max(1, ...heat.map((h) => h.count));
  const estRevenue = summary
    ? Object.entries(summary.by_type).reduce((s, [, c]) => s + c, 0)
    : 0;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-white">Analytics</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-300">Hourly Trend (24h)</h2>
          <HourlyChart data={hourly} />
        </div>
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-300">Violation Breakdown</h2>
          {summary ? <TypeBreakdown data={summary.by_type} /> :
            <div className="flex h-[280px] items-center justify-center text-slate-500">No data</div>}
        </div>
      </div>

      <div className="card mt-6 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">Hotspots by Camera</h2>
        {heat.length === 0 ? (
          <div className="text-slate-500">No location data yet.</div>
        ) : (
          <div className="space-y-2">
            {heat.sort((a, b) => b.count - a.count).map((h) => (
              <div key={h.camera_id} className="flex items-center gap-3">
                <span className="w-48 truncate text-sm text-slate-300">{h.camera_name || h.camera_id}</span>
                <div className="h-5 flex-1 overflow-hidden rounded bg-black/30">
                  <div className="h-full rounded bg-gradient-to-r from-amber-500 to-red-600"
                    style={{ width: `${(h.count / maxCount) * 100}%` }} />
                </div>
                <span className="w-12 text-right text-sm text-slate-400">{h.count}</span>
              </div>
            ))}
          </div>
        )}
        <p className="mt-3 text-xs text-slate-500">
          Geo coordinates available for Leaflet map overlay: {heat.map((h) => `${h.lat?.toFixed(3)},${h.lng?.toFixed(3)}`).join(" · ") || "none"}
        </p>
      </div>

      {summary && (
        <div className="card mt-6 p-5 text-sm text-slate-400">
          Total violations: <span className="text-white">{estRevenue}</span> · All-time: <span className="text-white">{summary.total_all_time}</span> · Avg pipeline latency: <span className="text-white">{summary.avg_latency_ms.toFixed(1)}ms</span>
        </div>
      )}
    </div>
  );
}

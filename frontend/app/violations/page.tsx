"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ViolationList } from "@/lib/types";
import { ACTION_COLORS, STATUS_COLORS, prettyType, rupee, timeAgo } from "@/lib/format";
import Badge from "@/components/Badge";

const TYPES = [
  "", "HELMET_VIOLATION", "SEATBELT_VIOLATION", "TRIPLE_RIDING", "WRONG_SIDE_DRIVING",
  "STOP_LINE_VIOLATION", "RED_LIGHT_VIOLATION", "ILLEGAL_PARKING", "NO_PLATE",
];

export default function ViolationsPage() {
  const [data, setData] = useState<ViolationList | null>(null);
  const [page, setPage] = useState(1);
  const [type, setType] = useState("");
  const [plate, setPlate] = useState("");
  const [action, setAction] = useState("");

  useEffect(() => {
    api.violations({ page, page_size: 25, violation_type: type, plate, action })
      .then(setData).catch(() => {});
  }, [page, type, plate, action]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-white">Violations</h1>

      <div className="mb-4 flex flex-wrap gap-3">
        <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}
          className="rounded-lg border border-[var(--border)] bg-black/30 px-3 py-2 text-sm">
          {TYPES.map((t) => <option key={t} value={t}>{t ? prettyType(t) : "All types"}</option>)}
        </select>
        <select value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className="rounded-lg border border-[var(--border)] bg-black/30 px-3 py-2 text-sm">
          <option value="">All actions</option>
          <option value="AUTO_ENFORCE">Auto-enforce</option>
          <option value="HUMAN_REVIEW">Human review</option>
        </select>
        <input placeholder="Search plate…" value={plate}
          onChange={(e) => { setPlate(e.target.value); setPage(1); }}
          className="rounded-lg border border-[var(--border)] bg-black/30 px-3 py-2 text-sm" />
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-white/5 text-left text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Camera</th>
              <th className="px-4 py-3">Plate</th>
              <th className="px-4 py-3">Conf</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Fine</th>
              <th className="px-4 py-3">When</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((v) => (
              <tr key={v.id} className="border-t border-[var(--border)] hover:bg-white/5">
                <td className="px-4 py-3">
                  <Link href={`/violations/${v.violation_id}`} className="text-blue-300 hover:underline">
                    {prettyType(v.violation_type)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-300">{v.camera_name || v.camera_id}</td>
                <td className="px-4 py-3 font-mono text-slate-300">{v.plate_number || "—"}</td>
                <td className="px-4 py-3 text-slate-300">{(v.final_confidence * 100).toFixed(0)}%</td>
                <td className="px-4 py-3"><Badge label={v.enforcement_action.replace("_", " ")} className={ACTION_COLORS[v.enforcement_action]} /></td>
                <td className="px-4 py-3"><Badge label={v.status} className={STATUS_COLORS[v.status]} /></td>
                <td className="px-4 py-3 text-slate-300">{rupee(v.fine_inr)}</td>
                <td className="px-4 py-3 text-slate-500">{timeAgo(v.occurred_at)}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-10 text-center text-slate-500">No violations match.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <span>{data?.total ?? 0} total</span>
        <div className="flex items-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
            className="rounded border border-[var(--border)] px-3 py-1 disabled:opacity-40">Prev</button>
          <span>{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}
            className="rounded border border-[var(--border)] px-3 py-1 disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  );
}

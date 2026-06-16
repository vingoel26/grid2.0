"use client";
import { useEffect, useState } from "react";
import { api, evidenceUrl } from "@/lib/api";
import type { Violation } from "@/lib/types";
import { ACTION_COLORS, prettyType, rupee } from "@/lib/format";
import Badge from "@/components/Badge";

export default function ReviewQueue() {
  const [queue, setQueue] = useState<Violation[]>([]);
  const [idx, setIdx] = useState(0);
  const [notes, setNotes] = useState("");

  async function load() {
    const list = await api.violations({ status: "PENDING", action: "HUMAN_REVIEW", page_size: 100 });
    setQueue(list.items);
    setIdx(0);
  }
  useEffect(() => { load().catch(() => {}); }, []);

  const v = queue[idx];

  async function decide(status: "CONFIRMED" | "REJECTED") {
    if (!v) return;
    await api.review(v.violation_id, status, notes);
    setNotes("");
    const next = queue.filter((_, i) => i !== idx);
    setQueue(next);
    setIdx((i) => Math.min(i, Math.max(0, next.length - 1)));
  }

  if (!v) {
    return (
      <div>
        <h1 className="mb-6 text-2xl font-bold text-white">Review Queue</h1>
        <div className="card p-10 text-center text-slate-400">
          🎉 Queue empty — no violations awaiting review.
        </div>
      </div>
    );
  }

  const img = evidenceUrl(v.evidence_image_path) || evidenceUrl(v.evidence_thumbnail_path);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Review Queue</h1>
        <span className="text-sm text-slate-400">{queue.length} pending</span>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card overflow-hidden">
          {img ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={img} alt="evidence" className="w-full object-contain" />
          ) : (
            <div className="flex h-80 items-center justify-center text-slate-600">No evidence image</div>
          )}
        </div>

        <div className="card flex flex-col p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">{prettyType(v.violation_type)}</h2>
            <Badge label={v.enforcement_action.replace("_", " ")} className={ACTION_COLORS[v.enforcement_action]} />
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-y-3 text-sm">
            <dt className="text-slate-400">Camera</dt><dd className="text-slate-200">{v.camera_name || v.camera_id}</dd>
            <dt className="text-slate-400">Plate</dt><dd className="font-mono text-slate-200">{v.plate_number || "UNREADABLE"}</dd>
            <dt className="text-slate-400">Confidence</dt><dd className="text-slate-200">{(v.final_confidence * 100).toFixed(1)}%</dd>
            <dt className="text-slate-400">Section</dt><dd className="text-slate-200">{v.violation_code}</dd>
            <dt className="text-slate-400">Fine</dt><dd className="text-slate-200">{rupee(v.fine_inr)}</dd>
            <dt className="text-slate-400">Evidence hash</dt><dd className="truncate font-mono text-xs text-slate-400">{v.evidence_hash?.slice(0, 16)}…</dd>
          </dl>

          {v.gemini_verdict && (
            <div className="mt-4 rounded-lg border border-purple-600/40 bg-purple-600/10 p-3 text-sm">
              <span className="font-medium text-purple-300">Gemini pre-review: {v.gemini_verdict}</span>
              {v.gemini_explanation && <p className="mt-1 text-slate-400">{v.gemini_explanation}</p>}
            </div>
          )}

          <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
            placeholder="Review notes (optional)…" rows={3}
            className="mt-4 w-full rounded-lg border border-[var(--border)] bg-black/30 p-3 text-sm" />

          <div className="mt-4 flex gap-3">
            <button onClick={() => decide("CONFIRMED")}
              className="flex-1 rounded-lg bg-green-600 py-2.5 font-medium text-white hover:bg-green-500">
              ✓ Confirm & Challan
            </button>
            <button onClick={() => decide("REJECTED")}
              className="flex-1 rounded-lg bg-slate-600 py-2.5 font-medium text-white hover:bg-slate-500">
              ✕ Reject
            </button>
          </div>
          <div className="mt-3 flex justify-between text-xs text-slate-500">
            <button disabled={idx === 0} onClick={() => setIdx((i) => i - 1)} className="disabled:opacity-40">← Prev</button>
            <span>{idx + 1} of {queue.length}</span>
            <button disabled={idx >= queue.length - 1} onClick={() => setIdx((i) => i + 1)} className="disabled:opacity-40">Skip →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { api, evidenceUrl } from "@/lib/api";
import type { Violation } from "@/lib/types";
import { ACTION_COLORS, STATUS_COLORS, prettyType, rupee } from "@/lib/format";
import Badge from "@/components/Badge";

export default function EvidenceViewer({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [v, setV] = useState<Violation | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => { api.violation(id).then(setV).catch(() => setErr(true)); }, [id]);

  if (err) return <div className="card p-8 text-center text-slate-400">Violation not found.</div>;
  if (!v) return <div className="text-slate-500">Loading…</div>;

  const img = evidenceUrl(v.evidence_image_path);
  const video = evidenceUrl(v.evidence_video_path);

  return (
    <div>
      <Link href="/violations" className="mb-4 inline-block text-sm text-blue-300 hover:underline">← Back to violations</Link>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">{prettyType(v.violation_type)}</h1>
        <div className="flex gap-2">
          <Badge label={v.enforcement_action.replace("_", " ")} className={ACTION_COLORS[v.enforcement_action]} />
          <Badge label={v.status} className={STATUS_COLORS[v.status]} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="card overflow-hidden">
            {img ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={img} alt="annotated evidence" className="w-full" />
            ) : (
              <div className="flex h-96 items-center justify-center text-slate-600">No annotated image</div>
            )}
          </div>
          {video && (
            <div className="card overflow-hidden">
              <video src={video} controls className="w-full" />
            </div>
          )}
        </div>

        <div className="card h-fit p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">Metadata</h2>
          <dl className="space-y-3 text-sm">
            <Row k="Violation ID" v={v.violation_id} mono />
            <Row k="MVA Section" v={v.violation_code} />
            <Row k="Fine" v={rupee(v.fine_inr)} />
            <Row k="Camera" v={v.camera_name || v.camera_id} />
            <Row k="Vehicle" v={v.vehicle_type || "—"} />
            <Row k="Plate" v={v.plate_number || "UNREADABLE"} mono />
            <Row k="Raw conf" v={`${(v.raw_confidence * 100).toFixed(1)}%`} />
            <Row k="Final conf" v={`${(v.final_confidence * 100).toFixed(1)}%`} />
            <Row k="Latency" v={v.pipeline_latency_ms ? `${v.pipeline_latency_ms}ms` : "—"} />
            <Row k="Model" v={v.model_version || "—"} />
            <Row k="Occurred" v={new Date(v.occurred_at).toLocaleString()} />
            <Row k="SHA-256" v={v.evidence_hash || "—"} mono small />
          </dl>
          {v.reviewed_by && (
            <div className="mt-4 rounded-lg bg-white/5 p-3 text-xs text-slate-400">
              Reviewed by {v.reviewed_by} — {v.review_notes || "no notes"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ k, v, mono, small }: { k: string; v: string; mono?: boolean; small?: boolean }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-slate-400">{k}</dt>
      <dd className={`text-right text-slate-200 ${mono ? "font-mono" : ""} ${small ? "break-all text-xs" : ""}`}>{v}</dd>
    </div>
  );
}

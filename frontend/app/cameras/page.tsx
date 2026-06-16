"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Camera } from "@/lib/types";
import Badge from "@/components/Badge";

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);

  useEffect(() => { api.cameras().then(setCameras).catch(() => {}); }, []);

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-white">Cameras</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cameras.map((c) => (
          <div key={c.id} className="card p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-white">{c.name}</h2>
              <Badge label={c.is_active ? "Active" : "Inactive"}
                className={c.is_active ? "bg-green-500/20 text-green-400 border-green-500/40" : "bg-slate-500/20 text-slate-400 border-slate-500/40"} />
            </div>
            <div className="mt-1 font-mono text-xs text-slate-500">{c.id}</div>
            <dl className="mt-4 space-y-1 text-sm">
              <div className="flex justify-between"><dt className="text-slate-400">Location</dt>
                <dd className="text-slate-300">{c.location_lat?.toFixed(4)}, {c.location_lng?.toFixed(4)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Flow dir</dt>
                <dd className="text-slate-300">{(c.expected_flow_direction * 180 / Math.PI).toFixed(0)}°</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Stop line</dt>
                <dd className="text-slate-300">{c.stop_line_polygon?.length ? "configured" : "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Intersection</dt>
                <dd className="text-slate-300">{c.intersection_polygon?.length ? "configured" : "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">No-parking zones</dt>
                <dd className="text-slate-300">{c.no_parking_zones?.length || 0}</dd></div>
            </dl>
            <div className="mt-4 rounded-lg border border-dashed border-[var(--border)] p-3 text-center text-xs text-slate-500">
              Zone polygon editor — drag points on live MJPEG feed (one-time setup per camera)
            </div>
          </div>
        ))}
        {cameras.length === 0 && (
          <div className="card col-span-full p-8 text-center text-slate-500">No cameras registered.</div>
        )}
      </div>
    </div>
  );
}

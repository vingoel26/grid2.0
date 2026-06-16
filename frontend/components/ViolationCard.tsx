import Link from "next/link";
import type { Violation } from "@/lib/types";
import { ACTION_COLORS, prettyType, rupee, timeAgo } from "@/lib/format";
import { evidenceUrl } from "@/lib/api";
import Badge from "./Badge";

export default function ViolationCard({ v }: { v: Violation }) {
  const thumb = evidenceUrl(v.evidence_thumbnail_path) || evidenceUrl(v.evidence_image_path);
  return (
    <Link href={`/violations/${v.violation_id}`}
      className="card flex gap-3 p-3 hover:border-blue-600/50 transition">
      <div className="h-16 w-16 shrink-0 overflow-hidden rounded-md bg-black/40">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={thumb} alt="evidence" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-2xl text-slate-600">⚠</div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate font-medium text-white">{prettyType(v.violation_type)}</span>
          <Badge label={v.enforcement_action.replace("_", " ")}
                 className={ACTION_COLORS[v.enforcement_action]} />
        </div>
        <div className="mt-1 truncate text-xs text-slate-400">
          {v.camera_name || v.camera_id} · {v.plate_number || "no plate"} · {rupee(v.fine_inr)}
        </div>
        <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
          <span>conf {(v.final_confidence * 100).toFixed(0)}%</span>
          <span>{timeAgo(v.occurred_at)}</span>
        </div>
      </div>
    </Link>
  );
}

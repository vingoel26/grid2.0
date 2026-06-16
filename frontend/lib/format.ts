export const ACTION_COLORS: Record<string, string> = {
  AUTO_ENFORCE: "bg-red-600/20 text-red-400 border-red-600/40",
  HUMAN_REVIEW: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  LOG_ONLY: "bg-green-500/20 text-green-400 border-green-500/40",
};

export const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  CONFIRMED: "bg-green-500/20 text-green-400 border-green-500/40",
  REJECTED: "bg-slate-500/20 text-slate-400 border-slate-500/40",
};

export function prettyType(t: string): string {
  return t.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function timeAgo(iso: string): string {
  const d = new Date(iso).getTime();
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export const rupee = (n: number) => `₹${n.toLocaleString("en-IN")}`;

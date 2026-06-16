export default function KpiCard({
  title, value, sub, accent,
}: {
  title: string;
  value: string | number;
  sub?: string;
  accent?: "red" | "amber" | "green" | "blue";
}) {
  const accentColor = {
    red: "text-red-400", amber: "text-amber-400",
    green: "text-green-400", blue: "text-blue-400",
  }[accent || "blue"];
  return (
    <div className="card p-5">
      <div className="text-xs uppercase tracking-wide text-slate-400">{title}</div>
      <div className={`mt-2 text-3xl font-bold ${accentColor}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

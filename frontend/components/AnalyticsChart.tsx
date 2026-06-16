"use client";
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

const TOOLTIP = {
  contentStyle: { background: "#141925", border: "1px solid #232a3a", borderRadius: 8 },
  labelStyle: { color: "#e6e9ef" },
};

export function HourlyChart({ data }: { data: { hour: string; count: number }[] }) {
  const fmt = data.map((d) => ({ ...d, label: new Date(d.hour).getHours() + ":00" }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={fmt}>
        <CartesianGrid strokeDasharray="3 3" stroke="#232a3a" />
        <XAxis dataKey="label" stroke="#64748b" fontSize={12} />
        <YAxis stroke="#64748b" fontSize={12} />
        <Tooltip {...TOOLTIP} />
        <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

const COLORS = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

export function TypeBreakdown({ data }: { data: Record<string, number> }) {
  const rows = Object.entries(data).map(([k, v]) => ({
    name: k.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
    count: v,
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} layout="vertical" margin={{ left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#232a3a" />
        <XAxis type="number" stroke="#64748b" fontSize={12} />
        <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={120} />
        <Tooltip {...TOOLTIP} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {rows.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

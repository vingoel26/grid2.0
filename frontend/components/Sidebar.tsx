"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "▦" },
  { href: "/dashboard/violations", label: "Violations", icon: "⚠" },
  { href: "/dashboard/review", label: "Review Queue", icon: "✓" },
  { href: "/dashboard/challans", label: "Challans", icon: "📋" },
  { href: "/dashboard/analytics", label: "Analytics", icon: "📈" },
  { href: "/dashboard/cameras", label: "Cameras", icon: "📷" },
];

export default function Sidebar() {
  const path = usePathname();
  const router = useRouter();
  if (path === "/login") return null;

  return (
    <aside className="w-60 shrink-0 border-r border-[var(--border)] bg-[var(--panel)] p-4 flex flex-col">
      <div className="mb-6">
        <div className="text-xl font-bold text-white">Gridlock 2.0</div>
        <div className="text-xs text-slate-400">BTP Violation Detection</div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((n) => {
          const active = path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href));
          return (
            <Link
              key={n.href}
              href={n.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active ? "bg-blue-600/20 text-blue-300" : "text-slate-300 hover:bg-white/5"
              }`}
            >
              <span>{n.icon}</span> {n.label}
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => { clearToken(); router.push("/login"); }}
        className="mt-auto rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5 text-left"
      >
        ⏻ Logout
      </button>
    </aside>
  );
}

"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Challan } from "@/lib/types";
import Badge from "@/components/Badge";

export default function ChallansPage() {
  const [data, setData] = useState<{ total: number; items: Challan[] }>({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  async function load() {
    setLoading(true);
    try {
      const list = await api.challans({ page, page_size: pageSize });
      setData(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [page]);

  const totalPages = Math.ceil(data.total / pageSize);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "GENERATED": return "bg-blue-600/20 text-blue-400 border border-blue-600/30";
      case "SENT": return "bg-yellow-600/20 text-yellow-400 border border-yellow-600/30";
      case "DELIVERED": return "bg-green-600/20 text-green-400 border border-green-600/30";
      case "FAILED": return "bg-red-600/20 text-red-400 border border-red-600/30";
      default: return "bg-slate-600/20 text-slate-400 border border-slate-600/30";
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case "PAID": return "bg-green-600/20 text-green-400 border border-green-600/30";
      case "UNPAID": return "bg-red-600/20 text-red-400 border border-red-600/30";
      case "OVERDUE": return "bg-orange-600/20 text-orange-400 border border-orange-600/30";
      default: return "bg-slate-600/20 text-slate-400 border border-slate-600/30";
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Challans Registry</h1>
          <p className="text-sm text-slate-400">Total {data.total} challans issued</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-[var(--border)] bg-black/20 text-xs font-semibold uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Challan No.</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Plate & Owner</th>
                <th className="px-4 py-3">Dispatch Status</th>
                <th className="px-4 py-3">Payment</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {loading && data.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading...</td>
                </tr>
              ) : data.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No challans found</td>
                </tr>
              ) : (
                data.items.map((c) => (
                  <tr key={c.id} className="transition-colors hover:bg-white/5">
                    <td className="px-4 py-3 font-mono text-slate-200">
                      {c.challan_number}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {new Date(c.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-mono text-white">{c.plate_number || "Unknown Plate"}</div>
                      <div className="text-xs text-slate-400">{c.owner_name || "Unknown Owner"}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1 items-start">
                        <Badge label={c.status} className={getStatusColor(c.status)} />
                        {c.sent_via && <span className="text-[10px] text-slate-500">via {c.sent_via}</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge label={c.payment_status} className={getPaymentStatusColor(c.payment_status)} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      {c.pdf_path && (
                        <a
                          href={api.challanPdfUrl(c.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center rounded-lg bg-blue-600/10 px-3 py-1.5 text-xs font-medium text-blue-400 transition-colors hover:bg-blue-600/20"
                        >
                          📄 PDF
                        </a>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-[var(--border)] p-4 text-sm text-slate-400">
            <div>Page {page} of {totalPages}</div>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="rounded-lg border border-[var(--border)] px-3 py-1 hover:bg-white/5 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="rounded-lg border border-[var(--border)] px-3 py-1 hover:bg-white/5 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

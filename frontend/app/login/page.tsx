"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("officer_42");
  const [password, setPassword] = useState("officer123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const r = await api.login(username, password);
      setToken(r.access_token);
      router.push("/");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center">
      <form onSubmit={submit} className="card w-full max-w-sm p-8">
        <div className="mb-1 text-2xl font-bold text-white">Gridlock 2.0</div>
        <div className="mb-6 text-sm text-slate-400">Bengaluru Traffic Police</div>
        <label className="mb-1 block text-xs text-slate-400">Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)}
          className="mb-4 w-full rounded-lg border border-[var(--border)] bg-black/30 px-3 py-2 text-sm" />
        <label className="mb-1 block text-xs text-slate-400">Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full rounded-lg border border-[var(--border)] bg-black/30 px-3 py-2 text-sm" />
        {error && <div className="mb-3 text-sm text-red-400">{error}</div>}
        <button disabled={loading}
          className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50">
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <div className="mt-4 text-center text-xs text-slate-500">
          Demo: officer_42 / officer123 · admin / admin123
        </div>
      </form>
    </div>
  );
}

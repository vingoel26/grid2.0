import type {
  Camera, HeatmapPoint, HourlyPoint, Summary, Violation, ViolationList,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

const TOKEN_KEY = "gridlock_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string) { localStorage.setItem(TOKEN_KEY, t); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !path.includes("/auth/")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    req<{ access_token: string; role: string; username: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ username, password }) },
    ),

  summary: () => req<Summary>("/api/v1/analytics/summary"),
  hourly: (hours = 24) => req<HourlyPoint[]>(`/api/v1/analytics/hourly?hours=${hours}`),
  heatmap: () => req<HeatmapPoint[]>("/api/v1/analytics/heatmap"),

  violations: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    return req<ViolationList>(`/api/v1/violations?${q.toString()}`);
  },
  violation: (id: string) => req<Violation>(`/api/v1/violations/${id}`),
  review: (id: string, status: "CONFIRMED" | "REJECTED", notes?: string) =>
    req<Violation>(`/api/v1/violations/${id}/review`, {
      method: "PATCH",
      body: JSON.stringify({ status, review_notes: notes }),
    }),

  cameras: () => req<Camera[]>("/api/v1/cameras"),
};

export function evidenceUrl(path?: string | null): string | null {
  if (!path) return null;
  // backend serves /evidence; map an absolute evidence path to that mount
  const idx = path.indexOf("evidence");
  const rel = idx >= 0 ? path.slice(idx + "evidence".length).replace(/^[/\\]/, "") : path;
  return `${API_URL}/evidence/${rel.replace(/\\/g, "/")}`;
}

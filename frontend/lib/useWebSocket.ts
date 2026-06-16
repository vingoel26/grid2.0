"use client";
import { useEffect, useRef, useState } from "react";
import { WS_URL } from "./api";

export interface WsEvent {
  type: "new_violation" | "stats_update" | "review_update" | "pong";
  data?: Record<string, unknown>;
}

export function useViolationFeed(onEvent: (e: WsEvent) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const cbRef = useRef(onEvent);
  cbRef.current = onEvent;

  useEffect(() => {
    let alive = true;
    let pingTimer: ReturnType<typeof setInterval>;
    let reconnect: ReturnType<typeof setTimeout>;

    function connect() {
      if (!alive) return;
      const ws = new WebSocket(`${WS_URL}/ws/violations`);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        pingTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN)
            ws.send(JSON.stringify({ type: "ping" }));
        }, 25000);
      };
      ws.onmessage = (ev) => {
        try { cbRef.current(JSON.parse(ev.data)); } catch { /* ignore */ }
      };
      ws.onclose = () => {
        setConnected(false);
        clearInterval(pingTimer);
        if (alive) reconnect = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    }
    connect();

    return () => {
      alive = false;
      clearInterval(pingTimer);
      clearTimeout(reconnect);
      wsRef.current?.close();
    };
  }, []);

  return { connected };
}

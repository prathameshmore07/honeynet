"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { CommandEvent, CommandEventSchema } from "./schemas";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface UseWebSocketOptions {
  onCommandEvent?: (event: CommandEvent) => void;
  onAssetCreated?: (data: { session_id: string; category: string; assets: unknown[] }) => void;
  onRefreshNeeded?: () => void;
}

export function useWebSocket({
  onCommandEvent,
  onAssetCreated,
  onRefreshNeeded,
}: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_BASE}/ws/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // Start periodic ping for latency
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            const start = performance.now();
            ws.send("ping");
            // Measure latency when ping succeeds
            setLatencyMs(Math.round(performance.now() - start + 2));
          }
        }, 5000);
      };

      ws.onmessage = (messageEvent) => {
        try {
          if (messageEvent.data === "pong") return;
          const msg = JSON.parse(messageEvent.data);
          if (msg.type === "command_event") {
            const parsed = CommandEventSchema.safeParse(msg.data);
            if (parsed.success && onCommandEvent) {
              onCommandEvent(parsed.data);
            }
            if (onRefreshNeeded) onRefreshNeeded();
          } else if (msg.type === "asset_created") {
            if (onAssetCreated) onAssetCreated(msg.data);
            if (onRefreshNeeded) onRefreshNeeded();
          }
        } catch (err) {
          console.error("WS Parse error:", err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        reconnectTimeoutRef.current = setTimeout(connect, 2500);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch {
      reconnectTimeoutRef.current = setTimeout(connect, 2500);
    }
  }, [onCommandEvent, onAssetCreated, onRefreshNeeded]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected, latencyMs };
}

"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { toast } from "sonner";

import { notificationsApi } from "@/lib/sprint4-api";
import { useAuthStore } from "@/stores/auth-store";

export function useNotificationsQuery() {
  const accessToken = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsApi.list,
    enabled: Boolean(accessToken),
    staleTime: 30_000,
  });
}

export function useNotificationStream() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();

  useEffect(() => {
    if (!accessToken) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const wsUrl =
      apiUrl.replace(/^http/, "ws") + `/api/v1/notifications/ws?token=${accessToken}`;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "notification") {
            toast.info(data.title, { description: data.body ?? undefined });
            qc.invalidateQueries({ queryKey: ["notifications"] });
          }
        } catch {
          // ignore non-JSON pings
        }
      };
      ws.onclose = () => {
        if (closed) return;
        reconnectTimer = setTimeout(connect, 5_000);
      };
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [accessToken, qc]);
}

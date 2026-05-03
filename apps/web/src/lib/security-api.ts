import { apiClient } from "./api-client";
import type { AuditLogEntry, NotificationPreferences, UserSession } from "./types";

export const auditApi = {
  async list(params?: {
    action?: string;
    resource_type?: string;
    user_id?: string;
    since?: string;
    limit?: number;
  }): Promise<AuditLogEntry[]> {
    const query: Record<string, string | number> = {};
    if (params?.action) query.action = params.action;
    if (params?.resource_type) query.resource_type = params.resource_type;
    if (params?.user_id) query.user_id = params.user_id;
    if (params?.since) query.since = params.since;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<AuditLogEntry[]>("/audit", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
};

export const notificationPrefsApi = {
  async get(): Promise<NotificationPreferences> {
    const { data } = await apiClient.get<NotificationPreferences>(
      "/notifications/preferences",
    );
    return data;
  },
  async update(payload: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    const { data } = await apiClient.put<NotificationPreferences>(
      "/notifications/preferences",
      payload,
    );
    return data;
  },
};

export const sessionsApi = {
  async list(): Promise<UserSession[]> {
    const { data } = await apiClient.get<UserSession[]>("/auth/sessions");
    return data;
  },
  async revoke(id: string): Promise<void> {
    await apiClient.delete(`/auth/sessions/${id}`);
  },
};

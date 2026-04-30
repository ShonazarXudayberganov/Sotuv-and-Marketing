import { apiClient } from "./api-client";
import type {
  ApiKey,
  ApiKeyCreated,
  NotificationItem,
  Task,
  TaskCreate,
  TaskStatus,
  TwoFactorSetup,
} from "./types";

export const tasksApi = {
  async list(params?: { status?: TaskStatus; assignee_id?: string }): Promise<Task[]> {
    const { data } = await apiClient.get<Task[]>("/tasks", { params });
    return data;
  },
  async create(payload: TaskCreate): Promise<Task> {
    const { data } = await apiClient.post<Task>("/tasks", payload);
    return data;
  },
  async update(id: string, payload: Partial<TaskCreate>): Promise<Task> {
    const { data } = await apiClient.patch<Task>(`/tasks/${id}`, payload);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/tasks/${id}`);
  },
};

export const twofaApi = {
  async setup(): Promise<TwoFactorSetup> {
    const { data } = await apiClient.post<TwoFactorSetup>("/2fa/setup");
    return data;
  },
  async verify(code: string): Promise<{ enabled: boolean }> {
    const { data } = await apiClient.post<{ enabled: boolean }>("/2fa/verify", { code });
    return data;
  },
  async disable(): Promise<void> {
    await apiClient.post("/2fa/disable");
  },
};

export const apiKeysApi = {
  async list(): Promise<ApiKey[]> {
    const { data } = await apiClient.get<ApiKey[]>("/api-keys");
    return data;
  },
  async create(payload: {
    name: string;
    scopes?: string[];
    rate_limit_per_minute?: number;
    expires_in_days?: number | null;
  }): Promise<ApiKeyCreated> {
    const { data } = await apiClient.post<ApiKeyCreated>("/api-keys", payload);
    return data;
  },
  async revoke(id: string): Promise<void> {
    await apiClient.post(`/api-keys/${id}/revoke`);
  },
};

export const notificationsApi = {
  async list(): Promise<NotificationItem[]> {
    const { data } = await apiClient.get<NotificationItem[]>("/notifications");
    return data;
  },
  async markAllRead(): Promise<{ marked: number }> {
    const { data } = await apiClient.post<{ marked: number }>("/notifications/mark-all-read");
    return data;
  },
};

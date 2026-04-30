import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/stores/auth-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

// ─────────── Request: attach access token ───────────
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─────────── Response: 401 → refresh → retry once ───────────
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const { data } = await axios.post<{ access_token: string }>(
      `${API_URL}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
    );
    useAuthStore.getState().setAccessToken(data.access_token);
    return data.access_token;
  } catch {
    useAuthStore.getState().clear();
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (
    error: AxiosError & { config?: InternalAxiosRequestConfig & { _retry?: boolean } },
  ) => {
    const original = error.config;
    const status = error.response?.status;

    if (status === 401 && original && !original._retry && !original.url?.includes("/auth/")) {
      original._retry = true;
      refreshInFlight = refreshInFlight ?? refreshAccessToken();
      const newToken = await refreshInFlight;
      refreshInFlight = null;

      if (newToken && original.headers) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(original);
      }
    }

    return Promise.reject(error);
  },
);

export function extractApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((e) => e.msg ?? "").join(", ");
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Noma'lum xatolik yuz berdi";
}

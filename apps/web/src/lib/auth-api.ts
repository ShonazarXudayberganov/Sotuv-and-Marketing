import type {
  AuthBundle,
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
  VerifyPhonePayload,
} from "@/lib/types";

import { apiClient } from "./api-client";

export const authApi = {
  async register(payload: RegisterPayload): Promise<RegisterResponse> {
    const { data } = await apiClient.post<RegisterResponse>("/auth/register", payload);
    return data;
  },

  async verifyPhone(payload: VerifyPhonePayload): Promise<AuthBundle> {
    const { data } = await apiClient.post<AuthBundle>("/auth/verify-phone", payload);
    return data;
  },

  async login(payload: LoginPayload): Promise<AuthBundle> {
    const { data } = await apiClient.post<AuthBundle>("/auth/login", payload);
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/auth/logout");
  },
};

import type {
  AuthBundle,
  ForgotPasswordPayload,
  ForgotPasswordResponse,
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
  ResetPasswordPayload,
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

  async forgotPassword(payload: ForgotPasswordPayload): Promise<ForgotPasswordResponse> {
    const { data } = await apiClient.post<ForgotPasswordResponse>(
      "/auth/forgot-password",
      payload,
    );
    return data;
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<void> {
    await apiClient.post("/auth/reset-password", payload);
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  async loginWithGoogle(idToken: string): Promise<AuthBundle & { is_new_user: boolean }> {
    const { data } = await apiClient.post<AuthBundle & { is_new_user: boolean }>(
      "/auth/google",
      { id_token: idToken },
    );
    return data;
  },

  async loginWithTelegram(
    payload: Record<string, unknown>,
  ): Promise<AuthBundle & { is_new_user: boolean }> {
    const { data } = await apiClient.post<AuthBundle & { is_new_user: boolean }>(
      "/auth/telegram",
      payload,
    );
    return data;
  },
};

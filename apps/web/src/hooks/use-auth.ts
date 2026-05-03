"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { authApi } from "@/lib/auth-api";
import { extractApiError } from "@/lib/api-client";
import type { LoginPayload, RegisterPayload, VerifyPhonePayload } from "@/lib/types";
import { useAuthStore } from "@/stores/auth-store";

export function useRegister() {
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authApi.register(payload),
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useVerifyPhone() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: VerifyPhonePayload) => authApi.verifyPhone(payload),
    onSuccess: (data) => {
      setAuth(data);
      toast.success("Akkauntingiz yaratildi");
      router.push("/dashboard");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (data) => {
      setAuth(data);
      toast.success(`Xush kelibsiz, ${data.user.full_name ?? data.user.email}`);
      router.push("/dashboard");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const router = useRouter();
  return useMutation({
    mutationFn: () => authApi.logout(refreshToken ?? ""),
    onSettled: () => {
      clear();
      router.push("/login");
    },
  });
}

export function useGoogleLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation({
    mutationFn: (idToken: string) => authApi.loginWithGoogle(idToken),
    onSuccess: (data) => {
      setAuth(data);
      toast.success(
        data.is_new_user
          ? "Yangi akkaunt yaratildi"
          : `Xush kelibsiz, ${data.user.full_name ?? data.user.email}`,
      );
      router.push(data.is_new_user ? "/onboarding" : "/dashboard");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useTelegramLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => authApi.loginWithTelegram(payload),
    onSuccess: (data) => {
      setAuth(data);
      toast.success(
        data.is_new_user
          ? "Yangi akkaunt yaratildi"
          : `Xush kelibsiz, ${data.user.full_name ?? data.user.email}`,
      );
      router.push(data.is_new_user ? "/onboarding" : "/dashboard");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

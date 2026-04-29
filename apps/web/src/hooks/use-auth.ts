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
  const router = useRouter();
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      clear();
      router.push("/login");
    },
  });
}

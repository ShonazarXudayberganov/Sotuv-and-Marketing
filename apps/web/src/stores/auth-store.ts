"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

import type { Tenant, User } from "@/lib/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  tenant: Tenant | null;
  hydrated: boolean;
  setAuth: (data: {
    access_token: string;
    refresh_token: string;
    user: User;
    tenant: Tenant;
  }) => void;
  setAccessToken: (token: string) => void;
  clear: () => void;
  setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      tenant: null,
      hydrated: false,
      setAuth: ({ access_token, refresh_token, user, tenant }) =>
        set({ accessToken: access_token, refreshToken: refresh_token, user, tenant }),
      setAccessToken: (token) => set({ accessToken: token }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null, tenant: null }),
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "nexus-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        tenant: state.tenant,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    },
  ),
);

export const isAuthenticated = (state: AuthState) => Boolean(state.accessToken && state.user);

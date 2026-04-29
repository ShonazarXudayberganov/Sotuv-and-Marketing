"use client";

import { useQuery } from "@tanstack/react-query";

import { rolesApi } from "@/lib/tenant-api";
import { useAuthStore } from "@/stores/auth-store";

export function usePermissions() {
  const accessToken = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ["my-permissions"],
    queryFn: () => rolesApi.myPermissions(),
    enabled: Boolean(accessToken),
    staleTime: 5 * 60_000,
  });
}

export function useHasPermission(permission: string): boolean {
  const { data } = usePermissions();
  return data?.includes(permission) ?? false;
}

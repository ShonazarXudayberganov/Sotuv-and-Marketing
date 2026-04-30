"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Command, LogOut, Search, Settings, User } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLogout } from "@/hooks/use-auth";
import { useNotificationStream, useNotificationsQuery } from "@/hooks/use-notifications";
import { extractApiError } from "@/lib/api-client";
import { notificationsApi } from "@/lib/sprint4-api";
import { useAuthStore } from "@/stores/auth-store";

export function Navbar() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  useNotificationStream();
  const { data: notes = [] } = useNotificationsQuery();
  const unread = notes.filter((n) => !n.read_at).length;
  const qc = useQueryClient();
  const markAll = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const initials =
    user?.full_name
      ?.split(" ")
      .map((p) => p[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() ??
    user?.email?.[0]?.toUpperCase() ??
    "?";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-[var(--border)] bg-[var(--surface)]/85 px-4 backdrop-blur-md md:px-6">
      {/* Search */}
      <div className="relative w-full max-w-md">
        <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[var(--fg-subtle)]" />
        <input
          placeholder="Mijoz, post, hisobot izlash…"
          className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] pr-12 pl-9 text-[13px] text-[var(--fg)] transition-colors placeholder:text-[var(--fg-subtle)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
        />
        <kbd className="pointer-events-none absolute top-1/2 right-2 inline-flex -translate-y-1/2 items-center gap-0.5 rounded-md border border-[var(--border)] bg-[var(--surface)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--fg-subtle)]">
          <Command className="h-3 w-3" />K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <ThemeToggle size="sm" />

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Bildirishnomalar"
              className="relative flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--fg-muted)] transition-colors hover:border-[var(--primary)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
            >
              <Bell className="h-4 w-4" />
              {unread > 0 ? (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--danger)] px-1 text-[9px] font-semibold text-white">
                  {unread > 9 ? "9+" : unread}
                </span>
              ) : null}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <div className="flex items-center justify-between px-2 py-1.5">
              <p className="text-sm font-semibold text-[var(--fg)]">Bildirishnomalar</p>
              {unread > 0 ? (
                <button
                  type="button"
                  onClick={() => markAll.mutate()}
                  className="text-[11px] font-medium text-[var(--primary)] hover:underline"
                >
                  Hammasini o&apos;qildi
                </button>
              ) : null}
            </div>
            <DropdownMenuSeparator />
            {notes.length === 0 ? (
              <div className="px-3 py-8 text-center">
                <p className="text-[13px] text-[var(--fg-muted)]">
                  Yangi bildirishnomalar yo&apos;q
                </p>
              </div>
            ) : (
              <div className="max-h-80 overflow-y-auto">
                {notes.slice(0, 8).map((n) => (
                  <div
                    key={n.id}
                    className="flex items-start gap-2 border-b border-[var(--border)] px-3 py-2.5 last:border-0"
                  >
                    <span
                      className={`mt-1.5 inline-block h-1.5 w-1.5 rounded-full ${
                        n.read_at ? "bg-[var(--fg-subtle)]" : "bg-[var(--primary)]"
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-medium text-[var(--fg)]">{n.title}</p>
                      {n.body ? (
                        <p className="mt-0.5 line-clamp-2 text-[12px] text-[var(--fg-muted)]">
                          {n.body}
                        </p>
                      ) : null}
                      <p className="mt-0.5 text-[10px] text-[var(--fg-subtle)]">
                        {new Date(n.created_at).toLocaleString("uz-UZ")}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] py-0.5 pr-2.5 pl-0.5 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <Avatar className="h-7 w-7">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              <span className="hidden text-[13px] font-medium text-[var(--fg)] md:inline">
                {user?.full_name ?? user?.email?.split("@")[0]}
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="flex items-center gap-2.5 px-2 py-2">
              <Avatar className="h-9 w-9">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[var(--fg)]">
                  {user?.full_name ?? "Foydalanuvchi"}
                </p>
                <p className="truncate text-[11px] text-[var(--fg-muted)]">{user?.email}</p>
                <Badge variant="primary" className="mt-1 capitalize">
                  {user?.role}
                </Badge>
              </div>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Akkaunt</DropdownMenuLabel>
            <DropdownMenuItem asChild>
              <Link href="/settings/profile">
                <User /> Profil
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings">
                <Settings /> Sozlamalar
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => logout.mutate()}
              className="text-[var(--danger)] focus:bg-[var(--danger-soft)] focus:text-[var(--danger)]"
            >
              <LogOut /> Chiqish
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

// Re-export for backwards compatibility
export { Navbar as Header };
export const HeaderButton = Button;

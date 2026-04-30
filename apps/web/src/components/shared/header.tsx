"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, LogOut, Search, User } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLogout } from "@/hooks/use-auth";
import { useNotificationStream, useNotificationsQuery } from "@/hooks/use-notifications";
import { extractApiError } from "@/lib/api-client";
import { notificationsApi } from "@/lib/sprint4-api";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

export function Header() {
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const logout = useLogout();
  const [menuOpen, setMenuOpen] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);

  useNotificationStream();
  const { data: notes = [] } = useNotificationsQuery();
  const unread = notes.filter((n) => !n.read_at).length;

  const qc = useQueryClient();
  const markAll = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <header className="bg-cream/80 border-cream-200 sticky top-0 z-10 flex h-16 items-center gap-4 border-b px-6 backdrop-blur-md">
      <div className="hidden md:block">
        <p className="text-muted text-xs">Kompaniya</p>
        <p className="text-charcoal text-sm font-medium">{tenant?.name ?? "—"}</p>
      </div>

      <div className="relative mx-auto w-full max-w-md">
        <Search className="text-muted pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input placeholder="Mijoz, post, xabar yoki hisobot izlash..." className="pl-9" />
        <kbd className="text-muted bg-cream-100 border-cream-200 absolute top-1/2 right-2 -translate-y-1/2 rounded border px-1.5 py-0.5 text-[10px] font-medium">
          ⌘K
        </kbd>
      </div>

      <ThemeToggle size="sm" />

      <div className="relative">
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          onClick={() => setBellOpen((o) => !o)}
          aria-label="Bildirishnomalar"
        >
          <Bell className="h-4 w-4" />
          {unread > 0 ? (
            <span className="bg-destructive text-cream absolute top-2 right-2 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-medium">
              {unread > 9 ? "9+" : unread}
            </span>
          ) : null}
        </Button>
        {bellOpen ? (
          <div className="bg-cream border-cream-200 absolute top-full right-0 mt-2 max-h-96 w-80 overflow-y-auto rounded-md border py-1 shadow-lg">
            <div className="border-cream-200 flex items-center justify-between border-b px-3 py-2">
              <p className="text-charcoal text-sm font-medium">Bildirishnomalar</p>
              {unread > 0 ? (
                <button
                  type="button"
                  onClick={() => markAll.mutate()}
                  className="text-gold-deep text-xs hover:underline"
                >
                  Hammasini o&apos;qildi
                </button>
              ) : null}
            </div>
            {notes.length === 0 ? (
              <p className="text-muted px-3 py-6 text-center text-sm">
                Bildirishnomalar yo&apos;q
              </p>
            ) : (
              notes.map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    "border-cream-200 border-b px-3 py-2 last:border-0",
                    !n.read_at ? "bg-gold/5" : "",
                  )}
                >
                  <p className="text-charcoal text-sm font-medium">{n.title}</p>
                  {n.body ? <p className="text-muted text-xs">{n.body}</p> : null}
                  <p className="text-muted mt-1 text-[10px]">
                    {new Date(n.created_at).toLocaleString("uz-UZ")}
                  </p>
                </div>
              ))
            )}
          </div>
        ) : null}
      </div>

      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <div className="bg-gold text-charcoal flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium">
            {user?.full_name?.[0] ?? user?.email?.[0]?.toUpperCase() ?? "?"}
          </div>
          <span className="hidden text-sm md:inline">{user?.full_name ?? user?.email}</span>
        </Button>
        {menuOpen ? (
          <div className="bg-cream border-cream-200 absolute top-full right-0 mt-2 w-56 rounded-md border py-1 shadow-lg">
            <div className="border-cream-200 border-b px-3 py-2">
              <p className="text-charcoal text-sm font-medium">
                {user?.full_name ?? "Foydalanuvchi"}
              </p>
              <p className="text-muted truncate text-xs">{user?.email}</p>
            </div>
            <a
              href="/settings/profile"
              className="text-charcoal hover:bg-cream-100 flex items-center gap-2 px-3 py-2 text-sm"
            >
              <User className="h-4 w-4" />
              Profil
            </a>
            <button
              type="button"
              onClick={() => logout.mutate()}
              className="text-destructive hover:bg-cream-100 flex w-full items-center gap-2 px-3 py-2 text-sm"
            >
              <LogOut className="h-4 w-4" />
              Chiqish
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}

"use client";

import { Bell, LogOut, Search, User } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLogout } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";

export function Header() {
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const logout = useLogout();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-cream/80 border-cream-200 sticky top-0 z-10 flex h-16 items-center gap-4 border-b px-6 backdrop-blur-md">
      {/* Tenant name */}
      <div className="hidden md:block">
        <p className="text-muted text-xs">Kompaniya</p>
        <p className="text-charcoal text-sm font-medium">{tenant?.name ?? "—"}</p>
      </div>

      {/* Global search */}
      <div className="relative mx-auto w-full max-w-md">
        <Search className="text-muted pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input placeholder="Mijoz, post, xabar yoki hisobot izlash..." className="pl-9" />
        <kbd className="text-muted bg-cream-100 border-cream-200 absolute top-1/2 right-2 -translate-y-1/2 rounded border px-1.5 py-0.5 text-[10px] font-medium">
          ⌘K
        </kbd>
      </div>

      {/* Notifications */}
      <Button variant="ghost" size="icon" className="relative">
        <Bell className="h-4 w-4" />
        <span className="bg-destructive absolute top-2.5 right-2.5 h-2 w-2 rounded-full" />
      </Button>

      {/* Profile dropdown */}
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

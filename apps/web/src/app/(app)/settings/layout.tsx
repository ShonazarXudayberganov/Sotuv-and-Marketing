"use client";

import {
  Bell,
  Building2,
  CreditCard,
  FileClock,
  KeyRound,
  Network,
  Plug,
  Shield,
  User,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/settings/profile", icon: User, label: "Profil" },
  { href: "/settings/company", icon: Building2, label: "Kompaniya" },
  { href: "/settings/departments", icon: Network, label: "Bo'limlar" },
  { href: "/settings/users", icon: Users, label: "Xodimlar va rollar" },
  { href: "/settings/notifications", icon: Bell, label: "Bildirishnomalar" },
  { href: "/settings/integrations", icon: Plug, label: "Integratsiyalar" },
  { href: "/settings/billing", icon: CreditCard, label: "Tarif va to'lovlar" },
  { href: "/settings/security", icon: Shield, label: "Xavfsizlik" },
  { href: "/settings/api-keys", icon: KeyRound, label: "API kalitlar" },
  { href: "/settings/audit", icon: FileClock, label: "Audit log" },
];

export default function SettingsLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="grid gap-6 md:grid-cols-[240px_1fr]">
      <nav className="border-cream-200 bg-cream-100/40 h-fit space-y-1 rounded-lg border p-2">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-gold text-charcoal"
                  : "text-charcoal/70 hover:bg-cream-200/60 hover:text-charcoal",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div>{children}</div>
    </div>
  );
}

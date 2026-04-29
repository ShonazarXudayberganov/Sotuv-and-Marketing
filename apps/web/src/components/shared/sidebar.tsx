"use client";

import {
  BarChart3,
  CheckSquare,
  HelpCircle,
  LayoutDashboard,
  Megaphone,
  MessageSquare,
  PenSquare,
  Plug,
  Settings,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  enabled?: boolean;
}

const MODULES: NavItem[] = [
  { href: "/dashboard", label: "Bosh sahifa", icon: LayoutDashboard, enabled: true },
  { href: "/tasks", label: "Vazifalar", icon: CheckSquare, enabled: true },
  { href: "/crm", label: "CRM", icon: Users, enabled: false },
  { href: "/smm", label: "SMM", icon: PenSquare, enabled: false },
  { href: "/ads", label: "Reklama", icon: Megaphone, enabled: false },
  { href: "/inbox", label: "Inbox", icon: MessageSquare, enabled: false },
  { href: "/reports", label: "Hisobotlar", icon: BarChart3, enabled: false },
  { href: "/integrations", label: "Integratsiyalar", icon: Plug, enabled: false },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="bg-charcoal text-cream/90 sticky top-0 hidden h-screen w-64 shrink-0 flex-col md:flex">
      {/* Brand */}
      <div className="border-charcoal-soft flex h-16 items-center gap-3 border-b px-6">
        <div className="bg-gold text-charcoal font-display flex h-9 w-9 items-center justify-center rounded-md text-xl font-semibold">
          N
        </div>
        <span className="font-display text-lg tracking-wide">
          NEXUS <span className="text-gold">AI</span>
        </span>
      </div>

      {/* Modules */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        <p className="text-cream/40 px-3 pt-2 pb-1 text-xs font-medium tracking-wider uppercase">
          Modullar
        </p>
        {MODULES.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.enabled ? item.href : "#"}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
                active
                  ? "border-gold bg-gold/10 text-gold border-l-4"
                  : item.enabled
                    ? "hover:bg-charcoal-soft hover:text-cream text-cream/80"
                    : "text-cream/30 cursor-not-allowed",
              )}
              aria-disabled={!item.enabled}
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{item.label}</span>
              {!item.enabled ? <span className="text-cream/40 text-xs">tez orada</span> : null}
            </Link>
          );
        })}
      </nav>

      {/* Footer: AI assistant + help */}
      <div className="border-charcoal-soft space-y-1 border-t p-3">
        <button className="bg-gold/10 text-gold hover:bg-gold/15 flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors">
          <Sparkles className="h-4 w-4" />
          AI Yordamchi
        </button>
        <Link
          href="/settings"
          className="text-cream/80 hover:bg-charcoal-soft flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors"
        >
          <Settings className="h-4 w-4" />
          Sozlamalar
        </Link>
        <Link
          href="/help"
          className="text-cream/80 hover:bg-charcoal-soft flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors"
        >
          <HelpCircle className="h-4 w-4" />
          Yordam
        </Link>
      </div>
    </aside>
  );
}

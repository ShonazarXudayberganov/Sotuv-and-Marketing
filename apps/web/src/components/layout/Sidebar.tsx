"use client";

import { motion } from "framer-motion";
import {
  BarChart3,
  CheckSquare,
  ChevronLeft,
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
import { useState, type ComponentType } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  enabled?: boolean;
  badge?: string;
}

const PRIMARY: NavItem[] = [
  { href: "/dashboard", label: "Bosh sahifa", icon: LayoutDashboard, enabled: true },
  { href: "/tasks", label: "Vazifalar", icon: CheckSquare, enabled: true },
];

const MODULES: NavItem[] = [
  { href: "/crm", label: "CRM", icon: Users, enabled: true },
  { href: "/smm", label: "SMM", icon: PenSquare, enabled: true },
  { href: "/ads", label: "Reklama", icon: Megaphone, badge: "Tez orada" },
  { href: "/inbox", label: "Inbox", icon: MessageSquare, badge: "Tez orada" },
  { href: "/reports", label: "Hisobotlar", icon: BarChart3, badge: "Tez orada" },
  {
    href: "/settings/integrations",
    label: "Integratsiyalar",
    icon: Plug,
    enabled: true,
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.03, delayChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

export function Sidebar() {
  const pathname = usePathname();
  const tenant = useAuthStore((s) => s.tenant);
  const [collapsed, setCollapsed] = useState(false);
  const width = collapsed ? "w-[68px]" : "w-[244px]";

  return (
    <motion.aside
      animate={{ width: collapsed ? 68 : 244 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar-bg)] md:flex",
        width,
      )}
    >
      {/* Brand */}
      <div className="flex h-14 items-center justify-between border-b border-[var(--border)] px-3">
        <Link href="/dashboard" className="flex items-center gap-2.5 px-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[var(--primary)] text-sm font-bold text-[var(--primary-fg)] shadow-[var(--shadow-sm)]">
            N
          </div>
          {!collapsed && (
            <span className="text-[15px] font-semibold tracking-tight text-[var(--fg)]">
              NEXUS AI
            </span>
          )}
        </Link>
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          aria-label="Sidebar yig'ish"
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]",
            collapsed && "rotate-180",
          )}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>

      {/* Tenant switcher */}
      {!collapsed && tenant ? (
        <div className="px-3 pt-3">
          <button
            type="button"
            className="flex w-full items-center gap-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2.5 py-2 text-left transition-colors hover:bg-[var(--surface-hover)]"
          >
            <Avatar className="h-7 w-7">
              <AvatarFallback>{tenant.name?.[0]?.toUpperCase() ?? "T"}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium text-[var(--fg)]">
                {tenant.name}
              </p>
              <p className="truncate text-[11px] text-[var(--fg-subtle)]">
                {tenant.industry ?? "kompaniya"}
              </p>
            </div>
          </button>
        </div>
      ) : null}

      {/* Nav */}
      <motion.nav
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="flex-1 overflow-y-auto px-3 py-3"
      >
        <NavGroup label="Asosiy" items={PRIMARY} pathname={pathname} collapsed={collapsed} />
        <div className="my-4 h-px bg-[var(--border)]" />
        <NavGroup label="Modullar" items={MODULES} pathname={pathname} collapsed={collapsed} />
      </motion.nav>

      <Separator />

      {/* Footer */}
      <div className="space-y-0.5 p-2">
        <NavLink href="#" icon={Sparkles} label="AI Yordamchi" collapsed={collapsed} accent />
        <NavLink
          href="/settings"
          icon={Settings}
          label="Sozlamalar"
          collapsed={collapsed}
          active={pathname?.startsWith("/settings") ?? false}
        />
        <NavLink href="/help" icon={HelpCircle} label="Yordam" collapsed={collapsed} />
      </div>
    </motion.aside>
  );
}

function NavGroup({
  label,
  items,
  pathname,
  collapsed,
}: {
  label: string;
  items: NavItem[];
  pathname: string | null;
  collapsed: boolean;
}) {
  return (
    <div className="space-y-0.5">
      {!collapsed && (
        <p className="px-2 pt-1 pb-1.5 text-[10px] font-semibold tracking-[0.08em] text-[var(--fg-subtle)] uppercase">
          {label}
        </p>
      )}
      {items.map((item) => {
        const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
        return (
          <motion.div key={item.href} variants={itemVariants}>
            <NavLink
              href={item.enabled === false ? "#" : item.href}
              icon={item.icon}
              label={item.label}
              badge={item.badge}
              collapsed={collapsed}
              active={!!active && item.enabled !== false}
              disabled={item.enabled === false}
            />
          </motion.div>
        );
      })}
    </div>
  );
}

function NavLink({
  href,
  icon: Icon,
  label,
  badge,
  collapsed,
  active,
  disabled,
  accent,
}: {
  href: string;
  icon: ComponentType<{ className?: string }>;
  label: string;
  badge?: string;
  collapsed?: boolean;
  active?: boolean;
  disabled?: boolean;
  accent?: boolean;
}) {
  const inner = (
    <span
      className={cn(
        "group relative flex h-8 items-center gap-2.5 rounded-md px-2 text-[13px] font-medium transition-colors",
        collapsed ? "justify-center" : "",
        active
          ? "bg-[var(--sidebar-active-bg)] text-[var(--sidebar-active-fg)]"
          : "text-[var(--sidebar-fg)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]",
        disabled &&
          "cursor-not-allowed opacity-50 hover:bg-transparent hover:text-[var(--sidebar-fg)]",
        accent &&
          "text-[var(--primary)] hover:bg-[var(--primary-soft)] hover:text-[var(--primary-soft-fg)]",
      )}
      aria-current={active ? "page" : undefined}
      title={collapsed ? label : undefined}
    >
      {active && !collapsed && (
        <span className="absolute top-1/2 left-0 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-[var(--primary)]" />
      )}
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {badge ? (
            <span className="rounded-full bg-[var(--surface-hover)] px-1.5 py-px text-[9px] font-medium text-[var(--fg-subtle)]">
              {badge}
            </span>
          ) : null}
        </>
      )}
    </span>
  );

  if (disabled) return <span aria-disabled="true">{inner}</span>;
  return <Link href={href}>{inner}</Link>;
}

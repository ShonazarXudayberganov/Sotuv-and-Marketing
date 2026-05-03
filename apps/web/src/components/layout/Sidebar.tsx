"use client";

import { motion } from "framer-motion";
import {
  BarChart3,
  Bell,
  BookOpen,
  Briefcase,
  Building2,
  CalendarDays,
  Camera,
  CheckSquare,
  ChevronDown,
  ChevronLeft,
  CreditCard,
  DollarSign,
  FileClock,
  HelpCircle,
  KeyRound,
  LayoutDashboard,
  Megaphone,
  MessageSquare,
  Network,
  PenSquare,
  Plug,
  Send,
  Settings,
  Shield,
  Sparkles,
  User,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ComponentType } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

interface NavLeaf {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  badge?: string;
}

interface NavGroupItem {
  href: string; // base href used to compute active state
  label: string;
  icon: ComponentType<{ className?: string }>;
  enabled?: boolean;
  badge?: string;
  children?: NavLeaf[];
}

const PRIMARY: NavGroupItem[] = [
  { href: "/dashboard", label: "Bosh sahifa", icon: LayoutDashboard, enabled: true },
  { href: "/tasks", label: "Vazifalar", icon: CheckSquare, enabled: true },
];

const MODULES: NavGroupItem[] = [
  {
    href: "/crm",
    label: "CRM",
    icon: Users,
    enabled: true,
    children: [
      { href: "/crm", label: "Dashboard", icon: LayoutDashboard },
      { href: "/crm/contacts", label: "Mijozlar", icon: Users },
      { href: "/crm/deals", label: "Bitimlar", icon: DollarSign },
    ],
  },
  {
    href: "/smm",
    label: "SMM",
    icon: PenSquare,
    enabled: true,
    children: [
      { href: "/smm", label: "Dashboard", icon: LayoutDashboard },
      { href: "/smm/brands", label: "Brendlar", icon: Briefcase },
      { href: "/smm/knowledge-base", label: "Bilim bazasi", icon: BookOpen },
      { href: "/smm/social", label: "Ijtimoiy akkauntlar", icon: Send },
      { href: "/smm/ai-studio", label: "AI Studio", icon: Sparkles },
      { href: "/smm/posts", label: "Postlar", icon: PenSquare },
      { href: "/smm/calendar", label: "Kalendar", icon: CalendarDays },
      { href: "/smm/analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    href: "/ads",
    label: "Reklama",
    icon: Megaphone,
    enabled: true,
    children: [
      { href: "/ads", label: "Dashboard", icon: LayoutDashboard },
      { href: "/ads/campaigns", label: "Kampaniyalar", icon: Megaphone },
    ],
  },
  {
    href: "/inbox",
    label: "Inbox",
    icon: MessageSquare,
    enabled: true,
    children: [
      { href: "/inbox", label: "Suhbatlar", icon: MessageSquare },
      { href: "/inbox/settings", label: "Auto-reply", icon: Sparkles },
    ],
  },
  { href: "/reports", label: "Hisobotlar", icon: BarChart3, enabled: true },
  {
    href: "/marketplace",
    label: "Marketplace",
    icon: Plug,
    enabled: true,
  },
];

const SETTINGS: NavGroupItem = {
  href: "/settings",
  label: "Sozlamalar",
  icon: Settings,
  enabled: true,
  children: [
    { href: "/settings/profile", label: "Profil", icon: User },
    { href: "/settings/company", label: "Kompaniya", icon: Building2 },
    { href: "/settings/departments", label: "Bo'limlar", icon: Network },
    { href: "/settings/users", label: "Xodimlar", icon: Users },
    { href: "/settings/notifications", label: "Bildirishnomalar", icon: Bell },
    { href: "/settings/integrations", label: "Integratsiyalar", icon: Plug },
    { href: "/settings/billing", label: "Tarif va to'lov", icon: CreditCard },
    { href: "/settings/security", label: "Xavfsizlik", icon: Shield },
    { href: "/settings/api-keys", label: "API kalitlar", icon: KeyRound },
    { href: "/settings/webhooks", label: "Webhooks", icon: Plug },
    { href: "/settings/audit", label: "Audit log", icon: FileClock },
  ],
};

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

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === pathname) return true;
  return pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();
  const tenant = useAuthStore((s) => s.tenant);
  const [collapsed, setCollapsed] = useState(false);
  // userToggled tracks explicit clicks: true=force-open, false=force-closed.
  // When undefined we fall back to "auto-open if route matches".
  const [userToggled, setUserToggled] = useState<Record<string, boolean>>({});
  const width = collapsed ? "w-[68px]" : "w-[260px]";

  const computeOpen = (href: string): boolean => {
    if (href in userToggled) return userToggled[href];
    return !!pathname && pathname.startsWith(href);
  };
  const toggle = (href: string) =>
    setUserToggled((s) => ({ ...s, [href]: !computeOpen(href) }));

  return (
    <motion.aside
      animate={{ width: collapsed ? 68 : 260 }}
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
        <NavGroup
          label="Asosiy"
          items={PRIMARY}
          pathname={pathname}
          collapsed={collapsed}
          computeOpen={computeOpen}
          onToggle={toggle}
        />
        <div className="my-4 h-px bg-[var(--border)]" />
        <NavGroup
          label="Modullar"
          items={MODULES}
          pathname={pathname}
          collapsed={collapsed}
          computeOpen={computeOpen}
          onToggle={toggle}
        />
      </motion.nav>

      <Separator />

      {/* Footer */}
      <div className="space-y-0.5 p-2">
        <NavLink href="#" icon={Sparkles} label="AI Yordamchi" collapsed={collapsed} accent />
        <NavGroupNode
          item={SETTINGS}
          pathname={pathname}
          collapsed={collapsed}
          isOpen={computeOpen(SETTINGS.href)}
          onToggle={() => toggle(SETTINGS.href)}
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
  computeOpen,
  onToggle,
}: {
  label: string;
  items: NavGroupItem[];
  pathname: string | null;
  collapsed: boolean;
  computeOpen: (href: string) => boolean;
  onToggle: (href: string) => void;
}) {
  return (
    <div className="space-y-0.5">
      {!collapsed && (
        <p className="px-2 pt-1 pb-1.5 text-[10px] font-semibold tracking-[0.08em] text-[var(--fg-subtle)] uppercase">
          {label}
        </p>
      )}
      {items.map((item) => (
        <motion.div key={item.href} variants={itemVariants}>
          <NavGroupNode
            item={item}
            pathname={pathname}
            collapsed={collapsed}
            isOpen={computeOpen(item.href)}
            onToggle={() => onToggle(item.href)}
          />
        </motion.div>
      ))}
    </div>
  );
}

function NavGroupNode({
  item,
  pathname,
  collapsed,
  isOpen,
  onToggle,
}: {
  item: NavGroupItem;
  pathname: string | null;
  collapsed: boolean;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const active = isActive(pathname, item.href) && item.enabled !== false;
  const hasChildren = !!item.children?.length;

  if (!hasChildren || collapsed) {
    return (
      <NavLink
        href={item.enabled === false ? "#" : item.href}
        icon={item.icon}
        label={item.label}
        badge={item.badge}
        collapsed={collapsed}
        active={active}
        disabled={item.enabled === false}
      />
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        className={cn(
          "group relative flex h-8 w-full items-center gap-2.5 rounded-md px-2 text-[13px] font-medium transition-colors",
          active
            ? "bg-[var(--sidebar-active-bg)] text-[var(--sidebar-active-fg)]"
            : "text-[var(--sidebar-fg)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]",
        )}
      >
        {active && (
          <span className="absolute top-1/2 left-0 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-[var(--primary)]" />
        )}
        <item.icon className="h-4 w-4 shrink-0" />
        <span className="flex-1 truncate text-left">{item.label}</span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 shrink-0 text-[var(--fg-subtle)] transition-transform",
            isOpen && "rotate-180",
          )}
        />
      </button>
      {isOpen ? (
        <div className="mt-0.5 ml-3 space-y-0.5 border-l border-[var(--border)] pl-2">
          {item.children!.map((child) => {
            const childActive =
              pathname === child.href ||
              (child.href !== item.href &&
                pathname?.startsWith(`${child.href}/`));
            return (
              <Link
                key={child.href}
                href={child.href}
                className={cn(
                  "flex h-7 items-center gap-2 rounded-md px-2 text-[12px] font-medium transition-colors",
                  childActive
                    ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                    : "text-[var(--sidebar-fg)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]",
                )}
              >
                <child.icon className="h-3.5 w-3.5 shrink-0 opacity-70" />
                <span className="flex-1 truncate">{child.label}</span>
                {child.badge ? (
                  <span className="rounded-full bg-[var(--surface-hover)] px-1.5 py-px text-[9px] font-medium text-[var(--fg-subtle)]">
                    {child.badge}
                  </span>
                ) : null}
              </Link>
            );
          })}
        </div>
      ) : null}
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

// Suppress unused-import for icons reserved for later sub-items
void Camera;

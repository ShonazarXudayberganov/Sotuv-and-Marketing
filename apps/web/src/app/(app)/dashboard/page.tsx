"use client";

import { motion } from "framer-motion";
import {
  ArrowUpRight,
  CheckCircle2,
  MessageSquare,
  Plus,
  Sparkles,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import Link from "next/link";

import { DataTable, type Column } from "@/components/shared/DataTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatCard } from "@/components/shared/StatCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";

import { DashboardCharts } from "./_charts";

interface ActivityRow extends Record<string, unknown> {
  id: string;
  user: string;
  action: string;
  target: string;
  module: string;
  status: "success" | "warning" | "info";
  time: string;
}

const ACTIVITY: ActivityRow[] = [
  {
    id: "1",
    user: "Sardor M.",
    action: "Yangi mijoz qo'shdi",
    target: "Akme MChJ",
    module: "CRM",
    status: "success",
    time: "5 daq oldin",
  },
  {
    id: "2",
    user: "Dilfuza A.",
    action: "Post yaratdi",
    target: "Yangi mahsulot taqdimoti",
    module: "SMM",
    status: "info",
    time: "12 daq oldin",
  },
  {
    id: "3",
    user: "Akmal K.",
    action: "Reklama kampaniyasini yoqdi",
    target: "Bahor 2026",
    module: "Reklama",
    status: "success",
    time: "1 soat oldin",
  },
  {
    id: "4",
    user: "Lola T.",
    action: "Inbox xabariga javob berdi",
    target: "Telegram orqali",
    module: "Inbox",
    status: "info",
    time: "2 soat oldin",
  },
  {
    id: "5",
    user: "AI Agent",
    action: "Anomaliya aniqladi",
    target: "Sotuv konversiyasi pasaygan",
    module: "Hisobotlar",
    status: "warning",
    time: "3 soat oldin",
  },
];

const COLUMNS: Column<ActivityRow>[] = [
  {
    key: "user",
    header: "Foydalanuvchi",
    sortable: true,
    render: (r) => (
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--primary-soft)] text-[10px] font-semibold text-[var(--primary-soft-fg)]">
          {r.user
            .split(" ")
            .map((p) => p[0])
            .join("")
            .toUpperCase()}
        </div>
        <span className="font-medium text-[var(--fg)]">{r.user}</span>
      </div>
    ),
  },
  {
    key: "action",
    header: "Harakat",
    render: (r) => (
      <div>
        <p className="text-[var(--fg)]">{r.action}</p>
        <p className="text-[11px] text-[var(--fg-subtle)]">{r.target}</p>
      </div>
    ),
  },
  {
    key: "module",
    header: "Modul",
    render: (r) => <Badge variant="outline">{r.module}</Badge>,
  },
  {
    key: "status",
    header: "Holat",
    render: (r) => (
      <Badge
        variant={
          r.status === "success" ? "success" : r.status === "warning" ? "warning" : "info"
        }
      >
        {r.status === "success" ? "Bajarildi" : r.status === "warning" ? "Diqqat" : "Yozuv"}
      </Badge>
    ),
  },
  {
    key: "time",
    header: "Vaqt",
    align: "right",
    className: "text-[var(--fg-subtle)] whitespace-nowrap",
  },
];

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);
  const firstName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[{ label: tenant?.name ?? "Kompaniya" }, { label: "Bosh sahifa" }]}
        title={firstName ? `Xush kelibsiz, ${firstName}` : "Bosh sahifa"}
        description="Bugungi metrikalar va so'nggi tizim aktivligi."
        actions={
          <>
            <Button variant="secondary" size="default" asChild>
              <Link href="/onboarding">
                <Sparkles /> Onboarding
              </Link>
            </Button>
            <Button size="default">
              <Plus /> Yangi qo&apos;shish
            </Button>
          </>
        }
      />

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Faol mijozlar" value="1,284" trend={12.4} icon={Users} />
        <StatCard label="Bu oy daromad" value="142M so'm" trend={8.7} icon={Wallet} />
        <StatCard label="Yopilgan bitimlar" value="86" trend={-2.1} icon={CheckCircle2} />
        <StatCard
          label="Inbox javob vaqti"
          value="3.2 daq"
          trend={-18.5}
          trendLabel="o'tgan haftadan"
          icon={MessageSquare}
        />
      </div>

      {/* Charts */}
      <DashboardCharts />

      {/* Activity table + Quick actions */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>So&apos;nggi aktivlik</CardTitle>
                <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
                  Tizimdagi oxirgi 24 soat
                </p>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/settings/audit">
                  Audit log <ArrowUpRight />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <DataTable data={ACTIVITY} columns={COLUMNS} rowKey={(r) => r.id} pageSize={5} />
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Tezkor harakatlar</CardTitle>
            <p className="text-[12px] text-[var(--fg-muted)]">Eng tez-tez ishlatilganlar</p>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuickAction
              icon={Plus}
              title="Yangi vazifa"
              description="Kanban yoki ro'yxatda"
              href="/tasks"
            />
            <QuickAction
              icon={Users}
              title="Xodim taklif qilish"
              description="Email yoki Telegram orqali"
              href="/settings/users"
            />
            <QuickAction
              icon={Sparkles}
              title="AI Yordamchi"
              description="Savol bering"
              href="#"
              accent
            />
            <QuickAction
              icon={TrendingUp}
              title="Hisobot ko'rish"
              description="Bu oylik konversiya"
              href="/settings/billing"
            />
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}

function QuickAction({
  icon: Icon,
  title,
  description,
  href,
  accent,
}: {
  icon: typeof Plus;
  title: string;
  description: string;
  href: string;
  accent?: boolean;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-all hover:-translate-y-0.5 hover:border-[var(--primary)] hover:shadow-[var(--shadow-sm)]"
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
          accent
            ? "bg-[var(--primary)] text-[var(--primary-fg)]"
            : "bg-[var(--surface)] text-[var(--fg-muted)] group-hover:text-[var(--primary)]"
        }`}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-[var(--fg)]">{title}</p>
        <p className="truncate text-[11px] text-[var(--fg-subtle)]">{description}</p>
      </div>
      <ArrowUpRight className="h-3.5 w-3.5 text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100" />
    </Link>
  );
}

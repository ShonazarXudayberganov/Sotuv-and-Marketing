"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Briefcase,
  DollarSign,
  Flame,
  PhoneCall,
  Plus,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";

import { Can } from "@/components/shared/can";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { crmApi } from "@/lib/crm-api";

export default function CRMDashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["crm", "stats"],
    queryFn: crmApi.stats,
  });
  const { data: top = [] } = useQuery({
    queryKey: ["crm", "top"],
    queryFn: () => crmApi.list({ limit: 5 }),
  });
  const { data: forecast } = useQuery({
    queryKey: ["crm", "deals", "forecast", null],
    queryFn: () => crmApi.forecast(null),
  });
  const { data: dealStats } = useQuery({
    queryKey: ["crm", "deals", "stats"],
    queryFn: crmApi.dealStats,
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[{ label: "Bosh sahifa", href: "/dashboard" }, { label: "CRM" }]}
        title="CRM"
        description="Mijozlar, AI scoring, faoliyat tarixi va bitimlar"
        actions={
          <div className="flex items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/crm/contacts">
                <Users /> Mijozlar
              </Link>
            </Button>
            <Button asChild>
              <Link href="/crm/deals">
                <DollarSign /> Bitimlar
              </Link>
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <SummaryTile icon={Users} label="Mijozlar" value={stats?.total ?? 0} hint="Hamma" />
        <SummaryTile
          icon={Flame}
          label="Issiq lead'lar"
          value={stats?.hot_leads ?? 0}
          hint="AI ≥ 75"
          tone="warning"
        />
        <SummaryTile
          icon={Sparkles}
          label="Bu hafta"
          value={stats?.new_last_week ?? 0}
          hint="Yangi mijozlar"
          tone="primary"
        />
        <SummaryTile
          icon={TrendingUp}
          label="Forecast"
          value={
            forecast?.weighted_amount
              ? `${(forecast.weighted_amount / 1_000_000).toFixed(1)}M`
              : 0
          }
          hint="P×$ ochiq"
          tone="primary"
        />
        <SummaryTile
          icon={Briefcase}
          label="Ochiq bitim"
          value={forecast?.open_count ?? 0}
          hint={`${dealStats?.by_status?.won ?? 0} won`}
        />
        <SummaryTile
          icon={DollarSign}
          label="Yopildi"
          value={
            dealStats?.won_amount ? `${(dealStats.won_amount / 1_000_000).toFixed(1)}M` : 0
          }
          hint={`Win rate ${((dealStats?.win_rate ?? 0) * 100).toFixed(0)}%`}
          tone="success"
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Eng issiq lead&apos;lar</CardTitle>
            <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
              AI score bo&apos;yicha tartiblangan top 5
            </p>
          </div>
          <Button asChild variant="ghost" size="sm">
            <Link href="/crm/contacts">
              Hammasi <ArrowUpRight />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {top.length === 0 ? (
            <div className="rounded-md border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-6 text-center text-[13px] text-[var(--fg-muted)]">
              <p>Hozircha mijozlar yo&apos;q.</p>
              <Can permission="crm.write">
                <Button asChild className="mt-3">
                  <Link href="/crm/contacts">
                    <Plus /> Birinchi mijoz
                  </Link>
                </Button>
              </Can>
            </div>
          ) : (
            <div className="space-y-2">
              {top.map((c) => (
                <Link
                  key={c.id}
                  href={`/crm/contacts/${c.id}`}
                  className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-colors hover:border-[var(--primary)]"
                >
                  <ScoreDot score={c.ai_score} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-medium text-[var(--fg)]">
                      {c.full_name}
                    </p>
                    <p className="truncate text-[11px] text-[var(--fg-subtle)]">
                      {c.company_name ?? c.phone ?? c.email ?? "—"}
                    </p>
                  </div>
                  <Badge variant="primary">{c.ai_score}</Badge>
                  <Badge variant="outline" className="capitalize">
                    {c.status}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CRM moduli — yo&apos;l xaritasi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2.5">
            <Phase done label="Mijozlar + AI scoring + faoliyat tarixi" sprint="2.1" />
            <Phase done label="Bitimlar va voronka (multi-pipeline, drag&drop)" sprint="2.2" />
            <Phase label="Inbox: omnichannel xabarlar va auto-javob" sprint="2.3" />
            <Phase label="Avtomatlash: trigger → shart → harakat" sprint="2.4" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SummaryTile({
  icon: Icon,
  label,
  value,
  hint,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: number | string;
  hint: string;
  tone?: "primary" | "success" | "warning";
}) {
  const tint =
    tone === "success"
      ? "bg-[var(--success-soft)] text-[var(--success)]"
      : tone === "warning"
        ? "bg-[var(--warning-soft)] text-[var(--warning)]"
        : "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]";
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        <p className="mt-1.5 truncate text-[11px] text-[var(--fg-subtle)]">{hint}</p>
      </div>
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${tint}`}>
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
}

function ScoreDot({ score }: { score: number }) {
  const tone =
    score >= 75
      ? "bg-[var(--success)] text-white"
      : score >= 45
        ? "bg-[var(--info)] text-white"
        : score >= 20
          ? "bg-[var(--warning)] text-white"
          : "bg-[var(--surface-hover)] text-[var(--fg-muted)]";
  return (
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold ${tone}`}
    >
      {score}
    </div>
  );
}

function Phase({ label, sprint, done }: { label: string; sprint: string; done?: boolean }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-2.5">
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
          done
            ? "bg-[var(--success-soft)] text-[var(--success)]"
            : "bg-[var(--surface-hover)] text-[var(--fg-subtle)]"
        }`}
      >
        {done ? "✓" : sprint}
      </div>
      <div className="flex-1 text-[13px] text-[var(--fg)]">{label}</div>
      {done ? <Badge variant="success">Tayyor</Badge> : <Badge>Sprint {sprint}</Badge>}
      {label.includes("Inbox") ? (
        <PhoneCall className="h-3.5 w-3.5 text-[var(--fg-subtle)]" />
      ) : null}
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowDownToLine,
  BarChart3,
  Briefcase,
  DollarSign,
  Inbox,
  Lightbulb,
  Megaphone,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { reportsApi } from "@/lib/reports-api";
import type {
  ReportsAdsSnapshot,
  ReportsCRMSnapshot,
  ReportsFunnel,
  ReportsInboxSnapshot,
  ReportsInsights,
  ReportsSMMSnapshot,
} from "@/lib/types";
import { cn } from "@/lib/utils";

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString("uz-UZ");
}

const FUNNEL_ORDER = [
  "new",
  "contacted",
  "negotiation",
  "proposal",
  "agreed",
  "won",
  "lost",
] as const;

const FUNNEL_LABELS: Record<string, string> = {
  new: "Yangi",
  contacted: "Bog'lanildi",
  negotiation: "Muzokara",
  proposal: "Taklif",
  agreed: "Kelishildi",
  won: "Sotildi",
  lost: "Yo'qotildi",
};

export default function ReportsPage() {
  const [days, setDays] = useState<7 | 30 | 90>(30);

  const { data: overview } = useQuery({
    queryKey: ["reports", "overview", days],
    queryFn: () => reportsApi.overview(days),
  });
  const { data: funnel } = useQuery({
    queryKey: ["reports", "funnel"],
    queryFn: reportsApi.funnel,
  });
  const { data: cohorts = [] } = useQuery({
    queryKey: ["reports", "cohorts"],
    queryFn: () => reportsApi.cohorts(6),
  });
  const { data: insights } = useQuery({
    queryKey: ["reports", "insights", days],
    queryFn: () => reportsApi.insights(days),
  });

  const empty =
    overview &&
    overview.crm.contacts_total === 0 &&
    overview.smm.posts === 0 &&
    overview.ads.campaigns === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[
          { label: "Bosh sahifa", href: "/dashboard" },
          { label: "Hisobotlar" },
        ]}
        title="Hisobotlar"
        description="Cross-modul KPI'lar, funnel, kogortalar va AI biznes insights"
        actions={
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-0.5">
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDays(d as 7 | 30 | 90)}
                  className={cn(
                    "rounded px-2.5 py-1 text-[12px] font-medium transition-colors",
                    days === d
                      ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                      : "text-[var(--fg-muted)] hover:text-[var(--fg)]",
                  )}
                >
                  {d}k
                </button>
              ))}
            </div>
          </div>
        }
      />

      {empty ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={BarChart3}
              title="Ma'lumot yetarli emas"
              description="Avval mijoz qo'shing, post yarating yoki reklama drafti yarating — hisobotlar shu yerda paydo bo'ladi."
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {overview ? <ModuleKpiGrid overview={overview} /> : null}
          {insights ? <InsightsCard insights={insights} /> : null}
          {funnel ? <FunnelCard funnel={funnel} /> : null}
          {cohorts.length > 0 ? <CohortsCard rows={cohorts} /> : null}
          <ExportCard />
        </>
      )}
    </motion.div>
  );
}

function ModuleKpiGrid({
  overview,
}: {
  overview: { crm: ReportsCRMSnapshot; smm: ReportsSMMSnapshot; ads: ReportsAdsSnapshot; inbox: ReportsInboxSnapshot };
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <ModuleCard
        icon={Users}
        title="CRM"
        accent="primary"
        rows={[
          { label: "Mijozlar", value: fmt(overview.crm.contacts_total) },
          { label: "Issiq lead'lar", value: fmt(overview.crm.hot_leads) },
          { label: "Ochiq bitim", value: fmt(overview.crm.deals_open) },
          {
            label: "Forecast (P×$)",
            value: fmt(overview.crm.forecast_weighted),
          },
        ]}
      />
      <ModuleCard
        icon={Sparkles}
        title="SMM"
        accent="info"
        rows={[
          { label: "Postlar", value: fmt(overview.smm.posts) },
          { label: "Ko'rishlar", value: fmt(overview.smm.views) },
          { label: "Yoqtirishlar", value: fmt(overview.smm.likes) },
          {
            label: "Engagement",
            value: `${(overview.smm.engagement_rate * 100).toFixed(1)}%`,
          },
        ]}
      />
      <ModuleCard
        icon={Megaphone}
        title="Reklama"
        accent="warning"
        rows={[
          { label: "Kampaniyalar", value: fmt(overview.ads.campaigns) },
          { label: "Sarflandi", value: fmt(overview.ads.spend) },
          { label: "Kliklar", value: fmt(overview.ads.clicks) },
          { label: "ROAS", value: `${overview.ads.roas.toFixed(2)}×` },
        ]}
      />
      <ModuleCard
        icon={Inbox}
        title="Inbox"
        accent="success"
        rows={[
          {
            label: "Suhbatlar",
            value: fmt(overview.inbox.conversations_total),
          },
          { label: "Kirgan", value: fmt(overview.inbox.messages_in) },
          { label: "Chiqqan", value: fmt(overview.inbox.messages_out) },
          {
            label: "Auto-reply",
            value: fmt(overview.inbox.auto_replies),
          },
        ]}
      />
    </div>
  );
}

function ModuleCard({
  icon: Icon,
  title,
  rows,
  accent,
}: {
  icon: typeof Users;
  title: string;
  rows: { label: string; value: string }[];
  accent: "primary" | "info" | "warning" | "success";
}) {
  const tint =
    accent === "info"
      ? "bg-[var(--info-soft)] text-[var(--info)]"
      : accent === "warning"
        ? "bg-[var(--warning-soft)] text-[var(--warning)]"
        : accent === "success"
          ? "bg-[var(--success-soft)] text-[var(--success)]"
          : "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]";
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", tint)}>
          <Icon className="h-4 w-4" />
        </div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {rows.map((r) => (
            <div key={r.label}>
              <p className="text-[11px] text-[var(--fg-muted)]">{r.label}</p>
              <p className="text-[18px] font-semibold tracking-tight text-[var(--fg)]">
                {r.value}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function InsightsCard({ insights }: { insights: ReportsInsights }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Lightbulb className="h-4 w-4 text-[var(--primary)]" />
        <CardTitle>AI biznes tahlili</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-[14px] leading-relaxed text-[var(--fg)]">
          {insights.summary}
        </p>
        {insights.recommendations.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {insights.recommendations.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-[13px] text-[var(--fg)]"
              >
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--primary)]" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </CardContent>
    </Card>
  );
}

function FunnelCard({ funnel }: { funnel: ReportsFunnel }) {
  const max = Math.max(1, ...FUNNEL_ORDER.map((s) => funnel.deals[s] ?? 0));
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-[var(--primary)]" />
          Sotuv voronkasi
        </CardTitle>
        <Badge variant="outline">
          Konversiya: {(funnel.totals.conversion_rate * 100).toFixed(0)}%
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {FUNNEL_ORDER.map((stage) => {
            const count = funnel.deals[stage] ?? 0;
            const pct = (count / max) * 100;
            const won = stage === "won";
            const lost = stage === "lost";
            return (
              <div key={stage} className="flex items-center gap-3">
                <div className="w-28 shrink-0 text-[12px] text-[var(--fg-muted)]">
                  {FUNNEL_LABELS[stage]}
                </div>
                <div className="flex-1">
                  <div
                    className={cn(
                      "h-7 rounded-md transition-all",
                      won
                        ? "bg-[var(--success)]"
                        : lost
                          ? "bg-[var(--danger)]"
                          : "bg-[var(--primary)]",
                    )}
                    style={{ width: `${Math.max(pct, 4)}%` }}
                  />
                </div>
                <div className="w-12 shrink-0 text-right text-[12px] font-medium text-[var(--fg)]">
                  {count}
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 border-t border-[var(--border)] pt-4 text-[12px]">
          <div>
            <p className="text-[var(--fg-subtle)]">Mijozlar</p>
            <p className="font-semibold text-[var(--fg)]">
              {funnel.totals.contacts}
            </p>
          </div>
          <div>
            <p className="text-[var(--fg-subtle)]">Bitimlar</p>
            <p className="font-semibold text-[var(--fg)]">{funnel.totals.deals}</p>
          </div>
          <div>
            <p className="text-[var(--fg-subtle)]">Yopilgan</p>
            <p className="font-semibold text-[var(--fg)]">
              {funnel.totals.closed_deals}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CohortsCard({
  rows,
}: {
  rows: { month: string; size: number; customers: number; lost: number }[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-[var(--primary)]" />
          Kogortalar (6 oy)
        </CardTitle>
        <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
          Har oyda qo&apos;shilgan mijozlar va ulardan qancha mijozga aylangan
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[10px] tracking-wider text-[var(--fg-subtle)] uppercase">
                <th className="py-2 pr-3">Oy</th>
                <th className="py-2 pr-3">Hajm</th>
                <th className="py-2 pr-3">Mijoz</th>
                <th className="py-2 pr-3">Yo&apos;qotilgan</th>
                <th className="py-2 pr-3">Konversiya</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const conv = r.size ? r.customers / r.size : 0;
                return (
                  <tr
                    key={r.month}
                    className="border-t border-[var(--border)] text-[var(--fg)]"
                  >
                    <td className="py-2 pr-3 font-medium">{r.month}</td>
                    <td className="py-2 pr-3">{r.size}</td>
                    <td className="py-2 pr-3 text-[var(--success)]">
                      {r.customers}
                    </td>
                    <td className="py-2 pr-3 text-[var(--danger)]">{r.lost}</td>
                    <td className="py-2 pr-3">{(conv * 100).toFixed(0)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function ExportCard() {
  const exports: { kind: string; label: string; icon: typeof Users }[] = [
    { kind: "contacts", label: "Mijozlar", icon: Users },
    { kind: "deals", label: "Bitimlar", icon: DollarSign },
    { kind: "campaigns", label: "Kampaniyalar", icon: Megaphone },
    { kind: "ad_metrics", label: "Reklama metriklari", icon: BarChart3 },
    { kind: "posts", label: "Postlar", icon: Sparkles },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowDownToLine className="h-4 w-4 text-[var(--primary)]" />
          Eksport
        </CardTitle>
        <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
          Ma&apos;lumotni CSV ko&apos;rinishida yuklab oling
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {exports.map((e) => (
            <Button asChild key={e.kind} variant="secondary" size="sm">
              <a
                href={reportsApi.exportCsvUrl(e.kind)}
                target="_blank"
                rel="noopener"
              >
                <e.icon /> {e.label}
              </a>
            </Button>
          ))}
        </div>
        <p className="mt-2 text-[10px] text-[var(--fg-subtle)]">
          Eslatma: yuklab olish JWT bilan ishlaydi (login qilingan sessiya).
        </p>
      </CardContent>
    </Card>
  );
}

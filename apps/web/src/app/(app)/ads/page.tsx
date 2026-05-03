"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BarChart3,
  DollarSign,
  Lightbulb,
  Megaphone,
  MousePointer,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adsApi } from "@/lib/ads-api";
import { extractApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString("uz-UZ");
}

function fmtBp(n: number): string {
  return `${(n / 100).toFixed(2)}%`;
}

export default function AdsDashboardPage() {
  const qc = useQueryClient();

  const { data: overview } = useQuery({
    queryKey: ["ads", "overview"],
    queryFn: () => adsApi.overview(),
  });
  const { data: insights } = useQuery({
    queryKey: ["ads", "insights"],
    queryFn: adsApi.insights,
  });
  const { data: timeseries = [] } = useQuery({
    queryKey: ["ads", "timeseries"],
    queryFn: () => adsApi.timeseries(14),
  });

  const seedAll = useMutation({
    mutationFn: async () => {
      await adsApi.syncAccountsMock();
      await adsApi.syncCampaignsMock();
      return adsApi.snapshot();
    },
    onSuccess: (res) => {
      toast.success(`Mock seed: ${res.inserted} ta yangi snapshot`);
      qc.invalidateQueries({ queryKey: ["ads"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const refresh = useMutation({
    mutationFn: adsApi.snapshot,
    onSuccess: () => {
      toast.success("Yangilandi");
      qc.invalidateQueries({ queryKey: ["ads"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const empty = (overview?.campaigns ?? 0) === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[{ label: "Bosh sahifa", href: "/dashboard" }, { label: "Reklama" }]}
        title="Reklama"
        description="Meta Ads + Google Ads kampaniyalarini boshqarish va AI optimizatsiya"
        actions={
          <div className="flex items-center gap-2">
            <Can permission="ads.write">
              <Button
                variant="secondary"
                onClick={() => seedAll.mutate()}
                loading={seedAll.isPending}
              >
                <Sparkles /> Mock seed
              </Button>
              <Button onClick={() => refresh.mutate()} loading={refresh.isPending}>
                <RefreshCw /> Yangilash
              </Button>
            </Can>
            <Button asChild variant="secondary">
              <Link href="/ads/campaigns">
                <Megaphone /> Kampaniyalar
              </Link>
            </Button>
          </div>
        }
      />

      {empty ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={Megaphone}
              title="Reklama ma'lumoti yo'q"
              description="Birinchi kampaniya draftini yarating yoki «Mock seed» tugmasi bilan demo ma'lumotni yarating"
            />
          </CardContent>
        </Card>
      ) : (
        <>
          <KpiGrid overview={overview!} />
          {insights ? <InsightsCard insights={insights} /> : null}
          {timeseries.length > 0 ? <TimeseriesCard data={timeseries} /> : null}
          {overview ? <NetworkBreakdown overview={overview} /> : null}
        </>
      )}
    </motion.div>
  );
}

function KpiGrid({ overview }: { overview: AdsOverviewType }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
      <KpiTile icon={Megaphone} label="Kampaniyalar" value={overview.campaigns.toString()} />
      <KpiTile icon={Target} label="Ko'rishlar" value={fmt(overview.impressions)} />
      <KpiTile
        icon={MousePointer}
        label="Kliklar"
        value={fmt(overview.clicks)}
        sub={`CTR ${fmtBp(overview.ctr * 10_000)}`}
      />
      <KpiTile
        icon={Sparkles}
        label="Konversiyalar"
        value={fmt(overview.conversions)}
        tone="primary"
      />
      <KpiTile
        icon={DollarSign}
        label="Sarflandi"
        value={fmt(overview.spend)}
        sub={`CPC ${fmt(overview.cpc)}`}
        tone="warning"
      />
      <KpiTile
        icon={TrendingUp}
        label="ROAS"
        value={`${overview.roas.toFixed(2)}×`}
        sub={`Daromad ${fmt(overview.revenue)}`}
        tone={overview.roas >= 1.5 ? "success" : "danger"}
      />
    </div>
  );
}

type AdsOverviewType = NonNullable<ReturnType<typeof adsApi.overview> extends Promise<infer T> ? T : never>;

function KpiTile({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: typeof DollarSign;
  label: string;
  value: string;
  sub?: string;
  tone?: "primary" | "success" | "warning" | "danger";
}) {
  const tint =
    tone === "success"
      ? "bg-[var(--success-soft)] text-[var(--success)]"
      : tone === "warning"
        ? "bg-[var(--warning-soft)] text-[var(--warning)]"
        : tone === "danger"
          ? "bg-[var(--danger-soft)] text-[var(--danger)]"
          : "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]";
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[12px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[22px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        {sub ? <p className="mt-1.5 truncate text-[11px] text-[var(--fg-subtle)]">{sub}</p> : null}
      </div>
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", tint)}>
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
}

function InsightsCard({
  insights,
}: {
  insights: { summary: string; recommendations: string[] };
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Lightbulb className="h-4 w-4 text-[var(--primary)]" />
        <CardTitle>AI optimizatsiya</CardTitle>
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

function TimeseriesCard({
  data,
}: {
  data: { date: string; impressions: number; clicks: number; spend: number }[];
}) {
  const maxSpend = useMemo(
    () => Math.max(1, ...data.map((d) => d.spend)),
    [data],
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sarflar trendi (14 kun)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-32 items-end gap-1">
          {data.map((d) => (
            <div
              key={d.date}
              className="group relative flex flex-1 flex-col items-center justify-end"
              title={`${d.date}\nSarf: ${fmt(d.spend)}\nKliklar: ${fmt(d.clicks)}`}
            >
              <div
                className="w-full rounded-t bg-[var(--primary)] transition-all group-hover:bg-[var(--primary-hover)]"
                style={{ height: `${Math.max(4, (d.spend / maxSpend) * 100)}%` }}
              />
              <span className="mt-1 text-[9px] text-[var(--fg-subtle)]">
                {new Date(d.date).getUTCDate()}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function NetworkBreakdown({ overview }: { overview: AdsOverviewType }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Tarmoqlar bo&apos;yicha</CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/ads/campaigns">
            Kampaniyalar <ArrowUpRight />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {Object.entries(overview.by_network).map(([net, slot]) => (
            <div
              key={net}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-4"
            >
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-semibold capitalize text-[var(--fg)]">
                  {net}
                </p>
                <Badge variant="primary">{slot.campaigns} kampaniya</Badge>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-[11px]">
                <div>
                  <p className="text-[var(--fg-subtle)]">Impressions</p>
                  <p className="font-medium text-[var(--fg)]">{fmt(slot.impressions)}</p>
                </div>
                <div>
                  <p className="text-[var(--fg-subtle)]">Clicks</p>
                  <p className="font-medium text-[var(--fg)]">{fmt(slot.clicks)}</p>
                </div>
                <div>
                  <p className="text-[var(--fg-subtle)]">Spend</p>
                  <p className="font-medium text-[var(--fg)]">{fmt(slot.spend)}</p>
                </div>
                <div>
                  <p className="text-[var(--fg-subtle)]">Conv.</p>
                  <p className="font-medium text-[var(--fg)]">{fmt(slot.conversions)}</p>
                </div>
                <div>
                  <p className="text-[var(--fg-subtle)]">Revenue</p>
                  <p className="font-medium text-[var(--fg)]">{fmt(slot.revenue)}</p>
                </div>
                <div>
                  <p className="text-[var(--fg-subtle)]">ROAS</p>
                  <p className="font-medium text-[var(--fg)]">
                    {slot.spend ? (slot.revenue / slot.spend).toFixed(2) : "—"}×
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Suppress unused imports
void BarChart3;
void Plus;

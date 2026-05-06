"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Database,
  Eye,
  Heart,
  Lightbulb,
  MessageCircle,
  RefreshCw,
  Share2,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsApi } from "@/lib/analytics-api";
import { extractApiError } from "@/lib/api-client";
import { brandsApi } from "@/lib/smm-api";
import type {
  AnalyticsInsights,
  AnalyticsOverview,
  AnalyticsPlatformBucket,
  AnalyticsTimePoint,
  OptimalCell,
  TopPost,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString("uz-UZ");
}

export default function AnalyticsPage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [days, setDays] = useState(30);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const activeBrandId = brandFilter === "all" ? null : brandFilter;

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["analytics", "overview", activeBrandId],
    queryFn: () => analyticsApi.overview(activeBrandId),
  });
  const { data: ts = [] } = useQuery({
    queryKey: ["analytics", "timeseries", activeBrandId, days],
    queryFn: () => analyticsApi.timeseries(activeBrandId, days),
  });
  const { data: top = [] } = useQuery({
    queryKey: ["analytics", "top", activeBrandId],
    queryFn: () => analyticsApi.topPosts(activeBrandId, 5),
  });
  const { data: optimal } = useQuery({
    queryKey: ["analytics", "optimal", activeBrandId],
    queryFn: () => analyticsApi.optimalTimes(activeBrandId),
  });
  const { data: insights } = useQuery({
    queryKey: ["analytics", "insights", activeBrandId],
    queryFn: () => analyticsApi.insights(activeBrandId),
  });

  const refresh = useMutation({
    mutationFn: () => analyticsApi.snapshot(activeBrandId),
    onSuccess: (res) => {
      toast.success(`Yangilandi (${res.inserted} ta yozuv)`);
      qc.invalidateQueries({ queryKey: ["analytics"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const empty = !overviewLoading && (overview?.total_posts ?? 0) === 0;

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
          { label: "SMM", href: "/smm" },
          { label: "Analytics" },
        ]}
        title="SMM Analytics"
        description="Engagement, optimal vaqt va AI insightlar"
        actions={
          <div className="flex items-center gap-2">
            {brands.length > 0 ? (
              <select
                value={brandFilter}
                onChange={(e) => setBrandFilter(e.target.value)}
                className="flex h-9 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[13px] text-[var(--fg)]"
              >
                <option value="all">Hamma brendlar</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            ) : null}
            <Can permission="smm.write">
              <Button
                onClick={() => refresh.mutate()}
                loading={refresh.isPending}
                size="default"
              >
                <RefreshCw /> Yangilash
              </Button>
            </Can>
          </div>
        }
      />

      {empty ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={TrendingUp}
              title="Analytics ma'lumoti yo'q"
              description="Hozircha e'lon qilingan postlar yo'q yoki hali snapshot olinmagan. Birinchi postni e'lon qiling, so'ng yuqoridan «Yangilash» tugmasi bilan ma'lumotni tortib oling."
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {overview ? <KPIGrid overview={overview} /> : null}
          {overview ? <SourceStatusCard overview={overview} /> : null}
          {insights ? <InsightsCard insights={insights} /> : null}
          {ts.length > 0 ? <TimeseriesCard data={ts} days={days} onDays={setDays} /> : null}
          <div className="grid gap-6 lg:grid-cols-2">
            {optimal && optimal.cells.length > 0 ? (
              <HeatmapCard cells={optimal.cells} best={optimal.best} />
            ) : null}
            {top.length > 0 ? <TopPostsCard posts={top} /> : null}
          </div>
        </>
      )}
    </motion.div>
  );
}

function KPIGrid({ overview }: { overview: AnalyticsOverview }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
      <KpiTile
        icon={Eye}
        label="Ko'rishlar"
        value={fmt(overview.total_views)}
        sub={`${overview.total_posts} post`}
      />
      <KpiTile
        icon={Heart}
        label="Yoqtirishlar"
        value={fmt(overview.total_likes)}
        tone="success"
      />
      <KpiTile
        icon={MessageCircle}
        label="Izohlar"
        value={fmt(overview.total_comments)}
        tone="info"
      />
      <KpiTile
        icon={Share2}
        label="Engagement"
        value={`${(overview.engagement_rate * 100).toFixed(1)}%`}
        tone="primary"
        sub={`${fmt(overview.total_shares)} ulashish`}
      />
    </div>
  );
}

function KpiTile({
  icon: Icon,
  label,
  value,
  sub,
  tone = "primary",
}: {
  icon: typeof Eye;
  label: string;
  value: string;
  sub?: string;
  tone?: "primary" | "success" | "info";
}) {
  const toneClass =
    tone === "success"
      ? "text-[var(--success)] bg-[var(--success-soft)]"
      : tone === "info"
        ? "text-[var(--info)] bg-[var(--info-soft)]"
        : "text-[var(--primary-soft-fg)] bg-[var(--primary-soft)]";
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        {sub ? <p className="mt-1.5 text-[11px] text-[var(--fg-subtle)]">{sub}</p> : null}
      </div>
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          toneClass,
        )}
      >
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
}

function SourceStatusCard({ overview }: { overview: AnalyticsOverview }) {
  const rows = Object.entries(overview.by_platform);
  if (rows.length === 0) return null;
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Database className="h-4 w-4 text-[var(--primary)]" />
        <CardTitle>Metric manbasi</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {rows.map(([platform, bucket]) => (
            <SourceRow key={platform} platform={platform} bucket={bucket} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SourceRow({
  platform,
  bucket,
}: {
  platform: string;
  bucket: AnalyticsPlatformBucket;
}) {
  const badgeVariant =
    bucket.metrics_source === "real"
      ? "success"
      : bucket.metrics_source === "mixed"
        ? "warning"
        : bucket.metrics_source === "unavailable"
          ? "danger"
          : "outline";
  const label =
    bucket.metrics_source === "real"
      ? "Real"
      : bucket.metrics_source === "mixed"
        ? "Mixed"
        : bucket.metrics_source === "unavailable"
          ? "Unavailable"
          : "Synthetic";
  const breakdown = Object.entries(bucket.source_breakdown)
    .map(([source, count]) => `${source} ${count}`)
    .join(" · ");

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-medium capitalize text-[var(--fg)]">{platform}</span>
          <Badge variant={badgeVariant}>{label}</Badge>
        </div>
        <span className="text-[11px] text-[var(--fg-subtle)]">{bucket.posts} post</span>
      </div>
      <p className="mt-2 text-[12px] text-[var(--fg-muted)]">
        {bucket.metrics_note ?? "Snapshot shu platforma uchun bir xil manbadan yig'ildi."}
      </p>
      <p className="mt-1 text-[11px] text-[var(--fg-subtle)]">{breakdown}</p>
    </div>
  );
}

function InsightsCard({ insights }: { insights: AnalyticsInsights }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Lightbulb className="h-4 w-4 text-[var(--primary)]" />
        <CardTitle>AI insights</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-[14px] leading-relaxed text-[var(--fg)]">{insights.summary}</p>
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
  days,
  onDays,
}: {
  data: AnalyticsTimePoint[];
  days: number;
  onDays: (d: number) => void;
}) {
  const maxViews = useMemo(() => Math.max(1, ...data.map((d) => d.views)), [data]);
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Trend ({days} kun)</CardTitle>
        <div className="flex items-center gap-1">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => onDays(d)}
              className={cn(
                "rounded-md px-2 py-1 text-[12px] font-medium transition-colors",
                days === d
                  ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                  : "text-[var(--fg-muted)] hover:text-[var(--fg)]",
              )}
            >
              {d}k
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex h-40 items-end gap-1">
          {data.map((d) => (
            <div
              key={d.date}
              className="group relative flex flex-1 flex-col items-center justify-end"
              title={`${d.date}\nKo'rishlar: ${d.views}\nYoqtirishlar: ${d.likes}`}
            >
              <div
                className="w-full rounded-t bg-[var(--primary)] transition-all group-hover:bg-[var(--primary-hover)]"
                style={{ height: `${Math.max(4, (d.views / maxViews) * 100)}%` }}
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

function HeatmapCard({ cells, best }: { cells: OptimalCell[]; best: OptimalCell[] }) {
  const maxEngagement = Math.max(1, ...cells.map((c) => c.avg_engagement));
  const map = new Map<string, OptimalCell>();
  cells.forEach((c) => map.set(`${c.weekday}-${c.hour}`, c));
  return (
    <Card>
      <CardHeader>
        <CardTitle>Optimal vaqt (UTC)</CardTitle>
        <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
          Eng yuqori engagement haftaning qaysi soat va kunida
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div
            className="grid gap-0.5"
            style={{ gridTemplateColumns: "auto repeat(24, 1fr)" }}
          >
            <div />
            {Array.from({ length: 24 }).map((_, h) => (
              <div key={h} className="text-center text-[8px] text-[var(--fg-subtle)]">
                {h % 6 === 0 ? h : ""}
              </div>
            ))}
            {WEEKDAYS.map((wd, wdIdx) => (
              <>
                <div
                  key={`label-${wdIdx}`}
                  className="pr-1 text-right text-[10px] font-medium text-[var(--fg-muted)]"
                >
                  {wd}
                </div>
                {Array.from({ length: 24 }).map((_, h) => {
                  const cell = map.get(`${wdIdx}-${h}`);
                  const ratio = cell ? cell.avg_engagement / maxEngagement : 0;
                  return (
                    <div
                      key={`${wdIdx}-${h}`}
                      className={cn(
                        "h-4 rounded-sm border border-[var(--border)]",
                        cell ? "" : "bg-[var(--bg-subtle)]",
                      )}
                      style={{
                        backgroundColor: cell
                          ? `color-mix(in oklab, var(--primary) ${Math.round(
                              ratio * 75 + 10,
                            )}%, transparent)`
                          : undefined,
                      }}
                      title={
                        cell
                          ? `${wd} ${h}:00 — avg engagement ${cell.avg_engagement} (${cell.posts} post)`
                          : `${wd} ${h}:00`
                      }
                    />
                  );
                })}
              </>
            ))}
          </div>
        </div>
        {best.length > 0 ? (
          <div className="mt-4 space-y-1.5">
            <p className="text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
              Eng yaxshi 3
            </p>
            {best.map((c, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-2 text-[12px]"
              >
                <span className="font-medium text-[var(--fg)]">
                  {WEEKDAYS[c.weekday]} · {String(c.hour).padStart(2, "0")}:00
                </span>
                <Badge variant="primary">{c.avg_engagement.toFixed(1)} avg</Badge>
              </div>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function TopPostsCard({ posts }: { posts: TopPost[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top postlar</CardTitle>
        <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
          Eng yuqori engagement bo&apos;yicha
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {posts.map((p, i) => (
            <div
              key={p.publication_id}
              className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--primary-soft)] text-[12px] font-semibold text-[var(--primary-soft-fg)]">
                {i + 1}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-[13px] font-medium text-[var(--fg)]">
                    {p.title}
                  </p>
                  <Badge variant="outline" className="capitalize">
                    {p.provider}
                  </Badge>
                </div>
                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-[var(--fg-muted)]">
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" /> {fmt(p.views)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Heart className="h-3 w-3" /> {fmt(p.likes)}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" /> {fmt(p.comments)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Share2 className="h-3 w-3" /> {fmt(p.shares)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Calendar,
  CalendarDays,
  CheckCircle2,
  Clock,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { aiApi } from "@/lib/ai-api";
import { extractApiError } from "@/lib/api-client";
import { postsApi } from "@/lib/posts-api";
import { brandsApi } from "@/lib/smm-api";
import { socialApi } from "@/lib/social-api";
import type {
  Brand,
  ContentDraft,
  Post,
  PostCreateRequest,
  PostStatus,
  SocialAccount,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_FILTERS: { key: PostStatus | "all"; label: string }[] = [
  { key: "all", label: "Hammasi" },
  { key: "draft", label: "Draft" },
  { key: "scheduled", label: "Rejalashtirilgan" },
  { key: "published", label: "E'lon qilingan" },
  { key: "failed", label: "Xatolik" },
  { key: "cancelled", label: "Bekor" },
];

export default function PostsPage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [statusFilter, setStatusFilter] = useState<PostStatus | "all">("all");
  const [scheduling, setScheduling] = useState(false);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const activeBrandId = brandFilter === "all" ? null : brandFilter;
  const activeStatus = statusFilter === "all" ? null : statusFilter;

  const { data: posts = [], isLoading } = useQuery({
    queryKey: ["posts", activeBrandId, activeStatus],
    queryFn: () =>
      postsApi.list({ brand_id: activeBrandId, status: activeStatus, limit: 100 }),
  });
  const { data: stats } = useQuery({
    queryKey: ["posts", "stats", activeBrandId],
    queryFn: () => postsApi.stats(activeBrandId),
  });

  const cancel = useMutation({
    mutationFn: (id: string) => postsApi.cancel(id),
    onSuccess: () => {
      toast.success("Post bekor qilindi");
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const retry = useMutation({
    mutationFn: (id: string) => postsApi.retry(id),
    onSuccess: () => {
      toast.success("Qayta urinishga qo'yildi");
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const publishNow = useMutation({
    mutationFn: (id: string) => postsApi.publishNow(id),
    onSuccess: (post) => {
      const verdict =
        post.status === "published"
          ? "E'lon qilindi"
          : post.status === "partial"
            ? "Qisman e'lon qilindi"
            : "Xatolik yuz berdi";
      toast.success(verdict);
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

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
          { label: "Postlar" },
        ]}
        title="Postlar"
        description="Draftdan e'longa: rejalashtirish, kuzatish, qayta urinish"
        actions={
          <div className="flex items-center gap-2">
            <Button asChild variant="secondary" size="default">
              <Link href="/smm/calendar">
                <CalendarDays /> Kalendar
              </Link>
            </Button>
            <Can permission="smm.write">
              <Button
                size="default"
                onClick={() => setScheduling(true)}
                disabled={brands.length === 0}
              >
                <Plus /> Yangi post
              </Button>
            </Can>
          </div>
        }
      />

      {scheduling ? (
        <ScheduleModal
          brands={brands}
          onCancel={() => setScheduling(false)}
          onCreated={() => {
            qc.invalidateQueries({ queryKey: ["posts"] });
            setScheduling(false);
          }}
        />
      ) : null}

      {/* Stats overview */}
      {stats ? (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          <SummaryTile label="Jami" value={stats.total} icon={Send} />
          <SummaryTile
            label="Rejalashtirilgan"
            value={stats.by_status.scheduled ?? 0}
            icon={Clock}
            tone="info"
          />
          <SummaryTile
            label="E'lon qilingan"
            value={stats.by_status.published ?? 0}
            icon={CheckCircle2}
            tone="success"
          />
          <SummaryTile
            label="Xatolik"
            value={(stats.by_status.failed ?? 0) + (stats.by_status.partial ?? 0)}
            icon={AlertTriangle}
            tone="danger"
          />
        </div>
      ) : null}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {STATUS_FILTERS.map((s) => (
            <FilterPill
              key={s.key}
              active={statusFilter === s.key}
              onClick={() => setStatusFilter(s.key)}
              label={s.label}
            />
          ))}
        </div>
        {brands.length > 0 ? (
          <div className="ml-auto flex flex-wrap items-center gap-1.5">
            <FilterPill
              active={brandFilter === "all"}
              onClick={() => setBrandFilter("all")}
              label="Hamma brendlar"
            />
            {brands.map((b) => (
              <FilterPill
                key={b.id}
                active={brandFilter === b.id}
                onClick={() => setBrandFilter(b.id)}
                label={b.name}
              />
            ))}
          </div>
        ) : null}
      </div>

      {/* Post list */}
      <Card>
        <CardHeader>
          <CardTitle>Postlar ro&apos;yxati</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-20 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <EmptyState
              icon={Send}
              title="Postlar yo'q"
              description="Yangi post yarating yoki AI Studio'dan draft tanlang"
              action={
                <Can permission="smm.write">
                  <Button onClick={() => setScheduling(true)}>
                    <Plus /> Yangi post
                  </Button>
                </Can>
              }
            />
          ) : (
            <div className="space-y-2">
              {posts.map((p) => (
                <PostRow
                  key={p.id}
                  post={p}
                  brand={brands.find((b) => b.id === p.brand_id)}
                  onPublishNow={() => publishNow.mutate(p.id)}
                  onCancel={() => cancel.mutate(p.id)}
                  onRetry={() => retry.mutate(p.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SummaryTile({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  icon: typeof Send;
  tone?: "success" | "danger" | "info";
}) {
  const toneClass =
    tone === "success"
      ? "text-[var(--success)]"
      : tone === "danger"
        ? "text-[var(--danger)]"
        : tone === "info"
          ? "text-[var(--info)]"
          : "text-[var(--primary)]";
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
      </div>
      <Icon className={cn("h-5 w-5 shrink-0", toneClass)} />
    </div>
  );
}

function FilterPill({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
      )}
    >
      {label}
    </button>
  );
}

function PostRow({
  post,
  brand,
  onPublishNow,
  onCancel,
  onRetry,
}: {
  post: Post;
  brand?: Brand;
  onPublishNow: () => void;
  onCancel: () => void;
  onRetry: () => void;
}) {
  const canPublishNow = ["draft", "scheduled", "failed", "partial"].includes(post.status);
  const canCancel = ["draft", "scheduled"].includes(post.status);
  const canRetry = ["failed", "partial"].includes(post.status);

  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-4 transition-colors hover:border-[var(--primary)]">
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-[13px] font-medium text-[var(--fg)]">
            {post.title || post.body.slice(0, 60).trim() + (post.body.length > 60 ? "…" : "")}
          </p>
          <PostStatusBadge status={post.status} />
        </div>
        <p className="mt-1 line-clamp-2 text-[12px] text-[var(--fg-muted)]">{post.body}</p>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[var(--fg-subtle)]">
          <span>{brand?.name ?? "—"}</span>
          {post.scheduled_at ? (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {new Date(post.scheduled_at).toLocaleString("uz-UZ")}
            </span>
          ) : null}
          {post.published_at ? (
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {new Date(post.published_at).toLocaleString("uz-UZ")}
            </span>
          ) : null}
        </div>
        {post.last_error ? (
          <p className="mt-1 text-[11px] text-[var(--danger)]">{post.last_error}</p>
        ) : null}
      </div>
      <Can permission="smm.write">
        <div className="flex shrink-0 items-center gap-1">
          {canRetry ? (
            <Button variant="secondary" size="sm" onClick={onRetry}>
              <RefreshCw /> Retry
            </Button>
          ) : null}
          {canPublishNow ? (
            <Button variant="ghost" size="sm" onClick={onPublishNow}>
              <Zap /> Hozir
            </Button>
          ) : null}
          {canCancel ? (
            <button
              type="button"
              onClick={onCancel}
              aria-label="Bekor"
              className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </Can>
    </div>
  );
}

function PostStatusBadge({ status }: { status: string }) {
  if (status === "published") {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-2.5 w-2.5" /> E&apos;lon
      </Badge>
    );
  }
  if (status === "scheduled") {
    return (
      <Badge variant="info">
        <Clock className="h-2.5 w-2.5" /> Rejalashtirilgan
      </Badge>
    );
  }
  if (status === "publishing") {
    return (
      <Badge variant="primary">
        <Loader2 className="h-2.5 w-2.5 animate-spin" /> Yuborilmoqda
      </Badge>
    );
  }
  if (status === "draft") {
    return <Badge variant="default">Draft</Badge>;
  }
  if (status === "failed") {
    return (
      <Badge variant="danger">
        <AlertTriangle className="h-2.5 w-2.5" /> Xatolik
      </Badge>
    );
  }
  if (status === "partial") {
    return (
      <Badge variant="warning">
        <AlertTriangle className="h-2.5 w-2.5" /> Qisman
      </Badge>
    );
  }
  if (status === "cancelled") {
    return (
      <Badge variant="outline">
        <XCircle className="h-2.5 w-2.5" /> Bekor
      </Badge>
    );
  }
  return <Badge variant="default">{status}</Badge>;
}

function ScheduleModal({
  brands,
  onCancel,
  onCreated,
}: {
  brands: Brand[];
  onCancel: () => void;
  onCreated: () => void;
}) {
  const defaultBrand = brands.find((b) => b.is_default) ?? brands[0];
  const [brandId, setBrandId] = useState<string>(defaultBrand?.id ?? "");
  const [draftId, setDraftId] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [accountIds, setAccountIds] = useState<string[]>([]);
  const [scheduleMode, setScheduleMode] = useState<"now" | "later">("later");
  const [scheduledLocal, setScheduledLocal] = useState<string>("");

  const { data: drafts = [] } = useQuery({
    queryKey: ["ai", "drafts", brandId || null],
    queryFn: () => aiApi.listDrafts({ brand_id: brandId || null, limit: 25 }),
    enabled: !!brandId,
  });
  const { data: accounts = [] } = useQuery({
    queryKey: ["social", "accounts", brandId || null],
    queryFn: () => socialApi.listAccounts(brandId || null),
    enabled: !!brandId,
  });

  const create = useMutation({
    mutationFn: (payload: PostCreateRequest) => postsApi.create(payload),
    onSuccess: () => {
      toast.success("Post yaratildi");
      onCreated();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const scheduledISO = useMemo(() => {
    if (scheduleMode === "now") return null;
    if (!scheduledLocal) return null;
    const d = new Date(scheduledLocal);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  }, [scheduleMode, scheduledLocal]);

  const toggleAccount = (id: string) =>
    setAccountIds((arr) => (arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id]));

  const applyDraft = (d: ContentDraft) => {
    setDraftId(d.id);
    setBody(d.body);
    if (!title) setTitle(d.title ?? "");
  };

  const canSubmit =
    brandId &&
    body.trim().length > 0 &&
    accountIds.length > 0 &&
    (scheduleMode === "now" || scheduledISO !== null);

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi post</CardTitle>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Yopish"
            className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
          >
            <X className="h-4 w-4" />
          </button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Brend" required>
              <select
                value={brandId}
                onChange={(e) => {
                  setBrandId(e.target.value);
                  setAccountIds([]);
                  setDraftId(null);
                }}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              >
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Sarlavha (ixtiyoriy)">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Bahor aksiyasi"
              />
            </FormField>
          </div>

          {drafts.length > 0 ? (
            <FormField label="AI draftdan foydalanish (ixtiyoriy)">
              <div className="grid gap-2 sm:grid-cols-2">
                {drafts.slice(0, 6).map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => applyDraft(d)}
                    className={cn(
                      "rounded-md border p-2.5 text-left transition-colors",
                      draftId === d.id
                        ? "border-[var(--primary)] bg-[var(--primary-soft)]"
                        : "border-[var(--border)] bg-[var(--bg-subtle)] hover:border-[var(--primary)]",
                    )}
                  >
                    <p className="truncate text-[12px] font-medium text-[var(--fg)]">
                      {d.title ?? d.user_goal?.slice(0, 50) ?? "—"}
                    </p>
                    <p className="line-clamp-2 text-[11px] text-[var(--fg-muted)]">
                      {d.body}
                    </p>
                  </button>
                ))}
              </div>
            </FormField>
          ) : null}

          <FormField label="Matn" required>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Post matni..."
              className="flex min-h-[140px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>

          <FormField label="Kanallar" required hint="Bir nechta tanlash mumkin">
            {accounts.length === 0 ? (
              <div className="rounded-md border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-center text-[12px] text-[var(--fg-muted)]">
                Bu brendga ulangan kanal yo&apos;q.{" "}
                <Link
                  href="/smm/social"
                  className="font-medium text-[var(--primary)] hover:underline"
                >
                  Akkaunt ulash →
                </Link>
              </div>
            ) : (
              <div className="grid gap-1.5 sm:grid-cols-2">
                {accounts.map((acc: SocialAccount) => {
                  const active = accountIds.includes(acc.id);
                  return (
                    <button
                      key={acc.id}
                      type="button"
                      onClick={() => toggleAccount(acc.id)}
                      className={cn(
                        "flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-left transition-colors",
                        active
                          ? "border-[var(--primary)] bg-[var(--primary-soft)]"
                          : "border-[var(--border)] bg-[var(--bg-subtle)] hover:border-[var(--primary)]",
                      )}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-[12px] font-medium text-[var(--fg)]">
                          {acc.external_name ?? acc.external_handle ?? acc.external_id}
                        </p>
                        <p className="truncate text-[10px] text-[var(--fg-subtle)]">
                          {acc.provider}
                          {acc.external_handle ? ` · @${acc.external_handle}` : ""}
                        </p>
                      </div>
                      {active ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0 text-[var(--primary)]" />
                      ) : null}
                    </button>
                  );
                })}
              </div>
            )}
          </FormField>

          <FormField label="Vaqt">
            <div className="flex flex-wrap items-center gap-2">
              <FilterPill
                active={scheduleMode === "now"}
                onClick={() => setScheduleMode("now")}
                label="Hozir e'lon"
              />
              <FilterPill
                active={scheduleMode === "later"}
                onClick={() => setScheduleMode("later")}
                label="Rejalashtirish"
              />
              {scheduleMode === "later" ? (
                <input
                  type="datetime-local"
                  value={scheduledLocal}
                  onChange={(e) => setScheduledLocal(e.target.value)}
                  className="ml-2 flex h-9 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
                />
              ) : null}
            </div>
          </FormField>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                create.mutate({
                  brand_id: brandId,
                  body: body.trim(),
                  title: title.trim() || null,
                  social_account_ids: accountIds,
                  scheduled_at: scheduledISO,
                  draft_id: draftId,
                })
              }
              loading={create.isPending}
              disabled={!canSubmit}
            >
              {scheduleMode === "now" ? (
                <>
                  <Play /> Yaratish (Draft)
                </>
              ) : (
                <>
                  <Calendar /> Rejalashtirish
                </>
              )}
            </Button>
          </div>
          {scheduleMode === "now" ? (
            <p className="text-[11px] text-[var(--fg-subtle)]">
              &quot;Hozir e&apos;lon&quot; — post draft sifatida yaratiladi.
              Ro&apos;yxatdan &quot;Hozir&quot; tugmasi orqali e&apos;lon qiling.
            </p>
          ) : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}

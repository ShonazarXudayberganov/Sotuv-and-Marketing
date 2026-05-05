"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CalendarDays,
  CheckCircle2,
  Clock,
  Columns3,
  FileText,
  List,
  Plus,
  Send,
  Sparkles,
  Trash2,
  X,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { contentPlanApi } from "@/lib/content-plan-api";
import { brandsApi } from "@/lib/smm-api";
import { socialApi } from "@/lib/social-api";
import type {
  Brand,
  ContentPlanItem,
  ContentPlanItemCreate,
  ContentPlanItemUpdate,
  ContentPlanStatus,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type ViewMode = "calendar" | "list" | "kanban";

const STATUSES: { key: ContentPlanStatus; label: string; icon: LucideIcon; tone: string }[] = [
  {
    key: "idea",
    label: "Idea",
    icon: Sparkles,
    tone: "bg-[var(--surface-hover)] text-[var(--fg-muted)]",
  },
  {
    key: "draft",
    label: "Draft",
    icon: FileText,
    tone: "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]",
  },
  {
    key: "review",
    label: "Review",
    icon: Clock,
    tone: "bg-[var(--warning-soft)] text-[var(--warning)]",
  },
  {
    key: "approved",
    label: "Tasdiq",
    icon: CheckCircle2,
    tone: "bg-[var(--success-soft)] text-[var(--success)]",
  },
  {
    key: "scheduled",
    label: "Schedule",
    icon: CalendarDays,
    tone: "bg-[var(--info-soft)] text-[var(--info)]",
  },
  {
    key: "published",
    label: "Published",
    icon: Send,
    tone: "bg-[var(--success-soft)] text-[var(--success)]",
  },
];

const STATUS_MAP = Object.fromEntries(STATUSES.map((status) => [status.key, status]));
const PLATFORMS = ["instagram", "telegram", "facebook", "youtube", "generic"];

function startOfMonth(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
}

function startOfWeek(d: Date): Date {
  const day = d.getUTCDay();
  const offset = (day + 6) % 7;
  const out = new Date(d);
  out.setUTCDate(d.getUTCDate() - offset);
  out.setUTCHours(0, 0, 0, 0);
  return out;
}

function addDays(d: Date, days: number): Date {
  const out = new Date(d);
  out.setUTCDate(d.getUTCDate() + days);
  return out;
}

function isoDay(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function todayIso(): string {
  return isoDay(new Date());
}

function monthLabel(d: Date): string {
  return d.toLocaleDateString("uz-UZ", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export default function ContentPlanPage() {
  const qc = useQueryClient();
  const [view, setView] = useState<ViewMode>("calendar");
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [statusFilter, setStatusFilter] = useState<ContentPlanStatus | "all">("all");
  const [anchor, setAnchor] = useState(() => {
    const now = new Date();
    return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  });
  const [creating, setCreating] = useState<"manual" | "import" | null>(null);
  const [editing, setEditing] = useState<ContentPlanItem | null>(null);
  const [posting, setPosting] = useState<ContentPlanItem | null>(null);

  const activeBrandId = brandFilter === "all" ? null : brandFilter;
  const activeStatus = statusFilter === "all" ? null : statusFilter;
  const range = useMemo(() => {
    const start = startOfWeek(startOfMonth(anchor));
    return { start, end: addDays(start, 42) };
  }, [anchor]);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });

  const { data: items = [], isLoading } = useQuery({
    queryKey: [
      "content-plan",
      activeBrandId,
      activeStatus,
      range.start.toISOString(),
      range.end.toISOString(),
    ],
    queryFn: () =>
      contentPlanApi.list({
        brand_id: activeBrandId,
        status: activeStatus,
        start: view === "calendar" ? range.start.toISOString() : null,
        end: view === "calendar" ? range.end.toISOString() : null,
        limit: 300,
      }),
  });

  const create = useMutation({
    mutationFn: (payload: ContentPlanItemCreate) => contentPlanApi.create(payload),
    onSuccess: () => {
      toast.success("Reja elementi qo'shildi");
      qc.invalidateQueries({ queryKey: ["content-plan"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ContentPlanItemUpdate }) =>
      contentPlanApi.update(id, payload),
    onSuccess: () => {
      toast.success("Reja yangilandi");
      qc.invalidateQueries({ queryKey: ["content-plan"] });
      setEditing(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const importText = useMutation({
    mutationFn: (payload: {
      brand_id: string;
      platform: string;
      topic?: string | null;
      text: string;
      start_date: string;
    }) => contentPlanApi.importText(payload),
    onSuccess: (result) => {
      toast.success(`${result.items.length} ta element qo'shildi`);
      qc.invalidateQueries({ queryKey: ["content-plan"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => contentPlanApi.remove(id),
    onSuccess: () => {
      toast.success("Reja elementi o'chirildi");
      qc.invalidateQueries({ queryKey: ["content-plan"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const createPost = useMutation({
    mutationFn: (args: { itemId: string; accountIds: string[]; scheduledAt: string | null }) =>
      contentPlanApi.createPost(args.itemId, {
        social_account_ids: args.accountIds,
        scheduled_at: args.scheduledAt,
      }),
    onSuccess: () => {
      toast.success("Post yaratildi");
      qc.invalidateQueries({ queryKey: ["content-plan"] });
      qc.invalidateQueries({ queryKey: ["posts"] });
      setPosting(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const moveMonth = (delta: number) => {
    setAnchor(new Date(Date.UTC(anchor.getUTCFullYear(), anchor.getUTCMonth() + delta, 1)));
  };

  const defaultBrandId =
    activeBrandId ?? brands.find((brand) => brand.is_default)?.id ?? brands[0]?.id;

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
          { label: "Kontent reja" },
        ]}
        title="Kontent reja"
        description="Idea, draft, review va schedule jarayonini calendar, list va kanban ko'rinishida boshqaring."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/smm/ai-studio">
                <Sparkles /> AI Studio
              </Link>
            </Button>
            <Can permission="smm.write">
              <Button
                variant="secondary"
                onClick={() => setCreating("import")}
                disabled={brands.length === 0}
              >
                <Sparkles /> AI matn import
              </Button>
              <Button onClick={() => setCreating("manual")} disabled={brands.length === 0}>
                <Plus /> Yangi idea
              </Button>
            </Can>
          </div>
        }
      />

      {brands.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Avval brend yarating"
          description="Kontent reja har bir brendga bog'lanadi."
        />
      ) : null}

      <Toolbar
        brands={brands}
        brandFilter={brandFilter}
        statusFilter={statusFilter}
        view={view}
        anchor={anchor}
        onBrandChange={setBrandFilter}
        onStatusChange={setStatusFilter}
        onViewChange={setView}
        onPrev={() => moveMonth(-1)}
        onNext={() => moveMonth(1)}
        onToday={() => setAnchor(new Date())}
      />

      {creating === "manual" ? (
        <PlanItemForm
          brands={brands}
          defaultBrandId={defaultBrandId}
          onCancel={() => setCreating(null)}
          onSubmit={(payload) => create.mutate(payload)}
          loading={create.isPending}
        />
      ) : null}

      {creating === "import" ? (
        <ImportPlanForm
          brands={brands}
          defaultBrandId={defaultBrandId}
          onCancel={() => setCreating(null)}
          onSubmit={(payload) => importText.mutate(payload)}
          loading={importText.isPending}
        />
      ) : null}

      {editing ? (
        <PlanItemForm
          brands={brands}
          initial={editing}
          defaultBrandId={editing.brand_id}
          onCancel={() => setEditing(null)}
          onSubmit={(payload) => update.mutate({ id: editing.id, payload })}
          loading={update.isPending}
        />
      ) : null}

      {posting ? (
        <CreatePostForm
          item={posting}
          onCancel={() => setPosting(null)}
          onSubmit={(accountIds, scheduledAt) =>
            createPost.mutate({ itemId: posting.id, accountIds, scheduledAt })
          }
          loading={createPost.isPending}
        />
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-44 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Reja bo'sh"
          description="Tanlangan filter bo'yicha kontent g'oyalari topilmadi."
          action={
            <Can permission="smm.write">
              <Button onClick={() => setCreating("manual")} disabled={brands.length === 0}>
                <Plus /> Idea qo&apos;shish
              </Button>
            </Can>
          }
        />
      ) : view === "calendar" ? (
        <CalendarView
          anchor={anchor}
          rangeStart={range.start}
          items={items}
          brands={brands}
          onEdit={setEditing}
          onDelete={(item) => remove.mutate(item.id)}
          onPost={setPosting}
          onMove={(item, iso) => update.mutate({ id: item.id, payload: { planned_at: iso } })}
        />
      ) : view === "kanban" ? (
        <KanbanView
          items={items}
          brands={brands}
          onEdit={setEditing}
          onDelete={(item) => remove.mutate(item.id)}
          onPost={setPosting}
          onStatus={(item, status) => update.mutate({ id: item.id, payload: { status } })}
        />
      ) : (
        <ListView
          items={items}
          brands={brands}
          onEdit={setEditing}
          onDelete={(item) => remove.mutate(item.id)}
          onPost={setPosting}
          onStatus={(item, status) => update.mutate({ id: item.id, payload: { status } })}
        />
      )}
    </motion.div>
  );
}

function Toolbar({
  brands,
  brandFilter,
  statusFilter,
  view,
  anchor,
  onBrandChange,
  onStatusChange,
  onViewChange,
  onPrev,
  onNext,
  onToday,
}: {
  brands: Brand[];
  brandFilter: string | "all";
  statusFilter: ContentPlanStatus | "all";
  view: ViewMode;
  anchor: Date;
  onBrandChange: (value: string | "all") => void;
  onStatusChange: (value: ContentPlanStatus | "all") => void;
  onViewChange: (value: ViewMode) => void;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <Segment active={view === "calendar"} onClick={() => onViewChange("calendar")}>
            <CalendarDays className="h-3.5 w-3.5" /> Calendar
          </Segment>
          <Segment active={view === "list"} onClick={() => onViewChange("list")}>
            <List className="h-3.5 w-3.5" /> List
          </Segment>
          <Segment active={view === "kanban"} onClick={() => onViewChange("kanban")}>
            <Columns3 className="h-3.5 w-3.5" /> Kanban
          </Segment>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {view === "calendar" ? (
            <>
              <Button variant="ghost" size="sm" onClick={onPrev}>
                Oldingi
              </Button>
              <span className="min-w-32 text-center text-sm font-semibold text-[var(--fg)]">
                {monthLabel(anchor)}
              </span>
              <Button variant="ghost" size="sm" onClick={onNext}>
                Keyingi
              </Button>
              <Button variant="secondary" size="sm" onClick={onToday}>
                Bugun
              </Button>
            </>
          ) : null}
          <select
            value={brandFilter}
            onChange={(e) => onBrandChange(e.target.value)}
            className="h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[12px] text-[var(--fg)]"
          >
            <option value="all">Hamma brendlar</option>
            {brands.map((brand) => (
              <option key={brand.id} value={brand.id}>
                {brand.name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value as ContentPlanStatus | "all")}
            className="h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[12px] text-[var(--fg)]"
          >
            <option value="all">Hamma statuslar</option>
            {STATUSES.map((status) => (
              <option key={status.key} value={status.key}>
                {status.label}
              </option>
            ))}
          </select>
        </div>
      </CardContent>
    </Card>
  );
}

function Segment({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex h-8 items-center gap-1.5 rounded-md border px-3 text-[12px] font-medium transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "border-[var(--border)] bg-[var(--surface)] text-[var(--fg-muted)] hover:border-[var(--primary)] hover:text-[var(--fg)]",
      )}
    >
      {children}
    </button>
  );
}

function PlanItemForm({
  brands,
  defaultBrandId,
  initial,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string | undefined;
  initial?: ContentPlanItem;
  onCancel: () => void;
  onSubmit: (payload: ContentPlanItemCreate) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(initial?.brand_id ?? defaultBrandId ?? "");
  const [platform, setPlatform] = useState(initial?.platform ?? "instagram");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [idea, setIdea] = useState(initial?.idea ?? "");
  const [goal, setGoal] = useState(initial?.goal ?? "");
  const [cta, setCta] = useState(initial?.cta ?? "");
  const [status, setStatus] = useState<ContentPlanStatus>(
    (initial?.status as ContentPlanStatus | undefined) ?? "idea",
  );
  const [dateValue, setDateValue] = useState(initial?.planned_at?.slice(0, 10) ?? todayIso());
  const [timeValue, setTimeValue] = useState(initial?.planned_at?.slice(11, 16) ?? "09:00");
  const canSubmit = Boolean(brandId && title.trim() && idea.trim());

  const plannedAt =
    dateValue && timeValue
      ? new Date(`${dateValue}T${timeValue}:00.000Z`).toISOString()
      : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{initial ? "Rejani tahrirlash" : "Yangi content idea"}</CardTitle>
        <CloseButton onClick={onCancel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <FormField label="Brend" required>
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
              disabled={Boolean(initial)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] disabled:opacity-60"
            >
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Platforma">
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
            >
              {PLATFORMS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Sana">
            <Input
              type="date"
              value={dateValue}
              onChange={(e) => setDateValue(e.target.value)}
            />
          </FormField>
          <FormField label="Vaqt">
            <Input
              type="time"
              value={timeValue}
              onChange={(e) => setTimeValue(e.target.value)}
            />
          </FormField>
        </div>
        <div className="grid gap-4 md:grid-cols-[1fr_180px]">
          <FormField label="Sarlavha" required>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="May aksiyasi teaser"
            />
          </FormField>
          <FormField label="Status">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as ContentPlanStatus)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
            >
              {STATUSES.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.label}
                </option>
              ))}
            </select>
          </FormField>
        </div>
        <FormField label="Idea" required>
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            className="min-h-[120px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            placeholder="Post mazmuni, angle, format va asosiy fikr..."
          />
        </FormField>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Maqsad">
            <Input value={goal} onChange={(e) => setGoal(e.target.value)} />
          </FormField>
          <FormField label="CTA">
            <Input value={cta} onChange={(e) => setCta(e.target.value)} />
          </FormField>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] pt-4">
          <Button variant="ghost" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button
            onClick={() =>
              onSubmit({
                brand_id: brandId,
                platform,
                title: title.trim(),
                idea: idea.trim(),
                goal: goal.trim() || null,
                cta: cta.trim() || null,
                status,
                planned_at: plannedAt,
                source: initial?.source ?? "manual",
              })
            }
            loading={loading}
            disabled={!canSubmit}
          >
            {initial ? "Saqlash" : "Qo'shish"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ImportPlanForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string | undefined;
  onCancel: () => void;
  onSubmit: (payload: {
    brand_id: string;
    platform: string;
    topic?: string | null;
    text: string;
    start_date: string;
  }) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId ?? "");
  const [platform, setPlatform] = useState("instagram");
  const [topic, setTopic] = useState("");
  const [startDate, setStartDate] = useState(todayIso());
  const [text, setText] = useState("");
  const canSubmit = Boolean(brandId && text.trim().length >= 2);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>AI reja import</CardTitle>
        <CloseButton onClick={onCancel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <FormField label="Brend" required>
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
            >
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Platforma">
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
            >
              {PLATFORMS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Start sana">
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </FormField>
          <FormField label="Mavzu">
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} />
          </FormField>
        </div>
        <FormField label="AI reja matni" required>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[180px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            placeholder="Day 1: ...&#10;Day 2: ..."
          />
        </FormField>
        <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] pt-4">
          <Button variant="ghost" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button
            onClick={() =>
              onSubmit({
                brand_id: brandId,
                platform,
                topic: topic.trim() || null,
                text: text.trim(),
                start_date: startDate,
              })
            }
            loading={loading}
            disabled={!canSubmit}
          >
            Import qilish
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function CreatePostForm({
  item,
  onCancel,
  onSubmit,
  loading,
}: {
  item: ContentPlanItem;
  onCancel: () => void;
  onSubmit: (accountIds: string[], scheduledAt: string | null) => void;
  loading: boolean;
}) {
  const { data: accounts = [] } = useQuery({
    queryKey: ["social-accounts", item.brand_id],
    queryFn: () => socialApi.listAccounts(item.brand_id),
  });
  const [selected, setSelected] = useState<string[]>([]);
  const [dateValue, setDateValue] = useState(item.planned_at?.slice(0, 10) ?? todayIso());
  const [timeValue, setTimeValue] = useState(item.planned_at?.slice(11, 16) ?? "09:00");
  const scheduledAt =
    dateValue && timeValue
      ? new Date(`${dateValue}T${timeValue}:00.000Z`).toISOString()
      : null;

  const toggle = (id: string) =>
    setSelected((value) =>
      value.includes(id) ? value.filter((x) => x !== id) : [...value, id],
    );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Post yaratish</CardTitle>
        <CloseButton onClick={onCancel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3">
          <p className="text-sm font-semibold text-[var(--fg)]">{item.title}</p>
          <p className="mt-1 line-clamp-3 text-[12px] text-[var(--fg-muted)]">{item.idea}</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Sana">
            <Input
              type="date"
              value={dateValue}
              onChange={(e) => setDateValue(e.target.value)}
            />
          </FormField>
          <FormField label="Vaqt">
            <Input
              type="time"
              value={timeValue}
              onChange={(e) => setTimeValue(e.target.value)}
            />
          </FormField>
        </div>
        <FormField label="Akkauntlar">
          <div className="flex flex-wrap gap-2">
            {accounts.map((account) => (
              <button
                key={account.id}
                type="button"
                onClick={() => toggle(account.id)}
                className={cn(
                  "rounded-md border px-2.5 py-1 text-[12px] font-medium transition-colors",
                  selected.includes(account.id)
                    ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                    : "border-[var(--border)] text-[var(--fg-muted)] hover:text-[var(--fg)]",
                )}
              >
                {account.provider} ·{" "}
                {account.external_name ?? account.external_handle ?? account.external_id}
              </button>
            ))}
          </div>
        </FormField>
        <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] pt-4">
          <Button variant="ghost" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button
            onClick={() => onSubmit(selected, scheduledAt)}
            loading={loading}
            disabled={selected.length === 0}
          >
            Post yaratish
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function CalendarView({
  anchor,
  rangeStart,
  items,
  brands,
  onEdit,
  onDelete,
  onPost,
  onMove,
}: {
  anchor: Date;
  rangeStart: Date;
  items: ContentPlanItem[];
  brands: Brand[];
  onEdit: (item: ContentPlanItem) => void;
  onDelete: (item: ContentPlanItem) => void;
  onPost: (item: ContentPlanItem) => void;
  onMove: (item: ContentPlanItem, iso: string) => void;
}) {
  const byDay = new Map<string, ContentPlanItem[]>();
  for (const item of items) {
    const key = item.planned_at?.slice(0, 10);
    if (!key) continue;
    byDay.set(key, [...(byDay.get(key) ?? []), item]);
  }
  const days = Array.from({ length: 42 }, (_, index) => {
    const day = addDays(rangeStart, index);
    return { day, key: isoDay(day), items: byDay.get(isoDay(day)) ?? [] };
  });

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-2 grid grid-cols-7 gap-1.5">
          {["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"].map((day) => (
            <div
              key={day}
              className="text-center text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase"
            >
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1.5">
          {days.map(({ day, key, items: dayItems }) => (
            <DayCell
              key={key}
              day={day}
              inMonth={day.getUTCMonth() === anchor.getUTCMonth()}
              items={dayItems}
              brands={brands}
              onEdit={onEdit}
              onDelete={onDelete}
              onPost={onPost}
              onMove={(item) => {
                const prev = item.planned_at ? new Date(item.planned_at) : new Date();
                onMove(
                  item,
                  new Date(
                    Date.UTC(
                      day.getUTCFullYear(),
                      day.getUTCMonth(),
                      day.getUTCDate(),
                      prev.getUTCHours(),
                      prev.getUTCMinutes(),
                    ),
                  ).toISOString(),
                );
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function DayCell({
  day,
  inMonth,
  items,
  brands,
  onEdit,
  onDelete,
  onPost,
  onMove,
}: {
  day: Date;
  inMonth: boolean;
  items: ContentPlanItem[];
  brands: Brand[];
  onEdit: (item: ContentPlanItem) => void;
  onDelete: (item: ContentPlanItem) => void;
  onPost: (item: ContentPlanItem) => void;
  onMove: (item: ContentPlanItem) => void;
}) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        setHover(true);
      }}
      onDragLeave={() => setHover(false)}
      onDrop={(event) => {
        event.preventDefault();
        setHover(false);
        const raw = event.dataTransfer.getData("application/json");
        if (!raw) return;
        try {
          onMove(JSON.parse(raw) as ContentPlanItem);
        } catch {
          /* ignore */
        }
      }}
      className={cn(
        "min-h-32 rounded-md border p-1.5 transition-colors",
        inMonth
          ? "border-[var(--border)] bg-[var(--bg-subtle)]"
          : "border-[var(--border)] bg-[var(--surface)] opacity-60",
        hover && "border-[var(--primary)] bg-[var(--primary-soft)]/40",
      )}
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[var(--fg-muted)]">
          {day.getUTCDate()}
        </span>
        {items.length ? (
          <span className="text-[10px] text-[var(--fg-subtle)]">{items.length}</span>
        ) : null}
      </div>
      <div className="space-y-1">
        {items.slice(0, 3).map((item) => (
          <PlanChip
            key={item.id}
            item={item}
            brand={brands.find((brand) => brand.id === item.brand_id)}
            onEdit={() => onEdit(item)}
            onDelete={() => onDelete(item)}
            onPost={() => onPost(item)}
          />
        ))}
        {items.length > 3 ? (
          <p className="px-1 text-[10px] text-[var(--fg-subtle)]">+{items.length - 3}</p>
        ) : null}
      </div>
    </div>
  );
}

function PlanChip({
  item,
  brand,
  onEdit,
  onDelete,
  onPost,
}: {
  item: ContentPlanItem;
  brand: Brand | undefined;
  onEdit: () => void;
  onDelete: () => void;
  onPost: () => void;
}) {
  const meta = STATUS_MAP[item.status] ?? STATUS_MAP.idea;
  return (
    <div
      draggable
      onDragStart={(event) => {
        event.dataTransfer.setData("application/json", JSON.stringify(item));
        event.dataTransfer.effectAllowed = "move";
      }}
      className={cn("group rounded px-1.5 py-1 text-[10px]", meta.tone)}
      title={item.idea}
    >
      <button type="button" onClick={onEdit} className="block w-full min-w-0 text-left">
        <span className="block truncate font-semibold">{item.title}</span>
        <span className="block truncate opacity-80">
          {brand?.name ?? "Brend"} · {item.platform}
        </span>
      </button>
      <Can permission="smm.write">
        <div className="mt-1 hidden items-center gap-1 group-hover:flex">
          <button type="button" onClick={onPost} className="hover:underline">
            post
          </button>
          <button type="button" onClick={onDelete} className="hover:underline">
            delete
          </button>
        </div>
      </Can>
    </div>
  );
}

function KanbanView({
  items,
  brands,
  onEdit,
  onDelete,
  onPost,
  onStatus,
}: {
  items: ContentPlanItem[];
  brands: Brand[];
  onEdit: (item: ContentPlanItem) => void;
  onDelete: (item: ContentPlanItem) => void;
  onPost: (item: ContentPlanItem) => void;
  onStatus: (item: ContentPlanItem, status: ContentPlanStatus) => void;
}) {
  return (
    <div className="grid gap-3 xl:grid-cols-6">
      {STATUSES.map((status) => (
        <KanbanColumn
          key={status.key}
          status={status}
          items={items.filter((item) => item.status === status.key)}
          brands={brands}
          onEdit={onEdit}
          onDelete={onDelete}
          onPost={onPost}
          onDrop={(item) => onStatus(item, status.key)}
          onStatus={onStatus}
        />
      ))}
    </div>
  );
}

function KanbanColumn({
  status,
  items,
  brands,
  onEdit,
  onDelete,
  onPost,
  onDrop,
  onStatus,
}: {
  status: (typeof STATUSES)[number];
  items: ContentPlanItem[];
  brands: Brand[];
  onEdit: (item: ContentPlanItem) => void;
  onDelete: (item: ContentPlanItem) => void;
  onPost: (item: ContentPlanItem) => void;
  onDrop: (item: ContentPlanItem) => void;
  onStatus: (item: ContentPlanItem, status: ContentPlanStatus) => void;
}) {
  const [hover, setHover] = useState(false);
  const Icon = status.icon;
  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        setHover(true);
      }}
      onDragLeave={() => setHover(false)}
      onDrop={(event) => {
        event.preventDefault();
        setHover(false);
        const raw = event.dataTransfer.getData("application/json");
        if (!raw) return;
        try {
          onDrop(JSON.parse(raw) as ContentPlanItem);
        } catch {
          /* ignore */
        }
      }}
      className={cn(
        "min-h-96 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-3",
        hover && "border-[var(--primary)]",
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-[12px] font-semibold text-[var(--fg)]">
          <Icon className="h-3.5 w-3.5" /> {status.label}
        </p>
        <Badge variant="outline">{items.length}</Badge>
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <PlanCard
            key={item.id}
            item={item}
            brand={brands.find((brand) => brand.id === item.brand_id)}
            compact
            onEdit={() => onEdit(item)}
            onDelete={() => onDelete(item)}
            onPost={() => onPost(item)}
            onStatus={(next) => onStatus(item, next)}
          />
        ))}
      </div>
    </div>
  );
}

function ListView({
  items,
  brands,
  onEdit,
  onDelete,
  onPost,
  onStatus,
}: {
  items: ContentPlanItem[];
  brands: Brand[];
  onEdit: (item: ContentPlanItem) => void;
  onDelete: (item: ContentPlanItem) => void;
  onPost: (item: ContentPlanItem) => void;
  onStatus: (item: ContentPlanItem, status: ContentPlanStatus) => void;
}) {
  return (
    <div className="grid gap-3">
      {items.map((item) => (
        <PlanCard
          key={item.id}
          item={item}
          brand={brands.find((brand) => brand.id === item.brand_id)}
          onEdit={() => onEdit(item)}
          onDelete={() => onDelete(item)}
          onPost={() => onPost(item)}
          onStatus={(status) => onStatus(item, status)}
        />
      ))}
    </div>
  );
}

function PlanCard({
  item,
  brand,
  compact,
  onEdit,
  onDelete,
  onPost,
  onStatus,
}: {
  item: ContentPlanItem;
  brand: Brand | undefined;
  compact?: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onPost: () => void;
  onStatus: (status: ContentPlanStatus) => void;
}) {
  const status = STATUS_MAP[item.status] ?? STATUS_MAP.idea;
  const Icon = status.icon;
  return (
    <Card
      draggable
      onDragStart={(event) => {
        event.dataTransfer.setData("application/json", JSON.stringify(item));
        event.dataTransfer.effectAllowed = "move";
      }}
      className={cn("p-4 transition-shadow hover:shadow-[var(--shadow-md)]", compact && "p-3")}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <button type="button" onClick={onEdit} className="block min-w-0 text-left">
            <p className="truncate text-sm font-semibold text-[var(--fg)]">{item.title}</p>
            <p className="mt-1 text-[12px] text-[var(--fg-subtle)]">
              {brand?.name ?? "Brend"} · {item.platform} · {dateLabel(item.planned_at)}
            </p>
          </button>
        </div>
        <Badge className={status.tone}>
          <Icon className="h-2.5 w-2.5" /> {status.label}
        </Badge>
      </div>
      <p
        className={cn(
          "mt-3 text-[12px] leading-relaxed text-[var(--fg-muted)]",
          compact ? "line-clamp-3" : "line-clamp-2",
        )}
      >
        {item.idea}
      </p>
      {!compact && (item.goal || item.cta) ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.goal ? <Badge variant="outline">{item.goal}</Badge> : null}
          {item.cta ? <Badge variant="default">{item.cta}</Badge> : null}
        </div>
      ) : null}
      <Can permission="smm.write">
        <div className="mt-3 flex items-center justify-between gap-2 border-t border-[var(--border)] pt-3">
          <select
            value={item.status}
            onChange={(event) => onStatus(event.target.value as ContentPlanStatus)}
            className="h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[12px] text-[var(--fg)]"
          >
            {STATUSES.map((next) => (
              <option key={next.key} value={next.key}>
                {next.label}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={onPost}
              disabled={Boolean(item.post_id)}
            >
              <Send /> Post
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              onClick={onDelete}
              aria-label="O'chirish"
              className="text-[var(--danger)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
            >
              <Trash2 />
            </Button>
          </div>
        </div>
      </Can>
    </Card>
  );
}

function CloseButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Yopish"
      className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
    >
      <X className="h-4 w-4" />
    </button>
  );
}

function dateLabel(value: string | null): string {
  if (!value) return "sana yo'q";
  return new Date(value).toLocaleDateString("uz-UZ", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

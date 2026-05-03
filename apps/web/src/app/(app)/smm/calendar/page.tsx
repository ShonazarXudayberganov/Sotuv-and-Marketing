"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Loader2,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { extractApiError } from "@/lib/api-client";
import { postsApi } from "@/lib/posts-api";
import { brandsApi } from "@/lib/smm-api";
import type { Post } from "@/lib/types";
import { cn } from "@/lib/utils";

type ViewMode = "month" | "week";

const STATUS_TONE: Record<string, string> = {
  draft: "bg-[var(--surface-hover)] text-[var(--fg-muted)]",
  scheduled: "bg-[var(--info-soft)] text-[var(--info)]",
  publishing: "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]",
  published: "bg-[var(--success-soft)] text-[var(--success)]",
  partial: "bg-[var(--warning-soft)] text-[var(--warning)]",
  failed: "bg-[var(--danger-soft)] text-[var(--danger)]",
  cancelled: "bg-[var(--surface-hover)] text-[var(--fg-subtle)]",
};

function startOfMonth(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
}
function startOfWeek(d: Date): Date {
  const day = d.getUTCDay(); // 0 = Sun
  const offset = (day + 6) % 7; // shift to Mon-start
  const out = new Date(d);
  out.setUTCDate(d.getUTCDate() - offset);
  out.setUTCHours(0, 0, 0, 0);
  return out;
}
function addDays(d: Date, n: number): Date {
  const out = new Date(d);
  out.setUTCDate(d.getUTCDate() + n);
  return out;
}
function fmtIsoDay(d: Date): string {
  return d.toISOString().slice(0, 10);
}
function monthLabel(d: Date): string {
  return d.toLocaleDateString("uz-UZ", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export default function CalendarPage() {
  const qc = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [anchor, setAnchor] = useState<Date>(() => {
    const now = new Date();
    return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  });
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const activeBrandId = brandFilter === "all" ? null : brandFilter;

  const range = useMemo(() => {
    if (viewMode === "month") {
      const first = startOfMonth(anchor);
      const gridStart = startOfWeek(first);
      const gridEnd = addDays(gridStart, 42); // 6 weeks
      return { start: gridStart, end: gridEnd, days: 42 };
    }
    const start = startOfWeek(anchor);
    return { start, end: addDays(start, 7), days: 7 };
  }, [anchor, viewMode]);

  const { data: calendar, isLoading } = useQuery({
    queryKey: [
      "posts",
      "calendar",
      range.start.toISOString(),
      range.end.toISOString(),
      activeBrandId,
    ],
    queryFn: () =>
      postsApi.calendar(range.start.toISOString(), range.end.toISOString(), activeBrandId),
  });

  const reschedule = useMutation({
    mutationFn: (args: { id: string; iso: string }) => postsApi.reschedule(args.id, args.iso),
    onSuccess: () => {
      toast.success("Vaqt o'zgartirildi");
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const days: { date: Date; key: string; posts: Post[] }[] = useMemo(() => {
    const byDay = new Map<string, Post[]>();
    for (const d of calendar?.days ?? []) byDay.set(d.date, d.posts);
    return Array.from({ length: range.days }).map((_, i) => {
      const date = addDays(range.start, i);
      const key = fmtIsoDay(date);
      return { date, key, posts: byDay.get(key) ?? [] };
    });
  }, [calendar, range]);

  const move = (delta: number) => {
    if (viewMode === "month") {
      setAnchor(new Date(Date.UTC(anchor.getUTCFullYear(), anchor.getUTCMonth() + delta, 1)));
    } else {
      setAnchor(addDays(anchor, 7 * delta));
    }
  };

  const handleDrop = (post: Post, targetDay: Date) => {
    if (post.status !== "scheduled" && post.status !== "draft") {
      toast.error("Faqat draft yoki rejalashtirilgan postni surish mumkin");
      return;
    }
    const prev = post.scheduled_at ? new Date(post.scheduled_at) : new Date();
    const iso = new Date(
      Date.UTC(
        targetDay.getUTCFullYear(),
        targetDay.getUTCMonth(),
        targetDay.getUTCDate(),
        prev.getUTCHours(),
        prev.getUTCMinutes(),
      ),
    ).toISOString();
    reschedule.mutate({ id: post.id, iso });
  };

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
          { label: "Kontent kalendar" },
        ]}
        title="Kontent kalendar"
        description="Postlarni oy va hafta ko'rinishida kuzating, sana ustiga sudrab tashlab qayta rejalashtiring"
        actions={
          <Button asChild variant="secondary">
            <Link href="/smm/posts">Postlar</Link>
          </Button>
        }
      />

      <Card>
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => move(-1)} aria-label="Oldingi">
              <ChevronLeft />
            </Button>
            <CardTitle className="min-w-[180px] text-center">
              {viewMode === "month"
                ? monthLabel(anchor)
                : `${fmtIsoDay(range.start)} → ${fmtIsoDay(addDays(range.end, -1))}`}
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={() => move(1)} aria-label="Keyingi">
              <ChevronRight />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setAnchor(new Date())}>
              Bugun
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-0.5">
              <ViewPill active={viewMode === "month"} onClick={() => setViewMode("month")}>
                Oy
              </ViewPill>
              <ViewPill active={viewMode === "week"} onClick={() => setViewMode("week")}>
                Hafta
              </ViewPill>
            </div>
            {brands.length > 0 ? (
              <select
                value={brandFilter}
                onChange={(e) => setBrandFilter(e.target.value)}
                className="flex h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[12px] text-[var(--fg)]"
              >
                <option value="all">Hamma brendlar</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-7 gap-1.5">
              {Array.from({ length: range.days }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 animate-pulse rounded-md border border-[var(--border)] bg-[var(--surface)]"
                />
              ))}
            </div>
          ) : (
            <CalendarGrid
              viewMode={viewMode}
              anchor={anchor}
              days={days}
              onDrop={handleDrop}
            />
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function ViewPill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded px-3 py-1 text-[12px] font-medium transition-colors",
        active
          ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "text-[var(--fg-muted)] hover:text-[var(--fg)]",
      )}
    >
      {children}
    </button>
  );
}

const WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];

function CalendarGrid({
  viewMode,
  anchor,
  days,
  onDrop,
}: {
  viewMode: ViewMode;
  anchor: Date;
  days: { date: Date; key: string; posts: Post[] }[];
  onDrop: (post: Post, day: Date) => void;
}) {
  return (
    <div>
      <div className="mb-2 grid grid-cols-7 gap-1.5">
        {WEEKDAYS.map((d) => (
          <div
            key={d}
            className="text-center text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase"
          >
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1.5">
        {days.map((d) => (
          <DayCell
            key={d.key}
            day={d.date}
            posts={d.posts}
            inMonth={viewMode === "week" || d.date.getUTCMonth() === anchor.getUTCMonth()}
            onDrop={(post) => onDrop(post, d.date)}
          />
        ))}
      </div>
    </div>
  );
}

function DayCell({
  day,
  posts,
  inMonth,
  onDrop,
}: {
  day: Date;
  posts: Post[];
  inMonth: boolean;
  onDrop: (post: Post) => void;
}) {
  const [hover, setHover] = useState(false);
  const today = new Date();
  const isToday =
    day.getUTCFullYear() === today.getUTCFullYear() &&
    day.getUTCMonth() === today.getUTCMonth() &&
    day.getUTCDate() === today.getUTCDate();

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setHover(true);
      }}
      onDragLeave={() => setHover(false)}
      onDrop={(e) => {
        e.preventDefault();
        setHover(false);
        const id = e.dataTransfer.getData("text/post-id");
        const raw = e.dataTransfer.getData("application/json");
        if (!id || !raw) return;
        try {
          const post = JSON.parse(raw) as Post;
          onDrop(post);
        } catch {
          /* ignore */
        }
      }}
      className={cn(
        "min-h-24 rounded-md border p-1.5 transition-colors",
        inMonth
          ? "border-[var(--border)] bg-[var(--bg-subtle)]"
          : "border-[var(--border)] bg-[var(--surface)] opacity-60",
        hover && "border-[var(--primary)] bg-[var(--primary-soft)]/40",
      )}
    >
      <div className="mb-1 flex items-center justify-between">
        <span
          className={cn(
            "text-[11px] font-semibold",
            isToday
              ? "rounded-md bg-[var(--primary)] px-1.5 py-0.5 text-[var(--primary-fg)]"
              : "text-[var(--fg-muted)]",
          )}
        >
          {day.getUTCDate()}
        </span>
        {posts.length > 0 ? (
          <span className="text-[10px] text-[var(--fg-subtle)]">{posts.length}</span>
        ) : null}
      </div>
      <div className="space-y-1">
        {posts.slice(0, 3).map((p) => (
          <PostChip key={p.id} post={p} />
        ))}
        {posts.length > 3 ? (
          <p className="px-1 text-[10px] text-[var(--fg-subtle)]">+{posts.length - 3} yana</p>
        ) : null}
      </div>
    </div>
  );
}

const STATUS_ICONS = {
  published: CheckCircle2,
  scheduled: Clock,
  publishing: Loader2,
  failed: AlertTriangle,
  partial: AlertTriangle,
  cancelled: XCircle,
  draft: CalendarDays,
} as const;

function PostChip({ post }: { post: Post }) {
  const draggable = post.status === "scheduled" || post.status === "draft";
  const tone = STATUS_TONE[post.status] ?? STATUS_TONE.draft;
  const Icon = STATUS_ICONS[post.status as keyof typeof STATUS_ICONS] ?? CalendarDays;
  const time = post.scheduled_at
    ? new Date(post.scheduled_at).toLocaleTimeString("uz-UZ", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;
  return (
    <Link
      href={`/smm/posts`}
      draggable={draggable}
      onDragStart={(e) => {
        if (!draggable) return;
        e.dataTransfer.setData("text/post-id", post.id);
        e.dataTransfer.setData("application/json", JSON.stringify(post));
        e.dataTransfer.effectAllowed = "move";
      }}
      className={cn(
        "flex items-center gap-1 rounded px-1.5 py-1 text-[10px] transition-shadow",
        tone,
        draggable ? "cursor-grab active:cursor-grabbing" : "cursor-pointer opacity-80",
        "hover:shadow-[var(--shadow-xs)]",
      )}
      title={`${post.title ?? post.body.slice(0, 80)}\n${post.status}`}
    >
      <Icon className="h-2.5 w-2.5 shrink-0" />
      {time ? <span className="font-medium">{time}</span> : null}
      <span className="truncate">{post.title ?? post.body}</span>
    </Link>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  Filter,
  LayoutGrid,
  List as ListIcon,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { tasksApi } from "@/lib/sprint4-api";
import type { Task, TaskPriority, TaskStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUSES: {
  key: TaskStatus;
  label: string;
  dot: string;
  badge: "default" | "primary" | "warning" | "success" | "info";
}[] = [
  { key: "new", label: "Yangi", dot: "bg-[var(--fg-subtle)]", badge: "default" },
  { key: "in_progress", label: "Jarayonda", dot: "bg-[var(--info)]", badge: "info" },
  { key: "review", label: "Tekshirishda", dot: "bg-[var(--warning)]", badge: "warning" },
  { key: "done", label: "Bajarildi", dot: "bg-[var(--success)]", badge: "success" },
  { key: "cancelled", label: "Bekor", dot: "bg-[var(--fg-subtle)]", badge: "default" },
];

const PRIORITY_LABELS: Record<TaskPriority, { label: string; cls: string; dot: string }> = {
  low: {
    label: "Past",
    cls: "text-[var(--fg-subtle)]",
    dot: "bg-[var(--fg-subtle)]",
  },
  medium: {
    label: "O'rta",
    cls: "text-[var(--info)]",
    dot: "bg-[var(--info)]",
  },
  high: {
    label: "Yuqori",
    cls: "text-[var(--warning)]",
    dot: "bg-[var(--warning)]",
  },
  critical: {
    label: "Kritik",
    cls: "text-[var(--danger)]",
    dot: "bg-[var(--danger)]",
  },
};

export default function TasksPage() {
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const qc = useQueryClient();
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

  const filtered = useMemo(() => {
    if (!search.trim()) return tasks;
    const q = search.toLowerCase();
    return tasks.filter(
      (t) => t.title.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q),
    );
  }, [tasks, search]);

  const create = useMutation({
    mutationFn: tasksApi.create,
    onSuccess: () => {
      toast.success("Vazifa yaratildi");
      qc.invalidateQueries({ queryKey: ["tasks"] });
      setShowForm(false);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) =>
      tasksApi.update(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: tasksApi.remove,
    onSuccess: () => {
      toast.success("Vazifa o'chirildi");
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const counts = STATUSES.reduce(
    (acc, s) => {
      acc[s.key] = tasks.filter((t) => t.status === s.key).length;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[{ label: "Bosh sahifa", href: "/dashboard" }, { label: "Vazifalar" }]}
        title="Vazifalar"
        description={`${tasks.length} ta vazifa · ${counts.in_progress} ta jarayonda · ${counts.done} ta bajarildi`}
        actions={
          <>
            <div className="flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-0.5 shadow-[var(--shadow-xs)]">
              <button
                type="button"
                onClick={() => setView("kanban")}
                aria-label="Kanban ko'rinish"
                className={cn(
                  "flex h-7 w-8 items-center justify-center rounded-md transition-colors",
                  view === "kanban"
                    ? "bg-[var(--bg-subtle)] text-[var(--fg)]"
                    : "text-[var(--fg-subtle)] hover:text-[var(--fg)]",
                )}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setView("list")}
                aria-label="Ro'yxat ko'rinish"
                className={cn(
                  "flex h-7 w-8 items-center justify-center rounded-md transition-colors",
                  view === "list"
                    ? "bg-[var(--bg-subtle)] text-[var(--fg)]"
                    : "text-[var(--fg-subtle)] hover:text-[var(--fg)]",
                )}
              >
                <ListIcon className="h-3.5 w-3.5" />
              </button>
            </div>

            <Button variant="secondary" size="default">
              <Filter /> Filter
            </Button>

            <Can permission="tasks.create">
              <Button size="default" onClick={() => setShowForm((s) => !s)}>
                <Plus /> Yangi vazifa
              </Button>
            </Can>
          </>
        }
      />

      {/* Toolbar — search */}
      <div className="flex items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[var(--fg-subtle)]" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Vazifa qidirish…"
            className="pl-9"
          />
        </div>
      </div>

      {showForm ? (
        <CreateForm
          onSubmit={(payload) => create.mutate(payload)}
          loading={create.isPending}
          onCancel={() => setShowForm(false)}
        />
      ) : null}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-5">
          {STATUSES.map((s) => (
            <div
              key={s.key}
              className="h-64 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : filtered.length === 0 && tasks.length === 0 ? (
        <EmptyState
          icon={LayoutGrid}
          title="Hozircha vazifalar yo'q"
          description="Birinchi vazifangizni qo'shing — Kanban ustunlar bo'ylab kuzatishingiz mumkin."
          action={
            <Can permission="tasks.create">
              <Button onClick={() => setShowForm(true)}>
                <Plus /> Birinchi vazifani qo&apos;shish
              </Button>
            </Can>
          }
        />
      ) : view === "kanban" ? (
        <Kanban
          tasks={filtered}
          counts={counts}
          onMove={(id, status) => update.mutate({ id, status })}
          onDelete={(id) => remove.mutate(id)}
        />
      ) : (
        <TableView tasks={filtered} onDelete={(id) => remove.mutate(id)} />
      )}
    </motion.div>
  );
}

function CreateForm({
  onSubmit,
  onCancel,
  loading,
}: {
  onSubmit: (p: { title: string; description: string; priority: TaskPriority }) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Yangi vazifa</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <FormField label="Sarlavha" required>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Masalan: Mijoz bilan qo'ng'iroq"
              autoFocus
            />
          </FormField>
          <FormField label="Tavsif">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Qo'shimcha kontekst…"
              className="flex min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>
          <FormField label="Muhimlik">
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
              className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            >
              {Object.entries(PRIORITY_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.label}
                </option>
              ))}
            </select>
          </FormField>
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => title.trim() && onSubmit({ title, description, priority })}
              loading={loading}
              disabled={!title.trim()}
            >
              Yaratish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function Kanban({
  tasks,
  counts,
  onMove,
  onDelete,
}: {
  tasks: Task[];
  counts: Record<string, number>;
  onMove: (id: string, status: TaskStatus) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {STATUSES.map((s) => {
        const items = tasks.filter((t) => t.status === s.key);
        return (
          <div
            key={s.key}
            className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-subtle)]"
          >
            {/* Column header */}
            <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2.5">
              <div className="flex items-center gap-2">
                <span className={cn("h-2 w-2 rounded-full", s.dot)} />
                <span className="text-[13px] font-semibold text-[var(--fg)]">{s.label}</span>
                <span className="rounded-full bg-[var(--surface-hover)] px-1.5 text-[10px] font-semibold text-[var(--fg-muted)]">
                  {counts[s.key] ?? 0}
                </span>
              </div>
              <button
                type="button"
                aria-label="Ustun sozlamalari"
                className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
              >
                <MoreHorizontal className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Cards */}
            <div className="flex min-h-[120px] flex-1 flex-col gap-2 p-2">
              {items.length === 0 ? (
                <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-[var(--border)] py-8 text-[11px] text-[var(--fg-subtle)]">
                  Bo&apos;sh
                </div>
              ) : (
                items.map((task, idx) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    delay={idx * 0.03}
                    onMove={onMove}
                    onDelete={onDelete}
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TaskCard({
  task,
  delay,
  onMove,
  onDelete,
}: {
  task: Task;
  delay: number;
  onMove: (id: string, status: TaskStatus) => void;
  onDelete: (id: string) => void;
}) {
  const priority = PRIORITY_LABELS[task.priority];
  const due = task.due_at ? new Date(task.due_at) : null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay, ease: "easeOut" }}
      whileHover={{ y: -1 }}
      className="group relative cursor-pointer rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 shadow-[var(--shadow-xs)] transition-all hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-sm)]"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="flex-1 text-[13px] leading-snug font-medium text-[var(--fg)]">
          {task.title}
        </p>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Vazifa amallari"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
            >
              <MoreHorizontal className="h-3.5 w-3.5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            {STATUSES.filter((s) => s.key !== task.status).map((s) => (
              <DropdownMenuItem key={s.key} onClick={() => onMove(task.id, s.key)}>
                <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} />
                {s.label}ga o&apos;tkazish
              </DropdownMenuItem>
            ))}
            <Can permission="tasks.delete">
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(task.id)}
                className="text-[var(--danger)] focus:bg-[var(--danger-soft)] focus:text-[var(--danger)]"
              >
                <Trash2 /> O&apos;chirish
              </DropdownMenuItem>
            </Can>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {task.description ? (
        <p className="mt-1.5 line-clamp-2 text-[11.5px] leading-relaxed text-[var(--fg-muted)]">
          {task.description}
        </p>
      ) : null}

      {/* Footer: priority + due */}
      <div className="mt-3 flex items-center justify-between gap-2">
        <div className={cn("inline-flex items-center gap-1 text-[11px]", priority.cls)}>
          <span className={cn("h-1.5 w-1.5 rounded-full", priority.dot)} />
          {priority.label}
        </div>
        {due ? (
          <span className="inline-flex items-center gap-0.5 text-[10.5px] text-[var(--fg-subtle)]">
            <Clock className="h-3 w-3" />
            {due.toLocaleDateString("uz-UZ", { day: "2-digit", month: "short" })}
          </span>
        ) : null}
      </div>
    </motion.div>
  );
}

function TableView({ tasks, onDelete }: { tasks: Task[]; onDelete: (id: string) => void }) {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-[var(--border)] bg-[var(--bg-subtle)] text-left">
              <tr>
                <th className="px-4 py-2.5 text-[11px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
                  Sarlavha
                </th>
                <th className="px-4 py-2.5 text-[11px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
                  Holat
                </th>
                <th className="px-4 py-2.5 text-[11px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
                  Muhimlik
                </th>
                <th className="px-4 py-2.5 text-[11px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Yaratilgan
                  </span>
                </th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {tasks.map((t) => {
                const status = STATUSES.find((s) => s.key === t.status);
                const priority = PRIORITY_LABELS[t.priority];
                return (
                  <tr key={t.id} className="transition-colors hover:bg-[var(--bg-subtle)]">
                    <td className="px-4 py-3">
                      <p className="font-medium text-[var(--fg)]">{t.title}</p>
                      {t.description ? (
                        <p className="mt-0.5 line-clamp-1 text-[11px] text-[var(--fg-subtle)]">
                          {t.description}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">
                      {status ? <Badge variant={status.badge}>{status.label}</Badge> : null}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 text-[12px]",
                          priority.cls,
                        )}
                      >
                        <span className={cn("h-1.5 w-1.5 rounded-full", priority.dot)} />
                        {priority.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-[var(--fg-subtle)]">
                      {new Date(t.created_at).toLocaleDateString("uz-UZ")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Can permission="tasks.delete">
                        <button
                          type="button"
                          onClick={() => onDelete(t.id)}
                          aria-label="O'chirish"
                          className="rounded-md p-1.5 text-[var(--fg-subtle)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </Can>
                    </td>
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

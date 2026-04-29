"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutGrid, List as ListIcon, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { tasksApi } from "@/lib/sprint4-api";
import type { Task, TaskPriority, TaskStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUSES: { key: TaskStatus; label: string; color: string }[] = [
  { key: "new", label: "Yangi", color: "bg-cream-200 text-charcoal" },
  { key: "in_progress", label: "Jarayonda", color: "bg-gold/20 text-gold-deep" },
  { key: "review", label: "Tekshirishda", color: "bg-warning/20 text-warning" },
  { key: "done", label: "Bajarildi", color: "bg-success/20 text-success" },
  { key: "cancelled", label: "Bekor", color: "bg-cream-100 text-muted" },
];

const PRIORITY_LABELS: Record<TaskPriority, { label: string; cls: string }> = {
  low: { label: "Past", cls: "text-muted" },
  medium: { label: "O'rta", cls: "text-charcoal" },
  high: { label: "Yuqori", cls: "text-warning" },
  critical: { label: "Kritik", cls: "text-destructive" },
};

export default function TasksPage() {
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-charcoal font-display text-3xl tracking-tight">Vazifalar</h1>
          <p className="text-muted text-sm">
            {tasks.length} ta vazifa · {tasks.filter((t) => t.status === "in_progress").length}{" "}
            jarayonda
          </p>
        </div>
        <div className="flex gap-2">
          <div className="border-cream-200 bg-cream inline-flex rounded-md border p-1">
            <button
              type="button"
              onClick={() => setView("kanban")}
              className={cn(
                "rounded px-3 py-1 text-sm",
                view === "kanban" ? "bg-gold text-charcoal" : "text-muted",
              )}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setView("list")}
              className={cn(
                "rounded px-3 py-1 text-sm",
                view === "list" ? "bg-gold text-charcoal" : "text-muted",
              )}
            >
              <ListIcon className="h-4 w-4" />
            </button>
          </div>
          <Can permission="tasks.create">
            <Button onClick={() => setShowForm((s) => !s)}>
              <Plus className="h-4 w-4" /> Vazifa
            </Button>
          </Can>
        </div>
      </div>

      {showForm ? (
        <CreateForm
          onSubmit={(payload) => create.mutate(payload)}
          loading={create.isPending}
        />
      ) : null}

      {isLoading ? (
        <p className="text-muted text-sm">Yuklanmoqda...</p>
      ) : view === "kanban" ? (
        <Kanban
          tasks={tasks}
          onMove={(id, status) => update.mutate({ id, status })}
          onDelete={(id) => remove.mutate(id)}
        />
      ) : (
        <TableView tasks={tasks} onDelete={(id) => remove.mutate(id)} />
      )}
    </div>
  );
}

function CreateForm({
  onSubmit,
  loading,
}: {
  onSubmit: (p: { title: string; description: string; priority: TaskPriority }) => void;
  loading: boolean;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Yangi vazifa</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <FormField label="Sarlavha" required>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </FormField>
        <FormField label="Tavsif">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="border-cream-200 bg-cream focus-visible:ring-gold/60 focus-visible:border-gold flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
          />
        </FormField>
        <FormField label="Muhimlik">
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
            className="border-cream-200 bg-cream focus-visible:ring-gold/60 focus-visible:border-gold flex h-11 w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
          >
            {Object.entries(PRIORITY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>
        </FormField>
        <Button
          onClick={() => title.trim() && onSubmit({ title, description, priority })}
          loading={loading}
        >
          Yaratish
        </Button>
      </CardContent>
    </Card>
  );
}

function Kanban({
  tasks,
  onMove,
  onDelete,
}: {
  tasks: Task[];
  onMove: (id: string, status: TaskStatus) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="grid gap-3 lg:grid-cols-5">
      {STATUSES.map((s) => {
        const items = tasks.filter((t) => t.status === s.key);
        return (
          <div key={s.key} className="bg-cream-100/40 border-cream-200 rounded-lg border p-3">
            <div className="mb-3 flex items-center justify-between">
              <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", s.color)}>
                {s.label}
              </span>
              <span className="text-muted text-xs">{items.length}</span>
            </div>
            <div className="space-y-2">
              {items.map((task) => (
                <TaskCard key={task.id} task={task} onMove={onMove} onDelete={onDelete} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TaskCard({
  task,
  onMove,
  onDelete,
}: {
  task: Task;
  onMove: (id: string, status: TaskStatus) => void;
  onDelete: (id: string) => void;
}) {
  const priority = PRIORITY_LABELS[task.priority];
  return (
    <div className="bg-cream border-cream-200 group rounded-md border p-3 text-sm shadow-sm">
      <p className="text-charcoal font-medium">{task.title}</p>
      {task.description ? (
        <p className="text-muted mt-1 line-clamp-2 text-xs">{task.description}</p>
      ) : null}
      <div className="mt-2 flex items-center justify-between">
        <span className={cn("text-xs", priority.cls)}>{priority.label}</span>
        <div className="flex items-center gap-1">
          <select
            value={task.status}
            onChange={(e) => onMove(task.id, e.target.value as TaskStatus)}
            className="border-cream-200 text-muted rounded border bg-transparent px-1 py-0.5 text-xs"
          >
            {STATUSES.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
          <Can permission="tasks.delete">
            <button
              type="button"
              onClick={() => onDelete(task.id)}
              className="text-destructive opacity-0 group-hover:opacity-100"
              aria-label="O'chirish"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </Can>
        </div>
      </div>
    </div>
  );
}

function TableView({ tasks, onDelete }: { tasks: Task[]; onDelete: (id: string) => void }) {
  return (
    <Card>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="border-cream-200 bg-cream-100/40 border-b text-left">
            <tr>
              <th className="px-4 py-2">Sarlavha</th>
              <th className="px-4 py-2">Holat</th>
              <th className="px-4 py-2">Muhimlik</th>
              <th className="px-4 py-2">Yaratilgan</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-cream-200 divide-y">
            {tasks.map((t) => {
              const status = STATUSES.find((s) => s.key === t.status);
              return (
                <tr key={t.id} className="hover:bg-cream-100/40">
                  <td className="px-4 py-2">{t.title}</td>
                  <td className="px-4 py-2">
                    <span className={cn("rounded-full px-2 py-0.5 text-xs", status?.color)}>
                      {status?.label}
                    </span>
                  </td>
                  <td className="px-4 py-2">{PRIORITY_LABELS[t.priority].label}</td>
                  <td className="text-muted px-4 py-2">
                    {new Date(t.created_at).toLocaleDateString("uz-UZ")}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Can permission="tasks.delete">
                      <button
                        type="button"
                        onClick={() => onDelete(t.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </Can>
                  </td>
                </tr>
              );
            })}
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-muted px-4 py-8 text-center text-sm">
                  Hozircha vazifalar yo&apos;q
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

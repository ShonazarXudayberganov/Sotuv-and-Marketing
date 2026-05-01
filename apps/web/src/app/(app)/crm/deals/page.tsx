"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Flame,
  Plus,
  Trash2,
  TrendingUp,
  Trophy,
  Users,
  X,
  XCircle,
} from "lucide-react";
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
import { extractApiError } from "@/lib/api-client";
import { crmApi } from "@/lib/crm-api";
import type {
  Contact,
  Deal,
  DealCreateRequest,
  Pipeline,
  PipelineStage,
} from "@/lib/types";
import { cn } from "@/lib/utils";

function fmtAmount(n: number, currency: string): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M ${currency}`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k ${currency}`;
  return `${n.toLocaleString("uz-UZ")} ${currency}`;
}

export default function DealsPage() {
  const qc = useQueryClient();
  const [pipelineId, setPipelineId] = useState<string | null>(null);
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [creating, setCreating] = useState(false);

  const { data: pipelines = [] } = useQuery({
    queryKey: ["crm", "pipelines"],
    queryFn: crmApi.listPipelines,
  });
  const activePipeline =
    pipelines.find((p) => p.id === pipelineId) ??
    pipelines.find((p) => p.is_default) ??
    pipelines[0] ??
    null;
  const activePipelineId = activePipeline?.id ?? null;

  const { data: deals = [], isLoading } = useQuery({
    queryKey: ["crm", "deals", activePipelineId],
    queryFn: () => crmApi.listDeals({ pipeline_id: activePipelineId, limit: 200 }),
    enabled: !!activePipelineId,
  });
  const { data: forecast } = useQuery({
    queryKey: ["crm", "deals", "forecast", activePipelineId],
    queryFn: () => crmApi.forecast(activePipelineId),
    enabled: !!activePipelineId,
  });
  const { data: stats } = useQuery({
    queryKey: ["crm", "deals", "stats"],
    queryFn: crmApi.dealStats,
  });

  const moveStage = useMutation({
    mutationFn: (args: { id: string; stageId: string }) =>
      crmApi.updateDeal(args.id, { stage_id: args.stageId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "deals"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const win = useMutation({
    mutationFn: (id: string) => crmApi.winDeal(id),
    onSuccess: () => {
      toast.success("🎉 Bitim yopildi (won)");
      qc.invalidateQueries({ queryKey: ["crm"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const lose = useMutation({
    mutationFn: (id: string) => crmApi.loseDeal(id),
    onSuccess: () => {
      toast.success("Bitim yopildi (lost)");
      qc.invalidateQueries({ queryKey: ["crm"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => crmApi.deleteDeal(id),
    onSuccess: () => {
      toast.success("O'chirildi");
      qc.invalidateQueries({ queryKey: ["crm"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const create = useMutation({
    mutationFn: (payload: DealCreateRequest) => crmApi.createDeal(payload),
    onSuccess: () => {
      toast.success("Bitim yaratildi");
      qc.invalidateQueries({ queryKey: ["crm"] });
      setCreating(false);
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
          { label: "CRM", href: "/crm" },
          { label: "Bitimlar" },
        ]}
        title="Bitimlar"
        description="Voronka bo'yicha bitimlar — drag & drop bilan bosqichdan-bosqichga"
        actions={
          <div className="flex items-center gap-2">
            {pipelines.length > 0 ? (
              <select
                value={activePipelineId ?? ""}
                onChange={(e) => setPipelineId(e.target.value)}
                className="flex h-9 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 text-[13px] text-[var(--fg)]"
              >
                {pipelines.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            ) : null}
            <div className="flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-0.5">
              <button
                type="button"
                onClick={() => setView("kanban")}
                className={cn(
                  "rounded px-3 py-1 text-[12px] font-medium transition-colors",
                  view === "kanban"
                    ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                    : "text-[var(--fg-muted)] hover:text-[var(--fg)]",
                )}
              >
                Kanban
              </button>
              <button
                type="button"
                onClick={() => setView("list")}
                className={cn(
                  "rounded px-3 py-1 text-[12px] font-medium transition-colors",
                  view === "list"
                    ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                    : "text-[var(--fg-muted)] hover:text-[var(--fg)]",
                )}
              >
                Ro&apos;yxat
              </button>
            </div>
            <Can permission="crm.write">
              <Button onClick={() => setCreating(true)}>
                <Plus /> Yangi bitim
              </Button>
            </Can>
          </div>
        }
      />

      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
        <SummaryTile
          icon={TrendingUp}
          label="Forecast (P×$)"
          value={fmtAmount(forecast?.weighted_amount ?? 0, "UZS")}
          hint={`${forecast?.open_count ?? 0} ochiq bitim`}
          tone="primary"
        />
        <SummaryTile
          icon={DollarSign}
          label="Ochiq summa"
          value={fmtAmount(forecast?.open_amount ?? 0, "UZS")}
          hint="Probability hisobga olinmagan"
        />
        <SummaryTile
          icon={Trophy}
          label="Yopilgan (won)"
          value={fmtAmount(stats?.won_amount ?? 0, "UZS")}
          hint={`Win rate: ${((stats?.win_rate ?? 0) * 100).toFixed(0)}%`}
          tone="success"
        />
        <SummaryTile
          icon={Flame}
          label="Yo'qotilgan"
          value={fmtAmount(stats?.lost_amount ?? 0, "UZS")}
          hint={`${stats?.by_status?.lost ?? 0} ta bitim`}
          tone="danger"
        />
      </div>

      {creating && activePipeline ? (
        <DealForm
          pipeline={activePipeline}
          onCancel={() => setCreating(false)}
          onSubmit={(p) => create.mutate(p)}
          loading={create.isPending}
        />
      ) : null}

      {!activePipeline ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={Users}
              title="Pipeline topilmadi"
              description="Tizim sozlanishi tugagach standart pipeline avtomatik yaratiladi"
            />
          </CardContent>
        </Card>
      ) : view === "kanban" ? (
        <KanbanBoard
          pipeline={activePipeline}
          deals={deals}
          loading={isLoading}
          onMove={(dealId, stageId) => moveStage.mutate({ id: dealId, stageId })}
          onWin={(id) => win.mutate(id)}
          onLose={(id) => lose.mutate(id)}
          onDelete={(id) => remove.mutate(id)}
        />
      ) : (
        <DealsTable deals={deals} pipeline={activePipeline} />
      )}
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
  icon: typeof TrendingUp;
  label: string;
  value: string;
  hint: string;
  tone?: "primary" | "success" | "danger";
}) {
  const tint =
    tone === "success"
      ? "bg-[var(--success-soft)] text-[var(--success)]"
      : tone === "danger"
        ? "bg-[var(--danger-soft)] text-[var(--danger)]"
        : "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]";
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[22px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        <p className="mt-1.5 truncate text-[11px] text-[var(--fg-subtle)]">{hint}</p>
      </div>
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${tint}`}
      >
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
}

function KanbanBoard({
  pipeline,
  deals,
  loading,
  onMove,
  onWin,
  onLose,
  onDelete,
}: {
  pipeline: Pipeline;
  deals: Deal[];
  loading: boolean;
  onMove: (dealId: string, stageId: string) => void;
  onWin: (id: string) => void;
  onLose: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const dealsByStage = useMemo(() => {
    const map = new Map<string, Deal[]>();
    for (const s of pipeline.stages) map.set(s.id, []);
    for (const d of deals) {
      if (map.has(d.stage_id)) map.get(d.stage_id)!.push(d);
    }
    return map;
  }, [deals, pipeline]);

  if (loading) {
    return (
      <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${pipeline.stages.length}, minmax(220px, 1fr))` }}>
        {pipeline.stages.map((s) => (
          <div
            key={s.id}
            className="h-64 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto pb-2">
      <div
        className="grid gap-3"
        style={{
          gridTemplateColumns: `repeat(${pipeline.stages.length}, minmax(240px, 1fr))`,
        }}
      >
        {pipeline.stages.map((stage) => {
          const stageDeals = dealsByStage.get(stage.id) ?? [];
          const sum = stageDeals.reduce((acc, d) => acc + d.amount, 0);
          return (
            <StageColumn
              key={stage.id}
              stage={stage}
              deals={stageDeals}
              sum={sum}
              onDrop={(dealId) => onMove(dealId, stage.id)}
              onWin={onWin}
              onLose={onLose}
              onDelete={onDelete}
            />
          );
        })}
      </div>
    </div>
  );
}

function StageColumn({
  stage,
  deals,
  sum,
  onDrop,
  onWin,
  onLose,
  onDelete,
}: {
  stage: PipelineStage;
  deals: Deal[];
  sum: number;
  onDrop: (dealId: string) => void;
  onWin: (id: string) => void;
  onLose: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [hover, setHover] = useState(false);
  const accent = stage.color ?? "var(--primary)";
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
        const id = e.dataTransfer.getData("text/deal-id");
        if (id) onDrop(id);
      }}
      className={cn(
        "flex min-h-[300px] flex-col gap-2 rounded-lg border bg-[var(--bg-subtle)] p-2 transition-colors",
        hover ? "border-[var(--primary)] bg-[var(--primary-soft)]/30" : "border-[var(--border)]",
      )}
    >
      <div className="flex items-center justify-between gap-2 px-1.5 py-1">
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: accent }}
          />
          <p className="text-[12px] font-semibold text-[var(--fg)]">{stage.name}</p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-[var(--fg-subtle)]">
          <span>{deals.length}</span>
          <span>·</span>
          <span>{stage.default_probability}%</span>
        </div>
      </div>
      <div className="px-1.5 text-[10px] text-[var(--fg-subtle)]">
        {fmtAmount(sum, "UZS")}
      </div>
      <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto">
        {deals.map((d) => (
          <DealCard
            key={d.id}
            deal={d}
            onWin={() => onWin(d.id)}
            onLose={() => onLose(d.id)}
            onDelete={() => onDelete(d.id)}
          />
        ))}
        {deals.length === 0 ? (
          <p className="px-1.5 py-3 text-center text-[11px] text-[var(--fg-subtle)]">
            Bo&apos;sh
          </p>
        ) : null}
      </div>
    </div>
  );
}

function DealCard({
  deal,
  onWin,
  onLose,
  onDelete,
}: {
  deal: Deal;
  onWin: () => void;
  onLose: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      draggable={deal.status === "open"}
      onDragStart={(e) => {
        if (deal.status !== "open") return;
        e.dataTransfer.setData("text/deal-id", deal.id);
        e.dataTransfer.effectAllowed = "move";
      }}
      className={cn(
        "group rounded-md border border-[var(--border)] bg-[var(--surface)] p-2.5 shadow-[var(--shadow-xs)]",
        deal.status === "open" ? "cursor-grab active:cursor-grabbing" : "opacity-70",
      )}
    >
      <p className="truncate text-[12px] font-medium text-[var(--fg)]">
        {deal.title}
      </p>
      <div className="mt-1 flex items-center justify-between gap-2 text-[10px]">
        <span className="font-semibold text-[var(--fg)]">
          {fmtAmount(deal.amount, deal.currency)}
        </span>
        <span className="text-[var(--fg-subtle)]">{deal.probability}%</span>
      </div>
      {deal.expected_close_at ? (
        <p className="mt-1 text-[10px] text-[var(--fg-subtle)]">
          Yopilish: {new Date(deal.expected_close_at).toLocaleDateString("uz-UZ")}
        </p>
      ) : null}
      <Can permission="crm.write">
        <div className="mt-1.5 flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
          {deal.status === "open" ? (
            <>
              <button
                type="button"
                onClick={onWin}
                aria-label="Won"
                className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--success-soft)] hover:text-[var(--success)]"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={onLose}
                aria-label="Lost"
                className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--warning-soft)] hover:text-[var(--warning)]"
              >
                <XCircle className="h-3.5 w-3.5" />
              </button>
            </>
          ) : null}
          <button
            type="button"
            onClick={onDelete}
            aria-label="O'chirish"
            className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </Can>
    </div>
  );
}

function DealsTable({
  deals,
  pipeline,
}: {
  deals: Deal[];
  pipeline: Pipeline;
}) {
  const stageMap = useMemo(() => {
    const map = new Map<string, PipelineStage>();
    for (const s of pipeline.stages) map.set(s.id, s);
    return map;
  }, [pipeline]);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hamma bitimlar</CardTitle>
      </CardHeader>
      <CardContent>
        {deals.length === 0 ? (
          <EmptyState
            icon={DollarSign}
            title="Bitimlar yo'q"
            description="Birinchi bitimni yarating"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-[11px] tracking-wider text-[var(--fg-subtle)] uppercase">
                  <th className="py-2 pr-3">Sarlavha</th>
                  <th className="py-2 pr-3">Bosqich</th>
                  <th className="py-2 pr-3">Summa</th>
                  <th className="py-2 pr-3">Ehtimol</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Yangilangan</th>
                </tr>
              </thead>
              <tbody>
                {deals.map((d) => {
                  const stage = stageMap.get(d.stage_id);
                  return (
                    <tr
                      key={d.id}
                      className="border-t border-[var(--border)] text-[var(--fg)]"
                    >
                      <td className="py-2 pr-3">{d.title}</td>
                      <td className="py-2 pr-3 text-[var(--fg-muted)]">
                        {stage?.name ?? "—"}
                      </td>
                      <td className="py-2 pr-3">
                        {fmtAmount(d.amount, d.currency)}
                      </td>
                      <td className="py-2 pr-3">{d.probability}%</td>
                      <td className="py-2 pr-3">
                        <DealStatusBadge status={d.status} />
                      </td>
                      <td className="py-2 pr-3 text-[var(--fg-subtle)]">
                        {new Date(d.updated_at).toLocaleDateString("uz-UZ")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DealStatusBadge({ status }: { status: string }) {
  if (status === "won") {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-2.5 w-2.5" /> Yopildi
      </Badge>
    );
  }
  if (status === "lost") {
    return (
      <Badge variant="danger">
        <AlertTriangle className="h-2.5 w-2.5" /> Yo&apos;qotildi
      </Badge>
    );
  }
  return <Badge variant="info">Ochiq</Badge>;
}

function DealForm({
  pipeline,
  onCancel,
  onSubmit,
  loading,
}: {
  pipeline: Pipeline;
  onCancel: () => void;
  onSubmit: (p: DealCreateRequest) => void;
  loading: boolean;
}) {
  const [title, setTitle] = useState("");
  const [contactQuery, setContactQuery] = useState("");
  const [contactId, setContactId] = useState<string | null>(null);
  const [stageId, setStageId] = useState(pipeline.stages[0]?.id ?? "");
  const [amount, setAmount] = useState("0");
  const [currency, setCurrency] = useState("UZS");
  const [expectedClose, setExpectedClose] = useState("");
  const [notes, setNotes] = useState("");

  const { data: matches = [] } = useQuery({
    queryKey: ["crm", "contacts", "search", contactQuery],
    queryFn: () => crmApi.list({ query: contactQuery, limit: 8 }),
    enabled: contactQuery.length >= 2,
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi bitim</CardTitle>
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
          <FormField label="Sarlavha" required>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Akme — server modernizatsiya"
              autoFocus
            />
          </FormField>

          <FormField
            label="Kontakt"
            hint="Ism yoki telefon kiriting (kamida 2 belgi)"
          >
            <Input
              value={contactQuery}
              onChange={(e) => {
                setContactQuery(e.target.value);
                setContactId(null);
              }}
              placeholder="Mijoz qidirish..."
            />
            {contactQuery.length >= 2 && matches.length > 0 ? (
              <div className="mt-1.5 max-h-40 overflow-y-auto rounded-md border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
                {matches.map((c: Contact) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => {
                      setContactId(c.id);
                      setContactQuery(c.full_name);
                    }}
                    className={cn(
                      "flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-[12px] transition-colors hover:bg-[var(--surface-hover)]",
                      contactId === c.id && "bg-[var(--primary-soft)]",
                    )}
                  >
                    <span className="truncate text-[var(--fg)]">{c.full_name}</span>
                    <span className="truncate text-[var(--fg-subtle)]">
                      {c.phone ?? c.email ?? "—"}
                    </span>
                  </button>
                ))}
              </div>
            ) : null}
          </FormField>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Bosqich">
              <select
                value={stageId}
                onChange={(e) => setStageId(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              >
                {pipeline.stages
                  .filter((s) => !s.is_won && !s.is_lost)
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.default_probability}%)
                    </option>
                  ))}
              </select>
            </FormField>
            <FormField label="Kutilgan yopilish sanasi">
              <input
                type="date"
                value={expectedClose}
                onChange={(e) => setExpectedClose(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              />
            </FormField>
            <FormField label="Summa">
              <Input
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ""))}
                placeholder="5000000"
              />
            </FormField>
            <FormField label="Valyuta">
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              >
                <option value="UZS">UZS</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </FormField>
          </div>

          <FormField label="Eslatma">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="flex min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)]"
              placeholder="Bitim haqida qisqacha..."
            />
          </FormField>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => {
                if (!title.trim()) return;
                onSubmit({
                  title: title.trim(),
                  contact_id: contactId,
                  pipeline_id: pipeline.id,
                  stage_id: stageId,
                  amount: parseInt(amount || "0", 10),
                  currency,
                  expected_close_at: expectedClose
                    ? new Date(expectedClose).toISOString()
                    : null,
                  notes: notes || null,
                });
              }}
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

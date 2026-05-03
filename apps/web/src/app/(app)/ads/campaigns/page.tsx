"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Megaphone,
  Pause,
  Play,
  Plus,
  Search,
  Trash2,
  X,
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
import { adsApi } from "@/lib/ads-api";
import { extractApiError } from "@/lib/api-client";
import type { Campaign, CampaignDraftRequest } from "@/lib/types";
import { cn } from "@/lib/utils";

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString("uz-UZ");
}

const STATUS_FILTERS = ["all", "active", "paused", "draft", "archived"] as const;
const NETWORK_FILTERS = ["all", "meta", "google"] as const;

export default function CampaignsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<(typeof STATUS_FILTERS)[number]>("all");
  const [networkFilter, setNetworkFilter] = useState<(typeof NETWORK_FILTERS)[number]>("all");
  const [creating, setCreating] = useState(false);
  const [query, setQuery] = useState("");

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["ads", "campaigns", statusFilter, networkFilter],
    queryFn: () =>
      adsApi.listCampaigns({
        status: statusFilter === "all" ? undefined : statusFilter,
        network: networkFilter === "all" ? undefined : networkFilter,
        limit: 200,
      }),
  });

  const { data: accounts = [] } = useQuery({
    queryKey: ["ads", "accounts"],
    queryFn: () => adsApi.listAccounts(),
  });

  const filtered = useMemo(() => {
    if (!query.trim()) return campaigns;
    const needle = query.trim().toLowerCase();
    return campaigns.filter((c) => c.name.toLowerCase().includes(needle));
  }, [campaigns, query]);

  const updateStatus = useMutation({
    mutationFn: (args: { id: string; status: string }) =>
      adsApi.updateCampaign(args.id, { status: args.status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ads"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => adsApi.deleteCampaign(id),
    onSuccess: () => {
      toast.success("Kampaniya o'chirildi");
      qc.invalidateQueries({ queryKey: ["ads"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const create = useMutation({
    mutationFn: (payload: CampaignDraftRequest) => adsApi.createDraft(payload),
    onSuccess: () => {
      toast.success("Draft yaratildi");
      qc.invalidateQueries({ queryKey: ["ads"] });
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
          { label: "Reklama", href: "/ads" },
          { label: "Kampaniyalar" },
        ]}
        title="Kampaniyalar"
        description="Meta + Google reklamalarni filtr qilish, draft yaratish, status boshqarish"
        actions={
          <Can permission="ads.write">
            <Button onClick={() => setCreating(true)} disabled={accounts.length === 0}>
              <Plus /> Yangi draft
            </Button>
          </Can>
        }
      />

      {creating ? (
        <DraftForm
          accounts={accounts.map((a) => ({
            id: a.id,
            label: `${a.network.toUpperCase()} · ${a.name}`,
          }))}
          onCancel={() => setCreating(false)}
          onSubmit={(p) => create.mutate(p)}
          loading={create.isPending}
        />
      ) : null}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[var(--fg-subtle)]" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Kampaniya nomi..."
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {STATUS_FILTERS.map((s) => (
            <FilterPill
              key={s}
              active={statusFilter === s}
              onClick={() => setStatusFilter(s)}
              label={s === "all" ? "Hammasi" : s}
            />
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {NETWORK_FILTERS.map((n) => (
            <FilterPill
              key={n}
              active={networkFilter === n}
              onClick={() => setNetworkFilter(n)}
              label={n === "all" ? "Tarmoqlar" : n.toUpperCase()}
            />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Kampaniyalar ro&apos;yxati</CardTitle>
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
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={Megaphone}
              title="Kampaniyalar yo'q"
              description={
                query
                  ? "Filterga to'g'ri keladigan kampaniya yo'q"
                  : "Yangi draft yarating yoki Mock seed bilan namuna ma'lumot olib keling"
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[10px] tracking-wider text-[var(--fg-subtle)] uppercase">
                    <th className="py-2 pr-3">Nomi</th>
                    <th className="py-2 pr-3">Tarmoq</th>
                    <th className="py-2 pr-3">Status</th>
                    <th className="py-2 pr-3">Maqsad</th>
                    <th className="py-2 pr-3">Byudjet/kun</th>
                    <th className="py-2 pr-3">Impressions</th>
                    <th className="py-2 pr-3">CTR</th>
                    <th className="py-2 pr-3">Spend</th>
                    <th className="py-2 pr-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => (
                    <CampaignRow
                      key={c.id}
                      campaign={c}
                      onPause={() => updateStatus.mutate({ id: c.id, status: "paused" })}
                      onActivate={() => updateStatus.mutate({ id: c.id, status: "active" })}
                      onDelete={() => remove.mutate(c.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
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
        "rounded-md border px-2.5 py-1 text-[12px] capitalize transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
      )}
    >
      {label}
    </button>
  );
}

function CampaignRow({
  campaign,
  onPause,
  onActivate,
  onDelete,
}: {
  campaign: Campaign;
  onPause: () => void;
  onActivate: () => void;
  onDelete: () => void;
}) {
  const m = campaign.metrics;
  return (
    <tr className="group border-t border-[var(--border)] text-[var(--fg)]">
      <td className="py-2 pr-3">
        <div className="flex items-center gap-2">
          <Megaphone className="h-3.5 w-3.5 text-[var(--fg-subtle)]" />
          <span className="font-medium">{campaign.name}</span>
        </div>
      </td>
      <td className="py-2 pr-3">
        <Badge variant="outline" className="capitalize">
          {campaign.network}
        </Badge>
      </td>
      <td className="py-2 pr-3">
        <StatusBadge status={campaign.status} />
      </td>
      <td className="py-2 pr-3 text-[var(--fg-muted)] capitalize">{campaign.objective}</td>
      <td className="py-2 pr-3 font-medium">
        {fmt(campaign.daily_budget)} {campaign.currency}
      </td>
      <td className="py-2 pr-3 text-[var(--fg-muted)]">{m ? fmt(m.impressions) : "—"}</td>
      <td className="py-2 pr-3 text-[var(--fg-muted)]">
        {m ? `${(m.ctr / 100).toFixed(2)}%` : "—"}
      </td>
      <td className="py-2 pr-3 text-[var(--fg-muted)]">{m ? fmt(m.spend) : "—"}</td>
      <td className="py-2 pr-3">
        <Can permission="ads.write">
          <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
            {campaign.status === "active" ? (
              <button
                type="button"
                onClick={onPause}
                aria-label="Pauza"
                className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--warning-soft)] hover:text-[var(--warning)]"
              >
                <Pause className="h-3.5 w-3.5" />
              </button>
            ) : campaign.status !== "archived" ? (
              <button
                type="button"
                onClick={onActivate}
                aria-label="Faollashtirish"
                className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--success-soft)] hover:text-[var(--success)]"
              >
                <Play className="h-3.5 w-3.5" />
              </button>
            ) : null}
            <button
              type="button"
              onClick={onDelete}
              aria-label="O'chirish"
              className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </Can>
      </td>
    </tr>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "active") {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-2.5 w-2.5" /> Faol
      </Badge>
    );
  }
  if (status === "paused") {
    return (
      <Badge variant="warning">
        <Pause className="h-2.5 w-2.5" /> Pauza
      </Badge>
    );
  }
  if (status === "draft") {
    return <Badge variant="default">Draft</Badge>;
  }
  if (status === "archived") {
    return <Badge variant="outline">Arxiv</Badge>;
  }
  return (
    <Badge variant="danger">
      <AlertTriangle className="h-2.5 w-2.5" /> {status}
    </Badge>
  );
}

function DraftForm({
  accounts,
  onCancel,
  onSubmit,
  loading,
}: {
  accounts: { id: string; label: string }[];
  onCancel: () => void;
  onSubmit: (p: CampaignDraftRequest) => void;
  loading: boolean;
}) {
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [name, setName] = useState("");
  const [objective, setObjective] = useState<
    "awareness" | "traffic" | "leads" | "conversions" | "sales"
  >("traffic");
  const [budget, setBudget] = useState("100000");
  const [currency, setCurrency] = useState("UZS");
  const [headline, setHeadline] = useState("");
  const [audience, setAudience] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi reklama drafti</CardTitle>
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
            <FormField label="Reklama akkaunti" required>
              <select
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              >
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Maqsad" required>
              <select
                value={objective}
                onChange={(e) => setObjective(e.target.value as typeof objective)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              >
                <option value="awareness">Awareness — tanitish</option>
                <option value="traffic">Traffic — saytga klik</option>
                <option value="leads">Leads — yangi mijoz</option>
                <option value="conversions">Conversions — sotuv</option>
                <option value="sales">Sales — to&apos;g&apos;ridan sotuv</option>
              </select>
            </FormField>
          </div>

          <FormField label="Kampaniya nomi" required>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Bahor aksiyasi 2026"
            />
          </FormField>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Kunlik byudjet">
              <Input
                value={budget}
                onChange={(e) => setBudget(e.target.value.replace(/[^\d]/g, ""))}
                placeholder="500000"
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
              </select>
            </FormField>
          </div>

          <FormField label="Sarlavha (kreativ uchun)">
            <Input
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="Yangi xizmat — 20% chegirma"
            />
          </FormField>

          <FormField
            label="Auditoriya tavsifi"
            hint="Yosh, manfaatlar, manzil — JSON kabi yozing yoki qoldiring"
          >
            <textarea
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder='age 25-45, interests: ["beauty","wellness"], cities: ["Toshkent"]'
              className="flex min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)]"
            />
          </FormField>

          <div className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-[12px] text-[var(--fg-muted)]">
            <Camera className="mr-1.5 inline h-3.5 w-3.5" />
            Sprint 3.1 — draft yaratish va lokal kuzatuv. Real Meta/Google API&apos;ga launch
            bo&apos;lish keyingi sprintda (inson tasdig&apos;i bilan).
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => {
                if (!name.trim() || !accountId) return;
                onSubmit({
                  account_id: accountId,
                  name: name.trim(),
                  objective,
                  daily_budget: parseInt(budget || "0", 10),
                  currency,
                  audience: audience.trim() ? { raw: audience.trim() } : null,
                  creative: headline.trim() ? { headline: headline.trim() } : null,
                });
              }}
              loading={loading}
              disabled={!name.trim() || !accountId}
            >
              Draft yaratish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

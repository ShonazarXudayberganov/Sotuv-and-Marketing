"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AtSign,
  Mail,
  MessageSquare,
  Phone,
  PhoneCall,
  Plus,
  Search,
  Sparkles,
  Trash2,
  Users,
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
import { extractApiError } from "@/lib/api-client";
import { crmApi } from "@/lib/crm-api";
import type {
  ActivityCreateRequest,
  Contact,
  ContactCreateRequest,
  ContactStatus,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_FILTERS: { key: ContactStatus | "all"; label: string }[] = [
  { key: "all", label: "Hammasi" },
  { key: "lead", label: "Yangi lead" },
  { key: "active", label: "Aktiv" },
  { key: "customer", label: "Mijoz" },
  { key: "lost", label: "Yo'qotilgan" },
];

export default function ContactsPage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ContactStatus | "all">("all");
  const [creating, setCreating] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeStatus = statusFilter === "all" ? undefined : statusFilter;
  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["crm", "contacts", query, activeStatus],
    queryFn: () => crmApi.list({ query, status: activeStatus, limit: 100 }),
  });

  const create = useMutation({
    mutationFn: (payload: ContactCreateRequest) => crmApi.create(payload),
    onSuccess: () => {
      toast.success("Mijoz qo'shildi");
      qc.invalidateQueries({ queryKey: ["crm"] });
      setCreating(false);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => crmApi.remove(id),
    onSuccess: () => {
      toast.success("O'chirildi");
      setActiveId(null);
      qc.invalidateQueries({ queryKey: ["crm"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const active = useMemo(
    () => contacts.find((c) => c.id === activeId) ?? null,
    [contacts, activeId],
  );

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
          { label: "Mijozlar" },
        ]}
        title="Mijozlar"
        description="Qidirish, AI scoring, faoliyat tarixi va inline tahrirlash"
        actions={
          <Can permission="crm.write">
            <Button onClick={() => setCreating(true)}>
              <Plus /> Yangi mijoz
            </Button>
          </Can>
        }
      />

      {creating ? (
        <ContactForm
          onCancel={() => setCreating(false)}
          onSubmit={(p) => create.mutate(p)}
          loading={create.isPending}
        />
      ) : null}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[var(--fg-subtle)]" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ism, telefon yoki email..."
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s.key}
              type="button"
              onClick={() => setStatusFilter(s.key)}
              className={cn(
                "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
                statusFilter === s.key
                  ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                  : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        <Card>
          <CardHeader>
            <CardTitle>Ro&apos;yxat</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-16 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                  />
                ))}
              </div>
            ) : contacts.length === 0 ? (
              <EmptyState
                icon={Users}
                title="Mijozlar yo'q"
                description={
                  query || statusFilter !== "all"
                    ? "Filterga to'g'ri keladigan mijoz yo'q"
                    : "Yangi mijoz qo'shing"
                }
              />
            ) : (
              <div className="space-y-2">
                {contacts.map((c) => (
                  <ContactRow
                    key={c.id}
                    contact={c}
                    active={c.id === activeId}
                    onSelect={() => setActiveId(c.id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {active ? (
          <ContactDrawer
            contact={active}
            onClose={() => setActiveId(null)}
            onDelete={() => remove.mutate(active.id)}
            onChanged={() => qc.invalidateQueries({ queryKey: ["crm"] })}
          />
        ) : (
          <Card>
            <CardContent>
              <EmptyState
                icon={Sparkles}
                title="Mijozni tanlang"
                description="Ro'yxatdan kontaktni bossangiz, bu yerda timeline va AI tahlil ochiladi"
              />
            </CardContent>
          </Card>
        )}
      </div>
    </motion.div>
  );
}

function ContactRow({
  contact,
  active,
  onSelect,
}: {
  contact: Contact;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)]/40"
          : "border-[var(--border)] bg-[var(--bg-subtle)] hover:border-[var(--primary)]",
      )}
    >
      <ScoreCircle score={contact.ai_score} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">
            {contact.full_name}
          </p>
          <Badge variant="outline" className="capitalize">
            {contact.status}
          </Badge>
          {contact.tags?.includes("vip") ? (
            <Badge variant="primary">VIP</Badge>
          ) : null}
        </div>
        <p className="truncate text-[11px] text-[var(--fg-subtle)]">
          {contact.company_name ?? "—"}
          {contact.phone ? ` · ${contact.phone}` : ""}
          {contact.email ? ` · ${contact.email}` : ""}
        </p>
      </div>
    </button>
  );
}

function ScoreCircle({ score }: { score: number }) {
  const tone =
    score >= 75
      ? "bg-[var(--success)] text-white"
      : score >= 45
        ? "bg-[var(--info)] text-white"
        : score >= 20
          ? "bg-[var(--warning)] text-white"
          : "bg-[var(--surface-hover)] text-[var(--fg-muted)]";
  return (
    <div
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold ${tone}`}
      title={`AI score ${score}/100`}
    >
      {score}
    </div>
  );
}

function ContactDrawer({
  contact,
  onClose,
  onDelete,
  onChanged,
}: {
  contact: Contact;
  onClose: () => void;
  onDelete: () => void;
  onChanged: () => void;
}) {
  const qc = useQueryClient();
  const { data: timeline = [] } = useQuery({
    queryKey: ["crm", "activities", contact.id],
    queryFn: () => crmApi.listActivities(contact.id, 50),
  });

  const addActivity = useMutation({
    mutationFn: (payload: ActivityCreateRequest) =>
      crmApi.addActivity(contact.id, payload),
    onSuccess: () => {
      toast.success("Faoliyat qo'shildi");
      qc.invalidateQueries({ queryKey: ["crm"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const rescore = useMutation({
    mutationFn: () => crmApi.rescore(contact.id),
    onSuccess: (res) => {
      toast.success(`Score: ${res.score}`);
      onChanged();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const setStatus = useMutation({
    mutationFn: (status: string) => crmApi.update(contact.id, { status }),
    onSuccess: () => {
      toast.success("Status yangilandi");
      onChanged();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>{contact.full_name}</CardTitle>
          <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
            {contact.company_name ?? "—"} · {contact.industry ?? "—"}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Yopish"
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
        >
          <X className="h-4 w-4" />
        </button>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Score */}
        <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3">
          <ScoreCircle score={contact.ai_score} />
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
              AI score
            </p>
            <p className="text-[13px] text-[var(--fg)]">
              {contact.ai_score_reason ?? "Hisoblanmagan"}
            </p>
          </div>
          <Can permission="crm.write">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => rescore.mutate()}
              loading={rescore.isPending}
            >
              <Sparkles /> Qayta hisobla
            </Button>
          </Can>
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap gap-1.5">
          {contact.phone ? (
            <ActionPill
              icon={PhoneCall}
              label="Qo'ng'iroq"
              onClick={() =>
                addActivity.mutate({
                  kind: "call_out",
                  channel: "phone",
                  direction: "out",
                  title: "Qo'ng'iroq",
                })
              }
            />
          ) : null}
          {contact.telegram_username ? (
            <ActionPill
              icon={MessageSquare}
              label="Xabar"
              onClick={() =>
                addActivity.mutate({
                  kind: "message_out",
                  channel: "telegram",
                  direction: "out",
                  title: "Xabar yuborildi",
                })
              }
            />
          ) : null}
          {contact.email ? (
            <ActionPill
              icon={Mail}
              label="Email"
              onClick={() =>
                addActivity.mutate({
                  kind: "email",
                  channel: "email",
                  direction: "out",
                  title: "Email",
                })
              }
            />
          ) : null}
          <ActionPill
            icon={Sparkles}
            label="Eslatma"
            onClick={() =>
              addActivity.mutate({ kind: "note", title: "Eslatma" })
            }
          />
        </div>

        {/* Status switcher */}
        <div>
          <p className="mb-1.5 text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
            Status
          </p>
          <div className="flex flex-wrap gap-1.5">
            {(["lead", "active", "customer", "lost", "archived"] as ContactStatus[]).map(
              (s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatus.mutate(s)}
                  disabled={setStatus.isPending || s === contact.status}
                  className={cn(
                    "rounded-md border px-2.5 py-1 text-[12px] transition-colors disabled:opacity-50",
                    s === contact.status
                      ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                      : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
                  )}
                >
                  {s}
                </button>
              ),
            )}
          </div>
        </div>

        {/* Channels */}
        <div className="space-y-1.5 text-[12px]">
          {contact.phone ? (
            <ChannelLine icon={Phone} value={contact.phone} />
          ) : null}
          {contact.email ? (
            <ChannelLine icon={Mail} value={contact.email} />
          ) : null}
          {contact.telegram_username ? (
            <ChannelLine
              icon={AtSign}
              value={`@${contact.telegram_username} (TG)`}
            />
          ) : null}
        </div>

        {/* Timeline */}
        <div>
          <p className="mb-2 text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
            Faoliyat tarixi
          </p>
          {timeline.length === 0 ? (
            <p className="text-[12px] text-[var(--fg-muted)]">
              Hozircha hech qanday faoliyat yo&apos;q.
            </p>
          ) : (
            <div className="space-y-2">
              {timeline.slice(0, 10).map((a) => (
                <div
                  key={a.id}
                  className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-2.5"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="capitalize">
                      {a.kind.replace("_", " ")}
                    </Badge>
                    {a.channel ? (
                      <Badge variant="default">{a.channel}</Badge>
                    ) : null}
                    <span className="ml-auto text-[10px] text-[var(--fg-subtle)]">
                      {new Date(a.occurred_at).toLocaleString("uz-UZ")}
                    </span>
                  </div>
                  {a.title || a.body ? (
                    <p className="mt-1 text-[12px] text-[var(--fg)]">
                      {a.title}
                      {a.body ? `: ${a.body}` : ""}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>

        <Can permission="crm.write">
          <button
            type="button"
            onClick={onDelete}
            className="flex items-center gap-1.5 text-[12px] text-[var(--danger)] hover:underline"
          >
            <Trash2 className="h-3.5 w-3.5" /> Mijozni o&apos;chirish
          </button>
        </Can>
      </CardContent>
    </Card>
  );
}

function ActionPill({
  icon: Icon,
  label,
  onClick,
}: {
  icon: typeof PhoneCall;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-[12px] text-[var(--fg-muted)] transition-colors hover:border-[var(--primary)] hover:text-[var(--fg)]"
    >
      <Icon className="h-3.5 w-3.5" /> {label}
    </button>
  );
}

function ChannelLine({
  icon: Icon,
  value,
}: {
  icon: typeof Phone;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2 text-[var(--fg)]">
      <Icon className="h-3.5 w-3.5 text-[var(--fg-subtle)]" />
      <span>{value}</span>
    </div>
  );
}

function ContactForm({
  onCancel,
  onSubmit,
  loading,
}: {
  onCancel: () => void;
  onSubmit: (p: ContactCreateRequest) => void;
  loading: boolean;
}) {
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [telegram, setTelegram] = useState("");
  const [status, setStatus] = useState<ContactStatus>("lead");
  const [notes, setNotes] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi mijoz</CardTitle>
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
            <FormField label="To'liq ism" required>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Akmal Karimov"
                autoFocus
              />
            </FormField>
            <FormField label="Kompaniya">
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Akme LLC"
              />
            </FormField>
            <FormField label="Telefon">
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+998 90 123 45 67"
              />
            </FormField>
            <FormField label="Email">
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
              />
            </FormField>
            <FormField label="Telegram">
              <Input
                value={telegram}
                onChange={(e) => setTelegram(e.target.value.replace(/^@/, ""))}
                placeholder="username"
              />
            </FormField>
            <FormField label="Status">
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as ContactStatus)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              >
                <option value="lead">Yangi lead</option>
                <option value="active">Aktiv</option>
                <option value="customer">Mijoz</option>
                <option value="lost">Yo&apos;qotilgan</option>
              </select>
            </FormField>
          </div>
          <FormField label="Eslatma">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Mijoz haqida qisqacha..."
              className="flex min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                fullName.trim() &&
                onSubmit({
                  full_name: fullName.trim(),
                  company_name: companyName || null,
                  phone: phone || null,
                  email: email || null,
                  telegram_username: telegram || null,
                  status,
                  notes: notes || null,
                })
              }
              loading={loading}
              disabled={!fullName.trim()}
            >
              Yaratish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

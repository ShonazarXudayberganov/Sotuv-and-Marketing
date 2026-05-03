"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpToLine,
  CheckCircle2,
  Copy,
  KeyRound,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  Webhook as WebhookIcon,
  X,
} from "lucide-react";
import { useState } from "react";
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
import { marketplaceApi } from "@/lib/marketplace-api";
import type { WebhookEndpoint, WebhookEndpointWithSecret } from "@/lib/types";
import { cn } from "@/lib/utils";

const SUPPORTED_EVENTS = [
  "contact.created",
  "contact.updated",
  "deal.created",
  "deal.won",
  "deal.lost",
  "post.published",
  "ads.snapshot",
  "inbox.message_in",
];

export default function WebhooksPage() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [revealedSecret, setRevealedSecret] = useState<{ id: string; secret: string } | null>(
    null,
  );
  const [activeId, setActiveId] = useState<string | null>(null);

  const { data: endpoints = [], isLoading } = useQuery({
    queryKey: ["webhooks"],
    queryFn: () => marketplaceApi.listWebhooks(),
  });

  const create = useMutation({
    mutationFn: (payload: {
      name: string;
      direction: "in" | "out";
      url?: string | null;
      events?: string[] | null;
    }) => marketplaceApi.createWebhook(payload),
    onSuccess: (rec) => {
      toast.success("Webhook yaratildi");
      setRevealedSecret({ id: rec.id, secret: rec.secret });
      qc.invalidateQueries({ queryKey: ["webhooks"] });
      setCreating(false);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const rotate = useMutation({
    mutationFn: (id: string) => marketplaceApi.rotateSecret(id),
    onSuccess: (rec: WebhookEndpointWithSecret) => {
      setRevealedSecret({ id: rec.id, secret: rec.secret });
      toast.success("Secret yangilandi");
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const toggle = useMutation({
    mutationFn: (args: { id: string; active: boolean }) =>
      marketplaceApi.toggleWebhook(args.id, args.active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => marketplaceApi.deleteWebhook(id),
    onSuccess: () => {
      toast.success("Webhook o'chirildi");
      qc.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const test = useMutation({
    mutationFn: (id: string) =>
      marketplaceApi.testWebhook(id, {
        event: "deal.won",
        payload: { deal_id: "test", amount: 1000000 },
      }),
    onSuccess: (res) => {
      toast.success(
        res.succeeded
          ? `Yuborildi (${res.status_code})`
          : `Xatolik (${res.error ?? res.status_code})`,
      );
      qc.invalidateQueries({ queryKey: ["webhooks", "deliveries"] });
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
          { label: "Sozlamalar", href: "/settings" },
          { label: "Webhooks" },
        ]}
        title="Webhooks API"
        description="Voqealarni tashqi tizimlarga POST qiling yoki tashqi tizimlardan xabar qabul qiling (HMAC SHA256)"
        actions={
          <Can permission="integrations.write">
            <Button onClick={() => setCreating(true)}>
              <Plus /> Yangi webhook
            </Button>
          </Can>
        }
      />

      {revealedSecret ? (
        <SecretReveal secret={revealedSecret.secret} onClose={() => setRevealedSecret(null)} />
      ) : null}

      {creating ? (
        <CreateForm
          onCancel={() => setCreating(false)}
          onSubmit={(p) => create.mutate(p)}
          loading={create.isPending}
        />
      ) : null}

      {isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : endpoints.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={WebhookIcon}
              title="Hozircha webhook'lar yo'q"
              description="Outbound webhook orqali Slack/Zapier'ga voqealarni yuboring yoki inbound endpoint orqali tashqi tizim ma'lumotini qabul qiling"
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {endpoints.map((ep) => (
            <EndpointRow
              key={ep.id}
              endpoint={ep}
              expanded={activeId === ep.id}
              onToggleDetails={() => setActiveId(activeId === ep.id ? null : ep.id)}
              onTest={() => test.mutate(ep.id)}
              onRotate={() => rotate.mutate(ep.id)}
              onActivate={() => toggle.mutate({ id: ep.id, active: !ep.is_active })}
              onDelete={() => remove.mutate(ep.id)}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function SecretReveal({ secret, onClose }: { secret: string; onClose: () => void }) {
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(secret);
      toast.success("Nusxa olindi");
    } catch {
      toast.error("Nusxa olib bo'lmadi");
    }
  };
  return (
    <Card className="border-[var(--warning)] bg-[var(--warning-soft)]/30">
      <CardHeader className="flex flex-row items-start justify-between">
        <div className="flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-[var(--warning)]" />
          <CardTitle>Secret faqat hozir ko&apos;rsatiladi</CardTitle>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Yopish"
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:text-[var(--fg)]"
        >
          <X className="h-4 w-4" />
        </button>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-[13px] text-[var(--fg)]">
          Bu secret HMAC-SHA256 imzo yaratish uchun ishlatiladi. Endi qaytadan
          ko&apos;rsatilmaydi — saqlab qo&apos;ying.
        </p>
        <div className="flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] p-2 font-mono text-[12px]">
          <span className="flex-1 truncate text-[var(--fg)]">{secret}</span>
          <Button variant="ghost" size="sm" onClick={copy}>
            <Copy /> Nusxa
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function EndpointRow({
  endpoint,
  expanded,
  onToggleDetails,
  onTest,
  onRotate,
  onActivate,
  onDelete,
}: {
  endpoint: WebhookEndpoint;
  expanded: boolean;
  onToggleDetails: () => void;
  onTest: () => void;
  onRotate: () => void;
  onActivate: () => void;
  onDelete: () => void;
}) {
  const isOutbound = endpoint.direction === "out";
  return (
    <Card>
      <CardContent className="flex items-start gap-3 py-4">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
            isOutbound
              ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
              : "bg-[var(--info-soft)] text-[var(--info)]",
          )}
        >
          {isOutbound ? (
            <ArrowUpToLine className="h-4 w-4" />
          ) : (
            <ArrowDownToLine className="h-4 w-4" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[14px] font-semibold text-[var(--fg)]">{endpoint.name}</p>
            <Badge variant="outline">{isOutbound ? "Outbound" : "Inbound"}</Badge>
            {endpoint.is_active ? (
              <Badge variant="success">
                <CheckCircle2 className="h-2.5 w-2.5" /> Faol
              </Badge>
            ) : (
              <Badge variant="warning">Pauza</Badge>
            )}
          </div>
          {endpoint.url ? (
            <p className="mt-1 truncate font-mono text-[11px] text-[var(--fg-subtle)]">
              {endpoint.url}
            </p>
          ) : (
            <p className="mt-1 text-[11px] text-[var(--fg-subtle)]">
              POST /api/v1/marketplace/webhooks/in/{endpoint.id}
            </p>
          )}
          <div className="mt-1.5 flex flex-wrap gap-2 text-[11px] text-[var(--fg-muted)]">
            <span>✓ {endpoint.success_count}</span>
            <span>✗ {endpoint.failure_count}</span>
            {endpoint.last_status ? <span>HTTP {endpoint.last_status}</span> : null}
            {endpoint.last_triggered_at ? (
              <span>{new Date(endpoint.last_triggered_at).toLocaleString("uz-UZ")}</span>
            ) : null}
          </div>
          {endpoint.last_error ? (
            <p className="mt-1 flex items-center gap-1 text-[11px] text-[var(--danger)]">
              <AlertTriangle className="h-3 w-3" /> {endpoint.last_error}
            </p>
          ) : null}
          {endpoint.events?.length ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {endpoint.events.map((e) => (
                <Badge key={e} variant="default">
                  {e}
                </Badge>
              ))}
            </div>
          ) : null}
          {expanded ? <DeliveriesPanel endpointId={endpoint.id} /> : null}
        </div>
        <Can permission="integrations.write">
          <div className="flex shrink-0 items-center gap-1">
            <Button variant="ghost" size="sm" onClick={onToggleDetails}>
              {expanded ? "Yashirish" : "Tarix"}
            </Button>
            {isOutbound ? (
              <Button variant="ghost" size="sm" onClick={onTest}>
                <Send /> Test
              </Button>
            ) : null}
            <Button variant="ghost" size="sm" onClick={onRotate}>
              <RefreshCw /> Rotate
            </Button>
            <Button variant="ghost" size="sm" onClick={onActivate}>
              {endpoint.is_active ? "Pauza" : "Faol"}
            </Button>
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
      </CardContent>
    </Card>
  );
}

function DeliveriesPanel({ endpointId }: { endpointId: string }) {
  const { data = [], isLoading } = useQuery({
    queryKey: ["webhooks", "deliveries", endpointId],
    queryFn: () => marketplaceApi.deliveries(endpointId, 25),
  });
  if (isLoading) {
    return (
      <div className="mt-3 h-16 animate-pulse rounded-md border border-[var(--border)] bg-[var(--surface)]" />
    );
  }
  if (data.length === 0) {
    return <p className="mt-3 text-[11px] text-[var(--fg-subtle)]">Tarix bo&apos;sh.</p>;
  }
  return (
    <div className="mt-3 space-y-1.5">
      {data.map((d) => (
        <div
          key={d.id}
          className={cn(
            "flex items-center justify-between gap-3 rounded-md border px-3 py-1.5 text-[11px]",
            d.succeeded
              ? "border-[var(--success-soft)] bg-[var(--success-soft)]/30 text-[var(--success)]"
              : "border-[var(--danger-soft)] bg-[var(--danger-soft)]/30 text-[var(--danger)]",
          )}
        >
          <div className="flex items-center gap-2">
            <span className="font-mono">{d.event ?? "—"}</span>
            <span>·</span>
            <span>HTTP {d.status_code ?? "—"}</span>
          </div>
          <span className="text-[var(--fg-subtle)]">
            {new Date(d.created_at).toLocaleString("uz-UZ")}
          </span>
        </div>
      ))}
    </div>
  );
}

function CreateForm({
  onCancel,
  onSubmit,
  loading,
}: {
  onCancel: () => void;
  onSubmit: (p: {
    name: string;
    direction: "in" | "out";
    url?: string | null;
    events?: string[] | null;
  }) => void;
  loading: boolean;
}) {
  const [name, setName] = useState("");
  const [direction, setDirection] = useState<"in" | "out">("out");
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>([]);

  const toggleEvent = (e: string) =>
    setEvents((arr) => (arr.includes(e) ? arr.filter((x) => x !== e) : [...arr, e]));

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi webhook</CardTitle>
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
            <FormField label="Nomi" required>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Slack notifications"
                autoFocus
              />
            </FormField>
            <FormField label="Yo'nalish">
              <div className="flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-0.5">
                {(["out", "in"] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDirection(d)}
                    className={cn(
                      "flex flex-1 items-center justify-center gap-1.5 rounded px-3 py-1 text-[12px] font-medium transition-colors",
                      direction === d
                        ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                        : "text-[var(--fg-muted)]",
                    )}
                  >
                    {d === "out" ? (
                      <>
                        <ArrowUpToLine className="h-3.5 w-3.5" /> Outbound
                      </>
                    ) : (
                      <>
                        <ArrowDownToLine className="h-3.5 w-3.5" /> Inbound
                      </>
                    )}
                  </button>
                ))}
              </div>
            </FormField>
          </div>

          {direction === "out" ? (
            <>
              <FormField label="URL" required>
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://hooks.slack.com/..."
                />
              </FormField>
              <FormField label="Voqealar" hint="Bo'sh qoldirsangiz hammasiga obuna bo'ladi">
                <div className="flex flex-wrap gap-1.5">
                  {SUPPORTED_EVENTS.map((e) => (
                    <button
                      key={e}
                      type="button"
                      onClick={() => toggleEvent(e)}
                      className={cn(
                        "rounded-md border px-2.5 py-1 text-[11px] transition-colors",
                        events.includes(e)
                          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
                      )}
                    >
                      {e}
                    </button>
                  ))}
                </div>
              </FormField>
            </>
          ) : (
            <div className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-[12px] text-[var(--fg-muted)]">
              Inbound webhook yaratilgach <code>POST</code> endpoint URL&apos;i va HMAC secret
              beriladi. Tashqi tizim shu URL&apos;ga <code>X-Nexus-Signature</code> headeri
              bilan POST qilishi kerak.
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                name.trim() &&
                onSubmit({
                  name: name.trim(),
                  direction,
                  url: direction === "out" ? url.trim() : null,
                  events: events.length ? events : null,
                })
              }
              loading={loading}
              disabled={!name.trim() || (direction === "out" && !url.trim())}
            >
              Yaratish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

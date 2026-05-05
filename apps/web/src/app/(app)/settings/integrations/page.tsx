"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Bot, Check, ExternalLink, Eye, EyeOff, Mail, Plug, Sparkles, X } from "lucide-react";
import { useEffect, useState, type ComponentType } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { integrationsApi } from "@/lib/smm-api";
import type { IntegrationCategory, IntegrationProvider } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<IntegrationCategory, string> = {
  ai: "Sun'iy intellekt",
  social: "Ijtimoiy tarmoqlar",
  auth: "Autentifikatsiya",
  messaging: "SMS va Email",
};

const CATEGORY_ICONS: Record<IntegrationCategory, ComponentType<{ className?: string }>> = {
  ai: Sparkles,
  social: Bot,
  auth: Plug,
  messaging: Mail,
};

const FIELD_LABELS: Record<string, { label: string; type?: string; placeholder?: string }> = {
  api_key: { label: "API Key", type: "password", placeholder: "sk-…" },
  bot_token: { label: "Bot Token", type: "password", placeholder: "1234:ABC…" },
  bot_username: { label: "Bot Username", placeholder: "my_company_bot" },
  app_id: { label: "App ID", placeholder: "1234567890" },
  app_secret: { label: "App Secret", type: "password" },
  page_access_token: { label: "Page Access Token", type: "password" },
  page_name: { label: "Page Name", placeholder: "Akme Beauty" },
  oauth_refresh_token: { label: "OAuth Refresh Token", type: "password" },
  channel_name: { label: "Channel Name" },
  client_id: { label: "Client ID" },
  client_secret: { label: "Client Secret", type: "password" },
  email: { label: "Email", type: "email" },
  password: { label: "Parol", type: "password" },
  sender: { label: "Sender", placeholder: "4546" },
  from_email: { label: "From Email", type: "email" },
};

export default function IntegrationsPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [editing, setEditing] = useState<IntegrationProvider | null>(null);

  const { data: integrations = [], isLoading } = useQuery({
    queryKey: ["integrations"],
    queryFn: integrationsApi.list,
  });

  const connect = useMutation({
    mutationFn: ({
      provider,
      payload,
    }: {
      provider: string;
      payload: { label?: string; credentials: Record<string, string> };
    }) => integrationsApi.connect(provider, payload),
    onSuccess: () => {
      toast.success("Ulanish saqlandi");
      qc.invalidateQueries({ queryKey: ["integrations"] });
      setEditing(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const disconnect = useMutation({
    mutationFn: (provider: string) => integrationsApi.disconnect(provider),
    onSuccess: () => {
      toast.success("Ulanish o'chirildi");
      qc.invalidateQueries({ queryKey: ["integrations"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const startMetaOAuth = useMutation({
    mutationFn: () => {
      const redirectUri = `${window.location.origin}/settings/integrations/meta/callback`;
      return integrationsApi.startMetaOAuth(redirectUri);
    },
    onSuccess: (res) => {
      window.location.href = res.authorize_url;
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  useEffect(() => {
    const oauth = searchParams.get("oauth");
    const message = searchParams.get("message");
    if (!oauth) return;
    if (oauth === "meta-success") toast.success("Meta OAuth yakunlandi");
    if (oauth === "meta-error") toast.error(message || "Meta OAuth tugamadi");
    router.replace(pathname);
  }, [pathname, router, searchParams]);

  const grouped = integrations.reduce<Record<string, IntegrationProvider[]>>((acc, i) => {
    (acc[i.category] = acc[i.category] ?? []).push(i);
    return acc;
  }, {});

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-[24px] font-semibold tracking-tight text-[var(--fg)] md:text-[28px]">
          Integratsiyalar
        </h1>
        <p className="mt-1 max-w-2xl text-[13px] text-[var(--fg-muted)]">
          Tashqi xizmatlar uchun API kalitlarni shu yerda ulang. Maxfiy ma&apos;lumotlar
          shifrlangan holda saqlanadi (Fernet/AES) va faqat sizning tenant&apos;ingiz
          ko&apos;ra oladi.
        </p>
      </div>

      {editing ? (
        <ConnectModal
          provider={editing}
          onSubmit={(payload) => connect.mutate({ provider: editing.provider, payload })}
          onCancel={() => setEditing(null)}
          loading={connect.isPending}
        />
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : (
        <>
          {(Object.keys(grouped) as IntegrationCategory[]).map((cat) => {
            const Icon = CATEGORY_ICONS[cat];
            const items = grouped[cat];
            return (
              <section key={cat} className="space-y-3">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-[var(--fg-muted)]" />
                  <h2 className="text-[13px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
                    {CATEGORY_LABELS[cat]}
                  </h2>
                  <span className="text-[11px] text-[var(--fg-subtle)]">
                    {items.filter((i) => i.connected).length}/{items.length} ulangan
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map((p) => (
                    <ProviderCard
                      key={p.provider}
                      provider={p}
                      onConnect={() => setEditing(p)}
                      onDisconnect={() => disconnect.mutate(p.provider)}
                      onAuthorizeMeta={
                        p.provider === "meta_app" ? () => startMetaOAuth.mutate() : undefined
                      }
                      oauthLoading={startMetaOAuth.isPending}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </>
      )}
    </motion.div>
  );
}

function ProviderCard({
  provider,
  onConnect,
  onDisconnect,
  onAuthorizeMeta,
  oauthLoading,
}: {
  provider: IntegrationProvider;
  onConnect: () => void;
  onDisconnect: () => void;
  onAuthorizeMeta?: () => void;
  oauthLoading?: boolean;
}) {
  return (
    <Card className="group flex flex-col gap-3 p-4 transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-[14px] font-semibold text-[var(--fg)]">
              {provider.label}
            </p>
            {provider.connected ? (
              <Badge variant="success">
                <Check className="h-2.5 w-2.5" /> Ulangan
              </Badge>
            ) : null}
          </div>
          <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-[var(--fg-muted)]">
            {provider.description}
          </p>
        </div>
        {provider.docs_url ? (
          <a
            href={provider.docs_url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Hujjatlar"
            className="shrink-0 rounded-md p-1 text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>

      {provider.connected ? (
        <div className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-2.5">
          <p className="text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
            {provider.label_custom ?? "Konfiguratsiya"}
          </p>
          <div className="mt-1 space-y-0.5">
            {provider.display_value ? (
              <p className="truncate text-[12px] font-medium text-[var(--fg)]">
                {provider.display_value}
              </p>
            ) : null}
            {Object.entries(provider.masked_values)
              .slice(0, 1)
              .map(([k, v]) => (
                <p key={k} className="font-mono text-[11px] text-[var(--fg-muted)]">
                  {FIELD_LABELS[k]?.label ?? k}: {v}
                </p>
              ))}
            {provider.status_hint ? (
              <p className="text-[11px] text-[var(--fg-subtle)]">{provider.status_hint}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-auto flex items-center gap-2">
        <Can permission="integrations.write">
          <Button
            variant={provider.connected ? "secondary" : "primary"}
            size="sm"
            onClick={onConnect}
            className="flex-1"
          >
            {provider.connected ? "O'zgartirish" : "Ulash"}
          </Button>
          {provider.provider === "meta_app" && provider.connected ? (
            <Button
              variant={provider.oauth_connected ? "secondary" : "primary"}
              size="sm"
              onClick={onAuthorizeMeta}
              loading={oauthLoading}
              className="flex-1"
            >
              {provider.oauth_connected ? "Meta OAuth yangilash" : "Meta OAuth"}
            </Button>
          ) : null}
          {provider.connected ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDisconnect}
              aria-label="O'chirish"
              className="text-[var(--danger)]"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          ) : null}
        </Can>
      </div>
    </Card>
  );
}

function ConnectModal({
  provider,
  onSubmit,
  onCancel,
  loading,
}: {
  provider: IntegrationProvider;
  onSubmit: (payload: { label?: string; credentials: Record<string, string> }) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [label, setLabel] = useState(provider.label_custom ?? "");
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [show, setShow] = useState<Record<string, boolean>>({});

  const allFields = [
    ...provider.secret_fields,
    ...(provider.display_field ? [provider.display_field] : []),
  ];
  const dedup = Array.from(new Set(allFields));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.18 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.96, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.18 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-xl)]"
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold tracking-tight text-[var(--fg)]">
              {provider.label}
            </h3>
            <p className="mt-0.5 truncate text-[12px] text-[var(--fg-muted)]">
              {provider.description}
            </p>
          </div>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Yopish"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 px-5 py-4">
          {provider.docs_url ? (
            <a
              href={provider.docs_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--info-soft)] px-2.5 py-1.5 text-[12px] font-medium text-[var(--info)] hover:underline"
            >
              <ExternalLink className="h-3 w-3" /> Tokenni qaerdan olish kerak
            </a>
          ) : null}

          <FormField label="Yorliq" hint="Ixtiyoriy — ichki belgilash uchun">
            <Input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Production, Test, va h.k."
            />
          </FormField>

          {dedup.map((field) => {
            const meta = FIELD_LABELS[field] ?? { label: field };
            const isSecret = meta.type === "password";
            const isShown = show[field];
            return (
              <FormField
                key={field}
                label={meta.label}
                required={provider.secret_fields.includes(field)}
              >
                <div className="relative">
                  <Input
                    type={isSecret && !isShown ? "password" : "text"}
                    value={credentials[field] ?? ""}
                    onChange={(e) =>
                      setCredentials((c) => ({ ...c, [field]: e.target.value }))
                    }
                    placeholder={meta.placeholder ?? ""}
                    className={cn(isSecret && "pr-10 font-mono")}
                  />
                  {isSecret ? (
                    <button
                      type="button"
                      onClick={() => setShow((s) => ({ ...s, [field]: !s[field] }))}
                      aria-label={isShown ? "Yashirish" : "Ko'rsatish"}
                      className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1 text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
                    >
                      {isShown ? (
                        <EyeOff className="h-3.5 w-3.5" />
                      ) : (
                        <Eye className="h-3.5 w-3.5" />
                      )}
                    </button>
                  ) : null}
                </div>
              </FormField>
            );
          })}

          {provider.connected ? (
            <p className="text-[11px] text-[var(--fg-subtle)]">
              ⓘ Ushbu xizmat allaqachon ulangan. Yangi qiymatlar eskilarini almashtiradi.
            </p>
          ) : null}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] px-5 py-3">
          <Button variant="ghost" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button
            onClick={() => onSubmit({ label: label || undefined, credentials })}
            loading={loading}
            disabled={provider.secret_fields.some((f) => !credentials[f])}
          >
            {provider.connected ? "Yangilash" : "Ulash"}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

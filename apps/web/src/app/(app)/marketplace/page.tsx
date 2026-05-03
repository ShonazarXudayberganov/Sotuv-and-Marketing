"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Bot,
  Camera,
  Database,
  ExternalLink,
  Megaphone,
  MessageSquare,
  Plug,
  RefreshCw,
  Send,
  Shield,
  Sparkles,
  Store,
  Webhook,
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
import { extractApiError } from "@/lib/api-client";
import { marketplaceApi } from "@/lib/marketplace-api";
import type { MarketplaceProvider } from "@/lib/types";
import { cn } from "@/lib/utils";

const SYNCABLE = new Set([
  "amocrm",
  "bitrix24",
  "onec",
  "google_sheets",
  "zapier",
]);

const CATEGORY_LABELS: Record<string, string> = {
  ai: "AI",
  social: "Ijtimoiy tarmoqlar",
  auth: "Autentifikatsiya",
  messaging: "Xabarlar",
  crm: "CRM",
  erp: "ERP / Buxgalteriya",
  data: "Ma'lumot va integratsiya",
};

const CATEGORY_ICONS: Record<string, typeof Plug> = {
  ai: Bot,
  social: Camera,
  auth: Shield,
  messaging: MessageSquare,
  crm: Database,
  erp: Database,
  data: Plug,
};

export default function MarketplacePage() {
  const [filter, setFilter] = useState<string>("all");
  const { data: providers = [], isLoading } = useQuery({
    queryKey: ["marketplace", "catalog"],
    queryFn: marketplaceApi.catalog,
  });

  const categories = useMemo(() => {
    const set = new Set(providers.map((p) => p.category));
    return ["all", ...Array.from(set).sort()];
  }, [providers]);

  const filtered = useMemo(
    () =>
      filter === "all"
        ? providers
        : providers.filter((p) => p.category === filter),
    [providers, filter],
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
          { label: "Marketplace" },
        ]}
        title="Integratsiya marketplace"
        description="1C, AmoCRM, Bitrix24, Google Sheets, Zapier va Webhooks API — barchasini bir oynada"
        actions={
          <div className="flex items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/settings/integrations">
                <Plug /> Ulangan integratsiyalar
              </Link>
            </Button>
            <Button asChild>
              <Link href="/settings/webhooks">
                <Webhook /> Webhooks
              </Link>
            </Button>
          </div>
        }
      />

      <div className="flex flex-wrap gap-1.5">
        {categories.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilter(c)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
              filter === c
                ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
            )}
          >
            {c === "all" ? "Hammasi" : CATEGORY_LABELS[c] ?? c}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-44 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={Store}
              title="Provayder topilmadi"
              description="Filterni o'zgartiring yoki barcha kategoriyalarni ko'rib chiqing"
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <ProviderCard key={p.provider} provider={p} />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function ProviderCard({ provider }: { provider: MarketplaceProvider }) {
  const Icon = CATEGORY_ICONS[provider.category] ?? Plug;
  const canSync = SYNCABLE.has(provider.provider);

  const sync = useMutation({
    mutationFn: () => marketplaceApi.sync(provider.provider),
    onSuccess: (res) => {
      const summary =
        res.errors.length > 0
          ? res.errors.join("; ")
          : `Pulled ${res.pulled} · Pushed ${res.pushed}${res.mocked ? " (MOCK)" : ""}`;
      if (res.errors.length > 0) {
        toast.error(summary);
      } else {
        toast.success(summary);
      }
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-[15px]">{provider.label}</CardTitle>
              <p className="text-[11px] text-[var(--fg-subtle)]">
                {CATEGORY_LABELS[provider.category] ?? provider.category}
              </p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-3">
        <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">
          {provider.description}
        </p>
        {provider.secret_fields.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {provider.secret_fields.map((f) => (
              <Badge key={f} variant="outline">
                {f}
              </Badge>
            ))}
          </div>
        ) : null}
        <div className="mt-auto flex items-center justify-between gap-2 pt-3">
          {provider.docs_url ? (
            <a
              href={provider.docs_url}
              target="_blank"
              rel="noopener"
              className="flex items-center gap-1 text-[12px] font-medium text-[var(--primary)] hover:underline"
            >
              Hujjatlar <ExternalLink className="h-3 w-3" />
            </a>
          ) : (
            <span />
          )}
          <div className="flex items-center gap-1.5">
            {canSync ? (
              <Can permission="integrations.write">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => sync.mutate()}
                  loading={sync.isPending}
                >
                  <RefreshCw /> Sync
                </Button>
              </Can>
            ) : null}
            <Button asChild variant="secondary" size="sm">
              <Link href="/settings/integrations">
                Ulash <ArrowUpRight />
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Suppress unused — kept for future card variants
void Sparkles;
void Megaphone;
void Send;

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  BarChart3,
  Camera,
  CheckCircle2,
  Eye,
  Hash,
  Link2,
  Megaphone,
  Play,
  Plus,
  Send,
  ThumbsUp,
  Trash2,
  X,
} from "lucide-react";

const Facebook = Megaphone;
const Instagram = Camera;
const Youtube = Play;
import Link from "next/link";
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
import { brandsApi, integrationsApi } from "@/lib/smm-api";
import { socialApi } from "@/lib/social-api";
import type { Brand, MetaPageOption, SocialAccount, YouTubeStats } from "@/lib/types";
import { cn } from "@/lib/utils";

type LinkMode = null | "telegram" | "meta" | "youtube";

export default function SocialAccountsPage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [linking, setLinking] = useState<LinkMode>(null);
  const [testing, setTesting] = useState<SocialAccount | null>(null);
  const [statsAccount, setStatsAccount] = useState<SocialAccount | null>(null);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const { data: integrations = [] } = useQuery({
    queryKey: ["integrations"],
    queryFn: integrationsApi.list,
  });
  const telegramIntegration = integrations.find((i) => i.provider === "telegram_bot");
  const metaIntegration = integrations.find((i) => i.provider === "meta_app");
  const youtubeIntegration = integrations.find((i) => i.provider === "youtube");
  const telegramConnected = telegramIntegration?.connected ?? false;
  const metaConnected = metaIntegration?.connected ?? false;
  const metaOAuthConnected = metaIntegration?.oauth_connected ?? false;
  const metaReady = metaConnected && metaOAuthConnected;
  const youtubeConnected = youtubeIntegration?.connected ?? false;

  const { data: botInfo } = useQuery({
    queryKey: ["telegram", "bot-info"],
    queryFn: socialApi.telegramBotInfo,
    enabled: telegramConnected,
    retry: false,
  });

  const activeBrandId = brandFilter === "all" ? null : brandFilter;
  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["social", "accounts", activeBrandId],
    queryFn: () => socialApi.listAccounts(activeBrandId),
  });

  const linkTelegram = useMutation({
    mutationFn: (args: { brandId: string; chat: string }) =>
      socialApi.telegramLink(args.brandId, args.chat),
    onSuccess: () => {
      toast.success("Telegram kanal ulandi");
      qc.invalidateQueries({ queryKey: ["social"] });
      setLinking(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const linkMeta = useMutation({
    mutationFn: (args: {
      brandId: string;
      pageId: string;
      target: "facebook" | "instagram";
    }) => socialApi.metaLink(args.brandId, args.pageId, args.target),
    onSuccess: () => {
      toast.success("Meta akkaunt ulandi");
      qc.invalidateQueries({ queryKey: ["social"] });
      setLinking(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const linkYoutube = useMutation({
    mutationFn: (args: { brandId: string; handle?: string; channelId?: string }) =>
      socialApi.youtubeLink(args.brandId, args.handle, args.channelId),
    onSuccess: () => {
      toast.success("YouTube kanal ulandi");
      qc.invalidateQueries({ queryKey: ["social"] });
      setLinking(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => socialApi.removeAccount(id),
    onSuccess: () => {
      toast.success("Akkaunt o'chirildi");
      qc.invalidateQueries({ queryKey: ["social"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const sendTest = useMutation({
    mutationFn: async (args: { account: SocialAccount; text: string; imageUrl?: string }) => {
      if (args.account.provider === "telegram") {
        const r = await socialApi.telegramTest(args.account.id, args.text);
        return { id: `message_id=${r.message_id}`, mocked: r.mocked };
      }
      const r = await socialApi.metaTest(args.account.id, args.text, args.imageUrl);
      return { id: r.post_id, mocked: r.mocked };
    },
    onSuccess: (res) => {
      toast.success(res.mocked ? `Mock test: ${res.id}` : `Yuborildi: ${res.id}`);
      qc.invalidateQueries({ queryKey: ["social"] });
      setTesting(null);
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
          { label: "SMM", href: "/smm" },
          { label: "Ijtimoiy akkauntlar" },
        ]}
        title="Ijtimoiy akkauntlar"
        description="Brendlarga Telegram kanallari, Facebook sahifalari va Instagram akkauntlarini ulang"
        actions={
          <Can permission="smm.write">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                size="default"
                onClick={() => setLinking("telegram")}
                disabled={!telegramConnected || brands.length === 0}
              >
                <Send /> Telegram
              </Button>
              <Button
                size="default"
                onClick={() => setLinking("meta")}
                disabled={!metaReady || brands.length === 0}
              >
                <Plus /> Facebook / Instagram
              </Button>
              <Button
                variant="secondary"
                size="default"
                onClick={() => setLinking("youtube")}
                disabled={!youtubeConnected || brands.length === 0}
              >
                <Youtube /> YouTube
              </Button>
            </div>
          </Can>
        }
      />

      {/* Provider status row */}
      <div className="grid gap-4 md:grid-cols-3">
        <ProviderStatus
          provider="telegram"
          connected={telegramConnected}
          title="Telegram bot"
          subtitle={
            botInfo
              ? `${botInfo.first_name ?? "Bot"} (@${botInfo.username ?? "—"})`
              : "Token o'rnatilmagan"
          }
          mocked={botInfo?.mocked}
        />
        <ProviderStatus
          provider="meta"
          connected={metaConnected}
          title="Meta (Facebook + Instagram)"
          subtitle={
            metaConnected
              ? (metaIntegration?.status_hint ?? "Meta OAuth ulangan")
              : "App ID va Secret o'rnatilmagan"
          }
          actionHref={
            metaConnected && !metaOAuthConnected ? "/settings/integrations" : undefined
          }
          actionLabel={metaConnected && !metaOAuthConnected ? "Meta OAuth" : undefined}
        />
        <ProviderStatus
          provider="youtube"
          connected={youtubeConnected}
          title="YouTube Data API"
          subtitle={youtubeConnected ? "API key ulangan" : "API key o'rnatilmagan"}
        />
      </div>

      {/* Forms */}
      {linking === "telegram" ? (
        <TelegramLinkForm
          brands={brands}
          defaultBrandId={brands.find((b) => b.is_default)?.id ?? brands[0]?.id ?? ""}
          onCancel={() => setLinking(null)}
          onSubmit={(args) => linkTelegram.mutate(args)}
          loading={linkTelegram.isPending}
        />
      ) : null}

      {linking === "meta" ? (
        <MetaLinkForm
          brands={brands}
          defaultBrandId={brands.find((b) => b.is_default)?.id ?? brands[0]?.id ?? ""}
          oauthConnected={metaOAuthConnected}
          onCancel={() => setLinking(null)}
          onSubmit={(args) => linkMeta.mutate(args)}
          loading={linkMeta.isPending}
        />
      ) : null}

      {linking === "youtube" ? (
        <YouTubeLinkForm
          brands={brands}
          defaultBrandId={brands.find((b) => b.is_default)?.id ?? brands[0]?.id ?? ""}
          onCancel={() => setLinking(null)}
          onSubmit={(args) => linkYoutube.mutate(args)}
          loading={linkYoutube.isPending}
        />
      ) : null}

      {statsAccount ? (
        <YouTubeStatsCard account={statsAccount} onClose={() => setStatsAccount(null)} />
      ) : null}

      {testing ? (
        <TestSendForm
          account={testing}
          onCancel={() => setTesting(null)}
          onSubmit={(text, imageUrl) => sendTest.mutate({ account: testing, text, imageUrl })}
          loading={sendTest.isPending}
        />
      ) : null}

      {/* Brand filter */}
      {brands.length > 0 ? (
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setBrandFilter("all")}
            className={cn(
              "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
              brandFilter === "all"
                ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
            )}
          >
            Hammasi
          </button>
          {brands.map((b) => (
            <button
              key={b.id}
              type="button"
              onClick={() => setBrandFilter(b.id)}
              className={cn(
                "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
                brandFilter === b.id
                  ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                  : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
              )}
            >
              {b.name}
            </button>
          ))}
        </div>
      ) : null}

      {/* Accounts list */}
      <Card>
        <CardHeader>
          <CardTitle>Ulangan akkauntlar</CardTitle>
          <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
            Telegram, Facebook va Instagram — har brend uchun
          </p>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[0, 1].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                />
              ))}
            </div>
          ) : accounts.length === 0 ? (
            <EmptyState
              icon={Link2}
              title="Hech qanday akkaunt ulanmagan"
              description={
                telegramConnected || metaReady
                  ? "Yuqoridagi tugmalar orqali Telegram, Facebook yoki Instagram qo'shing."
                  : "Avval sozlamalardan Telegram bot tokeni yoki Meta OAuth'ni tayyorlang."
              }
              action={
                !telegramConnected && !metaReady ? (
                  <Button asChild variant="secondary">
                    <Link href="/settings/integrations">Sozlamalar</Link>
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-2">
              {accounts.map((acc) => (
                <AccountRow
                  key={acc.id}
                  account={acc}
                  brand={brands.find((b) => b.id === acc.brand_id)}
                  onTest={() => setTesting(acc)}
                  onStats={acc.provider === "youtube" ? () => setStatsAccount(acc) : undefined}
                  onDelete={() => remove.mutate(acc.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function ProviderStatus({
  provider,
  connected,
  title,
  subtitle,
  mocked,
  actionHref,
  actionLabel,
}: {
  provider: "telegram" | "meta" | "youtube";
  connected: boolean;
  title: string;
  subtitle: string;
  mocked?: boolean;
  actionHref?: string;
  actionLabel?: string;
}) {
  const Icon = provider === "telegram" ? Send : provider === "youtube" ? Youtube : Facebook;
  if (!connected) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-[var(--warning)] bg-[var(--warning-soft)] p-4">
        <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--warning)]" />
        <div className="flex-1 text-[13px] text-[var(--fg)]">
          <p className="font-medium">{title} — ulanmagan</p>
          <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">{subtitle}</p>
        </div>
        <Button asChild variant="secondary" size="sm">
          <Link href="/settings/integrations">Ulash</Link>
        </Button>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-4 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[14px] font-semibold text-[var(--fg)]">{title}</p>
          {mocked ? <Badge variant="outline">MOCK</Badge> : null}
        </div>
        <p className="mt-0.5 truncate text-[11px] text-[var(--fg-subtle)]">{subtitle}</p>
      </div>
      {actionHref && actionLabel ? (
        <Button asChild variant="secondary" size="sm">
          <Link href={actionHref}>{actionLabel}</Link>
        </Button>
      ) : (
        <Badge variant="success">
          <CheckCircle2 className="h-2.5 w-2.5" /> Faol
        </Badge>
      )}
    </div>
  );
}

function AccountRow({
  account,
  brand,
  onTest,
  onStats,
  onDelete,
}: {
  account: SocialAccount;
  brand?: Brand;
  onTest: () => void;
  onStats?: () => void;
  onDelete: () => void;
}) {
  const Icon =
    account.provider === "telegram"
      ? Send
      : account.provider === "instagram"
        ? Instagram
        : account.provider === "youtube"
          ? Youtube
          : Facebook;
  const isYouTube = account.provider === "youtube";
  return (
    <div className="group flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-colors hover:border-[var(--primary)]">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">
            {account.external_name ?? account.external_handle ?? account.external_id}
          </p>
          <Badge variant="outline" className="capitalize">
            {account.provider}
          </Badge>
          {account.external_handle ? (
            <Badge variant="default">
              <Hash className="h-2.5 w-2.5" />
              {account.external_handle}
            </Badge>
          ) : null}
        </div>
        <p className="truncate text-[11px] text-[var(--fg-subtle)]">
          {brand?.name ?? "—"} · ID: {account.external_id}
          {account.last_published_at
            ? ` · Oxirgi: ${new Date(account.last_published_at).toLocaleString("uz-UZ")}`
            : ""}
        </p>
        {account.last_error ? (
          <p className="mt-0.5 truncate text-[11px] text-[var(--danger)]">
            {account.last_error}
          </p>
        ) : null}
      </div>
      <Can permission="smm.write">
        <div className="flex items-center gap-1">
          {isYouTube && onStats ? (
            <Button variant="ghost" size="sm" onClick={onStats}>
              <BarChart3 /> Stats
            </Button>
          ) : (
            <Button variant="ghost" size="sm" onClick={onTest}>
              <Send /> Test
            </Button>
          )}
          <button
            type="button"
            onClick={onDelete}
            aria-label="Uzish"
            className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </Can>
    </div>
  );
}

function TelegramLinkForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string;
  onCancel: () => void;
  onSubmit: (args: { brandId: string; chat: string }) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId);
  const [chat, setChat] = useState("");
  return (
    <FormCard title="Telegram kanal ulash" onCancel={onCancel}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Brend" required>
          <BrandSelect value={brandId} onChange={setBrandId} brands={brands} />
        </FormField>
        <FormField
          label="Kanal/Guruh"
          required
          hint="Username (@akme_news) yoki numeric chat ID"
        >
          <Input
            value={chat}
            onChange={(e) => setChat(e.target.value)}
            placeholder="@akme_news"
          />
        </FormField>
      </div>
      <FormActions
        onCancel={onCancel}
        onSubmit={() => brandId && chat.trim() && onSubmit({ brandId, chat: chat.trim() })}
        loading={loading}
        disabled={!brandId || !chat.trim()}
        cta="Ulash"
      />
    </FormCard>
  );
}

function MetaLinkForm({
  brands,
  defaultBrandId,
  oauthConnected,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string;
  oauthConnected: boolean;
  onCancel: () => void;
  onSubmit: (args: {
    brandId: string;
    pageId: string;
    target: "facebook" | "instagram";
  }) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId);
  const [pageId, setPageId] = useState("");
  const [target, setTarget] = useState<"facebook" | "instagram">("facebook");

  const { data: pages = [], isLoading } = useQuery({
    queryKey: ["meta", "pages"],
    queryFn: socialApi.metaListPages,
    enabled: oauthConnected,
  });

  const selected = pages.find((p) => p.id === pageId) ?? null;
  const igDisabled = selected !== null && !selected.has_instagram;

  return (
    <FormCard title="Facebook / Instagram ulash" onCancel={onCancel}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Brend" required>
          <BrandSelect value={brandId} onChange={setBrandId} brands={brands} />
        </FormField>
        <FormField label="Platforma" required>
          <div className="flex gap-2">
            <PlatformPill
              active={target === "facebook"}
              onClick={() => setTarget("facebook")}
              icon={Facebook}
              label="Facebook"
            />
            <PlatformPill
              active={target === "instagram"}
              onClick={() => setTarget("instagram")}
              icon={Instagram}
              label="Instagram"
              disabled={igDisabled}
            />
          </div>
        </FormField>
      </div>

      <FormField
        label="Facebook sahifa"
        required
        hint={
          isLoading
            ? "Sahifalar yuklanmoqda…"
            : "Botingiz boshqaradigan sahifalar ro'yxati. Instagram uchun sahifaga IG Business akkaunt biriktirilgan bo'lishi shart."
        }
      >
        {!oauthConnected ? (
          <p className="rounded-md border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-4 text-center text-[12px] text-[var(--fg-muted)]">
            Avval [Meta OAuth] ni yakunlang. So&apos;ng sahifalar shu yerda chiqadi.
          </p>
        ) : pages.length === 0 && !isLoading ? (
          <p className="rounded-md border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-4 text-center text-[12px] text-[var(--fg-muted)]">
            Sahifalar topilmadi. Meta app credentials va sahifaga ruxsatni tekshiring.
          </p>
        ) : (
          <div className="grid gap-2">
            {pages.map((p: MetaPageOption) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setPageId(p.id)}
                className={cn(
                  "flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors",
                  pageId === p.id
                    ? "border-[var(--primary)] bg-[var(--primary-soft)]"
                    : "border-[var(--border)] bg-[var(--bg-subtle)] hover:border-[var(--primary)]",
                )}
              >
                <div className="min-w-0">
                  <p className="truncate text-[13px] font-medium text-[var(--fg)]">{p.name}</p>
                  <p className="truncate text-[11px] text-[var(--fg-subtle)]">
                    {p.category ?? "—"} · ID: {p.id}
                  </p>
                </div>
                {p.has_instagram ? (
                  <Badge variant="primary">
                    <Instagram className="h-2.5 w-2.5" /> @{p.instagram_username ?? "ig"}
                  </Badge>
                ) : (
                  <Badge variant="outline">FB only</Badge>
                )}
              </button>
            ))}
          </div>
        )}
      </FormField>

      <FormActions
        onCancel={onCancel}
        onSubmit={() => brandId && pageId && onSubmit({ brandId, pageId, target })}
        loading={loading}
        disabled={
          !oauthConnected || !brandId || !pageId || (target === "instagram" && igDisabled)
        }
        cta="Ulash"
      />
    </FormCard>
  );
}

function YouTubeLinkForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string;
  onCancel: () => void;
  onSubmit: (args: { brandId: string; handle?: string; channelId?: string }) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId);
  const [input, setInput] = useState("");

  const trimmed = input.trim();
  const looksLikeChannelId = trimmed.startsWith("UC") && trimmed.length >= 20;

  return (
    <FormCard title="YouTube kanal ulash" onCancel={onCancel}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Brend" required>
          <BrandSelect value={brandId} onChange={setBrandId} brands={brands} />
        </FormField>
        <FormField
          label="Handle yoki Channel ID"
          required
          hint="@nexus_uz yoki UCxxxx... formatida"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="@nexus_uz"
          />
        </FormField>
      </div>
      <div className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-[12px] text-[var(--fg-muted)]">
        Sprint 1.5 da YouTube faqat o&apos;qish (statistika va video ro&apos;yxati) uchun.
        Video upload keyingi bosqichda (OAuth refresh token + resumable upload).
      </div>
      <FormActions
        onCancel={onCancel}
        onSubmit={() => {
          if (!brandId || !trimmed) return;
          onSubmit(
            looksLikeChannelId
              ? { brandId, channelId: trimmed }
              : { brandId, handle: trimmed.startsWith("@") ? trimmed : `@${trimmed}` },
          );
        }}
        loading={loading}
        disabled={!brandId || !trimmed}
        cta="Ulash"
      />
    </FormCard>
  );
}

function YouTubeStatsCard({
  account,
  onClose,
}: {
  account: SocialAccount;
  onClose: () => void;
}) {
  const { data: stats, isLoading } = useQuery<YouTubeStats>({
    queryKey: ["youtube", "stats", account.id],
    queryFn: () => socialApi.youtubeStats(account.id, 5),
  });

  return (
    <FormCard
      title={`YouTube statistikasi — ${account.external_name ?? account.external_id}`}
      onCancel={onClose}
    >
      {isLoading || !stats ? (
        <div className="grid gap-3 sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatTile label="Obunachilar" value={stats.subscribers.toLocaleString("uz-UZ")} />
            <StatTile label="Jami ko'rishlar" value={stats.views.toLocaleString("uz-UZ")} />
            <StatTile label="Videolar" value={stats.videos.toLocaleString("uz-UZ")} />
          </div>
          <div>
            <p className="mb-2 text-[12px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
              So&apos;nggi videolar
            </p>
            {stats.recent.length === 0 ? (
              <p className="text-[12px] text-[var(--fg-muted)]">Videolar topilmadi.</p>
            ) : (
              <div className="space-y-2">
                {stats.recent.map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
                      <Play className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-medium text-[var(--fg)]">
                        {v.title}
                      </p>
                      <p className="truncate text-[11px] text-[var(--fg-subtle)]">
                        {v.published_at
                          ? new Date(v.published_at).toLocaleDateString("uz-UZ")
                          : "—"}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-[var(--fg-muted)]">
                      <span className="flex items-center gap-1">
                        <Eye className="h-3 w-3" /> {v.view_count.toLocaleString("uz-UZ")}
                      </span>
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="h-3 w-3" /> {v.like_count.toLocaleString("uz-UZ")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {stats.mocked ? (
            <p className="text-[11px] text-[var(--fg-subtle)]">
              MOCK rejimi — haqiqiy YouTube ma&apos;lumoti emas.
            </p>
          ) : null}
        </>
      )}
    </FormCard>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow-xs)]">
      <p className="text-[11px] font-medium tracking-wider text-[var(--fg-muted)] uppercase">
        {label}
      </p>
      <p className="mt-1.5 text-[22px] font-semibold tracking-tight text-[var(--fg)]">
        {value}
      </p>
    </div>
  );
}

function PlatformPill({
  active,
  onClick,
  icon: Icon,
  label,
  disabled,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Facebook;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      className={cn(
        "flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-[13px] font-medium transition-colors",
        disabled && "cursor-not-allowed opacity-50",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
      )}
    >
      <Icon className="h-4 w-4" /> {label}
    </button>
  );
}

function TestSendForm({
  account,
  onCancel,
  onSubmit,
  loading,
}: {
  account: SocialAccount;
  onCancel: () => void;
  onSubmit: (text: string, imageUrl?: string) => void;
  loading: boolean;
}) {
  const [text, setText] = useState(
    "Test xabar — NEXUS AI orqali yuborildi.\nMuvaffaqiyatli ulanish belgisi.",
  );
  const [imageUrl, setImageUrl] = useState("https://picsum.photos/1080");
  const isInstagram = account.provider === "instagram";

  return (
    <FormCard
      title={`Test xabar — ${account.external_name ?? account.external_handle ?? "akkaunt"}`}
      onCancel={onCancel}
    >
      <FormField
        label="Matn"
        required
        hint="HTML/markdown qo'llab-quvvatlanadi (provayder cheklovlari bo'yicha)"
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="flex min-h-[120px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
        />
      </FormField>
      {isInstagram ? (
        <FormField
          label="Rasm URL"
          required
          hint="Instagram post sifatida e'lon qilish uchun ommaviy rasm URL'i kerak"
        >
          <Input
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/image.jpg"
          />
        </FormField>
      ) : null}
      <FormActions
        onCancel={onCancel}
        onSubmit={() =>
          text.trim() && onSubmit(text.trim(), isInstagram ? imageUrl.trim() : undefined)
        }
        loading={loading}
        disabled={!text.trim() || (isInstagram && !imageUrl.trim())}
        cta="Yuborish"
        cancelLabel="Bekor qilish"
      />
    </FormCard>
  );
}

function FormCard({
  title,
  onCancel,
  children,
}: {
  title: string;
  onCancel: () => void;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Yopish"
            className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
          >
            <X className="h-4 w-4" />
          </button>
        </CardHeader>
        <CardContent className="space-y-4">{children}</CardContent>
      </Card>
    </motion.div>
  );
}

function FormActions({
  onCancel,
  onSubmit,
  loading,
  disabled,
  cta,
  cancelLabel = "Bekor qilish",
}: {
  onCancel: () => void;
  onSubmit: () => void;
  loading: boolean;
  disabled: boolean;
  cta: string;
  cancelLabel?: string;
}) {
  return (
    <div className="flex items-center justify-end gap-2 pt-2">
      <Button variant="ghost" onClick={onCancel}>
        {cancelLabel}
      </Button>
      <Button onClick={onSubmit} loading={loading} disabled={disabled}>
        {cta}
      </Button>
    </div>
  );
}

function BrandSelect({
  value,
  onChange,
  brands,
}: {
  value: string;
  onChange: (v: string) => void;
  brands: Brand[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
    >
      {brands.map((b) => (
        <option key={b.id} value={b.id}>
          {b.name}
        </option>
      ))}
    </select>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Hash,
  Link2,
  Plus,
  Send,
  Trash2,
  X,
} from "lucide-react";
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
import type { Brand, SocialAccount } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function SocialAccountsPage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [linking, setLinking] = useState(false);
  const [testing, setTesting] = useState<SocialAccount | null>(null);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const { data: integrations = [] } = useQuery({
    queryKey: ["integrations"],
    queryFn: integrationsApi.list,
  });
  const telegramIntegration = integrations.find((i) => i.provider === "telegram_bot");
  const telegramConnected = telegramIntegration?.connected ?? false;

  const { data: botInfo } = useQuery({
    queryKey: ["telegram", "bot-info"],
    queryFn: socialApi.telegramBotInfo,
    enabled: telegramConnected,
    retry: false,
  });

  const activeBrandId = brandFilter === "all" ? null : brandFilter;
  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["social", "accounts", activeBrandId],
    queryFn: () => socialApi.listAccounts(activeBrandId, "telegram"),
  });

  const link = useMutation({
    mutationFn: (args: { brandId: string; chat: string }) =>
      socialApi.telegramLink(args.brandId, args.chat),
    onSuccess: () => {
      toast.success("Kanal ulandi");
      qc.invalidateQueries({ queryKey: ["social"] });
      setLinking(false);
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
    mutationFn: (args: { accountId: string; text: string }) =>
      socialApi.telegramTest(args.accountId, args.text),
    onSuccess: (res) => {
      toast.success(
        res.mocked
          ? `Mock test: message_id=${res.message_id}`
          : `Yuborildi (message_id=${res.message_id})`,
      );
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
        description="Brendlarga Telegram kanal/guruh, Instagram va Facebook akkauntlarini ulash"
        actions={
          <Can permission="smm.write">
            <Button
              size="default"
              onClick={() => setLinking(true)}
              disabled={!telegramConnected || brands.length === 0}
            >
              <Plus /> Telegram kanal
            </Button>
          </Can>
        }
      />

      {/* Bot status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="h-4 w-4 text-[var(--primary)]" /> Telegram bot
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!telegramConnected ? (
            <div className="flex items-start gap-3 rounded-lg border border-[var(--warning)] bg-[var(--warning-soft)] p-4">
              <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--warning)]" />
              <div className="flex-1 text-[13px] text-[var(--fg)]">
                <p className="font-medium">Bot tokeni o&apos;rnatilmagan</p>
                <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
                  Avval @BotFather&apos;dan token olib, sozlamalarda Telegram bot integratsiyasini
                  ulang.
                </p>
              </div>
              <Button asChild variant="secondary" size="sm">
                <Link href="/settings/integrations">Sozlamalar</Link>
              </Button>
            </div>
          ) : botInfo ? (
            <div className="flex items-center gap-4 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
                <Send className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-[14px] font-semibold text-[var(--fg)]">
                    {botInfo.first_name ?? "Telegram Bot"}
                  </p>
                  {botInfo.username ? (
                    <Badge variant="primary">@{botInfo.username}</Badge>
                  ) : null}
                  {botInfo.mocked ? <Badge variant="outline">MOCK</Badge> : null}
                </div>
                <p className="mt-0.5 text-[11px] text-[var(--fg-subtle)]">
                  Bot ID: {botInfo.bot_id ?? "—"} · Guruhlarga qo&apos;shilishi:{" "}
                  {botInfo.can_join_groups ? "ha" : "yo'q"}
                </p>
              </div>
              <Badge variant="success">
                <CheckCircle2 className="h-2.5 w-2.5" /> Faol
              </Badge>
            </div>
          ) : (
            <div className="h-16 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]" />
          )}
        </CardContent>
      </Card>

      {/* Link form */}
      {linking ? (
        <LinkForm
          brands={brands}
          defaultBrandId={brands.find((b) => b.is_default)?.id ?? brands[0]?.id ?? ""}
          onCancel={() => setLinking(false)}
          onSubmit={(args) => link.mutate(args)}
          loading={link.isPending}
        />
      ) : null}

      {/* Test send modal */}
      {testing ? (
        <TestSendForm
          account={testing}
          onCancel={() => setTesting(null)}
          onSubmit={(text) => sendTest.mutate({ accountId: testing.id, text })}
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
          <CardTitle>Ulangan kanallar</CardTitle>
          <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
            Har brend bir nechta kanal/guruhga post yuborishi mumkin
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
              title="Hech qanday kanal ulanmagan"
              description={
                telegramConnected
                  ? "Yuqoridan «Telegram kanal» tugmasi orqali kanal yoki guruh qo'shing."
                  : "Avval bot tokenini sozlamalardan ulang."
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

function AccountRow({
  account,
  brand,
  onTest,
  onDelete,
}: {
  account: SocialAccount;
  brand?: Brand;
  onTest: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="group flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-colors hover:border-[var(--primary)]">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Send className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">
            {account.external_name ?? account.external_handle ?? account.external_id}
          </p>
          {account.external_handle ? (
            <Badge variant="default">
              <Hash className="h-2.5 w-2.5" />
              {account.external_handle}
            </Badge>
          ) : null}
          {account.chat_type ? <Badge variant="outline">{account.chat_type}</Badge> : null}
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
          <Button variant="ghost" size="sm" onClick={onTest}>
            <Send /> Test
          </Button>
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

function LinkForm({
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
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Telegram kanal ulash</CardTitle>
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
            <FormField label="Brend" required>
              <select
                value={brandId}
                onChange={(e) => setBrandId(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              >
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
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
          <div className="rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-[12px] text-[var(--fg-muted)]">
            Botni avval kanalga admin sifatida qo&apos;shing — shundagina post yuborib, kanal
            ma&apos;lumotlarini ola oladi.
          </div>
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => brandId && chat.trim() && onSubmit({ brandId, chat: chat.trim() })}
              loading={loading}
              disabled={!brandId || !chat.trim()}
            >
              Ulash
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
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
  onSubmit: (text: string) => void;
  loading: boolean;
}) {
  const [text, setText] = useState(
    "Test xabar — NEXUS AI orqali yuborildi.\nMuvaffaqiyatli ulanish belgisi.",
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            Test xabar — {account.external_name ?? account.external_handle ?? "kanal"}
          </CardTitle>
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
          <FormField label="Matn" required hint="HTML qo'llab-quvvatlanadi (parse_mode=HTML)">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="flex min-h-[120px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => text.trim() && onSubmit(text.trim())}
              loading={loading}
              disabled={!text.trim()}
            >
              <Send /> Yuborish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

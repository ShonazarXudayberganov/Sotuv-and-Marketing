"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AtSign,
  Bot,
  Camera,
  CheckCircle2,
  Inbox as InboxIcon,
  Mail,
  Megaphone,
  MessageCircle,
  Search,
  Send,
  Sparkles,
  Wand2,
  XCircle,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { extractApiError } from "@/lib/api-client";
import { inboxApi } from "@/lib/inbox-api";
import type { Conversation, InboxMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_FILTERS: { key: "all" | "open" | "snoozed" | "closed"; label: string }[] = [
  { key: "all", label: "Hammasi" },
  { key: "open", label: "Ochiq" },
  { key: "snoozed", label: "Kutilmoqda" },
  { key: "closed", label: "Yopildi" },
];

const CHANNEL_ICON: Record<string, typeof Send> = {
  telegram: Send,
  instagram: Camera,
  facebook: Megaphone,
  email: Mail,
  web_widget: MessageCircle,
};

export default function InboxPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<"all" | "open" | "snoozed" | "closed">(
    "open",
  );
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const activeStatus = statusFilter === "all" ? null : statusFilter;
  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ["inbox", "conversations", activeStatus],
    queryFn: () => inboxApi.listConversations({ status: activeStatus, limit: 100 }),
  });
  const { data: stats } = useQuery({
    queryKey: ["inbox", "stats"],
    queryFn: inboxApi.stats,
  });
  const { data: autoReply } = useQuery({
    queryKey: ["inbox", "auto-reply"],
    queryFn: inboxApi.getAutoReply,
  });

  // Auto-select the first conversation when nothing is selected
  const selectedId = activeId ?? conversations[0]?.id ?? null;
  const active = conversations.find((c) => c.id === selectedId) ?? null;

  const { data: messages = [] } = useQuery({
    queryKey: ["inbox", "messages", selectedId],
    queryFn: () => (selectedId ? inboxApi.listMessages(selectedId) : []),
    enabled: !!selectedId,
  });

  // Mark-as-read on selection
  const markRead = useMutation({
    mutationFn: (id: string) => inboxApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox"] }),
  });
  useEffect(() => {
    if (selectedId && active && active.unread_count > 0) {
      markRead.mutate(selectedId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const send = useMutation({
    mutationFn: (args: { id: string; body: string }) =>
      inboxApi.sendMessage(args.id, args.body),
    onSuccess: () => {
      setDraft("");
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const draftReply = useMutation({
    mutationFn: (id: string) => inboxApi.draftReply(id),
    onSuccess: (res) => {
      setDraft(res.reply);
      toast.success(
        `AI taklif (${res.confidence}% ishonch${res.mocked ? " · MOCK" : ""})`,
      );
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const setStatus = useMutation({
    mutationFn: (args: { id: string; status: string }) =>
      inboxApi.setStatus(args.id, args.status),
    onSuccess: (rec) => {
      toast.success(`Status: ${rec.status}`);
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const seed = useMutation({
    mutationFn: () => inboxApi.seedMock(),
    onSuccess: (res) => {
      toast.success(`Mock seed: ${res.inserted} ta xabar`);
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-4"
    >
      <PageHeader
        breadcrumbs={[{ label: "Bosh sahifa", href: "/dashboard" }, { label: "Inbox" }]}
        title="Inbox"
        description="Telegram, Instagram, Facebook, email — bir oynada. AI auto-javob 90% confidence bilan."
        actions={
          <div className="flex items-center gap-2">
            <Link
              href="/inbox/settings"
              className={cn(
                "flex h-9 items-center gap-1.5 rounded-md border px-3 text-[12px] font-medium transition-colors",
                autoReply?.is_enabled
                  ? "border-[var(--success)] bg-[var(--success-soft)] text-[var(--success)]"
                  : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
              )}
            >
              <Bot className="h-3.5 w-3.5" />
              Auto-reply: {autoReply?.is_enabled ? "yoqilgan" : "o'chirilgan"}
            </Link>
            <Can permission="inbox.write">
              <Button
                variant="secondary"
                onClick={() => seed.mutate()}
                loading={seed.isPending}
              >
                <Sparkles /> Mock seed
              </Button>
            </Can>
          </div>
        }
      />

      {/* Status pills + counts */}
      <div className="flex flex-wrap items-center gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setStatusFilter(s.key)}
            className={cn(
              "flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] transition-colors",
              statusFilter === s.key
                ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
            )}
          >
            {s.label}
            {s.key !== "all" && stats?.by_status?.[s.key] ? (
              <span className="text-[10px] opacity-70">
                {stats.by_status[s.key]}
              </span>
            ) : null}
          </button>
        ))}
        {stats?.unread ? (
          <Badge variant="primary" className="ml-auto">
            {stats.unread} o&apos;qilmagan
          </Badge>
        ) : null}
      </div>

      {/* 3-pane layout */}
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        {/* Conversation list */}
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <InboxIcon className="h-4 w-4 text-[var(--primary)]" />
              Suhbatlar
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {isLoading ? (
              [0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                />
              ))
            ) : conversations.length === 0 ? (
              <EmptyState
                icon={InboxIcon}
                title="Suhbatlar yo'q"
                description="Telegram bot ulangan bo'lsa, kelgan xabarlar shu yerda paydo bo'ladi."
              />
            ) : (
              conversations.map((c) => (
                <ConversationRow
                  key={c.id}
                  conversation={c}
                  active={c.id === selectedId}
                  onSelect={() => {
                    setActiveId(c.id);
                    setDraft("");
                  }}
                />
              ))
            )}
          </CardContent>
        </Card>

        {/* Thread */}
        {active ? (
          <ThreadPane
            conversation={active}
            messages={messages}
            draft={draft}
            onDraftChange={setDraft}
            onSend={() => active && send.mutate({ id: active.id, body: draft })}
            sending={send.isPending}
            onAi={() => active && draftReply.mutate(active.id)}
            aiPending={draftReply.isPending}
            onStatus={(status) =>
              active && setStatus.mutate({ id: active.id, status })
            }
          />
        ) : (
          <Card>
            <CardContent>
              <EmptyState
                icon={Search}
                title="Suhbat tanlang"
                description="Chap paneldan suhbatni tanlang yoki Mock seed bilan namuna ma'lumotini yarating"
              />
            </CardContent>
          </Card>
        )}
      </div>
    </motion.div>
  );
}

function ConversationRow({
  conversation,
  active,
  onSelect,
}: {
  conversation: Conversation;
  active: boolean;
  onSelect: () => void;
}) {
  const Icon = CHANNEL_ICON[conversation.channel] ?? MessageCircle;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)]/30"
          : "border-[var(--border)] bg-[var(--bg-subtle)] hover:border-[var(--primary)]",
      )}
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">
            {conversation.title ?? conversation.external_id}
          </p>
          {conversation.unread_count > 0 ? (
            <Badge variant="primary">{conversation.unread_count}</Badge>
          ) : null}
        </div>
        <p className="line-clamp-2 text-[11px] text-[var(--fg-muted)]">
          {conversation.snippet ?? "—"}
        </p>
        <p className="mt-1 text-[10px] text-[var(--fg-subtle)]">
          {conversation.last_message_at
            ? new Date(conversation.last_message_at).toLocaleString("uz-UZ")
            : "—"}
        </p>
      </div>
    </button>
  );
}

function ThreadPane({
  conversation,
  messages,
  draft,
  onDraftChange,
  onSend,
  sending,
  onAi,
  aiPending,
  onStatus,
}: {
  conversation: Conversation;
  messages: InboxMessage[];
  draft: string;
  onDraftChange: (v: string) => void;
  onSend: () => void;
  sending: boolean;
  onAi: () => void;
  aiPending: boolean;
  onStatus: (status: string) => void;
}) {
  const Icon = CHANNEL_ICON[conversation.channel] ?? MessageCircle;
  const grouped = useMemo(() => {
    const map = new Map<string, InboxMessage[]>();
    for (const m of messages) {
      const key = new Date(m.occurred_at).toLocaleDateString("uz-UZ");
      map.set(key, [...(map.get(key) ?? []), m]);
    }
    return Array.from(map.entries());
  }, [messages]);

  return (
    <Card className="flex h-[calc(100vh-260px)] flex-col">
      <CardHeader className="flex flex-row items-start justify-between border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <CardTitle>{conversation.title ?? conversation.external_id}</CardTitle>
            <p className="text-[11px] text-[var(--fg-subtle)]">
              <AtSign className="inline h-3 w-3" /> {conversation.channel} ·{" "}
              {conversation.external_id}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Can permission="inbox.write">
            <button
              type="button"
              onClick={() =>
                onStatus(conversation.status === "closed" ? "open" : "closed")
              }
              className="flex h-7 items-center gap-1 rounded-md border border-[var(--border)] px-2 text-[11px] text-[var(--fg-muted)] hover:border-[var(--primary)] hover:text-[var(--fg)]"
            >
              {conversation.status === "closed" ? (
                <>
                  <CheckCircle2 className="h-3 w-3" /> Qayta ochish
                </>
              ) : (
                <>
                  <XCircle className="h-3 w-3" /> Yopish
                </>
              )}
            </button>
          </Can>
        </div>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden">
        <div className="flex-1 overflow-y-auto pr-1">
          {grouped.length === 0 ? (
            <EmptyState
              icon={MessageCircle}
              title="Xabarlar yo'q"
              description="Birinchi xabar bu yerda ko'rinadi"
            />
          ) : (
            <div className="space-y-4">
              {grouped.map(([day, items]) => (
                <div key={day} className="space-y-2">
                  <p className="text-center text-[10px] tracking-wider text-[var(--fg-subtle)] uppercase">
                    {day}
                  </p>
                  {items.map((m) => (
                    <MessageBubble key={m.id} msg={m} />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        <Can permission="inbox.write">
          <div className="space-y-2 border-t border-[var(--border)] pt-3">
            <textarea
              value={draft}
              onChange={(e) => onDraftChange(e.target.value)}
              placeholder="Javob yozing yoki AI tavsiyasini oling..."
              rows={3}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && draft.trim()) {
                  e.preventDefault();
                  onSend();
                }
              }}
            />
            <div className="flex items-center justify-between gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={onAi}
                loading={aiPending}
              >
                <Wand2 /> AI tavsiya
              </Button>
              <Button
                onClick={onSend}
                loading={sending}
                disabled={!draft.trim()}
              >
                <Send /> Yuborish
              </Button>
            </div>
            <p className="text-[10px] text-[var(--fg-subtle)]">
              ⌘/Ctrl + Enter — tezkor yuborish
            </p>
          </div>
        </Can>
      </CardContent>
    </Card>
  );
}

function MessageBubble({ msg }: { msg: InboxMessage }) {
  const isOut = msg.direction === "out";
  return (
    <div className={cn("flex", isOut ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[78%] rounded-2xl px-3 py-2 text-[13px] shadow-[var(--shadow-xs)]",
          isOut
            ? "bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
            : "bg-[var(--bg-subtle)] text-[var(--fg)]",
        )}
      >
        {msg.is_auto_reply ? (
          <div className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase text-[var(--primary)]">
            <Zap className="h-2.5 w-2.5" /> AI auto-javob
            {msg.confidence ? ` · ${msg.confidence}%` : ""}
          </div>
        ) : null}
        <p className="whitespace-pre-wrap">{msg.body}</p>
        <p className="mt-1 text-[10px] opacity-60">
          {new Date(msg.occurred_at).toLocaleTimeString("uz-UZ", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

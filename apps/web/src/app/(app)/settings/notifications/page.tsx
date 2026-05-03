"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { notificationPrefsApi } from "@/lib/security-api";
import type { NotificationCategory, NotificationChannel } from "@/lib/types";

const CATEGORIES: { key: NotificationCategory; label: string }[] = [
  { key: "tasks", label: "Vazifalar" },
  { key: "billing", label: "To'lov" },
  { key: "ai", label: "AI" },
  { key: "inbox", label: "Inbox" },
  { key: "social", label: "SMM / Social" },
  { key: "system", label: "Tizim" },
];

const CHANNELS: { key: NotificationChannel; label: string }[] = [
  { key: "in_app", label: "Ilovada" },
  { key: "email", label: "Email" },
  { key: "telegram", label: "Telegram" },
];

export default function NotificationsPage() {
  const { data, refetch } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: notificationPrefsApi.get,
  });

  const initial = useMemo(
    () => ({
      channels: { ...(data?.channels ?? {}) },
      quietStart: data?.quiet_hours_start?.toString() ?? "",
      quietEnd: data?.quiet_hours_end?.toString() ?? "",
      tgChatId: data?.telegram_chat_id ?? "",
    }),
    [data],
  );
  const [channels, setChannels] = useState<Record<string, string[]>>(initial.channels);
  const [quietStart, setQuietStart] = useState<string>(initial.quietStart);
  const [quietEnd, setQuietEnd] = useState<string>(initial.quietEnd);
  const [tgChatId, setTgChatId] = useState<string>(initial.tgChatId);
  const [hydrated, setHydrated] = useState(false);
  if (data && !hydrated) {
    setChannels(initial.channels);
    setQuietStart(initial.quietStart);
    setQuietEnd(initial.quietEnd);
    setTgChatId(initial.tgChatId);
    setHydrated(true);
  }

  const save = useMutation({
    mutationFn: () =>
      notificationPrefsApi.update({
        channels: channels as never,
        quiet_hours_start: quietStart ? Number.parseInt(quietStart, 10) : null,
        quiet_hours_end: quietEnd ? Number.parseInt(quietEnd, 10) : null,
        telegram_chat_id: tgChatId || null,
      }),
    onSuccess: async () => {
      toast.success("Saqlandi");
      await refetch();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  function toggle(category: string, channel: string) {
    setChannels((prev) => {
      const current = prev[category] ?? [];
      const next = current.includes(channel)
        ? current.filter((c) => c !== channel)
        : [...current, channel];
      return { ...prev, [category]: next };
    });
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Bildirishnoma kanallari</CardTitle>
          <CardDescription>
            Har kategoriyadan qaysi kanal orqali bildirishnoma olishingizni tanlang
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-cream-200 overflow-hidden rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-cream-100 text-muted text-xs">
                <tr>
                  <th className="px-3 py-2 text-left">Kategoriya</th>
                  {CHANNELS.map((c) => (
                    <th key={c.key} className="px-3 py-2 text-center">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-cream-200 divide-y">
                {CATEGORIES.map((cat) => (
                  <tr key={cat.key} className="bg-cream">
                    <td className="px-3 py-2 font-medium">{cat.label}</td>
                    {CHANNELS.map((ch) => (
                      <td key={ch.key} className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={channels[cat.key]?.includes(ch.key) ?? false}
                          onChange={() => toggle(cat.key, ch.key)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Indamas vaqt va Telegram</CardTitle>
          <CardDescription>
            Indamas vaqt davomida ovoz va push bildirishnomalar yuborilmaydi (24-soat
            formatida)
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <FormField label="Boshlanish (0-23)">
            <Input
              type="number"
              min={0}
              max={23}
              value={quietStart}
              onChange={(e) => setQuietStart(e.target.value)}
            />
          </FormField>
          <FormField label="Tugash (0-23)">
            <Input
              type="number"
              min={0}
              max={23}
              value={quietEnd}
              onChange={(e) => setQuietEnd(e.target.value)}
            />
          </FormField>
          <FormField label="Telegram chat ID" hint="Bot bilan suhbatdagi raqam">
            <Input value={tgChatId} onChange={(e) => setTgChatId(e.target.value)} />
          </FormField>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => save.mutate()} loading={save.isPending}>
          Saqlash
        </Button>
      </div>
    </div>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bot, Save } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { inboxApi } from "@/lib/inbox-api";
import { brandsApi } from "@/lib/smm-api";
import { cn } from "@/lib/utils";

const ALL_CHANNELS = ["telegram", "instagram", "facebook", "email", "web_widget"];

export default function InboxSettingsPage() {
  const qc = useQueryClient();
  const { data: cfg } = useQuery({
    queryKey: ["inbox", "auto-reply"],
    queryFn: inboxApi.getAutoReply,
  });
  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });

  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [threshold, setThreshold] = useState<string>("");
  const [quietStart, setQuietStart] = useState<string>("");
  const [quietEnd, setQuietEnd] = useState<string>("");
  const [defaultBrand, setDefaultBrand] = useState<string>("");
  const [fallback, setFallback] = useState<string>("");
  const [channels, setChannels] = useState<string[] | null>(null);

  const eff = {
    enabled: enabled ?? cfg?.is_enabled ?? false,
    threshold: threshold || String(cfg?.confidence_threshold ?? 90),
    quietStart: quietStart || (cfg?.quiet_hours_start?.toString() ?? ""),
    quietEnd: quietEnd || (cfg?.quiet_hours_end?.toString() ?? ""),
    defaultBrand: defaultBrand || cfg?.default_brand_id || "",
    fallback: fallback || cfg?.fallback_text || "",
    channels: channels ?? cfg?.channels_enabled ?? ["telegram"],
  };

  const save = useMutation({
    mutationFn: () =>
      inboxApi.updateAutoReply({
        is_enabled: eff.enabled,
        confidence_threshold: parseInt(eff.threshold || "90", 10),
        quiet_hours_start: eff.quietStart === "" ? null : parseInt(eff.quietStart, 10),
        quiet_hours_end: eff.quietEnd === "" ? null : parseInt(eff.quietEnd, 10),
        default_brand_id: eff.defaultBrand || null,
        fallback_text: eff.fallback || null,
        channels_enabled: eff.channels,
      }),
    onSuccess: () => {
      toast.success("Saqlandi");
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const toggleChannel = (c: string) =>
    setChannels((curr) => {
      const list = curr ?? cfg?.channels_enabled ?? ["telegram"];
      return list.includes(c) ? list.filter((x) => x !== c) : [...list, c];
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
          { label: "Inbox", href: "/inbox" },
          { label: "Sozlamalar" },
        ]}
        title="Auto-reply sozlamalari"
        description="AI auto-javob qachon yuborilishi va qaysi kanallarda ishlashini sozlang"
      />

      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Bot className="h-4 w-4 text-[var(--primary)]" />
          <CardTitle>AI auto-javob</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-3">
            <input
              type="checkbox"
              checked={eff.enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-4 w-4 accent-[var(--primary)]"
            />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-medium text-[var(--fg)]">Auto-reply yoqilgan</p>
              <p className="text-[11px] text-[var(--fg-muted)]">
                Confidence chegarasidan yuqori javoblar avtomatik yuboriladi
              </p>
            </div>
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Confidence chegarasi (%)"
              hint="Spec'ga ko'ra: 90% va undan yuqori"
            >
              <Input
                type="number"
                min={0}
                max={100}
                value={eff.threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
            </FormField>
            <FormField label="Standart brend" hint="RAG kontekst manbasi">
              <select
                value={eff.defaultBrand}
                onChange={(e) => setDefaultBrand(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)]"
              >
                <option value="">— tanlanmagan —</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Sukut soati boshi (UTC, 0-23)">
              <Input
                type="number"
                min={0}
                max={23}
                value={eff.quietStart}
                onChange={(e) => setQuietStart(e.target.value)}
                placeholder="22"
              />
            </FormField>
            <FormField label="Sukut soati oxiri (UTC, 0-23)">
              <Input
                type="number"
                min={0}
                max={23}
                value={eff.quietEnd}
                onChange={(e) => setQuietEnd(e.target.value)}
                placeholder="6"
              />
            </FormField>
          </div>

          <FormField label="Faol kanallar">
            <div className="flex flex-wrap gap-1.5">
              {ALL_CHANNELS.map((c) => {
                const active = eff.channels.includes(c);
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => toggleChannel(c)}
                    className={cn(
                      "rounded-md border px-2.5 py-1 text-[12px] capitalize transition-colors",
                      active
                        ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                        : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
                    )}
                  >
                    {c.replace("_", " ")}
                  </button>
                );
              })}
            </div>
          </FormField>

          <FormField
            label="Fallback matn"
            hint="AI confidence past bo'lganda yuboriladigan tayyor javob (kelajakda)"
          >
            <textarea
              value={eff.fallback}
              onChange={(e) => setFallback(e.target.value)}
              placeholder="Operator tez orada javob beradi..."
              className="flex min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)]"
            />
          </FormField>

          <Can permission="inbox.write">
            <div className="flex justify-end">
              <Button onClick={() => save.mutate()} loading={save.isPending}>
                <Save /> Saqlash
              </Button>
            </div>
          </Can>
        </CardContent>
      </Card>
    </motion.div>
  );
}

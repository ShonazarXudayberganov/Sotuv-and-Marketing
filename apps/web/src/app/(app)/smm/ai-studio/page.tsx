"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Camera,
  Copy,
  Globe,
  Megaphone,
  Play,
  Send,
  Sparkles,
  Star,
  Trash2,
  Wand2,
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
import { aiApi } from "@/lib/ai-api";
import { extractApiError } from "@/lib/api-client";
import { brandsApi } from "@/lib/smm-api";
import type { ContentDraft, ContentPlatform } from "@/lib/types";
import { cn } from "@/lib/utils";

const PLATFORMS: { key: ContentPlatform; label: string; icon: typeof Send }[] = [
  { key: "telegram", label: "Telegram", icon: Send },
  { key: "instagram", label: "Instagram", icon: Camera },
  { key: "facebook", label: "Facebook", icon: Megaphone },
  { key: "youtube", label: "YouTube", icon: Play },
  { key: "generic", label: "Generic", icon: Globe },
];

const LANGUAGES = [
  { code: "uz", label: "O'zbek (lotin)" },
  { code: "uz-cy", label: "O'zbek (kirill)" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

export default function AIStudioPage() {
  const qc = useQueryClient();

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const defaultBrand = brands.find((b) => b.is_default) ?? brands[0];

  const [brandIdState, setBrandId] = useState<string | null>(null);
  const [platform, setPlatform] = useState<ContentPlatform>("telegram");
  const [language, setLanguage] = useState("uz");
  const [userGoal, setUserGoal] = useState("");
  const [title, setTitle] = useState("");
  const [useCache, setUseCache] = useState(true);
  const [activeDraft, setActiveDraft] = useState<ContentDraft | null>(null);

  // Effective brand id — falls back to default brand at render time
  const brandId = brandIdState ?? defaultBrand?.id ?? "";

  const { data: drafts = [], isLoading: draftsLoading } = useQuery({
    queryKey: ["ai", "drafts", brandId || null],
    queryFn: () => aiApi.listDrafts({ brand_id: brandId || null, limit: 50 }),
  });
  const { data: usage } = useQuery({
    queryKey: ["ai", "usage"],
    queryFn: aiApi.usage,
  });

  const generate = useMutation({
    mutationFn: () =>
      aiApi.generatePost({
        brand_id: brandId,
        platform,
        user_goal: userGoal.trim(),
        language,
        title: title.trim() || null,
        use_cache: useCache,
      }),
    onSuccess: (draft) => {
      toast.success(
        draft.provider === "mock"
          ? `MOCK draft tayyor (${draft.tokens_used} token)`
          : `Tayyor! ${draft.provider} → ${draft.tokens_used} token`,
      );
      setActiveDraft(draft);
      qc.invalidateQueries({ queryKey: ["ai"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const star = useMutation({
    mutationFn: (id: string) => aiApi.toggleStar(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ai", "drafts"] }),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => aiApi.deleteDraft(id),
    onSuccess: () => {
      toast.success("Draft o'chirildi");
      setActiveDraft(null);
      qc.invalidateQueries({ queryKey: ["ai", "drafts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const update = useMutation({
    mutationFn: (args: { id: string; body: string }) =>
      aiApi.updateDraft(args.id, { body: args.body }),
    onSuccess: (draft) => {
      toast.success("Saqlandi");
      setActiveDraft(draft);
      qc.invalidateQueries({ queryKey: ["ai", "drafts"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const usagePct =
    usage && usage.tokens_cap > 0
      ? Math.min(100, Math.round((usage.tokens_used / usage.tokens_cap) * 100))
      : 0;

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
          { label: "AI Studio" },
        ]}
        title="AI Studio"
        description="Brend ovozi, RAG kontekst va platforma cheklovlari asosida post drafti generatsiya qiling"
        actions={
          usage ? (
            <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-2 text-[12px] text-[var(--fg-muted)]">
              <span className="font-medium text-[var(--fg)]">
                {usage.tokens_used.toLocaleString("uz-UZ")}
              </span>{" "}
              / {usage.tokens_cap > 0 ? usage.tokens_cap.toLocaleString("uz-UZ") : "∞"} token ·{" "}
              {usage.period}
              {usage.tokens_cap > 0 ? (
                <span className="ml-2 text-[var(--fg-subtle)]">{usagePct}%</span>
              ) : null}
            </div>
          ) : null
        }
      />

      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        {/* Generator panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-[var(--primary)]" /> Post generatsiya
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="Brend" required>
              <select
                value={brandId}
                onChange={(e) => setBrandId(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              >
                <option value="">— tanlang —</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Platforma" required>
              <div className="flex flex-wrap gap-1.5">
                {PLATFORMS.map((p) => {
                  const Icon = p.icon;
                  const active = platform === p.key;
                  return (
                    <button
                      key={p.key}
                      type="button"
                      onClick={() => setPlatform(p.key)}
                      className={cn(
                        "flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[12px] font-medium transition-colors",
                        active
                          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
                      )}
                    >
                      <Icon className="h-3.5 w-3.5" /> {p.label}
                    </button>
                  );
                })}
              </div>
            </FormField>

            <FormField label="Til">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Sarlavha (ixtiyoriy)">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Bahor aksiyasi"
              />
            </FormField>

            <FormField
              label="Maqsad / brief"
              required
              hint="Nima haqida post bo'lishini tushuntiring. AI brendingiz ovozi va bilim bazasini hisobga oladi."
            >
              <textarea
                value={userGoal}
                onChange={(e) => setUserGoal(e.target.value)}
                placeholder="Misol: yangi manikur xizmatini e'lon qilish, mart oyida 20% chegirma"
                className="flex min-h-[120px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
              />
            </FormField>

            <label className="flex items-center gap-2 text-[12px] text-[var(--fg)]">
              <input
                type="checkbox"
                checked={useCache}
                onChange={(e) => setUseCache(e.target.checked)}
                className="h-4 w-4 accent-[var(--primary)]"
              />
              24 soatlik cache (bir xil so&apos;rovni qayta ishlatmaslik)
            </label>

            <Can permission="smm.write">
              <Button
                onClick={() => generate.mutate()}
                loading={generate.isPending}
                disabled={!brandId || userGoal.trim().length < 2}
                className="w-full"
              >
                <Sparkles /> Generatsiya qilish
              </Button>
            </Can>
          </CardContent>
        </Card>

        {/* Preview + drafts */}
        <div className="space-y-4">
          {activeDraft ? (
            <DraftPreview
              draft={activeDraft}
              onClose={() => setActiveDraft(null)}
              onSave={(body) => update.mutate({ id: activeDraft.id, body })}
              saving={update.isPending}
            />
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Draftlar</CardTitle>
              <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
                Avval yaratilgan postlar — tahrirlash, yulduzcha berish yoki o&apos;chirish
              </p>
            </CardHeader>
            <CardContent>
              {draftsLoading ? (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-20 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                    />
                  ))}
                </div>
              ) : drafts.length === 0 ? (
                <EmptyState
                  icon={Sparkles}
                  title="Draftlar yo'q"
                  description="Chap paneldan post generatsiya qiling — bu yerda saqlanadi"
                />
              ) : (
                <div className="space-y-2">
                  {drafts.map((d) => (
                    <DraftCard
                      key={d.id}
                      draft={d}
                      brandName={brands.find((b) => b.id === d.brand_id)?.name}
                      onSelect={() => setActiveDraft(d)}
                      onStar={() => star.mutate(d.id)}
                      onDelete={() => remove.mutate(d.id)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}

function DraftPreview({
  draft,
  onClose,
  onSave,
  saving,
}: {
  draft: ContentDraft;
  onClose: () => void;
  onSave: (body: string) => void;
  saving: boolean;
}) {
  const [body, setBody] = useState(draft.body);
  const dirty = body !== draft.body;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(body);
      toast.success("Nusxa olindi");
    } catch {
      toast.error("Nusxa olib bo'lmadi");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--primary)]" />
            Preview — {draft.platform}
          </CardTitle>
          <p className="mt-0.5 text-[11px] text-[var(--fg-subtle)]">
            {draft.provider} · {draft.model} · {draft.tokens_used} token ·{" "}
            {new Date(draft.created_at).toLocaleString("uz-UZ")}
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
      <CardContent className="space-y-3">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="flex min-h-[260px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm leading-relaxed text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
        />
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] text-[var(--fg-subtle)]">
            {body.length} belgi
            {draft.rag_chunk_ids?.length
              ? ` · ${draft.rag_chunk_ids.length} ta KB bo'lakdan kontekst`
              : ""}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={copy}>
              <Copy /> Nusxa
            </Button>
            <Can permission="smm.write">
              <Button
                onClick={() => onSave(body)}
                disabled={!dirty}
                loading={saving}
                size="sm"
              >
                Saqlash
              </Button>
            </Can>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function DraftCard({
  draft,
  brandName,
  onSelect,
  onStar,
  onDelete,
}: {
  draft: ContentDraft;
  brandName?: string;
  onSelect: () => void;
  onStar: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="group flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-colors hover:border-[var(--primary)]">
      <button
        type="button"
        onClick={onSelect}
        className="flex min-w-0 flex-1 flex-col items-start gap-1 text-left"
      >
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">
            {draft.title || draft.user_goal?.slice(0, 60) || "—"}
          </p>
          <Badge variant="outline" className="capitalize">
            {draft.platform}
          </Badge>
          {draft.provider === "mock" ? <Badge variant="default">MOCK</Badge> : null}
        </div>
        <p className="line-clamp-2 text-[12px] text-[var(--fg-muted)]">{draft.body}</p>
        <p className="text-[10px] text-[var(--fg-subtle)]">
          {brandName ?? "—"} · {draft.provider ?? "—"} · {draft.tokens_used} token ·{" "}
          {new Date(draft.created_at).toLocaleString("uz-UZ")}
        </p>
      </button>
      <Can permission="smm.write">
        <div className="flex items-center gap-0.5">
          <button
            type="button"
            onClick={onStar}
            aria-label="Yulduzcha"
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md transition-colors",
              draft.is_starred
                ? "text-[var(--primary)]"
                : "text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]",
            )}
          >
            <Star className={cn("h-3.5 w-3.5", draft.is_starred && "fill-current")} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            aria-label="O'chirish"
            className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </Can>
    </div>
  );
}

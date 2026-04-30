"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Globe,
  MoreHorizontal,
  PenSquare,
  Plus,
  Sparkles,
  Star,
  Trash2,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { brandsApi } from "@/lib/smm-api";
import type { Brand, BrandCreate } from "@/lib/types";
import { cn } from "@/lib/utils";

const LANGS: { code: string; label: string }[] = [
  { code: "uz", label: "O'zbek (lotin)" },
  { code: "uz-cy", label: "O'zbek (kirill)" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

export default function BrandsPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Brand | null>(null);
  const [creating, setCreating] = useState(false);

  const { data: brands = [], isLoading } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });

  const create = useMutation({
    mutationFn: (payload: BrandCreate) => brandsApi.create(payload),
    onSuccess: () => {
      toast.success("Brend yaratildi");
      qc.invalidateQueries({ queryKey: ["brands"] });
      setCreating(false);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<BrandCreate> }) =>
      brandsApi.update(id, payload),
    onSuccess: () => {
      toast.success("Saqlandi");
      qc.invalidateQueries({ queryKey: ["brands"] });
      setEditing(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const setDefault = useMutation({
    mutationFn: (id: string) => brandsApi.setDefault(id),
    onSuccess: () => {
      toast.success("Asosiy brend o'zgartirildi");
      qc.invalidateQueries({ queryKey: ["brands"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => brandsApi.remove(id),
    onSuccess: () => {
      toast.success("Brend o'chirildi");
      qc.invalidateQueries({ queryKey: ["brands"] });
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
          { label: "Brendlar" },
        ]}
        title="Brendlar"
        description="Har bir brend o'z ovozi, kontent rejasi va ijtimoiy akkauntlariga ega"
        actions={
          <Can permission="smm.write">
            <Button size="default" onClick={() => setCreating(true)}>
              <Plus /> Yangi brend
            </Button>
          </Can>
        }
      />

      {creating ? (
        <BrandForm
          onSubmit={(payload) => create.mutate(payload)}
          onCancel={() => setCreating(false)}
          loading={create.isPending}
        />
      ) : null}

      {editing ? (
        <BrandForm
          initial={editing}
          onSubmit={(payload) => update.mutate({ id: editing.id, payload })}
          onCancel={() => setEditing(null)}
          loading={update.isPending}
        />
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-44 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : brands.length === 0 ? (
        <EmptyState
          icon={PenSquare}
          title="Hozircha brendlar yo'q"
          description="SMM moduli har brend uchun alohida ovoz, kontent reja va ijtimoiy akkauntlarni boshqaradi."
          action={
            <Can permission="smm.write">
              <Button onClick={() => setCreating(true)}>
                <Plus /> Birinchi brend yaratish
              </Button>
            </Can>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {brands.map((b) => (
            <BrandCard
              key={b.id}
              brand={b}
              onEdit={() => setEditing(b)}
              onSetDefault={() => setDefault.mutate(b.id)}
              onDelete={() => remove.mutate(b.id)}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function BrandCard({
  brand,
  onEdit,
  onSetDefault,
  onDelete,
}: {
  brand: Brand;
  onEdit: () => void;
  onSetDefault: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="group relative overflow-hidden p-5 transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-base font-bold"
            style={{
              background: brand.primary_color ?? "var(--primary-soft)",
              color: brand.primary_color ? "white" : "var(--primary-soft-fg)",
            }}
          >
            {brand.name[0]?.toUpperCase()}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate text-[15px] font-semibold tracking-tight text-[var(--fg)]">
                {brand.name}
              </p>
              {brand.is_default ? (
                <Badge variant="primary">
                  <Star className="h-2.5 w-2.5" /> Asosiy
                </Badge>
              ) : null}
            </div>
            <p className="truncate text-[12px] text-[var(--fg-subtle)]">@{brand.slug}</p>
          </div>
        </div>

        <Can permission="smm.write">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Brend amallari"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem onClick={onEdit}>
                <PenSquare /> Tahrirlash
              </DropdownMenuItem>
              {!brand.is_default ? (
                <DropdownMenuItem onClick={onSetDefault}>
                  <Star /> Asosiy qilish
                </DropdownMenuItem>
              ) : null}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDelete}
                className="text-[var(--danger)] focus:bg-[var(--danger-soft)] focus:text-[var(--danger)]"
              >
                <Trash2 /> O&apos;chirish
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </Can>
      </div>

      {brand.description ? (
        <p className="mt-3 line-clamp-2 text-[12px] leading-relaxed text-[var(--fg-muted)]">
          {brand.description}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-1.5 text-[11px]">
        {brand.industry ? <Badge variant="outline">{brand.industry}</Badge> : null}
        {brand.languages.map((lang) => (
          <Badge key={lang} variant="default">
            <Globe className="h-2.5 w-2.5" /> {lang}
          </Badge>
        ))}
      </div>

      {brand.voice_tone ? (
        <div className="mt-4 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] p-2.5">
          <p className="flex items-center gap-1 text-[10px] font-semibold tracking-wider text-[var(--fg-subtle)] uppercase">
            <Sparkles className="h-2.5 w-2.5" /> Ovoz va uslub
          </p>
          <p className="mt-1 line-clamp-2 text-[12px] text-[var(--fg-muted)]">
            {brand.voice_tone}
          </p>
        </div>
      ) : null}
    </Card>
  );
}

function BrandForm({
  initial,
  onSubmit,
  onCancel,
  loading,
}: {
  initial?: Brand;
  onSubmit: (p: BrandCreate) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [industry, setIndustry] = useState(initial?.industry ?? "");
  const [voiceTone, setVoiceTone] = useState(initial?.voice_tone ?? "");
  const [targetAudience, setTargetAudience] = useState(initial?.target_audience ?? "");
  const [primaryColor, setPrimaryColor] = useState(initial?.primary_color ?? "");
  const [languages, setLanguages] = useState<string[]>(initial?.languages ?? ["uz"]);
  const [isDefault, setIsDefault] = useState(initial?.is_default ?? false);

  const toggleLang = (code: string) =>
    setLanguages((l) => (l.includes(code) ? l.filter((x) => x !== code) : [...l, code]));

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{initial ? "Brendni tahrirlash" : "Yangi brend"}</CardTitle>
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
            <FormField label="Brend nomi" required>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Akme Beauty"
                autoFocus
              />
            </FormField>
            <FormField label="Soha" hint="Masalan: salon-klinika, restoran, IT">
              <Input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="salon-klinika"
              />
            </FormField>
          </div>

          <FormField
            label="Tavsif"
            hint="Brend haqida 1-2 jumla. AI shu kontekstdan foydalanadi."
          >
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Toshkent va viloyatlarda 5 ta filiali bor go'zallik salonlari tarmog'i…"
              className="flex min-h-[72px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>

          <FormField label="Ovoz va uslub" hint="AI kontent yaratganda shu uslubda yozadi">
            <Input
              value={voiceTone}
              onChange={(e) => setVoiceTone(e.target.value)}
              placeholder="Iliq, professional, ehtiyotkor"
            />
          </FormField>

          <FormField label="Maqsadli auditoriya">
            <textarea
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="25-45 yosh ayollar, o'rta va o'rtadan yuqori daromadli, Toshkent shahri…"
              className="flex min-h-[60px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Asosiy rang (HEX)" hint="Avatar va aksent uchun">
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={primaryColor || "#16a34a"}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-9 w-12 cursor-pointer rounded-md border border-[var(--border)] bg-[var(--surface)]"
                />
                <Input
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  placeholder="#16a34a"
                />
              </div>
            </FormField>

            <FormField label="Tillar">
              <div className="flex flex-wrap gap-1.5">
                {LANGS.map((l) => {
                  const active = languages.includes(l.code);
                  return (
                    <button
                      key={l.code}
                      type="button"
                      onClick={() => toggleLang(l.code)}
                      className={cn(
                        "rounded-md border px-2.5 py-1 text-[12px] transition-colors",
                        active
                          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
                          : "border-[var(--border)] text-[var(--fg-muted)] hover:border-[var(--primary)]",
                      )}
                    >
                      {l.label}
                    </button>
                  );
                })}
              </div>
            </FormField>
          </div>

          <label className="flex items-center gap-2 text-[13px] text-[var(--fg)]">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="h-4 w-4 accent-[var(--primary)]"
            />
            Asosiy brend qilish
          </label>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                name.trim() &&
                onSubmit({
                  name: name.trim(),
                  description: description || null,
                  industry: industry || null,
                  voice_tone: voiceTone || null,
                  target_audience: targetAudience || null,
                  primary_color: primaryColor || null,
                  languages,
                  is_default: isDefault,
                })
              }
              loading={loading}
              disabled={!name.trim()}
            >
              {initial ? "Saqlash" : "Yaratish"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

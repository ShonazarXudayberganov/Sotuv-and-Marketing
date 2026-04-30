"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  FileText,
  Loader2,
  Plus,
  Search,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
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
import { knowledgeApi } from "@/lib/kb-api";
import { brandsApi } from "@/lib/smm-api";
import type {
  Brand,
  KnowledgeDocument,
  KnowledgeSearchHit,
  TextDocumentCreate,
} from "@/lib/types";
import { cn } from "@/lib/utils";

export default function KnowledgeBasePage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [creating, setCreating] = useState<"text" | "file" | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KnowledgeSearchHit[] | null>(null);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const defaultBrand = brands.find((b) => b.is_default) ?? brands[0];
  const activeBrandId = brandFilter === "all" ? null : brandFilter;

  const { data: docs = [], isLoading } = useQuery({
    queryKey: ["knowledge", "documents", activeBrandId],
    queryFn: () => knowledgeApi.list(activeBrandId),
  });
  const { data: stats } = useQuery({
    queryKey: ["knowledge", "stats", activeBrandId],
    queryFn: () => knowledgeApi.stats(activeBrandId),
  });

  const createText = useMutation({
    mutationFn: (payload: TextDocumentCreate) => knowledgeApi.createText(payload),
    onSuccess: () => {
      toast.success("Hujjat qo'shildi");
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const uploadFile = useMutation({
    mutationFn: (args: { brandId: string; title: string; file: File }) =>
      knowledgeApi.uploadFile(args.brandId, args.title, args.file),
    onSuccess: () => {
      toast.success("Fayl yuklandi va indekslandi");
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => knowledgeApi.remove(id),
    onSuccess: () => {
      toast.success("Hujjat o'chirildi");
      qc.invalidateQueries({ queryKey: ["knowledge"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const search = useMutation({
    mutationFn: (q: string) => knowledgeApi.search(q, activeBrandId, 5),
    onSuccess: (resp) => setSearchResults(resp.hits),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const filteredDocs = useMemo(() => docs, [docs]);

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
          { label: "Bilim bazasi" },
        ]}
        title="Bilim bazasi"
        description="Brend hujjatlari, FAQ va kontent kontekstlari. AI shu bazadan kontekst oladi."
        actions={
          <Can permission="smm.write">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="default"
                onClick={() => setCreating("file")}
                disabled={brands.length === 0}
              >
                <Upload /> Fayl
              </Button>
              <Button
                size="default"
                onClick={() => setCreating("text")}
                disabled={brands.length === 0}
              >
                <Plus /> Yangi hujjat
              </Button>
            </div>
          </Can>
        }
      />

      {/* Stats overview */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatBox
          icon={BookOpen}
          label="Hujjatlar"
          value={stats?.documents ?? 0}
          hint={brandFilter === "all" ? "Hamma brendlarda" : "Joriy brendda"}
        />
        <StatBox
          icon={Sparkles}
          label="Bo'laklar (chunks)"
          value={stats?.chunks ?? 0}
          hint="Vector bazasida indekslangan"
        />
        <StatBox
          icon={FileText}
          label="Brendlar"
          value={brands.length}
          hint={defaultBrand ? `Asosiy: ${defaultBrand.name}` : "Brend qo'shilmagan"}
        />
      </div>

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

      {/* Forms */}
      {creating === "text" ? (
        <TextForm
          brands={brands}
          defaultBrandId={defaultBrand?.id ?? ""}
          onCancel={() => setCreating(null)}
          onSubmit={(p) => createText.mutate(p)}
          loading={createText.isPending}
        />
      ) : null}
      {creating === "file" ? (
        <FileForm
          brands={brands}
          defaultBrandId={defaultBrand?.id ?? ""}
          onCancel={() => setCreating(null)}
          onSubmit={(args) => uploadFile.mutate(args)}
          loading={uploadFile.isPending}
        />
      ) : null}

      {/* RAG search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-4 w-4 text-[var(--primary)]" /> RAG qidiruv
          </CardTitle>
          <p className="text-[12px] text-[var(--fg-muted)]">
            AI semantik qidiruv: bo&apos;laklar mazmun bo&apos;yicha topiladi, kalit so&apos;z bo&apos;yicha emas.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Misol: Bizning ish vaqti qachon?"
              onKeyDown={(e) => {
                if (e.key === "Enter" && searchQuery.trim()) search.mutate(searchQuery.trim());
              }}
            />
            <Button
              onClick={() => searchQuery.trim() && search.mutate(searchQuery.trim())}
              loading={search.isPending}
              disabled={!searchQuery.trim()}
            >
              <Search /> Qidirish
            </Button>
          </div>

          {searchResults !== null ? (
            searchResults.length === 0 ? (
              <p className="rounded-md border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-4 text-center text-[12px] text-[var(--fg-muted)]">
                Mos bo&apos;laklar topilmadi. Bilim bazasiga hujjat qo&apos;shing.
              </p>
            ) : (
              <div className="space-y-2">
                {searchResults.map((hit) => (
                  <SearchHitCard key={hit.chunk_id} hit={hit} />
                ))}
              </div>
            )
          ) : null}
        </CardContent>
      </Card>

      {/* Document list */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Hujjatlar</CardTitle>
            <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
              Yuklangan hujjatlar avtomatik bo&apos;laklarga ajratilib indekslanadi
            </p>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface)]"
                />
              ))}
            </div>
          ) : filteredDocs.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="Hujjatlar yo'q"
              description={
                brands.length === 0
                  ? "Avval SMM bo'limidan brend yarating, keyin hujjat qo'shing."
                  : "Birinchi hujjatingizni qo'shing — matn yoki PDF/TXT fayl."
              }
              action={
                brands.length > 0 ? (
                  <Can permission="smm.write">
                    <Button onClick={() => setCreating("text")}>
                      <Plus /> Birinchi hujjat
                    </Button>
                  </Can>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-2">
              {filteredDocs.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  brand={brands.find((b) => b.id === doc.brand_id)}
                  onDelete={() => remove.mutate(doc.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function StatBox({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof BookOpen;
  label: string;
  value: number | string;
  hint: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        <p className="mt-1.5 truncate text-[11px] text-[var(--fg-subtle)]">{hint}</p>
      </div>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
}

function DocumentRow({
  doc,
  brand,
  onDelete,
}: {
  doc: KnowledgeDocument;
  brand?: Brand;
  onDelete: () => void;
}) {
  return (
    <div className="group flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-3 transition-colors hover:border-[var(--primary)]">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--surface)] text-[var(--fg-muted)]">
        {doc.source_type === "file" ? (
          <FileText className="h-4 w-4" />
        ) : (
          <BookOpen className="h-4 w-4" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-[var(--fg)]">{doc.title}</p>
          <StatusBadge status={doc.embed_status} />
        </div>
        <p className="truncate text-[11px] text-[var(--fg-subtle)]">
          {brand?.name ?? "—"} · {doc.chunk_count} bo&apos;lak ·{" "}
          {new Date(doc.created_at).toLocaleDateString("uz-UZ")}
          {doc.source_url ? ` · ${doc.source_url}` : ""}
        </p>
      </div>
      <Can permission="smm.write">
        <button
          type="button"
          onClick={onDelete}
          aria-label="O'chirish"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--fg-subtle)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </Can>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "ready") {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-2.5 w-2.5" /> Tayyor
      </Badge>
    );
  }
  if (status === "processing") {
    return (
      <Badge variant="default">
        <Loader2 className="h-2.5 w-2.5 animate-spin" /> Indekslanmoqda
      </Badge>
    );
  }
  if (status === "failed") {
    return (
      <Badge variant="danger">
        <AlertTriangle className="h-2.5 w-2.5" /> Xatolik
      </Badge>
    );
  }
  if (status === "empty") {
    return <Badge variant="outline">Bo&apos;sh</Badge>;
  }
  return <Badge variant="default">{status}</Badge>;
}

function SearchHitCard({ hit }: { hit: KnowledgeSearchHit }) {
  const pct = Math.round(hit.similarity * 100);
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 shadow-[var(--shadow-xs)]">
      <div className="flex items-center justify-between gap-2">
        <p className="truncate text-[12px] font-medium text-[var(--fg)]">
          {hit.document_title}
        </p>
        <Badge variant="primary">{pct}% mos</Badge>
      </div>
      <p className="mt-1.5 line-clamp-3 text-[12px] leading-relaxed text-[var(--fg-muted)]">
        {hit.content}
      </p>
      <p className="mt-1.5 text-[10px] text-[var(--fg-subtle)]">
        Bo&apos;lak #{hit.position} · {hit.token_count} token
      </p>
    </div>
  );
}

function TextForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string;
  onCancel: () => void;
  onSubmit: (p: TextDocumentCreate) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Yangi matnli hujjat</CardTitle>
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
            <FormField label="Sarlavha" required>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Masalan: Ish vaqti va manzillar"
              />
            </FormField>
          </div>
          <FormField
            label="Matn"
            required
            hint="Hujjat avtomatik ~500 tokenli bo'laklarga ajratiladi."
          >
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Bizning kompaniya..."
              className="flex min-h-[180px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            />
          </FormField>
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                brandId &&
                title.trim() &&
                text.trim() &&
                onSubmit({ brand_id: brandId, title: title.trim(), text: text.trim() })
              }
              loading={loading}
              disabled={!brandId || !title.trim() || !text.trim()}
            >
              Qo&apos;shish
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function FileForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string;
  onCancel: () => void;
  onSubmit: (args: { brandId: string; title: string; file: File }) => void;
  loading: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [brandId, setBrandId] = useState(defaultBrandId);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Fayl yuklash</CardTitle>
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
            <FormField label="Sarlavha" required>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Masalan: Xizmatlar narxi"
              />
            </FormField>
          </div>

          <FormField label="Fayl" hint="PDF yoki .txt (UTF-8) qo'llab-quvvatlanadi">
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
              }}
              className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--border)] bg-[var(--bg-subtle)] p-6 text-[13px] text-[var(--fg-muted)] transition-colors hover:border-[var(--primary)]"
            >
              <Upload className="h-4 w-4" />
              {file ? (
                <span className="text-[var(--fg)]">{file.name}</span>
              ) : (
                <span>Fayl tanlash uchun bosing yoki sudrab tashlang</span>
              )}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.txt,text/plain,application/pdf"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setFile(f);
                if (f && !title.trim()) {
                  const base = f.name.replace(/\.[^.]+$/, "");
                  setTitle(base);
                }
              }}
              className="hidden"
            />
          </FormField>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onCancel}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                brandId && title.trim() && file && onSubmit({ brandId, title: title.trim(), file })
              }
              loading={loading}
              disabled={!brandId || !title.trim() || !file}
            >
              Yuklash
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

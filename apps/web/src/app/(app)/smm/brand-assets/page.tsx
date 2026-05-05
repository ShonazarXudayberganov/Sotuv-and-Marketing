"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  FileText,
  ImageIcon,
  LinkIcon,
  Palette,
  PenSquare,
  Plus,
  Star,
  Trash2,
  Type,
  Upload,
  Video,
  X,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
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
import { brandAssetsApi } from "@/lib/brand-assets-api";
import { brandsApi } from "@/lib/smm-api";
import type {
  Brand,
  BrandAsset,
  BrandAssetCreate,
  BrandAssetType,
  BrandAssetUpdate,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const ASSET_TYPES: { key: BrandAssetType; label: string; icon: LucideIcon }[] = [
  { key: "logo", label: "Logo", icon: ImageIcon },
  { key: "image", label: "Rasm", icon: ImageIcon },
  { key: "video", label: "Video", icon: Video },
  { key: "template", label: "Shablon", icon: FileText },
  { key: "font", label: "Font", icon: Type },
  { key: "color", label: "Rang", icon: Palette },
  { key: "reference", label: "Referens", icon: LinkIcon },
];

const TYPE_LABELS = Object.fromEntries(ASSET_TYPES.map((item) => [item.key, item.label]));

export default function BrandAssetsPage() {
  const qc = useQueryClient();
  const [brandFilter, setBrandFilter] = useState<string | "all">("all");
  const [typeFilter, setTypeFilter] = useState<BrandAssetType | "all">("all");
  const [creating, setCreating] = useState<"upload" | "manual" | null>(null);
  const [editing, setEditing] = useState<BrandAsset | null>(null);

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const activeBrandId = brandFilter === "all" ? null : brandFilter;
  const activeType = typeFilter === "all" ? null : typeFilter;

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ["brand-assets", activeBrandId, activeType],
    queryFn: () => brandAssetsApi.list(activeBrandId, activeType),
  });

  const createManual = useMutation({
    mutationFn: (payload: BrandAssetCreate) => brandAssetsApi.create(payload),
    onSuccess: () => {
      toast.success("Asset qo'shildi");
      qc.invalidateQueries({ queryKey: ["brand-assets"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const upload = useMutation({
    mutationFn: (payload: {
      brandId: string;
      assetType: BrandAssetType;
      name: string;
      file: File;
      isPrimary: boolean;
    }) => brandAssetsApi.upload(payload),
    onSuccess: () => {
      toast.success("Fayl yuklandi");
      qc.invalidateQueries({ queryKey: ["brand-assets"] });
      setCreating(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: BrandAssetUpdate }) =>
      brandAssetsApi.update(id, payload),
    onSuccess: () => {
      toast.success("Asset saqlandi");
      qc.invalidateQueries({ queryKey: ["brand-assets"] });
      setEditing(null);
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => brandAssetsApi.remove(id),
    onSuccess: () => {
      toast.success("Asset o'chirildi");
      qc.invalidateQueries({ queryKey: ["brand-assets"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const primaryCount = assets.filter((asset) => asset.is_primary).length;
  const uploadCount = assets.filter((asset) => asset.file_url?.startsWith("data:")).length;

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
          { label: "Brand assets" },
        ]}
        title="Brand assets"
        description="Logo, rang, font, referens va tayyor media fayllarni brend bo'yicha boshqarish."
        actions={
          <Can permission="smm.write">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                onClick={() => setCreating("manual")}
                disabled={brands.length === 0}
              >
                <Plus /> URL yoki rang
              </Button>
              <Button onClick={() => setCreating("upload")} disabled={brands.length === 0}>
                <Upload /> Fayl yuklash
              </Button>
            </div>
          </Can>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatBox icon={ImageIcon} label="Jami asset" value={assets.length} />
        <StatBox icon={Star} label="Asosiylar" value={primaryCount} />
        <StatBox icon={Upload} label="Yuklangan fayllar" value={uploadCount} />
      </div>

      {brands.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title="Avval brend yarating"
          description="Assetlar brendga bog'lanadi. Brend yaratilgach logo, rang va referenslarni qo'shish mumkin."
        />
      ) : null}

      {creating === "upload" ? (
        <UploadAssetForm
          brands={brands}
          defaultBrandId={
            activeBrandId ?? brands.find((b) => b.is_default)?.id ?? brands[0]?.id
          }
          onCancel={() => setCreating(null)}
          onSubmit={(payload) => upload.mutate(payload)}
          loading={upload.isPending}
        />
      ) : null}

      {creating === "manual" ? (
        <ManualAssetForm
          brands={brands}
          defaultBrandId={
            activeBrandId ?? brands.find((b) => b.is_default)?.id ?? brands[0]?.id
          }
          onCancel={() => setCreating(null)}
          onSubmit={(payload) => createManual.mutate(payload)}
          loading={createManual.isPending}
        />
      ) : null}

      {editing ? (
        <ManualAssetForm
          brands={brands}
          initial={editing}
          defaultBrandId={editing.brand_id}
          onCancel={() => setEditing(null)}
          onSubmit={(payload) =>
            update.mutate({
              id: editing.id,
              payload: {
                asset_type: payload.asset_type,
                name: payload.name,
                file_url: payload.file_url,
                metadata: payload.metadata,
                is_primary: payload.is_primary,
              },
            })
          }
          loading={update.isPending}
        />
      ) : null}

      <FilterBar
        brands={brands}
        brandFilter={brandFilter}
        typeFilter={typeFilter}
        onBrandChange={setBrandFilter}
        onTypeChange={setTypeFilter}
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-56 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title="Assetlar topilmadi"
          description="Tanlangan filter bo'yicha logo, rang, media yoki referens hali qo'shilmagan."
          action={
            <Can permission="smm.write">
              <Button onClick={() => setCreating("upload")} disabled={brands.length === 0}>
                <Upload /> Fayl yuklash
              </Button>
            </Can>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {assets.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              brand={brands.find((brand) => brand.id === asset.brand_id)}
              onEdit={() => setEditing(asset)}
              onDelete={() => remove.mutate(asset.id)}
              onMakePrimary={() =>
                update.mutate({ id: asset.id, payload: { is_primary: true } })
              }
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function FilterBar({
  brands,
  brandFilter,
  typeFilter,
  onBrandChange,
  onTypeChange,
}: {
  brands: Brand[];
  brandFilter: string | "all";
  typeFilter: BrandAssetType | "all";
  onBrandChange: (value: string | "all") => void;
  onTypeChange: (value: BrandAssetType | "all") => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <FilterButton active={brandFilter === "all"} onClick={() => onBrandChange("all")}>
          Hamma brendlar
        </FilterButton>
        {brands.map((brand) => (
          <FilterButton
            key={brand.id}
            active={brandFilter === brand.id}
            onClick={() => onBrandChange(brand.id)}
          >
            {brand.name}
          </FilterButton>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <FilterButton active={typeFilter === "all"} onClick={() => onTypeChange("all")}>
          Hamma turlar
        </FilterButton>
        {ASSET_TYPES.map((type) => {
          const Icon = type.icon;
          return (
            <FilterButton
              key={type.key}
              active={typeFilter === type.key}
              onClick={() => onTypeChange(type.key)}
            >
              <Icon className="h-3.5 w-3.5" /> {type.label}
            </FilterButton>
          );
        })}
      </div>
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex h-8 items-center gap-1.5 rounded-md border px-3 text-[12px] font-medium transition-colors",
        active
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]"
          : "border-[var(--border)] bg-[var(--surface)] text-[var(--fg-muted)] hover:border-[var(--primary)] hover:text-[var(--fg)]",
      )}
    >
      {children}
    </button>
  );
}

function UploadAssetForm({
  brands,
  defaultBrandId,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string | undefined;
  onCancel: () => void;
  onSubmit: (payload: {
    brandId: string;
    assetType: BrandAssetType;
    name: string;
    file: File;
    isPrimary: boolean;
  }) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(defaultBrandId ?? "");
  const [assetType, setAssetType] = useState<BrandAssetType>("logo");
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isPrimary, setIsPrimary] = useState(true);
  const canSubmit = Boolean(brandId && assetType && name.trim() && file);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Fayl yuklash</CardTitle>
        <CloseButton onClick={onCancel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Brend" required>
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
            >
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Asset turi" required>
            <AssetTypeSelect value={assetType} onChange={setAssetType} />
          </FormField>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Nomi" required>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Asosiy logo"
            />
          </FormField>
          <FormField label="Fayl" required hint="PNG, JPG, SVG, PDF, MP4, WEBM, font">
            <Input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="pt-1.5"
            />
          </FormField>
        </div>
        <label className="flex items-center gap-2 text-[13px] text-[var(--fg)]">
          <input
            type="checkbox"
            checked={isPrimary}
            onChange={(e) => setIsPrimary(e.target.checked)}
            className="h-4 w-4 accent-[var(--primary)]"
          />
          Shu tur uchun asosiy asset qilish
        </label>
        <FormActions
          onCancel={onCancel}
          onSubmit={() =>
            file &&
            onSubmit({
              brandId,
              assetType,
              name: name.trim(),
              file,
              isPrimary,
            })
          }
          loading={loading}
          disabled={!canSubmit}
          submitLabel="Yuklash"
        />
      </CardContent>
    </Card>
  );
}

function ManualAssetForm({
  brands,
  defaultBrandId,
  initial,
  onCancel,
  onSubmit,
  loading,
}: {
  brands: Brand[];
  defaultBrandId: string | undefined;
  initial?: BrandAsset;
  onCancel: () => void;
  onSubmit: (payload: BrandAssetCreate) => void;
  loading: boolean;
}) {
  const [brandId, setBrandId] = useState(initial?.brand_id ?? defaultBrandId ?? "");
  const [assetType, setAssetType] = useState<BrandAssetType>(
    (initial?.asset_type as BrandAssetType | undefined) ?? "color",
  );
  const [name, setName] = useState(initial?.name ?? "");
  const [url, setUrl] = useState(
    initial?.file_url && !initial.file_url.startsWith("data:") ? initial.file_url : "",
  );
  const [hex, setHex] = useState(asString(initial?.metadata?.hex) || "#16a34a");
  const [notes, setNotes] = useState(asString(initial?.metadata?.notes));
  const [isPrimary, setIsPrimary] = useState(initial?.is_primary ?? false);
  const canSubmit = Boolean(brandId && assetType && name.trim());

  const buildMetadata = (): Record<string, unknown> | null => {
    const metadata: Record<string, unknown> = { ...(initial?.metadata ?? {}) };
    if (assetType === "color" && hex) {
      metadata.hex = hex;
    } else {
      delete metadata.hex;
    }
    if (notes.trim()) {
      metadata.notes = notes.trim();
    } else {
      delete metadata.notes;
    }
    return Object.keys(metadata).length > 0 ? metadata : null;
  };

  const preservedDataUrl = initial?.file_url?.startsWith("data:") ? initial.file_url : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{initial ? "Assetni tahrirlash" : "URL yoki rang qo'shish"}</CardTitle>
        <CloseButton onClick={onCancel} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Brend" required>
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
              disabled={Boolean(initial)}
              className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none disabled:opacity-60"
            >
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Asset turi" required>
            <AssetTypeSelect value={assetType} onChange={setAssetType} />
          </FormField>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Nomi" required>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Brend rang palitrasi"
            />
          </FormField>
          {assetType === "color" ? (
            <FormField label="Rang (HEX)">
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={hex || "#16a34a"}
                  onChange={(e) => setHex(e.target.value)}
                  className="h-9 w-12 cursor-pointer rounded-md border border-[var(--border)] bg-[var(--surface)]"
                />
                <Input value={hex} onChange={(e) => setHex(e.target.value)} />
              </div>
            </FormField>
          ) : (
            <FormField label="URL" hint="Tashqi media, Figma, Canva yoki referens havolasi">
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
              />
            </FormField>
          )}
        </div>
        <FormField label="Izoh">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Qayerda ishlatiladi, o'lcham yoki uslub eslatmasi..."
            className="flex min-h-[96px] w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
          />
        </FormField>
        <label className="flex items-center gap-2 text-[13px] text-[var(--fg)]">
          <input
            type="checkbox"
            checked={isPrimary}
            onChange={(e) => setIsPrimary(e.target.checked)}
            className="h-4 w-4 accent-[var(--primary)]"
          />
          Shu tur uchun asosiy asset qilish
        </label>
        <FormActions
          onCancel={onCancel}
          onSubmit={() =>
            onSubmit({
              brand_id: brandId,
              asset_type: assetType,
              name: name.trim(),
              file_url:
                assetType === "color" ? preservedDataUrl : url.trim() || preservedDataUrl,
              metadata: buildMetadata(),
              is_primary: isPrimary,
            })
          }
          loading={loading}
          disabled={!canSubmit}
          submitLabel={initial ? "Saqlash" : "Qo'shish"}
        />
      </CardContent>
    </Card>
  );
}

function AssetTypeSelect({
  value,
  onChange,
}: {
  value: BrandAssetType;
  onChange: (value: BrandAssetType) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as BrandAssetType)}
      className="h-9 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--fg)] shadow-[var(--shadow-xs)] focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
    >
      {ASSET_TYPES.map((type) => (
        <option key={type.key} value={type.key}>
          {type.label}
        </option>
      ))}
    </select>
  );
}

function AssetCard({
  asset,
  brand,
  onEdit,
  onDelete,
  onMakePrimary,
}: {
  asset: BrandAsset;
  brand: Brand | undefined;
  onEdit: () => void;
  onDelete: () => void;
  onMakePrimary: () => void;
}) {
  return (
    <Card className="group overflow-hidden p-0 transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]">
      <AssetPreview asset={asset} />
      <div className="space-y-4 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <p className="truncate text-[15px] font-semibold text-[var(--fg)]">
                {asset.name}
              </p>
              {asset.is_primary ? (
                <Badge variant="primary">
                  <Star className="h-2.5 w-2.5" /> Asosiy
                </Badge>
              ) : null}
            </div>
            <p className="mt-1 truncate text-[12px] text-[var(--fg-subtle)]">
              {brand?.name ?? "Brend"} · {TYPE_LABELS[asset.asset_type] ?? asset.asset_type}
            </p>
          </div>
          <Badge variant="outline">{formatBytes(asset.file_size)}</Badge>
        </div>

        {asString(asset.metadata?.notes) ? (
          <p className="line-clamp-2 text-[12px] leading-relaxed text-[var(--fg-muted)]">
            {asString(asset.metadata?.notes)}
          </p>
        ) : null}

        <Can permission="smm.write">
          <div className="flex items-center justify-between gap-2 border-t border-[var(--border)] pt-3">
            <div className="flex items-center gap-1">
              <Button size="icon-sm" variant="ghost" aria-label="Tahrirlash" onClick={onEdit}>
                <PenSquare />
              </Button>
              <Button
                size="icon-sm"
                variant="ghost"
                aria-label="Asosiy qilish"
                disabled={asset.is_primary}
                onClick={onMakePrimary}
              >
                <Star />
              </Button>
            </div>
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="O'chirish"
              onClick={onDelete}
              className="text-[var(--danger)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
            >
              <Trash2 />
            </Button>
          </div>
        </Can>
      </div>
    </Card>
  );
}

function AssetPreview({ asset }: { asset: BrandAsset }) {
  const hex = asString(asset.metadata?.hex);
  const icon = ASSET_TYPES.find((type) => type.key === asset.asset_type)?.icon ?? ImageIcon;
  const Icon = icon;
  const isImage =
    asset.content_type?.startsWith("image/") ||
    asset.file_url?.startsWith("data:image/") ||
    /\.(png|jpe?g|webp|gif|svg)$/i.test(asset.file_url ?? "");
  const isVideo =
    asset.content_type?.startsWith("video/") ||
    asset.file_url?.startsWith("data:video/") ||
    /\.(mp4|webm)$/i.test(asset.file_url ?? "");

  if (asset.asset_type === "color" && hex) {
    return (
      <div className="flex aspect-[16/9] items-center justify-center bg-[var(--bg-subtle)]">
        <div
          className="h-24 w-24 rounded-xl border border-[var(--border)] shadow-[var(--shadow-sm)]"
          style={{ backgroundColor: hex }}
        />
      </div>
    );
  }

  if (asset.file_url && isImage) {
    return (
      <div
        className="aspect-[16/9] bg-[var(--bg-subtle)] bg-contain bg-center bg-no-repeat"
        style={{ backgroundImage: `url("${asset.file_url}")` }}
      />
    );
  }

  if (asset.file_url && isVideo) {
    return (
      <div className="flex aspect-[16/9] items-center justify-center bg-black text-white">
        <Video className="h-10 w-10" />
      </div>
    );
  }

  return (
    <div className="flex aspect-[16/9] items-center justify-center bg-[var(--bg-subtle)] text-[var(--fg-subtle)]">
      <Icon className="h-10 w-10" />
    </div>
  );
}

function StatBox({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow-xs)]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold tracking-wide text-[var(--fg-subtle)] uppercase">
            {label}
          </p>
          <p className="mt-1 text-2xl font-semibold tracking-tight text-[var(--fg)]">
            {value}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function FormActions({
  onCancel,
  onSubmit,
  loading,
  disabled,
  submitLabel,
}: {
  onCancel: () => void;
  onSubmit: () => void;
  loading: boolean;
  disabled: boolean;
  submitLabel: string;
}) {
  return (
    <div className="flex items-center justify-end gap-2 border-t border-[var(--border)] pt-4">
      <Button variant="ghost" onClick={onCancel}>
        Bekor qilish
      </Button>
      <Button onClick={onSubmit} loading={loading} disabled={disabled}>
        {submitLabel}
      </Button>
    </div>
  );
}

function CloseButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Yopish"
      className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--fg-subtle)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
    >
      <X className="h-4 w-4" />
    </button>
  );
}

function formatBytes(bytes: number): string {
  if (!bytes) return "URL";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

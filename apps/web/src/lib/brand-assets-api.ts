import { apiClient } from "./api-client";
import type { BrandAsset, BrandAssetCreate, BrandAssetType, BrandAssetUpdate } from "./types";

export const brandAssetsApi = {
  async list(
    brandId?: string | null,
    assetType?: BrandAssetType | string | null,
  ): Promise<BrandAsset[]> {
    const { data } = await apiClient.get<BrandAsset[]>("/brand-assets", {
      params: {
        ...(brandId ? { brand_id: brandId } : {}),
        ...(assetType ? { asset_type: assetType } : {}),
      },
    });
    return data;
  },
  async create(payload: BrandAssetCreate): Promise<BrandAsset> {
    const { data } = await apiClient.post<BrandAsset>("/brand-assets", payload);
    return data;
  },
  async upload(args: {
    brandId: string;
    assetType: BrandAssetType | string;
    name: string;
    file: File;
    isPrimary?: boolean;
  }): Promise<BrandAsset> {
    const form = new FormData();
    form.append("brand_id", args.brandId);
    form.append("asset_type", args.assetType);
    form.append("name", args.name);
    form.append("is_primary", String(args.isPrimary ?? false));
    form.append("file", args.file);
    const { data } = await apiClient.post<BrandAsset>("/brand-assets/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  async update(id: string, payload: BrandAssetUpdate): Promise<BrandAsset> {
    const { data } = await apiClient.patch<BrandAsset>(`/brand-assets/${id}`, payload);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/brand-assets/${id}`);
  },
};

import { apiClient } from "./api-client";
import type {
  ContentPlanCreatePostRequest,
  ContentPlanImportResult,
  ContentPlanImportTextRequest,
  ContentPlanItem,
  ContentPlanItemCreate,
  ContentPlanItemUpdate,
  PostDetail,
} from "./types";

export const contentPlanApi = {
  async list(params?: {
    brand_id?: string | null;
    platform?: string | null;
    status?: string | null;
    start?: string | null;
    end?: string | null;
    limit?: number;
  }): Promise<ContentPlanItem[]> {
    const query: Record<string, string | number> = {};
    if (params?.brand_id) query.brand_id = params.brand_id;
    if (params?.platform) query.platform = params.platform;
    if (params?.status) query.status = params.status;
    if (params?.start) query.start = params.start;
    if (params?.end) query.end = params.end;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<ContentPlanItem[]>("/content-plan", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async create(payload: ContentPlanItemCreate): Promise<ContentPlanItem> {
    const { data } = await apiClient.post<ContentPlanItem>("/content-plan", payload);
    return data;
  },
  async update(id: string, payload: ContentPlanItemUpdate): Promise<ContentPlanItem> {
    const { data } = await apiClient.patch<ContentPlanItem>(`/content-plan/${id}`, payload);
    return data;
  },
  async importText(payload: ContentPlanImportTextRequest): Promise<ContentPlanImportResult> {
    const { data } = await apiClient.post<ContentPlanImportResult>(
      "/content-plan/import-text",
      payload,
    );
    return data;
  },
  async createPost(id: string, payload: ContentPlanCreatePostRequest): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(
      `/content-plan/${id}/create-post`,
      payload,
    );
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/content-plan/${id}`);
  },
};

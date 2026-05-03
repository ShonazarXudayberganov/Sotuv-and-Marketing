import { apiClient } from "./api-client";
import type { AIUsage, ContentDraft, ContentStats, GeneratePostRequest } from "./types";

export const aiApi = {
  async generatePost(payload: GeneratePostRequest): Promise<ContentDraft> {
    const { data } = await apiClient.post<ContentDraft>("/ai/generate-post", payload);
    return data;
  },
  async listDrafts(params?: {
    brand_id?: string | null;
    platform?: string | null;
    starred?: boolean | null;
    limit?: number;
  }): Promise<ContentDraft[]> {
    const query: Record<string, string | number | boolean> = {};
    if (params?.brand_id) query.brand_id = params.brand_id;
    if (params?.platform) query.platform = params.platform;
    if (params?.starred != null) query.starred = params.starred;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<ContentDraft[]>("/ai/drafts", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async getDraft(id: string): Promise<ContentDraft> {
    const { data } = await apiClient.get<ContentDraft>(`/ai/drafts/${id}`);
    return data;
  },
  async updateDraft(
    id: string,
    payload: { title?: string | null; body?: string | null },
  ): Promise<ContentDraft> {
    const { data } = await apiClient.patch<ContentDraft>(`/ai/drafts/${id}`, payload);
    return data;
  },
  async toggleStar(id: string): Promise<ContentDraft> {
    const { data } = await apiClient.post<ContentDraft>(`/ai/drafts/${id}/star`);
    return data;
  },
  async deleteDraft(id: string): Promise<void> {
    await apiClient.delete(`/ai/drafts/${id}`);
  },
  async usage(): Promise<AIUsage> {
    const { data } = await apiClient.get<AIUsage>("/ai/usage");
    return data;
  },
  async stats(): Promise<ContentStats> {
    const { data } = await apiClient.get<ContentStats>("/ai/stats");
    return data;
  },
};

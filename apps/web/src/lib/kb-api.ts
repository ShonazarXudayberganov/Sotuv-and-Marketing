import { apiClient } from "./api-client";
import type {
  KnowledgeDocument,
  KnowledgeSearchResponse,
  KnowledgeStats,
  TextDocumentCreate,
} from "./types";

export const knowledgeApi = {
  async list(brandId?: string | null): Promise<KnowledgeDocument[]> {
    const { data } = await apiClient.get<KnowledgeDocument[]>("/knowledge/documents", {
      params: brandId ? { brand_id: brandId } : undefined,
    });
    return data;
  },
  async stats(brandId?: string | null): Promise<KnowledgeStats> {
    const { data } = await apiClient.get<KnowledgeStats>("/knowledge/stats", {
      params: brandId ? { brand_id: brandId } : undefined,
    });
    return data;
  },
  async createText(payload: TextDocumentCreate): Promise<KnowledgeDocument> {
    const { data } = await apiClient.post<KnowledgeDocument>(
      "/knowledge/documents/text",
      payload,
    );
    return data;
  },
  async uploadFile(brandId: string, title: string, file: File): Promise<KnowledgeDocument> {
    const form = new FormData();
    form.append("brand_id", brandId);
    form.append("title", title);
    form.append("file", file);
    const { data } = await apiClient.post<KnowledgeDocument>(
      "/knowledge/documents/file",
      form,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/knowledge/documents/${id}`);
  },
  async search(
    query: string,
    brandId?: string | null,
    topK = 5,
  ): Promise<KnowledgeSearchResponse> {
    const { data } = await apiClient.post<KnowledgeSearchResponse>("/knowledge/search", {
      query,
      brand_id: brandId ?? null,
      top_k: topK,
    });
    return data;
  },
};

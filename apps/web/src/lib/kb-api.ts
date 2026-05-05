import { apiClient } from "./api-client";
import type {
  AIChatImportPayload,
  InstagramImportPayload,
  KnowledgeDocument,
  KnowledgeSearchResponse,
  KnowledgeSection,
  KnowledgeStats,
  TextDocumentCreate,
  WebsiteImportPayload,
} from "./types";

export const knowledgeApi = {
  async list(brandId?: string | null, section?: string | null): Promise<KnowledgeDocument[]> {
    const { data } = await apiClient.get<KnowledgeDocument[]>("/knowledge/documents", {
      params: {
        ...(brandId ? { brand_id: brandId } : {}),
        ...(section ? { section } : {}),
      },
    });
    return data;
  },
  async stats(brandId?: string | null): Promise<KnowledgeStats> {
    const { data } = await apiClient.get<KnowledgeStats>("/knowledge/stats", {
      params: brandId ? { brand_id: brandId } : undefined,
    });
    return data;
  },
  async sections(brandId?: string | null): Promise<KnowledgeSection[]> {
    const { data } = await apiClient.get<KnowledgeSection[]>("/knowledge/sections", {
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
  async importWebsite(payload: WebsiteImportPayload): Promise<KnowledgeDocument> {
    const { data } = await apiClient.post<KnowledgeDocument>(
      "/knowledge/import/website",
      payload,
    );
    return data;
  },
  async importInstagram(payload: InstagramImportPayload): Promise<KnowledgeDocument> {
    const { data } = await apiClient.post<KnowledgeDocument>(
      "/knowledge/import/instagram",
      payload,
    );
    return data;
  },
  async importAIChat(payload: AIChatImportPayload): Promise<KnowledgeDocument> {
    const { data } = await apiClient.post<KnowledgeDocument>(
      "/knowledge/import/ai-chat",
      payload,
    );
    return data;
  },
  async uploadFile(
    brandId: string,
    title: string,
    section: string,
    file: File,
  ): Promise<KnowledgeDocument> {
    const form = new FormData();
    form.append("brand_id", brandId);
    form.append("title", title);
    form.append("section", section);
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

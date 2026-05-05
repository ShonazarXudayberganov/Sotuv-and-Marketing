import { apiClient } from "./api-client";
import type {
  CalendarResponse,
  Post,
  PostApproveRequest,
  PostCreateRequest,
  PostDetail,
  PostRejectRequest,
  PostReviewRequest,
  PostStats,
} from "./types";

export const postsApi = {
  async list(params?: {
    brand_id?: string | null;
    status?: string | null;
    limit?: number;
  }): Promise<Post[]> {
    const query: Record<string, string | number> = {};
    if (params?.brand_id) query.brand_id = params.brand_id;
    if (params?.status) query.status = params.status;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<Post[]>("/posts", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async stats(brandId?: string | null): Promise<PostStats> {
    const { data } = await apiClient.get<PostStats>("/posts/stats", {
      params: brandId ? { brand_id: brandId } : undefined,
    });
    return data;
  },
  async get(id: string): Promise<PostDetail> {
    const { data } = await apiClient.get<PostDetail>(`/posts/${id}`);
    return data;
  },
  async create(payload: PostCreateRequest): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>("/posts", payload);
    return data;
  },
  async reschedule(id: string, scheduledAt: string | null): Promise<PostDetail> {
    const { data } = await apiClient.patch<PostDetail>(`/posts/${id}`, {
      scheduled_at: scheduledAt,
    });
    return data;
  },
  async cancel(id: string): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/cancel`);
    return data;
  },
  async retry(id: string): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/retry`);
    return data;
  },
  async submitReview(id: string, payload: PostReviewRequest = {}): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/submit-review`, payload);
    return data;
  },
  async approve(id: string, payload: PostApproveRequest = {}): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/approve`, payload);
    return data;
  },
  async reject(id: string, payload: PostRejectRequest): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/reject`, payload);
    return data;
  },
  async publishNow(id: string): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/publish-now`);
    return data;
  },
  async syncStatus(id: string): Promise<PostDetail> {
    const { data } = await apiClient.post<PostDetail>(`/posts/${id}/sync-status`);
    return data;
  },
  async calendar(
    start: string,
    end: string,
    brandId?: string | null,
  ): Promise<CalendarResponse> {
    const params: Record<string, string> = { start, end };
    if (brandId) params.brand_id = brandId;
    const { data } = await apiClient.get<CalendarResponse>("/posts/calendar", { params });
    return data;
  },
};

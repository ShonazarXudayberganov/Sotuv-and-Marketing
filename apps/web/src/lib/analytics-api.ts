import { apiClient } from "./api-client";
import type {
  AnalyticsInsights,
  AnalyticsOverview,
  AnalyticsTimePoint,
  OptimalTimes,
  TopPost,
} from "./types";

function buildParams(brandId?: string | null): Record<string, string> | undefined {
  if (!brandId) return undefined;
  return { brand_id: brandId };
}

export const analyticsApi = {
  async overview(brandId?: string | null): Promise<AnalyticsOverview> {
    const { data } = await apiClient.get<AnalyticsOverview>("/analytics/overview", {
      params: buildParams(brandId),
    });
    return data;
  },
  async timeseries(brandId?: string | null, days = 30): Promise<AnalyticsTimePoint[]> {
    const params: Record<string, string | number> = { days };
    if (brandId) params.brand_id = brandId;
    const { data } = await apiClient.get<AnalyticsTimePoint[]>("/analytics/timeseries", {
      params,
    });
    return data;
  },
  async topPosts(brandId?: string | null, limit = 5): Promise<TopPost[]> {
    const params: Record<string, string | number> = { limit };
    if (brandId) params.brand_id = brandId;
    const { data } = await apiClient.get<TopPost[]>("/analytics/top-posts", {
      params,
    });
    return data;
  },
  async optimalTimes(brandId?: string | null): Promise<OptimalTimes> {
    const { data } = await apiClient.get<OptimalTimes>("/analytics/optimal-times", {
      params: buildParams(brandId),
    });
    return data;
  },
  async insights(brandId?: string | null): Promise<AnalyticsInsights> {
    const { data } = await apiClient.get<AnalyticsInsights>("/analytics/insights", {
      params: buildParams(brandId),
    });
    return data;
  },
  async snapshot(brandId?: string | null): Promise<{ inserted: number }> {
    const { data } = await apiClient.post<{ inserted: number }>("/analytics/snapshot", null, {
      params: buildParams(brandId),
    });
    return data;
  },
};

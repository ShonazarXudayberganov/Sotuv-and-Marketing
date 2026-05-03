import { apiClient } from "./api-client";
import type {
  AdAccount,
  AdsInsights,
  AdsOverview,
  AdsTimePoint,
  Campaign,
  CampaignDraftRequest,
} from "./types";

export const adsApi = {
  async listAccounts(network?: string): Promise<AdAccount[]> {
    const { data } = await apiClient.get<AdAccount[]>("/ads/accounts", {
      params: network ? { network } : undefined,
    });
    return data;
  },
  async syncAccountsMock(): Promise<{ inserted: number }> {
    const { data } = await apiClient.post<{ inserted: number }>("/ads/accounts/sync-mock");
    return data;
  },
  async syncCampaignsMock(): Promise<{ inserted: number }> {
    const { data } = await apiClient.post<{ inserted: number }>("/ads/campaigns/sync-mock");
    return data;
  },
  async snapshot(): Promise<{ inserted: number }> {
    const { data } = await apiClient.post<{ inserted: number }>("/ads/snapshot");
    return data;
  },
  async listCampaigns(params?: {
    account_id?: string;
    network?: string;
    status?: string;
    limit?: number;
  }): Promise<Campaign[]> {
    const query: Record<string, string | number> = {};
    if (params?.account_id) query.account_id = params.account_id;
    if (params?.network) query.network = params.network;
    if (params?.status) query.status = params.status;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<Campaign[]>("/ads/campaigns", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async getCampaign(id: string): Promise<Campaign> {
    const { data } = await apiClient.get<Campaign>(`/ads/campaigns/${id}`);
    return data;
  },
  async createDraft(payload: CampaignDraftRequest): Promise<Campaign> {
    const { data } = await apiClient.post<Campaign>("/ads/campaigns", payload);
    return data;
  },
  async updateCampaign(
    id: string,
    payload: Partial<CampaignDraftRequest> & {
      status?: string;
      daily_budget?: number;
    },
  ): Promise<Campaign> {
    const { data } = await apiClient.patch<Campaign>(`/ads/campaigns/${id}`, payload);
    return data;
  },
  async deleteCampaign(id: string): Promise<void> {
    await apiClient.delete(`/ads/campaigns/${id}`);
  },
  async overview(network?: string): Promise<AdsOverview> {
    const { data } = await apiClient.get<AdsOverview>("/ads/overview", {
      params: network ? { network } : undefined,
    });
    return data;
  },
  async timeseries(days = 14): Promise<AdsTimePoint[]> {
    const { data } = await apiClient.get<AdsTimePoint[]>("/ads/timeseries", {
      params: { days },
    });
    return data;
  },
  async insights(): Promise<AdsInsights> {
    const { data } = await apiClient.get<AdsInsights>("/ads/insights");
    return data;
  },
};

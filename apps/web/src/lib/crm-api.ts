import { apiClient } from "./api-client";
import type {
  ActivityCreateRequest,
  Contact,
  ContactActivity,
  ContactCreateRequest,
  ContactStats,
  Deal,
  DealCreateRequest,
  DealForecast,
  DealStats,
  Pipeline,
} from "./types";

export const crmApi = {
  async list(params?: {
    query?: string;
    status?: string;
    min_score?: number;
    limit?: number;
    offset?: number;
  }): Promise<Contact[]> {
    const query: Record<string, string | number> = {};
    if (params?.query) query.query = params.query;
    if (params?.status) query.status = params.status;
    if (params?.min_score != null) query.min_score = params.min_score;
    if (params?.limit) query.limit = params.limit;
    if (params?.offset) query.offset = params.offset;
    const { data } = await apiClient.get<Contact[]>("/crm/contacts", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async stats(): Promise<ContactStats> {
    const { data } = await apiClient.get<ContactStats>("/crm/contacts/stats");
    return data;
  },
  async get(id: string): Promise<Contact> {
    const { data } = await apiClient.get<Contact>(`/crm/contacts/${id}`);
    return data;
  },
  async create(payload: ContactCreateRequest): Promise<Contact> {
    const { data } = await apiClient.post<Contact>("/crm/contacts", payload);
    return data;
  },
  async update(id: string, payload: Partial<ContactCreateRequest>): Promise<Contact> {
    const { data } = await apiClient.patch<Contact>(`/crm/contacts/${id}`, payload);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/crm/contacts/${id}`);
  },
  async listActivities(id: string, limit = 50): Promise<ContactActivity[]> {
    const { data } = await apiClient.get<ContactActivity[]>(
      `/crm/contacts/${id}/activities`,
      { params: { limit } },
    );
    return data;
  },
  async addActivity(
    id: string,
    payload: ActivityCreateRequest,
  ): Promise<ContactActivity> {
    const { data } = await apiClient.post<ContactActivity>(
      `/crm/contacts/${id}/activities`,
      payload,
    );
    return data;
  },
  async rescore(id: string): Promise<{ score: number; reason: string }> {
    const { data } = await apiClient.post<{ score: number; reason: string }>(
      `/crm/contacts/${id}/rescore`,
    );
    return data;
  },
  async contactDeals(id: string): Promise<Deal[]> {
    const { data } = await apiClient.get<Deal[]>(`/crm/contacts/${id}/deals`);
    return data;
  },

  // Deals + Pipelines
  async listPipelines(): Promise<Pipeline[]> {
    const { data } = await apiClient.get<Pipeline[]>("/crm/pipelines");
    return data;
  },
  async listDeals(params?: {
    pipeline_id?: string | null;
    status?: string | null;
    contact_id?: string | null;
    limit?: number;
  }): Promise<Deal[]> {
    const query: Record<string, string | number> = {};
    if (params?.pipeline_id) query.pipeline_id = params.pipeline_id;
    if (params?.status) query.status = params.status;
    if (params?.contact_id) query.contact_id = params.contact_id;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<Deal[]>("/crm/deals", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async getDeal(id: string): Promise<Deal> {
    const { data } = await apiClient.get<Deal>(`/crm/deals/${id}`);
    return data;
  },
  async createDeal(payload: DealCreateRequest): Promise<Deal> {
    const { data } = await apiClient.post<Deal>("/crm/deals", payload);
    return data;
  },
  async updateDeal(id: string, payload: Partial<DealCreateRequest> & {
    stage_id?: string;
    probability?: number;
  }): Promise<Deal> {
    const { data } = await apiClient.patch<Deal>(`/crm/deals/${id}`, payload);
    return data;
  },
  async winDeal(id: string): Promise<Deal> {
    const { data } = await apiClient.post<Deal>(`/crm/deals/${id}/win`);
    return data;
  },
  async loseDeal(id: string): Promise<Deal> {
    const { data } = await apiClient.post<Deal>(`/crm/deals/${id}/lose`);
    return data;
  },
  async deleteDeal(id: string): Promise<void> {
    await apiClient.delete(`/crm/deals/${id}`);
  },
  async forecast(pipelineId?: string | null): Promise<DealForecast> {
    const { data } = await apiClient.get<DealForecast>("/crm/deals/forecast", {
      params: pipelineId ? { pipeline_id: pipelineId } : undefined,
    });
    return data;
  },
  async dealStats(): Promise<DealStats> {
    const { data } = await apiClient.get<DealStats>("/crm/deals/stats");
    return data;
  },
};

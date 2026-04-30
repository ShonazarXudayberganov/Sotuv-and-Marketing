import { apiClient } from "./api-client";
import type { Brand, BrandCreate, IntegrationConnect, IntegrationProvider } from "./types";

export const brandsApi = {
  async list(): Promise<Brand[]> {
    const { data } = await apiClient.get<Brand[]>("/brands");
    return data;
  },
  async get(id: string): Promise<Brand> {
    const { data } = await apiClient.get<Brand>(`/brands/${id}`);
    return data;
  },
  async create(payload: BrandCreate): Promise<Brand> {
    const { data } = await apiClient.post<Brand>("/brands", payload);
    return data;
  },
  async update(id: string, payload: Partial<BrandCreate>): Promise<Brand> {
    const { data } = await apiClient.patch<Brand>(`/brands/${id}`, payload);
    return data;
  },
  async setDefault(id: string): Promise<Brand> {
    const { data } = await apiClient.post<Brand>(`/brands/${id}/set-default`);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/brands/${id}`);
  },
};

export const integrationsApi = {
  async list(): Promise<IntegrationProvider[]> {
    const { data } = await apiClient.get<IntegrationProvider[]>("/integrations");
    return data;
  },
  async connect(provider: string, payload: IntegrationConnect): Promise<IntegrationProvider> {
    const { data } = await apiClient.put<IntegrationProvider>(
      `/integrations/${provider}`,
      payload,
    );
    return data;
  },
  async disconnect(provider: string): Promise<void> {
    await apiClient.delete(`/integrations/${provider}`);
  },
};

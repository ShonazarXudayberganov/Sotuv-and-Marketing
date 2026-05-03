import { apiClient } from "./api-client";
import type {
  MarketplaceProvider,
  WebhookDelivery,
  WebhookEndpoint,
  WebhookEndpointWithSecret,
} from "./types";

export const marketplaceApi = {
  async catalog(): Promise<MarketplaceProvider[]> {
    const { data } = await apiClient.get<MarketplaceProvider[]>(
      "/marketplace/catalog",
    );
    return data;
  },
  async listWebhooks(direction?: "in" | "out"): Promise<WebhookEndpoint[]> {
    const { data } = await apiClient.get<WebhookEndpoint[]>(
      "/marketplace/webhooks",
      { params: direction ? { direction } : undefined },
    );
    return data;
  },
  async createWebhook(payload: {
    name: string;
    direction: "in" | "out";
    url?: string | null;
    events?: string[] | null;
  }): Promise<WebhookEndpointWithSecret> {
    const { data } = await apiClient.post<WebhookEndpointWithSecret>(
      "/marketplace/webhooks",
      payload,
    );
    return data;
  },
  async rotateSecret(id: string): Promise<WebhookEndpointWithSecret> {
    const { data } = await apiClient.post<WebhookEndpointWithSecret>(
      `/marketplace/webhooks/${id}/rotate-secret`,
    );
    return data;
  },
  async toggleWebhook(id: string, active: boolean): Promise<WebhookEndpoint> {
    const { data } = await apiClient.post<WebhookEndpoint>(
      `/marketplace/webhooks/${id}/toggle`,
      null,
      { params: { active } },
    );
    return data;
  },
  async testWebhook(
    id: string,
    payload: { event?: string; payload?: Record<string, unknown> },
  ): Promise<WebhookDelivery> {
    const { data } = await apiClient.post<WebhookDelivery>(
      `/marketplace/webhooks/${id}/test`,
      { event: payload.event ?? "deal.won", payload: payload.payload ?? {} },
    );
    return data;
  },
  async deleteWebhook(id: string): Promise<void> {
    await apiClient.delete(`/marketplace/webhooks/${id}`);
  },
  async deliveries(id: string, limit = 50): Promise<WebhookDelivery[]> {
    const { data } = await apiClient.get<WebhookDelivery[]>(
      `/marketplace/webhooks/${id}/deliveries`,
      { params: { limit } },
    );
    return data;
  },
  async sync(provider: string): Promise<{
    provider: string;
    direction: string;
    pulled: number;
    pushed: number;
    errors: string[];
    mocked: boolean;
  }> {
    const { data } = await apiClient.post(`/marketplace/sync/${provider}`);
    return data;
  },
};

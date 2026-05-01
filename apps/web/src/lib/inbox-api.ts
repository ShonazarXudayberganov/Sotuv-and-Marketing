import { apiClient } from "./api-client";
import type {
  AutoReplyConfig,
  AutoReplyDraft,
  Conversation,
  InboxMessage,
  InboxStats,
} from "./types";

export const inboxApi = {
  async listConversations(params?: {
    status?: string | null;
    channel?: string | null;
    limit?: number;
  }): Promise<Conversation[]> {
    const query: Record<string, string | number> = {};
    if (params?.status) query.status = params.status;
    if (params?.channel) query.channel = params.channel;
    if (params?.limit) query.limit = params.limit;
    const { data } = await apiClient.get<Conversation[]>("/inbox/conversations", {
      params: Object.keys(query).length ? query : undefined,
    });
    return data;
  },
  async getConversation(id: string): Promise<Conversation> {
    const { data } = await apiClient.get<Conversation>(`/inbox/conversations/${id}`);
    return data;
  },
  async listMessages(id: string, limit = 100): Promise<InboxMessage[]> {
    const { data } = await apiClient.get<InboxMessage[]>(
      `/inbox/conversations/${id}/messages`,
      { params: { limit } },
    );
    return data;
  },
  async sendMessage(id: string, body: string): Promise<InboxMessage> {
    const { data } = await apiClient.post<InboxMessage>(
      `/inbox/conversations/${id}/messages`,
      { body },
    );
    return data;
  },
  async markRead(id: string): Promise<Conversation> {
    const { data } = await apiClient.post<Conversation>(
      `/inbox/conversations/${id}/read`,
    );
    return data;
  },
  async setStatus(id: string, status: string): Promise<Conversation> {
    const { data } = await apiClient.post<Conversation>(
      `/inbox/conversations/${id}/status`,
      { status },
    );
    return data;
  },
  async draftReply(id: string): Promise<AutoReplyDraft> {
    const { data } = await apiClient.post<AutoReplyDraft>(
      `/inbox/conversations/${id}/draft-reply`,
    );
    return data;
  },
  async stats(): Promise<InboxStats> {
    const { data } = await apiClient.get<InboxStats>("/inbox/stats");
    return data;
  },
  async seedMock(): Promise<{ inserted: number }> {
    const { data } = await apiClient.post<{ inserted: number }>(
      "/inbox/seed-mock",
    );
    return data;
  },
  async getAutoReply(): Promise<AutoReplyConfig> {
    const { data } = await apiClient.get<AutoReplyConfig>("/inbox/auto-reply");
    return data;
  },
  async updateAutoReply(payload: Partial<AutoReplyConfig>): Promise<AutoReplyConfig> {
    const { data } = await apiClient.patch<AutoReplyConfig>(
      "/inbox/auto-reply",
      payload,
    );
    return data;
  },
};

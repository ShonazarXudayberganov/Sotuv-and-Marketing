import { apiClient } from "./api-client";
import type {
  MetaPageOption,
  MetaSendResult,
  SocialAccount,
  TelegramBotInfo,
  TelegramSendResult,
  YouTubeChannelInfo,
  YouTubeStats,
} from "./types";

export const socialApi = {
  async listAccounts(brandId?: string | null, provider?: string): Promise<SocialAccount[]> {
    const params: Record<string, string> = {};
    if (brandId) params.brand_id = brandId;
    if (provider) params.provider = provider;
    const { data } = await apiClient.get<SocialAccount[]>("/social/accounts", {
      params: Object.keys(params).length ? params : undefined,
    });
    return data;
  },
  async removeAccount(id: string): Promise<void> {
    await apiClient.delete(`/social/accounts/${id}`);
  },
  async telegramBotInfo(): Promise<TelegramBotInfo> {
    const { data } = await apiClient.get<TelegramBotInfo>("/social/telegram/bot-info");
    return data;
  },
  async telegramLink(brandId: string, chat: string): Promise<SocialAccount> {
    const { data } = await apiClient.post<SocialAccount>("/social/telegram/link", {
      brand_id: brandId,
      chat,
    });
    return data;
  },
  async telegramTest(accountId: string, text: string): Promise<TelegramSendResult> {
    const { data } = await apiClient.post<TelegramSendResult>("/social/telegram/test", {
      account_id: accountId,
      text,
    });
    return data;
  },
  async metaListPages(): Promise<MetaPageOption[]> {
    const { data } = await apiClient.get<MetaPageOption[]>("/social/meta/pages");
    return data;
  },
  async metaLink(
    brandId: string,
    pageId: string,
    target: "facebook" | "instagram",
  ): Promise<SocialAccount> {
    const { data } = await apiClient.post<SocialAccount>("/social/meta/link", {
      brand_id: brandId,
      page_id: pageId,
      target,
    });
    return data;
  },
  async metaTest(
    accountId: string,
    text: string,
    imageUrl?: string,
  ): Promise<MetaSendResult> {
    const { data } = await apiClient.post<MetaSendResult>("/social/meta/test", {
      account_id: accountId,
      text,
      image_url: imageUrl ?? null,
    });
    return data;
  },
  async youtubeLookup(handle?: string, channelId?: string): Promise<YouTubeChannelInfo> {
    const params: Record<string, string> = {};
    if (handle) params.handle = handle;
    if (channelId) params.channel_id = channelId;
    const { data } = await apiClient.get<YouTubeChannelInfo>("/social/youtube/lookup", {
      params,
    });
    return data;
  },
  async youtubeLink(
    brandId: string,
    handle?: string,
    channelId?: string,
  ): Promise<SocialAccount> {
    const { data } = await apiClient.post<SocialAccount>("/social/youtube/link", {
      brand_id: brandId,
      handle: handle ?? null,
      channel_id: channelId ?? null,
    });
    return data;
  },
  async youtubeStats(accountId: string, limit = 5): Promise<YouTubeStats> {
    const { data } = await apiClient.get<YouTubeStats>(
      `/social/youtube/${accountId}/stats`,
      { params: { limit } },
    );
    return data;
  },
};

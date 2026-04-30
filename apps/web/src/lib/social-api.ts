import { apiClient } from "./api-client";
import type { SocialAccount, TelegramBotInfo, TelegramSendResult } from "./types";

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
};

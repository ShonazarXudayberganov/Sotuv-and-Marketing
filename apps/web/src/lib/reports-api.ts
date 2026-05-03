import { apiClient } from "./api-client";
import type {
  ReportsCohortRow,
  ReportsFunnel,
  ReportsInsights,
  ReportsOverview,
  SavedReport,
} from "./types";

export const reportsApi = {
  async overview(days = 30): Promise<ReportsOverview> {
    const { data } = await apiClient.get<ReportsOverview>("/reports/overview", {
      params: { days },
    });
    return data;
  },
  async funnel(): Promise<ReportsFunnel> {
    const { data } = await apiClient.get<ReportsFunnel>("/reports/funnel");
    return data;
  },
  async cohorts(months = 6): Promise<ReportsCohortRow[]> {
    const { data } = await apiClient.get<ReportsCohortRow[]>("/reports/cohorts", {
      params: { months },
    });
    return data;
  },
  async insights(days = 30): Promise<ReportsInsights> {
    const { data } = await apiClient.get<ReportsInsights>("/reports/insights", {
      params: { days },
    });
    return data;
  },
  async listSaved(): Promise<SavedReport[]> {
    const { data } = await apiClient.get<SavedReport[]>("/reports/saved");
    return data;
  },
  async createSaved(payload: {
    name: string;
    description?: string | null;
    definition: Record<string, unknown>;
    is_pinned?: boolean;
  }): Promise<SavedReport> {
    const { data } = await apiClient.post<SavedReport>("/reports/saved", payload);
    return data;
  },
  async deleteSaved(id: string): Promise<void> {
    await apiClient.delete(`/reports/saved/${id}`);
  },
  exportCsvUrl(kind: string): string {
    const base = apiClient.defaults.baseURL ?? "";
    return `${base}/reports/export/${kind}.csv`;
  },
};

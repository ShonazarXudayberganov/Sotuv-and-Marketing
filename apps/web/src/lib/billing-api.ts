import { apiClient } from "./api-client";
import type { BillingCatalog, BillingStatus, InvoiceRow, PriceQuote } from "./types";

export const billingApi = {
  async catalog(): Promise<BillingCatalog> {
    const { data } = await apiClient.get<BillingCatalog>("/billing/catalog");
    return data;
  },
  async status(): Promise<BillingStatus> {
    const { data } = await apiClient.get<BillingStatus>("/billing/status");
    return data;
  },
  async quote(payload: {
    modules: string[];
    tier: string;
    package?: string | null;
    billing_cycle_months: number;
  }): Promise<PriceQuote> {
    const { data } = await apiClient.post<PriceQuote>("/billing/quote", payload);
    return data;
  },
  async startTrial(): Promise<void> {
    await apiClient.post("/billing/start-trial");
  },
  async subscribe(payload: {
    modules: string[];
    tier: string;
    package?: string | null;
    billing_cycle_months: number;
  }): Promise<InvoiceRow> {
    const { data } = await apiClient.post<InvoiceRow>("/billing/subscribe", payload);
    return data;
  },
  async listInvoices(): Promise<InvoiceRow[]> {
    const { data } = await apiClient.get<InvoiceRow[]>("/billing/invoices");
    return data;
  },
  async markPaid(invoiceId: string): Promise<InvoiceRow> {
    const { data } = await apiClient.post<InvoiceRow>(
      `/billing/invoices/${invoiceId}/mark-paid`,
    );
    return data;
  },
  invoicePdfUrl(invoiceId: string, accessToken: string): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    // PDF download uses Authorization header — but anchor downloads can't set
    // headers, so the helper is for fetch-based download.
    return `${apiUrl}/api/v1/billing/invoices/${invoiceId}/pdf?access_token=${encodeURIComponent(accessToken)}`;
  },
};

export async function downloadInvoicePdf(
  invoiceId: string,
  invoiceNumber: string,
): Promise<void> {
  const resp = await apiClient.get(`/billing/invoices/${invoiceId}/pdf`, {
    responseType: "blob",
  });
  const blob = new Blob([resp.data], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${invoiceNumber}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

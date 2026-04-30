"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { extractApiError } from "@/lib/api-client";
import { billingApi, downloadInvoicePdf } from "@/lib/billing-api";
import type { GraceState } from "@/lib/types";
import { cn } from "@/lib/utils";

const TIERS: { key: "start" | "pro" | "business"; label: string }[] = [
  { key: "start", label: "Start" },
  { key: "pro", label: "Pro" },
  { key: "business", label: "Business" },
];

const PACKAGES: { key: string | null; label: string }[] = [
  { key: null, label: "Maxsus tanlov" },
  { key: "marketing", label: "Marketing Pack" },
  { key: "sales", label: "Sales Pack" },
  { key: "full", label: "Full Ecosystem" },
];

const CYCLES: { months: 1 | 6 | 12; label: string }[] = [
  { months: 1, label: "Oylik" },
  { months: 6, label: "6 oylik (-10%)" },
  { months: 12, label: "12 oylik (-20%)" },
];

const GRACE_LABEL: Record<GraceState, { label: string; cls: string }> = {
  active: { label: "Faol", cls: "bg-success/15 text-success" },
  banner: { label: "Muddat tugadi (7 kun ichida)", cls: "bg-warning/15 text-warning" },
  read_only: { label: "Faqat o'qish", cls: "bg-warning/15 text-warning" },
  locked: { label: "Qulflangan", cls: "bg-destructive/15 text-destructive" },
};

const formatSoum = (n: number) => `${n.toLocaleString("uz-UZ")} so'm`;

export default function BillingPage() {
  const qc = useQueryClient();
  const [tier, setTier] = useState<"start" | "pro" | "business">("pro");
  const [pkg, setPkg] = useState<string | null>("full");
  const [cycle, setCycle] = useState<1 | 6 | 12>(1);
  const [modules, setModules] = useState<string[]>([
    "crm",
    "smm",
    "ads",
    "inbox",
    "reports",
    "integrations",
  ]);

  const { data: catalog } = useQuery({
    queryKey: ["billing-catalog"],
    queryFn: billingApi.catalog,
  });
  const { data: status } = useQuery({
    queryKey: ["billing-status"],
    queryFn: billingApi.status,
  });
  const { data: invoices = [] } = useQuery({
    queryKey: ["invoices"],
    queryFn: billingApi.listInvoices,
  });

  const effectiveModules = useMemo(() => {
    if (pkg && catalog?.packages[pkg]) return catalog.packages[pkg].modules;
    return modules;
  }, [pkg, modules, catalog]);

  const { data: quote } = useQuery({
    queryKey: ["billing-quote", effectiveModules, tier, pkg, cycle],
    queryFn: () =>
      billingApi.quote({
        modules: effectiveModules,
        tier,
        package: pkg,
        billing_cycle_months: cycle,
      }),
    enabled: effectiveModules.length > 0,
  });

  const startTrial = useMutation({
    mutationFn: billingApi.startTrial,
    onSuccess: () => {
      toast.success("7 kunlik bepul sinov boshlandi");
      qc.invalidateQueries({ queryKey: ["billing-status"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const subscribe = useMutation({
    mutationFn: () =>
      billingApi.subscribe({
        modules: effectiveModules,
        tier,
        package: pkg,
        billing_cycle_months: cycle,
      }),
    onSuccess: () => {
      toast.success("Invoice yaratildi. Email ko'rib chiqing.");
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["billing-status"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const markPaid = useMutation({
    mutationFn: (id: string) => billingApi.markPaid(id),
    onSuccess: () => {
      toast.success("To'lov tasdiqlandi");
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["billing-status"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const sub = status?.subscription;
  const grace = status?.grace_state ?? "locked";

  const toggleModule = (key: string) =>
    setModules((m) => (m.includes(key) ? m.filter((x) => x !== key) : [...m, key]));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Joriy tarif</CardTitle>
            <p className="text-muted mt-1 text-sm">
              Holat:{" "}
              <span className={cn("rounded-full px-2 py-0.5 text-xs", GRACE_LABEL[grace].cls)}>
                {GRACE_LABEL[grace].label}
              </span>
            </p>
          </div>
          {!sub ? (
            <Can permission="billing.update">
              <Button onClick={() => startTrial.mutate()} loading={startTrial.isPending}>
                <Sparkles className="h-4 w-4" /> 7 kunlik sinov
              </Button>
            </Can>
          ) : null}
        </CardHeader>
        <CardContent>
          {sub ? (
            <div className="grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <p className="text-muted">Modullar</p>
                <p className="text-charcoal">{sub.selected_modules.join(", ")}</p>
              </div>
              <div>
                <p className="text-muted">Tarif</p>
                <p className="text-charcoal capitalize">
                  {sub.tier} {sub.package ? `(${sub.package})` : ""}
                </p>
              </div>
              <div>
                <p className="text-muted">Davr</p>
                <p className="text-charcoal">{sub.billing_cycle_months} oy</p>
              </div>
              <div>
                <p className="text-muted">Narx (chegirma {sub.discount_percent}%)</p>
                <p className="text-charcoal font-semibold">{formatSoum(sub.price_total)}</p>
              </div>
              <div>
                <p className="text-muted">Boshlandi</p>
                <p className="text-charcoal">
                  {new Date(sub.starts_at).toLocaleDateString("uz-UZ")}
                </p>
              </div>
              <div>
                <p className="text-muted">Tugaydi</p>
                <p className="text-charcoal">
                  {new Date(sub.expires_at).toLocaleDateString("uz-UZ")}
                  {status?.days_until_expiry !== null &&
                  status?.days_until_expiry !== undefined
                    ? ` (${status.days_until_expiry} kun)`
                    : null}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-muted text-sm">
              Tarif faollashtirilmagan. Sinov yoki kerakli modullarni tanlab, obuna
              bo&apos;ling.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tarifni o&apos;zgartirish</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-muted mb-2 text-xs tracking-wide uppercase">Paket</p>
            <div className="flex flex-wrap gap-2">
              {PACKAGES.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => setPkg(p.key)}
                  className={cn(
                    "rounded-md border px-3 py-1.5 text-sm transition-colors",
                    pkg === p.key
                      ? "border-gold bg-gold/10 text-charcoal"
                      : "border-cream-200 text-muted hover:border-gold/40",
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-muted mb-2 text-xs tracking-wide uppercase">Modullar</p>
            <div className="grid gap-2 sm:grid-cols-3">
              {(catalog?.modules ?? []).map((m) => {
                const checked = effectiveModules.includes(m.key);
                const disabled = pkg !== null;
                return (
                  <label
                    key={m.key}
                    className={cn(
                      "border-cream-200 bg-cream flex items-center gap-2 rounded-md border p-2 text-sm",
                      disabled ? "opacity-60" : "hover:border-gold/40",
                    )}
                  >
                    <input
                      type="checkbox"
                      className="accent-gold h-4 w-4"
                      checked={checked}
                      disabled={disabled}
                      onChange={() => toggleModule(m.key)}
                    />
                    <span className="flex-1">{m.label}</span>
                    <span className="text-muted text-xs">
                      {(m.prices[tier] / 1000).toFixed(0)}k
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-muted mb-2 text-xs tracking-wide uppercase">Tarif</p>
              <div className="flex gap-2">
                {TIERS.map((t) => (
                  <button
                    key={t.key}
                    type="button"
                    onClick={() => setTier(t.key)}
                    className={cn(
                      "flex-1 rounded-md border px-3 py-1.5 text-sm",
                      tier === t.key
                        ? "border-gold bg-gold/10 text-charcoal"
                        : "border-cream-200 text-muted",
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-muted mb-2 text-xs tracking-wide uppercase">Davr</p>
              <div className="flex gap-2">
                {CYCLES.map((c) => (
                  <button
                    key={c.months}
                    type="button"
                    onClick={() => setCycle(c.months)}
                    className={cn(
                      "flex-1 rounded-md border px-2 py-1.5 text-xs",
                      cycle === c.months
                        ? "border-gold bg-gold/10 text-charcoal"
                        : "border-cream-200 text-muted",
                    )}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {quote ? (
            <div className="bg-charcoal text-cream rounded-lg p-4">
              <div className="flex items-baseline justify-between">
                <span className="text-cream/70 text-sm">
                  Jami (chegirma {quote.discount_percent}%)
                </span>
                <span className="font-display text-3xl">{formatSoum(quote.price_total)}</span>
              </div>
              <p className="text-cream/60 mt-1 text-xs">
                AI tokenlar/oy: {quote.ai_token_cap_monthly.toLocaleString("uz-UZ")}
              </p>
            </div>
          ) : null}

          <Can permission="billing.update">
            <Button
              onClick={() => subscribe.mutate()}
              loading={subscribe.isPending}
              disabled={effectiveModules.length === 0}
              size="lg"
            >
              <Check className="h-4 w-4" /> Obuna bo&apos;lish (Invoice yaratiladi)
            </Button>
          </Can>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoice tarixi</CardTitle>
        </CardHeader>
        <CardContent>
          {invoices.length === 0 ? (
            <p className="text-muted text-sm">Invoice&apos;lar yo&apos;q</p>
          ) : (
            <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
              {invoices.map((inv) => (
                <li
                  key={inv.id}
                  className="bg-cream flex items-center justify-between px-3 py-3 text-sm first:rounded-t-md last:rounded-b-md"
                >
                  <div>
                    <p className="text-charcoal font-mono">{inv.invoice_number}</p>
                    <p className="text-muted text-xs">
                      {formatSoum(inv.amount)} ·{" "}
                      <span
                        className={cn(
                          "rounded px-1.5 py-0.5 text-[10px]",
                          inv.status === "paid"
                            ? "bg-success/15 text-success"
                            : "bg-warning/15 text-warning",
                        )}
                      >
                        {inv.status}
                      </span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        downloadInvoicePdf(inv.id, inv.invoice_number).catch((e) =>
                          toast.error(extractApiError(e)),
                        )
                      }
                    >
                      <Download className="h-3 w-3" /> PDF
                    </Button>
                    {inv.status !== "paid" ? (
                      <Can permission="billing.update">
                        <Button
                          size="sm"
                          onClick={() => markPaid.mutate(inv.id)}
                          loading={markPaid.isPending}
                        >
                          To&apos;langan
                        </Button>
                      </Can>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

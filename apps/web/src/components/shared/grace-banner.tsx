"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Lock } from "lucide-react";
import Link from "next/link";

import { billingApi } from "@/lib/billing-api";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

export function GraceBanner() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const { data } = useQuery({
    queryKey: ["billing-status"],
    queryFn: billingApi.status,
    enabled: Boolean(accessToken),
    refetchInterval: 5 * 60_000,
  });

  if (!data) return null;
  const state = data.grace_state;
  if (state === "active") return null;

  const config = {
    banner: {
      icon: AlertCircle,
      cls: "bg-warning/15 text-warning border-warning/30",
      title: "Tarif muddati tugadi",
      description: `${data.days_past_expiry ?? 0} kun oldin tugagan. To'lov qilmasangiz, akkaunt o'qish-rejimiga o'tadi.`,
    },
    read_only: {
      icon: AlertCircle,
      cls: "bg-warning/20 text-warning border-warning/40",
      title: "O'qish-rejimi",
      description:
        "Yangi yozish operatsiyalari bloklangan. Bilingni tekshiring va to'lov qiling.",
    },
    locked: {
      icon: Lock,
      cls: "bg-destructive/15 text-destructive border-destructive/30",
      title: "Akkaunt qulflangan",
      description:
        "Tarif muddati 30+ kun oldin tugagan. Akkauntni qayta tiklash uchun to'lov qiling.",
    },
  }[state];

  if (!config) return null;
  const Icon = config.icon;

  return (
    <div className={cn("border-b px-6 py-3", config.cls)}>
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Icon className="h-5 w-5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium">{config.title}</p>
            <p className="opacity-80">{config.description}</p>
          </div>
        </div>
        <Link
          href="/settings/billing"
          className="bg-charcoal text-cream hover:bg-charcoal-soft inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium"
        >
          Bilingga o&apos;tish
        </Link>
      </div>
    </div>
  );
}

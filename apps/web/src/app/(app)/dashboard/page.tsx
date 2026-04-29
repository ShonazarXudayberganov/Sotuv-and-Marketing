"use client";

import { useAuthStore } from "@/stores/auth-store";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const tenant = useAuthStore((s) => s.tenant);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-gold-deep font-accent text-sm italic">Bosh sahifa</p>
        <h1 className="text-charcoal font-display text-4xl tracking-tight">
          Xush kelibsiz{user?.full_name ? `, ${user.full_name}` : ""}!
        </h1>
        <p className="text-muted mt-2">
          {tenant?.name} — sizning AI-quvvatlangan biznes platformangiz tayyor.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-cream-100/40 border-cream-200 rounded-lg border p-6">
          <p className="text-muted text-sm">Joriy bosqich</p>
          <p className="text-charcoal mt-1 text-2xl font-semibold">Bosqich 0</p>
          <p className="text-muted mt-1 text-xs">Tayyorgarlik (Foundation)</p>
        </div>
        <div className="bg-cream-100/40 border-cream-200 rounded-lg border p-6">
          <p className="text-muted text-sm">Modullar</p>
          <p className="text-charcoal mt-1 text-2xl font-semibold">0 / 6</p>
          <p className="text-muted mt-1 text-xs">tez orada faollashadi</p>
        </div>
        <div className="bg-cream-100/40 border-cream-200 rounded-lg border p-6">
          <p className="text-muted text-sm">Sizning rolingiz</p>
          <p className="text-charcoal mt-1 text-2xl font-semibold capitalize">
            {user?.role ?? "—"}
          </p>
          <p className="text-muted mt-1 text-xs">tenant: {tenant?.schema_name}</p>
        </div>
      </div>

      <div className="bg-charcoal text-cream rounded-lg p-8">
        <h2 className="font-display text-2xl">Sprint 3 yakunlandi</h2>
        <p className="text-cream/70 mt-2 text-sm">
          Onboarding wizard, sozlamalar (10 sahifa), RBAC va bo&apos;limlar tayyor. Sprint 4 da
          vazifalar moduli, real-time bildirishnomalar va 2FA qo&apos;shiladi.
        </p>
        <div className="mt-4 flex gap-2">
          <a
            href="/onboarding"
            className="bg-gold text-charcoal hover:bg-gold-deep inline-flex items-center rounded-md px-4 py-2 text-sm font-medium"
          >
            Onboarding wizard
          </a>
          <a
            href="/settings"
            className="border-cream/30 text-cream hover:bg-cream/10 inline-flex items-center rounded-md border px-4 py-2 text-sm font-medium"
          >
            Sozlamalar
          </a>
        </div>
      </div>
    </div>
  );
}

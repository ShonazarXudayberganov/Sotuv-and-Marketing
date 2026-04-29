"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Profil</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-[120px_1fr]">
          <span className="text-muted text-sm">F.I.O.</span>
          <span className="text-charcoal">{user?.full_name ?? "—"}</span>
          <span className="text-muted text-sm">Email</span>
          <span className="text-charcoal">{user?.email}</span>
          <span className="text-muted text-sm">Rol</span>
          <span className="text-charcoal capitalize">{user?.role}</span>
        </div>
        <p className="text-muted mt-6 text-xs">
          Tahrirlash funksiyasi Sprint 4 da qo&apos;shiladi.
        </p>
      </CardContent>
    </Card>
  );
}

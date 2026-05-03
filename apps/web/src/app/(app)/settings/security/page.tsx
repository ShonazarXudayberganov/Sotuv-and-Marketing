"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut, ShieldCheck } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { sessionsApi } from "@/lib/security-api";
import { twofaApi } from "@/lib/sprint4-api";
import type { TwoFactorSetup } from "@/lib/types";

export default function SecurityPage() {
  const [setup, setSetup] = useState<TwoFactorSetup | null>(null);
  const [code, setCode] = useState("");

  const startSetup = useMutation({
    mutationFn: twofaApi.setup,
    onSuccess: (data) => setSetup(data),
    onError: (e) => toast.error(extractApiError(e)),
  });

  const verify = useMutation({
    mutationFn: () => twofaApi.verify(code),
    onSuccess: () => {
      toast.success("2FA yoqildi");
      setSetup(null);
      setCode("");
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const disable = useMutation({
    mutationFn: twofaApi.disable,
    onSuccess: () => toast.success("2FA o'chirildi"),
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Ikki bosqichli autentifikatsiya (2FA)</CardTitle>
          <CardDescription>
            Authenticator ilovasi (Google Authenticator, 1Password, Authy) orqali
            qo&apos;shimcha himoya
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!setup ? (
            <div className="flex gap-2">
              <Button onClick={() => startSetup.mutate()} loading={startSetup.isPending}>
                <ShieldCheck className="h-4 w-4" /> 2FA ni yoqish
              </Button>
              <Button
                variant="outline"
                onClick={() => disable.mutate()}
                loading={disable.isPending}
              >
                O&apos;chirish
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col items-center gap-3 sm:flex-row">
                <Image
                  src={setup.qr_data_url}
                  alt="2FA QR"
                  width={160}
                  height={160}
                  unoptimized
                  className="border-cream-200 rounded border"
                />
                <div className="flex-1 text-sm">
                  <p className="text-muted">
                    Authenticator ilovasida QR kodni skanerlang yoki:
                  </p>
                  <code className="bg-cream-100 mt-2 inline-block rounded px-2 py-1 text-xs">
                    {setup.secret}
                  </code>
                  <p className="text-muted mt-3 text-xs">
                    Backup kodlar (xavfsiz joyda saqlang):
                  </p>
                  <div className="mt-1 grid grid-cols-2 gap-1">
                    {setup.backup_codes.map((c) => (
                      <code
                        key={c}
                        className="bg-cream-100 rounded px-2 py-0.5 text-center text-xs"
                      >
                        {c}
                      </code>
                    ))}
                  </div>
                </div>
              </div>
              <FormField label="Authenticator dan 6 raqamli kod">
                <Input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                  inputMode="numeric"
                  maxLength={8}
                />
              </FormField>
              <Button onClick={() => verify.mutate()} loading={verify.isPending}>
                Tasdiqlash va yoqish
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <ActiveSessions />
    </div>
  );
}

function ActiveSessions() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: sessionsApi.list,
  });

  const revoke = useMutation({
    mutationFn: sessionsApi.revoke,
    onSuccess: () => {
      toast.success("Sessiya bekor qilindi");
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Faol sessiyalar ({data.length})</CardTitle>
        <CardDescription>
          Bu yerda hozirda kirilgan barcha qurilmalarni ko&apos;rasiz. Tanish bo&apos;lmagan
          sessiyani darhol bekor qiling.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-muted text-sm">Yuklanmoqda...</p>
        ) : data.length === 0 ? (
          <p className="text-muted text-sm">Faol sessiya yo&apos;q</p>
        ) : (
          <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
            {data.map((s) => (
              <li
                key={s.id}
                className="bg-cream flex items-center justify-between gap-3 px-3 py-3 text-sm first:rounded-t-md last:rounded-b-md"
              >
                <div className="min-w-0">
                  <p className="text-charcoal truncate text-xs">
                    {s.user_agent ?? "Noma'lum qurilma"}
                  </p>
                  <p className="text-muted mt-0.5 text-[11px]">
                    IP: {s.ip_address ?? "—"} · oxirgi faollik:{" "}
                    {new Date(s.last_active_at).toLocaleString("uz-UZ")}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => revoke.mutate(s.id)}
                  loading={revoke.isPending}
                >
                  <LogOut className="h-3.5 w-3.5" /> Chiqish
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

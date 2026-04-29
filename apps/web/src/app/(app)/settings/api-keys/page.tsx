"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { apiKeysApi } from "@/lib/sprint4-api";
import type { ApiKeyCreated } from "@/lib/types";

export default function ApiKeysPage() {
  const qc = useQueryClient();
  const [newName, setNewName] = useState("");
  const [created, setCreated] = useState<ApiKeyCreated | null>(null);

  const { data: keys = [] } = useQuery({
    queryKey: ["api-keys"],
    queryFn: apiKeysApi.list,
  });

  const create = useMutation({
    mutationFn: apiKeysApi.create,
    onSuccess: (data) => {
      setCreated(data);
      setNewName("");
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const revoke = useMutation({
    mutationFn: apiKeysApi.revoke,
    onSuccess: () => {
      toast.success("Bekor qilindi");
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>API kalitlar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Can permission="api_keys.create">
            <div className="flex gap-2">
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Kalit nomi (masalan: CI bot)"
              />
              <Button
                onClick={() => newName.trim() && create.mutate({ name: newName.trim() })}
                loading={create.isPending}
              >
                <Plus className="h-4 w-4" /> Yaratish
              </Button>
            </div>
          </Can>

          {created ? (
            <div className="border-gold/40 bg-gold/5 rounded-md border p-4">
              <p className="text-charcoal text-sm font-medium">
                Yangi kalit yaratildi (faqat hozir ko&apos;rinadi):
              </p>
              <code className="bg-cream mt-2 block rounded px-3 py-2 text-xs break-all">
                {created.plaintext_key}
              </code>
              <Button
                size="sm"
                variant="outline"
                className="mt-2"
                onClick={() => {
                  navigator.clipboard.writeText(created.plaintext_key);
                  toast.success("Buferga ko'chirildi");
                }}
              >
                Nusxa olish
              </Button>
              <button
                type="button"
                onClick={() => setCreated(null)}
                className="text-muted ml-2 text-xs underline"
              >
                Yopish
              </button>
            </div>
          ) : null}

          {keys.length === 0 ? (
            <p className="text-muted text-sm">Hozircha kalitlar yo&apos;q</p>
          ) : (
            <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
              {keys.map((k) => (
                <li
                  key={k.id}
                  className="bg-cream flex items-center justify-between px-3 py-3 text-sm first:rounded-t-md last:rounded-b-md"
                >
                  <div>
                    <p className="text-charcoal">
                      {k.name}
                      {k.revoked_at ? (
                        <span className="bg-destructive/10 text-destructive ml-2 rounded px-1.5 py-0.5 text-[10px]">
                          bekor qilingan
                        </span>
                      ) : null}
                    </p>
                    <p className="text-muted text-xs">
                      <code>{k.key_prefix}…</code> · {k.rate_limit_per_minute}/min
                    </p>
                  </div>
                  {!k.revoked_at ? (
                    <Can permission="api_keys.revoke">
                      <Button size="sm" variant="outline" onClick={() => revoke.mutate(k.id)}>
                        Bekor qilish
                      </Button>
                    </Can>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export const dynamic = "force-dynamic";

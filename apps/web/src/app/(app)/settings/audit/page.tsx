"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { auditApi } from "@/lib/security-api";

export default function AuditPage() {
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");

  const { data = [], isLoading } = useQuery({
    queryKey: ["audit", action, resourceType],
    queryFn: () =>
      auditApi.list({
        action: action || undefined,
        resource_type: resourceType || undefined,
        limit: 200,
      }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit log ({data.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid gap-2 sm:grid-cols-2">
          <FormField label="Harakat" hint="Masalan: users.invite">
            <Input value={action} onChange={(e) => setAction(e.target.value)} />
          </FormField>
          <FormField label="Resurs turi" hint="Masalan: user / role / contact">
            <Input value={resourceType} onChange={(e) => setResourceType(e.target.value)} />
          </FormField>
        </div>
        {isLoading ? (
          <p className="text-muted text-sm">Yuklanmoqda...</p>
        ) : data.length === 0 ? (
          <p className="text-muted text-sm">Yozuvlar yo&apos;q</p>
        ) : (
          <div className="border-cream-200 overflow-hidden rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-cream-100 text-muted text-xs">
                <tr>
                  <th className="px-3 py-2 text-left">Vaqt</th>
                  <th className="px-3 py-2 text-left">Harakat</th>
                  <th className="px-3 py-2 text-left">Resurs</th>
                  <th className="px-3 py-2 text-left">Foydalanuvchi</th>
                  <th className="px-3 py-2 text-left">IP</th>
                </tr>
              </thead>
              <tbody className="divide-cream-200 divide-y">
                {data.map((row) => (
                  <tr key={row.id} className="bg-cream">
                    <td className="px-3 py-2 font-mono text-xs">
                      {new Date(row.created_at).toLocaleString("uz-UZ")}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{row.action}</td>
                    <td className="px-3 py-2 text-xs">
                      <span className="text-muted">{row.resource_type}</span>
                      {row.resource_id ? (
                        <span className="ml-1 font-mono text-[10px]">
                          {row.resource_id.slice(0, 8)}…
                        </span>
                      ) : null}
                    </td>
                    <td className="px-3 py-2 font-mono text-[10px]">
                      {row.user_id ? row.user_id.slice(0, 8) + "…" : "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-[10px]">
                      {row.ip_address ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

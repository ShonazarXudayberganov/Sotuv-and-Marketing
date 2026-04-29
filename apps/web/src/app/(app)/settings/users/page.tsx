"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { rolesApi, usersApi } from "@/lib/tenant-api";

export default function UsersPage() {
  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: usersApi.list });
  const { data: roles = [] } = useQuery({ queryKey: ["roles"], queryFn: rolesApi.list });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Xodimlar</CardTitle>
        </CardHeader>
        <CardContent>
          {users.length === 0 ? (
            <p className="text-muted text-sm">Yuklanmoqda yoki xodim yo&apos;q</p>
          ) : (
            <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="bg-cream flex items-center justify-between px-3 py-3 text-sm first:rounded-t-md last:rounded-b-md"
                >
                  <div>
                    <p className="text-charcoal">{u.full_name ?? u.email}</p>
                    <p className="text-muted text-xs">{u.email}</p>
                  </div>
                  <span className="bg-gold/10 text-gold-deep rounded-full px-2 py-0.5 text-xs">
                    {u.role}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="text-muted mt-4 text-xs">
            Xodim taklif qilish funksiyasi Sprint 4 da qo&apos;shiladi.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rollar</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            {roles.map((r) => (
              <div key={r.id} className="border-cream-200 bg-cream rounded-md border p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{r.name}</p>
                  {r.is_system ? (
                    <span className="bg-charcoal text-cream rounded px-1.5 py-0.5 text-[10px]">
                      tizim
                    </span>
                  ) : null}
                </div>
                <p className="text-muted mt-1 text-xs">{r.description}</p>
                <p className="text-muted mt-2 text-xs">{r.permissions.length} ta imtiyoz</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

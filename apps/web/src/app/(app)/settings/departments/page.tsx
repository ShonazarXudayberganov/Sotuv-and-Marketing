"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Can } from "@/components/shared/can";
import { extractApiError } from "@/lib/api-client";
import { departmentsApi } from "@/lib/tenant-api";

export default function DepartmentsPage() {
  const qc = useQueryClient();
  const { data: depts = [], isLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });
  const [newName, setNewName] = useState("");

  const create = useMutation({
    mutationFn: (name: string) => departmentsApi.create({ name }),
    onSuccess: () => {
      toast.success("Bo'lim qo'shildi");
      setNewName("");
      qc.invalidateQueries({ queryKey: ["departments"] });
    },
    onError: (error) => toast.error(extractApiError(error)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => departmentsApi.remove(id),
    onSuccess: () => {
      toast.success("Bo'lim o'chirildi");
      qc.invalidateQueries({ queryKey: ["departments"] });
    },
    onError: (error) => toast.error(extractApiError(error)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bo&apos;limlar</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Can permission="departments.create">
          <div className="flex gap-2">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Yangi bo'lim nomi"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newName.trim()) create.mutate(newName.trim());
              }}
            />
            <Button
              onClick={() => newName.trim() && create.mutate(newName.trim())}
              loading={create.isPending}
            >
              <Plus className="h-4 w-4" /> Qo&apos;shish
            </Button>
          </div>
        </Can>

        {isLoading ? (
          <p className="text-muted text-sm">Yuklanmoqda...</p>
        ) : depts.length === 0 ? (
          <p className="text-muted text-sm">Hozircha bo&apos;limlar yo&apos;q</p>
        ) : (
          <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
            {depts.map((d) => (
              <li
                key={d.id}
                className="bg-cream flex items-center justify-between px-3 py-2.5 text-sm first:rounded-t-md last:rounded-b-md"
              >
                <span>{d.name}</span>
                <Can permission="departments.delete">
                  <button
                    type="button"
                    onClick={() => remove.mutate(d.id)}
                    className="text-destructive hover:text-destructive/80"
                    aria-label={`O'chirish ${d.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </Can>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

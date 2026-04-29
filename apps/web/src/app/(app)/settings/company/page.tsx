"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { toast } from "sonner";

import { Can } from "@/components/shared/can";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { tenantApi } from "@/lib/tenant-api";

export default function CompanyPage() {
  const qc = useQueryClient();
  const { data: tenant, isLoading } = useQuery({
    queryKey: ["tenant-me"],
    queryFn: tenantApi.me,
  });
  const nameRef = useRef<HTMLInputElement>(null);
  const industryRef = useRef<HTMLInputElement>(null);

  const update = useMutation({
    mutationFn: () =>
      tenantApi.update({
        name: nameRef.current?.value,
        industry: industryRef.current?.value,
      }),
    onSuccess: () => {
      toast.success("Saqlandi");
      qc.invalidateQueries({ queryKey: ["tenant-me"] });
    },
    onError: (error) => toast.error(extractApiError(error)),
  });

  if (isLoading || !tenant) {
    return (
      <Card>
        <CardContent className="p-6">Yuklanmoqda...</CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kompaniya ma&apos;lumotlari</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <FormField label="Kompaniya nomi" htmlFor="company_name">
          <Input
            id="company_name"
            ref={nameRef}
            defaultValue={tenant.name}
            key={`name-${tenant.id}`}
          />
        </FormField>
        <FormField label="Soha" htmlFor="industry">
          <Input
            id="industry"
            ref={industryRef}
            defaultValue={tenant.industry ?? ""}
            placeholder="savdo, restoran, ..."
            key={`industry-${tenant.id}`}
          />
        </FormField>
        <FormField label="Schema (read-only)">
          <Input value={tenant.schema_name} disabled />
        </FormField>
        <Can
          permission="tenant.update"
          fallback={
            <p className="text-muted text-xs">Bu sahifani tahrirlash uchun ruxsat yo&apos;q</p>
          }
        >
          <Button onClick={() => update.mutate()} loading={update.isPending}>
            Saqlash
          </Button>
        </Can>
      </CardContent>
    </Card>
  );
}

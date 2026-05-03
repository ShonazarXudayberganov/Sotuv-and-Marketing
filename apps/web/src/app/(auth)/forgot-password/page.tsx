"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

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
import { authApi } from "@/lib/auth-api";

const requestSchema = z.object({
  email_or_phone: z.string().min(3, "Email yoki telefon raqamini kiriting"),
});

const resetSchema = z.object({
  code: z.string().min(4, "Tasdiq kodini kiriting").max(8),
  new_password: z
    .string()
    .min(8, "Parol kamida 8 belgi bo'lishi kerak")
    .regex(/[A-Z]/, "Parolda kamida bitta katta harf bo'lishi kerak")
    .regex(/[0-9]/, "Parolda kamida bitta raqam bo'lishi kerak"),
});

type RequestForm = z.infer<typeof requestSchema>;
type ResetForm = z.infer<typeof resetSchema>;

export default function ForgotPasswordPage() {
  const [verificationId, setVerificationId] = useState<string | null>(null);
  const [phoneMasked, setPhoneMasked] = useState<string | null>(null);

  const requestForm = useForm<RequestForm>({
    resolver: zodResolver(requestSchema),
    defaultValues: { email_or_phone: "" },
  });
  const resetForm = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
    defaultValues: { code: "", new_password: "" },
  });

  const requestReset = requestForm.handleSubmit(async (values) => {
    try {
      const res = await authApi.forgotPassword(values);
      setVerificationId(res.verification_id);
      setPhoneMasked(res.phone_masked);
      toast.success("Tasdiq kodi yuborildi");
    } catch (error) {
      toast.error(extractApiError(error));
    }
  });

  const resetPassword = resetForm.handleSubmit(async (values) => {
    if (!verificationId) return;
    try {
      await authApi.resetPassword({
        verification_id: verificationId,
        code: values.code,
        new_password: values.new_password,
      });
      toast.success("Parol yangilandi");
      resetForm.reset();
    } catch (error) {
      toast.error(extractApiError(error));
    }
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parolni tiklash</CardTitle>
        <CardDescription>
          Akkaunt telefoniga yuborilgan kod bilan yangi parol o&apos;rnating
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!verificationId ? (
          <form onSubmit={requestReset} className="flex flex-col gap-4">
            <FormField
              label="Email yoki telefon"
              htmlFor="email_or_phone"
              error={requestForm.formState.errors.email_or_phone?.message}
              required
            >
              <Input
                id="email_or_phone"
                autoComplete="username"
                placeholder="email@example.uz yoki +998901234567"
                invalid={!!requestForm.formState.errors.email_or_phone}
                {...requestForm.register("email_or_phone")}
              />
            </FormField>

            <Button type="submit" loading={requestForm.formState.isSubmitting} size="lg">
              Kod yuborish
            </Button>
          </form>
        ) : (
          <form onSubmit={resetPassword} className="flex flex-col gap-4">
            {phoneMasked ? (
              <p className="text-muted text-sm">Kod yuborildi: {phoneMasked}</p>
            ) : null}
            <FormField
              label="Tasdiq kodi"
              htmlFor="code"
              error={resetForm.formState.errors.code?.message}
              required
            >
              <Input
                id="code"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="123456"
                invalid={!!resetForm.formState.errors.code}
                {...resetForm.register("code")}
              />
            </FormField>

            <FormField
              label="Yangi parol"
              htmlFor="new_password"
              error={resetForm.formState.errors.new_password?.message}
              required
            >
              <Input
                id="new_password"
                type="password"
                autoComplete="new-password"
                invalid={!!resetForm.formState.errors.new_password}
                {...resetForm.register("new_password")}
              />
            </FormField>

            <Button type="submit" loading={resetForm.formState.isSubmitting} size="lg">
              Parolni yangilash
            </Button>
          </form>
        )}

        <Link
          href="/login"
          className="text-muted hover:text-gold-deep mt-4 inline-block text-sm"
        >
          Kirishga qaytish
        </Link>
      </CardContent>
    </Card>
  );
}

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
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
import { useVerifyPhone } from "@/hooks/use-auth";

const schema = z.object({
  code: z.string().regex(/^\d{4,8}$/, "4-8 raqam"),
});

type Form = z.infer<typeof schema>;

const TTL_SECONDS = 300;

function VerifyPhoneForm() {
  const params = useSearchParams();
  const verificationId = params.get("verification_id");
  const phone = params.get("phone") ?? "";
  const [secondsLeft, setSecondsLeft] = useState(TTL_SECONDS);

  const verify = useVerifyPhone();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { code: "" },
  });

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const t = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, [secondsLeft]);

  if (!verificationId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Tasdiqlash so&apos;rovi topilmadi</CardTitle>
          <CardDescription>
            Iltimos, ro&apos;yxatdan o&apos;tishni qaytadan boshlang.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const onSubmit = (values: Form) =>
    verify.mutate({ verification_id: verificationId, code: values.code });

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Telefon raqamingizni tasdiqlang</CardTitle>
        <CardDescription>
          {phone} raqamiga 6 raqamli kod yubordik. Kod {minutes}:
          {String(seconds).padStart(2, "0")} ichida amal qiladi.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <FormField label="Tasdiq kodi" htmlFor="code" error={errors.code?.message} required>
            <Input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={8}
              placeholder="123456"
              className="text-center text-2xl tracking-[0.5em]"
              invalid={!!errors.code}
              {...register("code")}
            />
          </FormField>

          <Button type="submit" loading={verify.isPending} size="lg">
            Tasdiqlash
          </Button>

          <p className="text-muted text-center text-xs">
            SMS kelmadi?{" "}
            {minutes === 0 && seconds === 0
              ? "Yangi kod so'rang"
              : `${minutes}:${String(seconds).padStart(2, "0")} dan keyin yangi kod so'rashingiz mumkin`}
          </p>
        </form>
      </CardContent>
    </Card>
  );
}

export default function VerifyPhonePage() {
  return (
    <Suspense
      fallback={
        <Card>
          <CardHeader>
            <CardTitle>Yuklanmoqda...</CardTitle>
          </CardHeader>
        </Card>
      }
    >
      <VerifyPhoneForm />
    </Suspense>
  );
}

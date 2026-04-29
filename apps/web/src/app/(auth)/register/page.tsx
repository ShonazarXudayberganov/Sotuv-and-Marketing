"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
import { useRegister } from "@/hooks/use-auth";
import { uzPhoneToE164 } from "@/lib/utils";
import type { Industry } from "@/lib/types";

const INDUSTRIES: { value: Industry; label: string }[] = [
  { value: "savdo", label: "Savdo" },
  { value: "restoran", label: "Restoran" },
  { value: "salon-klinika", label: "Salon / Klinika" },
  { value: "talim", label: "Ta'lim" },
  { value: "xizmat", label: "Xizmat ko'rsatish" },
  { value: "it", label: "IT" },
  { value: "boshqa", label: "Boshqa" },
];

const schema = z.object({
  company_name: z.string().min(2, "Kamida 2 belgi").max(100, "Maksimal 100 belgi"),
  industry: z.enum([
    "savdo",
    "restoran",
    "salon-klinika",
    "talim",
    "xizmat",
    "it",
    "boshqa",
  ] as const),
  phone: z.string().refine((v) => v.replace(/\D/g, "").length >= 12, {
    message: "To'liq telefon raqamini kiriting (+998 90 123 45 67)",
  }),
  email: z.email("Email noto'g'ri"),
  password: z
    .string()
    .min(8, "Kamida 8 belgi")
    .regex(/[A-Z]/, "Kamida bitta katta harf bo'lishi kerak")
    .regex(/[0-9]/, "Kamida bitta raqam bo'lishi kerak"),
  accept_terms: z.literal(true, { error: "Shartnomani qabul qiling" }),
});

type RegisterForm = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const registerMut = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    defaultValues: {
      company_name: "",
      industry: "boshqa",
      phone: "+998",
      email: "",
      password: "",
      accept_terms: undefined as unknown as true,
    },
  });

  const onSubmit = (values: RegisterForm) => {
    registerMut.mutate(
      {
        company_name: values.company_name,
        industry: values.industry,
        phone: uzPhoneToE164(values.phone),
        email: values.email,
        password: values.password,
        accept_terms: values.accept_terms,
      },
      {
        onSuccess: (data) => {
          const params = new URLSearchParams({
            verification_id: data.verification_id,
            phone: data.phone_masked,
          });
          router.push(`/verify-phone?${params.toString()}`);
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Akkaunt yaratish</CardTitle>
        <CardDescription>7 kunlik bepul sinov, karta talab qilinmaydi</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <FormField
            label="Kompaniya nomi"
            htmlFor="company_name"
            error={errors.company_name?.message}
            required
          >
            <Input
              id="company_name"
              placeholder="Akme MChJ"
              invalid={!!errors.company_name}
              {...register("company_name")}
            />
          </FormField>

          <FormField label="Soha" htmlFor="industry" error={errors.industry?.message} required>
            <select
              id="industry"
              className="border-cream-200 bg-cream focus-visible:ring-gold/60 focus-visible:border-gold flex h-11 w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
              {...register("industry")}
            >
              {INDUSTRIES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </FormField>

          <FormField
            label="Telefon raqam"
            htmlFor="phone"
            error={errors.phone?.message}
            hint="O'zbekiston raqami: +998 ..."
            required
          >
            <Input
              id="phone"
              inputMode="tel"
              placeholder="+998 90 123 45 67"
              invalid={!!errors.phone}
              {...register("phone")}
            />
          </FormField>

          <FormField label="Email" htmlFor="email" error={errors.email?.message} required>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="email@kompaniya.uz"
              invalid={!!errors.email}
              {...register("email")}
            />
          </FormField>

          <FormField
            label="Parol"
            htmlFor="password"
            error={errors.password?.message}
            hint="8+ belgi, 1 katta harf, 1 raqam"
            required
          >
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.password}
              {...register("password")}
            />
          </FormField>

          <label className="text-charcoal/80 flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-gold mt-1 h-4 w-4"
              {...register("accept_terms")}
            />
            <span>Foydalanuvchi shartnomasi va Maxfiylik siyosatini qabul qilaman</span>
          </label>
          {errors.accept_terms ? (
            <p className="text-destructive -mt-2 text-xs">{errors.accept_terms.message}</p>
          ) : null}

          <Button type="submit" loading={registerMut.isPending} size="lg">
            Ro&apos;yxatdan o&apos;tish
          </Button>

          <p className="text-muted text-center text-sm">
            Akkauntingiz bormi?{" "}
            <Link href="/login" className="text-gold-deep hover:underline">
              Kirish
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}

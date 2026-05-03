"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useGoogleLogin, useLogin, useTelegramLogin } from "@/hooks/use-auth";

const schema = z.object({
  email_or_phone: z.string().min(3, "Email yoki telefon raqamini kiriting"),
  password: z.string().min(1, "Parolni kiriting"),
  remember_me: z.boolean().optional(),
});

type LoginForm = z.infer<typeof schema>;

export default function LoginPage() {
  const login = useLogin();
  const googleLogin = useGoogleLogin();
  const telegramLogin = useTelegramLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email_or_phone: "", password: "", remember_me: false },
  });

  const onSubmit = (values: LoginForm) =>
    login.mutate({
      email_or_phone: values.email_or_phone,
      password: values.password,
      remember_me: values.remember_me ?? false,
    });

  const oauthMockEnabled = process.env.NEXT_PUBLIC_OAUTH_MOCK !== "false";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kirish</CardTitle>
        <CardDescription>
          Akkauntingizga kirish uchun ma&apos;lumotlarni kiriting
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <FormField
            label="Email yoki telefon"
            htmlFor="email_or_phone"
            error={errors.email_or_phone?.message}
            required
          >
            <Input
              id="email_or_phone"
              autoComplete="username"
              placeholder="email@example.uz yoki +998901234567"
              invalid={!!errors.email_or_phone}
              {...register("email_or_phone")}
            />
          </FormField>

          <FormField
            label="Parol"
            htmlFor="password"
            error={errors.password?.message}
            required
          >
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              invalid={!!errors.password}
              {...register("password")}
            />
          </FormField>

          <label className="text-charcoal/80 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-gold h-4 w-4"
              {...register("remember_me")}
            />
            30 kun eslab qol
          </label>

          <Button type="submit" loading={login.isPending} size="lg">
            Kirish
          </Button>

          <div className="text-muted flex justify-between text-sm">
            <Link href="/forgot-password" className="hover:text-gold-deep">
              Parolni unutdingizmi?
            </Link>
            <Link href="/register" className="hover:text-gold-deep">
              Akkaunt yaratish
            </Link>
          </div>
        </form>

        <div className="border-cream-200 mt-6 border-t pt-4">
          <p className="text-muted mb-3 text-center text-xs tracking-wide uppercase">yoki</p>
          <div className="flex flex-col gap-2">
            <Button
              type="button"
              variant="outline"
              loading={googleLogin.isPending}
              onClick={() => {
                if (oauthMockEnabled) {
                  const email = window.prompt(
                    "Mock Google: emailingizni kiriting",
                    "demo@gmail.com",
                  );
                  if (email) googleLogin.mutate(`mock:${email}:Google Demo`);
                } else {
                  toast.error("Google kirish hozircha mavjud emas");
                }
              }}
            >
              Google bilan kirish
            </Button>
            <Button
              type="button"
              variant="outline"
              loading={telegramLogin.isPending}
              onClick={() => {
                if (oauthMockEnabled) {
                  const username = window.prompt(
                    "Mock Telegram: usernameingizni kiriting",
                    "demo_user",
                  );
                  if (username)
                    telegramLogin.mutate({
                      mock_token: `mock:${username}@telegram.nexus.local:${username}`,
                    });
                } else {
                  toast.error("Telegram kirish hozircha mavjud emas");
                }
              }}
            >
              Telegram bilan kirish
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

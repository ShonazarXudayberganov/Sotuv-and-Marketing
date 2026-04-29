"use client";

import { ArrowLeft, ArrowRight, Check, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
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
import { departmentsApi, onboardingApi, tenantApi } from "@/lib/tenant-api";
import { MODULES, PLANS, type ModuleKey } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS = [
  { n: 1, label: "Boshlash" },
  { n: 2, label: "Kompaniya" },
  { n: 3, label: "Bo'limlar" },
  { n: 4, label: "Xodimlar" },
  { n: 5, label: "Modullar" },
  { n: 6, label: "Tarif" },
  { n: 7, label: "Tayyor" },
];

const DEFAULT_DEPTS = ["Sotuv", "Marketing", "Qo'llab-quvvatlash", "Boshqaruv"];

interface State {
  step: number;
  inn: string;
  address: string;
  website: string;
  description: string;
  departments: string[];
  newDept: string;
  invites: { email: string; role: string }[];
  modules: ModuleKey[];
  plan: "start" | "pro" | "business";
}

export default function OnboardingPage() {
  const router = useRouter();
  const [state, setState] = useState<State>({
    step: 1,
    inn: "",
    address: "",
    website: "",
    description: "",
    departments: [...DEFAULT_DEPTS],
    newDept: "",
    invites: [],
    modules: ["crm", "inbox"],
    plan: "pro",
  });
  const [submitting, setSubmitting] = useState(false);

  const update = (patch: Partial<State>) => setState((s) => ({ ...s, ...patch }));
  const next = () => update({ step: Math.min(7, state.step + 1) });
  const prev = () => update({ step: Math.max(1, state.step - 1) });

  const finish = async () => {
    setSubmitting(true);
    try {
      if (state.description.trim()) {
        await tenantApi.update({}); // placeholder — full company update Sprint 4
      }
      // Create departments in parallel
      await Promise.all(
        state.departments
          .filter((d) => d.trim())
          .map((name) => departmentsApi.create({ name }).catch(() => null)),
      );
      await onboardingApi.complete({
        step: 7,
        completed: true,
        departments: state.departments,
        selected_modules: state.modules,
        selected_plan: state.plan,
      });
      toast.success("Sozlash tugadi! Bosh sahifaga o'tamiz");
      router.push("/dashboard");
    } catch (error) {
      toast.error(extractApiError(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <ProgressBar current={state.step} />

      <Card className="mt-6">
        {state.step === 1 ? (
          <Step1 onNext={next} />
        ) : state.step === 2 ? (
          <Step2 state={state} update={update} onNext={next} onBack={prev} />
        ) : state.step === 3 ? (
          <Step3 state={state} update={update} onNext={next} onBack={prev} />
        ) : state.step === 4 ? (
          <Step4 state={state} update={update} onNext={next} onBack={prev} />
        ) : state.step === 5 ? (
          <Step5 state={state} update={update} onNext={next} onBack={prev} />
        ) : state.step === 6 ? (
          <Step6 state={state} update={update} onNext={next} onBack={prev} />
        ) : (
          <Step7 onFinish={finish} submitting={submitting} />
        )}
      </Card>
    </div>
  );
}

function ProgressBar({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-between">
      {STEPS.map((s, i) => (
        <div key={s.n} className="flex flex-1 items-center">
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 text-sm font-medium",
              s.n < current
                ? "bg-gold border-gold text-charcoal"
                : s.n === current
                  ? "border-gold text-gold-deep bg-cream"
                  : "border-cream-200 text-muted bg-cream",
            )}
          >
            {s.n < current ? <Check className="h-4 w-4" /> : s.n}
          </div>
          {i < STEPS.length - 1 ? (
            <div
              className={cn(
                "mx-2 h-0.5 flex-1 transition-colors",
                s.n < current ? "bg-gold" : "bg-cream-200",
              )}
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}

function Step1({ onNext }: { onNext: () => void }) {
  return (
    <>
      <CardHeader className="items-center text-center">
        <div className="bg-gold/10 mb-4 flex h-16 w-16 items-center justify-center rounded-full">
          <Sparkles className="text-gold-deep h-8 w-8" />
        </div>
        <CardTitle className="text-3xl">NEXUS AI&apos;ga xush kelibsiz!</CardTitle>
        <CardDescription className="text-base">
          Sizni 7 ta oddiy qadamga olib boramiz. ~3 daqiqa.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex justify-center pb-8">
        <Button size="lg" onClick={onNext}>
          Boshlash <ArrowRight className="h-4 w-4" />
        </Button>
      </CardContent>
    </>
  );
}

function StepActions({
  onBack,
  onNext,
  nextLabel = "Keyingi",
  submitting,
}: {
  onBack: () => void;
  onNext: () => void;
  nextLabel?: string;
  submitting?: boolean;
}) {
  return (
    <div className="border-cream-200 mt-6 flex justify-between border-t pt-4">
      <Button variant="ghost" onClick={onBack}>
        <ArrowLeft className="h-4 w-4" /> Orqaga
      </Button>
      <Button onClick={onNext} loading={submitting}>
        {nextLabel} <ArrowRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

function Step2({
  state,
  update,
  onNext,
  onBack,
}: {
  state: State;
  update: (p: Partial<State>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <>
      <CardHeader>
        <CardTitle>Kompaniya ma&apos;lumotlari</CardTitle>
        <CardDescription>Bu ma&apos;lumotlar AI uchun kontekst bo&apos;ladi</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <FormField label="INN/STIR" htmlFor="inn" hint="Ixtiyoriy">
          <Input
            id="inn"
            value={state.inn}
            onChange={(e) => update({ inn: e.target.value })}
            placeholder="123456789"
          />
        </FormField>
        <FormField label="Manzil" htmlFor="address" hint="Viloyat, tuman, ko'cha">
          <Input
            id="address"
            value={state.address}
            onChange={(e) => update({ address: e.target.value })}
            placeholder="Toshkent shahri, Yunusobod tumani..."
          />
        </FormField>
        <FormField label="Sayt URL" htmlFor="website" hint="Ixtiyoriy">
          <Input
            id="website"
            value={state.website}
            onChange={(e) => update({ website: e.target.value })}
            placeholder="https://kompaniya.uz"
          />
        </FormField>
        <FormField
          label="Faoliyat tavsifi"
          htmlFor="description"
          hint="2-3 jumlada — AI uchun muhim"
        >
          <textarea
            id="description"
            value={state.description}
            onChange={(e) => update({ description: e.target.value })}
            className="border-cream-200 bg-cream focus-visible:ring-gold/60 focus-visible:border-gold flex min-h-[100px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
            placeholder="Biz Toshkent va viloyatlarda faoliyat yurituvchi salon-klinikamiz..."
          />
        </FormField>
        <StepActions onBack={onBack} onNext={onNext} />
      </CardContent>
    </>
  );
}

function Step3({
  state,
  update,
  onNext,
  onBack,
}: {
  state: State;
  update: (p: Partial<State>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const toggle = (name: string) =>
    update({
      departments: state.departments.includes(name)
        ? state.departments.filter((d) => d !== name)
        : [...state.departments, name],
    });

  const addNew = () => {
    if (!state.newDept.trim()) return;
    update({
      departments: [...state.departments, state.newDept.trim()],
      newDept: "",
    });
  };

  return (
    <>
      <CardHeader>
        <CardTitle>Bo&apos;limlar</CardTitle>
        <CardDescription>
          Standart shablon yoki o&apos;z bo&apos;limlaringizni qo&apos;shing
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2">
          {DEFAULT_DEPTS.map((dept) => (
            <label
              key={dept}
              className="border-cream-200 hover:border-gold/40 bg-cream flex cursor-pointer items-center gap-3 rounded-md border p-3"
            >
              <input
                type="checkbox"
                className="accent-gold h-4 w-4"
                checked={state.departments.includes(dept)}
                onChange={() => toggle(dept)}
              />
              <span className="text-sm">{dept}</span>
            </label>
          ))}
          {state.departments
            .filter((d) => !DEFAULT_DEPTS.includes(d))
            .map((dept) => (
              <label
                key={dept}
                className="border-gold/30 bg-gold/5 flex items-center gap-3 rounded-md border p-3"
              >
                <input
                  type="checkbox"
                  className="accent-gold h-4 w-4"
                  checked
                  onChange={() => toggle(dept)}
                />
                <span className="text-sm">{dept}</span>
              </label>
            ))}
        </div>
        <div className="mt-4 flex gap-2">
          <Input
            value={state.newDept}
            onChange={(e) => update({ newDept: e.target.value })}
            placeholder="Yangi bo'lim nomi"
            onKeyDown={(e) => e.key === "Enter" && addNew()}
          />
          <Button variant="outline" onClick={addNew}>
            + Qo&apos;shish
          </Button>
        </div>
        <StepActions onBack={onBack} onNext={onNext} />
      </CardContent>
    </>
  );
}

function Step4({
  state,
  onNext,
  onBack,
}: {
  state: State;
  update: (p: Partial<State>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <>
      <CardHeader>
        <CardTitle>Xodimlarni taklif qiling</CardTitle>
        <CardDescription>
          Hozir o&apos;tkazib yuborsangiz, sozlamalardan keyinroq qo&apos;shasiz
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-muted text-sm">
          Bu qadam Sprint 4 da to&apos;liq ishlaydi. Hozircha o&apos;tkazib yuboramiz.
        </p>
        <p className="text-muted mt-2 text-sm">
          Taklif qilingan: <strong>{state.invites.length}</strong>
        </p>
        <StepActions onBack={onBack} onNext={onNext} nextLabel="O'tkazib yuborish" />
      </CardContent>
    </>
  );
}

function Step5({
  state,
  update,
  onNext,
  onBack,
}: {
  state: State;
  update: (p: Partial<State>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const toggle = (key: ModuleKey) =>
    update({
      modules: state.modules.includes(key)
        ? state.modules.filter((m) => m !== key)
        : [...state.modules, key],
    });

  return (
    <>
      <CardHeader>
        <CardTitle>Modullarni tanlang</CardTitle>
        <CardDescription>Tariflar Sprint 5 da yakuniy ishga tushadi</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {MODULES.map((m) => {
            const active = state.modules.includes(m.key);
            return (
              <button
                key={m.key}
                type="button"
                onClick={() => toggle(m.key)}
                className={cn(
                  "rounded-lg border p-4 text-left transition-colors",
                  active
                    ? "border-gold bg-gold/5 text-charcoal"
                    : "border-cream-200 bg-cream hover:border-gold/40",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{m.label}</span>
                  {active ? <Check className="text-gold-deep h-4 w-4" /> : null}
                </div>
                <p className="text-muted mt-1 text-xs">
                  Start: {(m.price.start / 1000).toFixed(0)}k so&apos;m/oy
                </p>
              </button>
            );
          })}
        </div>
        <StepActions onBack={onBack} onNext={onNext} />
      </CardContent>
    </>
  );
}

function Step6({
  state,
  update,
  onNext,
  onBack,
}: {
  state: State;
  update: (p: Partial<State>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <>
      <CardHeader>
        <CardTitle>Tarifni tanlang</CardTitle>
        <CardDescription>7 kunlik bepul sinov, karta talab qilinmaydi</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-3">
          {PLANS.map((p) => {
            const active = state.plan === p.key;
            return (
              <button
                key={p.key}
                type="button"
                onClick={() => update({ plan: p.key })}
                className={cn(
                  "relative rounded-lg border p-4 text-left transition-colors",
                  active
                    ? "border-gold bg-gold/5"
                    : "border-cream-200 bg-cream hover:border-gold/40",
                )}
              >
                {"recommended" in p && p.recommended ? (
                  <span className="bg-gold text-charcoal absolute -top-2 right-3 rounded px-2 py-0.5 text-xs font-medium">
                    Tavsiya
                  </span>
                ) : null}
                <p className="font-display text-charcoal text-xl">{p.label}</p>
                <p className="text-muted mt-1 text-sm">
                  {(p.priceTotal / 1_000_000).toFixed(1)}M so&apos;m/oy
                </p>
              </button>
            );
          })}
        </div>
        <StepActions onBack={onBack} onNext={onNext} />
      </CardContent>
    </>
  );
}

function Step7({ onFinish, submitting }: { onFinish: () => void; submitting: boolean }) {
  return (
    <>
      <CardHeader className="items-center text-center">
        <div className="bg-success/10 mb-4 flex h-16 w-16 items-center justify-center rounded-full">
          <Check className="text-success h-8 w-8" />
        </div>
        <CardTitle className="text-3xl">Tabriklaymiz!</CardTitle>
        <CardDescription className="text-base">
          Akkauntingiz tayyor. Sozlamalarni saqlash uchun tugmani bosing.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex justify-center pb-8">
        <Button size="lg" onClick={onFinish} loading={submitting}>
          Saqlab, bosh sahifaga
        </Button>
      </CardContent>
    </>
  );
}

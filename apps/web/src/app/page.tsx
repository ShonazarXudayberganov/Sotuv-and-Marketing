import {
  ArrowRight,
  BarChart3,
  Check,
  MessageSquare,
  Megaphone,
  PenSquare,
  Plug,
  Shield,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Button } from "@/components/ui/button";

const MODULES = [
  {
    icon: Users,
    title: "CRM",
    description:
      "Mijozlar, bitimlar, savdo voronkasi. AI scoring har mijoz uchun va keyingi qadam tavsiyasi.",
    price: "290k so'm/oy",
  },
  {
    icon: PenSquare,
    title: "SMM",
    description:
      "Telegram, Instagram, Facebook, YouTube. AI kontent generatsiya va kontent reja kalendari.",
    price: "390k so'm/oy",
  },
  {
    icon: Megaphone,
    title: "Reklama",
    description:
      "Meta va Google reklama kampaniyalari. AI byudjet optimizatsiyasi va A/B testlar.",
    price: "290k so'm/oy",
  },
  {
    icon: MessageSquare,
    title: "Inbox",
    description:
      "Barcha kanallar bir oynada — sayt, Telegram, Instagram, WhatsApp. AI auto-javob (90%+ confidence).",
    price: "390k so'm/oy",
  },
  {
    icon: BarChart3,
    title: "Hisobotlar",
    description:
      "Real-time dashboardlar, anomaliya monitor, AI biznes maslahat va kunlik insights.",
    price: "190k so'm/oy",
  },
  {
    icon: Plug,
    title: "Integratsiyalar",
    description: "1C, AmoCRM, Bitrix24, Google Sheets. 50+ tayyor integratsiya marketplace.",
    price: "190k so'm/oy",
  },
];

const DIFFERENTIATORS = [
  {
    icon: Sparkles,
    title: "AI yadro qismi",
    text: "Kontent, scoring, optimizatsiya, sentiment, biznes maslahat — har modulda Claude va GPT-4o.",
  },
  {
    icon: Shield,
    title: "Multi-tenant xavfsizlik",
    text: "Schema-per-tenant izolyatsiya. Sizning ma'lumotlaringiz O'zbekistonda saqlanadi (qonun talabi).",
  },
  {
    icon: Zap,
    title: "Tezda boshlash",
    text: "7 kunlik bepul sinov. 7 qadamli onboarding — ~3 daqiqada akkaunt sozlanadi.",
  },
];

const PLANS = [
  {
    key: "start",
    label: "Start",
    price: "690k",
    audience: "1-10 xodim, kichik biznes",
    features: ["6 modulgacha", "50 000 AI token/oy", "5 ta xodim", "Email qo'llab-quvvatlash"],
  },
  {
    key: "pro",
    label: "Pro",
    price: "1.5M",
    audience: "10-30 xodim, o'sayotgan biznes",
    recommended: true,
    features: [
      "6 modul + paket chegirma",
      "200 000 AI token/oy",
      "Cheksiz xodim",
      "Telegram/email priority support",
      "Custom rollar va RBAC",
    ],
  },
  {
    key: "business",
    label: "Business",
    price: "3.0M",
    audience: "30-50+ xodim, o'rta biznes",
    features: [
      "Hammasi Pro'da +",
      "1 000 000 AI token/oy",
      "Custom integratsiyalar",
      "SLA 99.9% va dedicated CSM",
      "On-call qo'llab-quvvatlash",
    ],
  },
];

const STATS = [
  { value: "6", label: "AI-quvvatlangan modul" },
  { value: "1M+", label: "AI tokens/oy (Business)" },
  { value: "99.9%", label: "SLA uptime maqsadi" },
  { value: "7 kun", label: "Bepul sinov" },
];

export default function Home() {
  return (
    <main className="bg-cream min-h-screen">
      {/* ─────────── Header ─────────── */}
      <header className="border-cream-200 bg-cream/85 sticky top-0 z-20 border-b backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link
            href="/"
            className="text-charcoal font-display text-2xl font-black tracking-tight"
          >
            NEXUS <span className="gold-gradient">AI</span>
          </Link>
          <nav className="hidden items-center gap-6 text-sm md:flex">
            <a href="#modullar" className="text-charcoal/70 hover:text-charcoal">
              Modullar
            </a>
            <a href="#nima-uchun" className="text-charcoal/70 hover:text-charcoal">
              Nima uchun NEXUS
            </a>
            <a href="#tariflar" className="text-charcoal/70 hover:text-charcoal">
              Tariflar
            </a>
            <Link href="/login" className="text-charcoal/70 hover:text-charcoal">
              Kirish
            </Link>
            <ThemeToggle size="sm" />
            <Link href="/register">
              <Button size="sm" className="btn-luxury">Bepul boshlash</Button>
            </Link>
          </nav>
          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle size="sm" />
            <Link href="/register">
              <Button size="sm" className="btn-luxury">Boshlash</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ─────────── Hero ─────────── */}
      <section className="relative overflow-hidden px-6 py-24 md:py-36">
        <div className="hero-glow absolute inset-0 -z-10" />
        <div className="mx-auto max-w-5xl text-center">
          <div className="border-gold/30 bg-gold/10 text-gold-deep mx-auto mb-10 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-semibold tracking-wider uppercase">
            <Sparkles className="h-3.5 w-3.5" />
            O&apos;zbekiston bozori uchun · AI-quvvatlangan SaaS
          </div>

          <p className="text-gold-deep font-accent mb-4 text-xl italic md:text-2xl">
            Biznesingizning intellektual markazi
          </p>
          <h1 className="text-charcoal font-display mb-8 text-6xl leading-[1.02] font-black tracking-tight md:text-8xl">
            Sotuv, marketing va xizmat —
            <br />
            <span className="gold-gradient">bitta tizimda</span>
          </h1>

          <p className="text-muted mx-auto mb-10 max-w-2xl text-lg leading-relaxed md:text-xl">
            CRM, SMM, Reklama, Inbox, Hisobotlar va Integratsiyalar. AI har bir modulda —
            kontent yaratadi, mijozlarni baholaydi, reklamani optimallashtiradi va biznes
            maslahat beradi.
          </p>

          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/register">
              <Button size="lg" className="btn-luxury min-w-[200px]">
                7 kunlik bepul sinov
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#modullar">
              <Button variant="outline" size="lg" className="btn-luxury-outline">
                Modullarni ko&apos;rish
              </Button>
            </a>
          </div>

          <p className="text-muted mt-4 text-xs">
            Karta talab qilinmaydi · Istalgan paytda bekor
          </p>

          {/* Stats */}
          <div className="border-cream-200 mt-20 grid grid-cols-2 gap-6 border-y py-10 md:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label}>
                <p className="gold-gradient font-display text-4xl font-black md:text-5xl">
                  {s.value}
                </p>
                <p className="text-muted mt-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────── Modules ─────────── */}
      <section id="modullar" className="bg-surface px-6 py-20 md:py-28">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <p className="text-gold-deep font-accent mb-3 text-lg italic">Mahsulot</p>
            <h2 className="text-charcoal font-display text-5xl font-black tracking-tight md:text-6xl">
              6 ta modul, <span className="gold-gradient">1 ta hisob</span>
            </h2>
            <p className="text-muted mt-5 text-lg">
              Kerakli modullarni tanlang yoki paket bilan 25% gacha tejang.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {MODULES.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.title}
                  className="group border-cream-200 bg-cream hover:border-gold/50 relative overflow-hidden rounded-2xl border p-7 transition-all hover:-translate-y-1 hover:shadow-[0_20px_40px_-12px_rgba(176,131,61,0.25)]"
                >
                  <div className="bg-gold/10 text-gold-deep group-hover:bg-gold group-hover:text-primary-foreground mb-5 flex h-12 w-12 items-center justify-center rounded-xl transition-colors">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <h3 className="text-charcoal font-display text-3xl font-bold">
                      {m.title}
                    </h3>
                    <span className="text-gold-deep text-sm font-semibold tracking-wide">
                      {m.price}
                    </span>
                  </div>
                  <p className="text-muted mt-3 text-sm leading-relaxed">{m.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─────────── Why NEXUS — emerald accent block ─────────── */}
      <section
        id="nima-uchun"
        className="relative overflow-hidden bg-[var(--bg-subtle)] px-6 py-24 md:py-32"
      >
        <div className="hero-glow absolute inset-0 opacity-70" />
        <div className="relative mx-auto max-w-7xl">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <p className="font-accent mb-3 text-lg text-[var(--primary)] italic">
              Nima uchun NEXUS AI
            </p>
            <h2 className="font-display text-5xl font-black tracking-tight text-[var(--fg)] md:text-6xl">
              Boshqalardan <span className="gold-gradient">farqi</span>
            </h2>
            <p className="mt-5 text-lg text-[var(--fg-muted)]">
              Biz AI&apos;ni qo&apos;shimcha xususiyat sifatida emas, tizim yadrosi sifatida
              quramiz.
            </p>
          </div>

          <div className="grid gap-10 md:grid-cols-3">
            {DIFFERENTIATORS.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.title} className="text-center">
                  <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-[color-mix(in_oklab,var(--primary)_35%,transparent)] bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
                    <Icon className="h-7 w-7" />
                  </div>
                  <h3 className="font-display mb-3 text-2xl font-bold text-[var(--fg)]">
                    {d.title}
                  </h3>
                  <p className="leading-relaxed text-[var(--fg-muted)]">{d.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─────────── Pricing ─────────── */}
      <section id="tariflar" className="px-6 py-24 md:py-32">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <p className="text-gold-deep font-accent mb-3 text-lg italic">Tariflar</p>
            <h2 className="text-charcoal font-display text-5xl font-black tracking-tight md:text-6xl">
              Sodda va <span className="gold-gradient">shaffof</span> narxlash
            </h2>
            <p className="text-muted mt-5 text-lg">
              Yillik to&apos;lovda −20%. Kompaniyangiz o&apos;sganda istalgan paytda yangilang.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {PLANS.map((plan) => (
              <div
                key={plan.key}
                className={
                  plan.recommended
                    ? "relative rounded-2xl border-2 border-[var(--primary)] bg-[var(--surface)] p-8 shadow-[var(--shadow-lg)]"
                    : "relative rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8"
                }
              >
                {plan.recommended ? (
                  <span className="absolute -top-3 right-6 rounded-full bg-[var(--primary)] px-3 py-1 text-xs font-bold tracking-wider text-[var(--primary-fg)] uppercase">
                    ★ Tavsiya
                  </span>
                ) : null}
                <h3 className="font-display text-4xl font-black text-[var(--fg)]">
                  {plan.label}
                </h3>
                <p className="mt-1 text-sm text-[var(--fg-muted)]">{plan.audience}</p>
                <div className="my-7 flex items-baseline gap-2">
                  <span
                    className={
                      plan.recommended
                        ? "gold-gradient font-display text-6xl font-black"
                        : "font-display text-6xl font-black text-[var(--fg)]"
                    }
                  >
                    {plan.price}
                  </span>
                  <span className="text-sm text-[var(--fg-muted)]">so&apos;m/oy</span>
                </div>
                <ul className="space-y-3 text-sm">
                  {plan.features.map((f) => (
                    <li key={f} className="flex gap-2.5 text-[var(--fg)]">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[var(--primary)]" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="mt-8 block">
                  <Button
                    size="lg"
                    className={`w-full ${plan.recommended ? "btn-luxury" : "btn-luxury-outline"}`}
                    variant={plan.recommended ? "primary" : "outline"}
                  >
                    Boshlash
                  </Button>
                </Link>
              </div>
            ))}
          </div>

          <p className="text-muted mt-12 text-center text-sm">
            Korporativ ehtiyojlar uchun{" "}
            <a
              href="mailto:sales@nexusai.uz"
              className="text-gold-deep font-semibold hover:underline"
            >
              sales@nexusai.uz
            </a>{" "}
            — Enterprise tarif individual.
          </p>
        </div>
      </section>

      {/* ─────────── CTA ─────────── */}
      <section className="px-6 py-24">
        <div className="from-gold/15 via-gold-soft/10 to-cream-100 border-gold/20 mx-auto max-w-4xl rounded-3xl border bg-gradient-to-br p-14 text-center shadow-[0_30px_80px_-20px_rgba(176,131,61,0.3)] md:p-20">
          <h2 className="text-charcoal font-display text-5xl font-black tracking-tight md:text-6xl">
            Bugundan <span className="gold-gradient">boshlang</span>
          </h2>
          <p className="text-muted mx-auto mt-5 max-w-xl text-lg">
            7 kunlik bepul sinov. Karta kiritmasdan. Akkauntingiz 3 daqiqada tayyor
            bo&apos;ladi.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/register">
              <Button size="lg" className="btn-luxury min-w-[220px]">
                Bepul akkaunt yaratish
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#modullar">
              <Button variant="ghost" size="lg" className="btn-luxury-outline">
                Yana bilish
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* ─────────── Footer ─────────── */}
      <footer className="border-cream-200 bg-surface-elevated border-t px-6 py-14">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <p className="text-charcoal font-display text-2xl font-black">
              NEXUS <span className="gold-gradient">AI</span>
            </p>
            <p className="text-muted mt-3 max-w-md text-sm">
              O&apos;zbekiston biznesi uchun AI-quvvatlangan SaaS ekotizimi. CRM, SMM, Reklama,
              Inbox, Hisobotlar — bir tizimda.
            </p>
          </div>
          <div>
            <p className="text-charcoal mb-3 text-sm font-medium">Mahsulot</p>
            <ul className="text-muted space-y-2 text-sm">
              <li>
                <a href="#modullar" className="hover:text-gold-deep">
                  Modullar
                </a>
              </li>
              <li>
                <a href="#tariflar" className="hover:text-gold-deep">
                  Tariflar
                </a>
              </li>
              <li>
                <Link href="/login" className="hover:text-gold-deep">
                  Kirish
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-charcoal mb-3 text-sm font-medium">Aloqa</p>
            <ul className="text-muted space-y-2 text-sm">
              <li>
                <a href="mailto:support@nexusai.uz" className="hover:text-gold-deep">
                  support@nexusai.uz
                </a>
              </li>
              <li>
                <a href="mailto:sales@nexusai.uz" className="hover:text-gold-deep">
                  sales@nexusai.uz
                </a>
              </li>
              <li>Toshkent, O&apos;zbekiston</li>
            </ul>
          </div>
        </div>
        <div className="border-cream-200 mx-auto mt-10 flex max-w-7xl items-center justify-between border-t pt-6 text-xs">
          <p className="text-muted">
            © {new Date().getFullYear()} NEXUS AI. Barcha huquqlar himoyalangan.
          </p>
          <p className="text-muted">Made with ✦ in Uzbekistan</p>
        </div>
      </footer>
    </main>
  );
}

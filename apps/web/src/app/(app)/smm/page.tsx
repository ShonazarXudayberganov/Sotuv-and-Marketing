"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  Megaphone,
  PenSquare,
  Plug,
  Plus,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

import { Can } from "@/components/shared/can";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { knowledgeApi } from "@/lib/kb-api";
import { brandsApi, integrationsApi } from "@/lib/smm-api";

export default function SmmDashboardPage() {
  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  });
  const { data: integrations = [] } = useQuery({
    queryKey: ["integrations"],
    queryFn: integrationsApi.list,
  });
  const { data: kbStats } = useQuery({
    queryKey: ["knowledge", "stats", null],
    queryFn: () => knowledgeApi.stats(null),
  });

  const socialIntegrations = integrations.filter((i) => i.category === "social");
  const aiIntegrations = integrations.filter((i) => i.category === "ai");
  const connectedSocial = socialIntegrations.filter((i) => i.connected).length;
  const connectedAi = aiIntegrations.filter((i) => i.connected).length;
  const defaultBrand = brands.find((b) => b.is_default) ?? brands[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="space-y-6"
    >
      <PageHeader
        breadcrumbs={[{ label: "Bosh sahifa", href: "/dashboard" }, { label: "SMM" }]}
        title="SMM"
        description="Brendlar, ijtimoiy akkauntlar, AI kontent generatsiya va kontent reja."
        actions={
          <Can permission="smm.write">
            <div className="flex items-center gap-2">
              <Button size="default" variant="secondary" asChild>
                <Link href="/smm/calendar">
                  <CalendarDays /> Kalendar
                </Link>
              </Button>
              <Button size="default" variant="secondary" asChild>
                <Link href="/smm/brands">
                  <PenSquare /> Brendlar
                </Link>
              </Button>
              <Button size="default" asChild>
                <Link href="/smm/ai-studio">
                  <Sparkles /> AI Studio
                </Link>
              </Button>
            </div>
          </Can>
        }
      />

      {/* Stats overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          icon={Megaphone}
          label="Brendlar"
          value={brands.length}
          hint={defaultBrand ? `Joriy: ${defaultBrand.name}` : "Brend qo'shilmagan"}
          href="/smm/brands"
        />
        <SummaryCard
          icon={Plug}
          label="Ijtimoiy ulanishlar"
          value={`${connectedSocial}/${socialIntegrations.length}`}
          hint="Telegram, Instagram, Facebook…"
          href="/smm/social"
        />
        <SummaryCard
          icon={Sparkles}
          label="AI provayderlar"
          value={`${connectedAi}/${aiIntegrations.length}`}
          hint="Anthropic, OpenAI"
          href="/settings/integrations"
        />
        <SummaryCard
          icon={BookOpen}
          label="Bilim bazasi"
          value={kbStats?.documents ?? 0}
          hint={`${kbStats?.chunks ?? 0} bo'lak indekslangan`}
          href="/smm/knowledge-base"
        />
      </div>

      {/* Brands quick view */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Brendlar</CardTitle>
            <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
              Har bir brend o&apos;z ijtimoiy akkauntlari va AI ovoziga ega
            </p>
          </div>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/smm/brands">
              Hammasi <ArrowUpRight />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {brands.length === 0 ? (
            <EmptyState
              icon={PenSquare}
              title="Brendlar yo'q"
              description="Birinchi brendingizni qo'shing — masalan, kompaniya nomini ishlating."
              action={
                <Can permission="smm.write">
                  <Button asChild>
                    <Link href="/smm/brands">
                      <Plus /> Birinchi brend
                    </Link>
                  </Button>
                </Can>
              }
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {brands.slice(0, 6).map((b) => (
                <Link
                  key={b.id}
                  href={`/smm/brands`}
                  className="group flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] p-4 transition-all hover:-translate-y-0.5 hover:border-[var(--primary)] hover:shadow-[var(--shadow-sm)]"
                >
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-semibold"
                    style={{
                      background: b.primary_color ?? "var(--primary-soft)",
                      color: b.primary_color ? "white" : "var(--primary-soft-fg)",
                    }}
                  >
                    {b.name[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-[13px] font-medium text-[var(--fg)]">
                        {b.name}
                      </p>
                      {b.is_default ? (
                        <Badge variant="primary" className="shrink-0">
                          Asosiy
                        </Badge>
                      ) : null}
                    </div>
                    <p className="truncate text-[11px] text-[var(--fg-subtle)]">
                      {b.industry ?? "—"} · {b.languages.join(", ") || "uz"}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Roadmap */}
      <Card>
        <CardHeader>
          <CardTitle>SMM moduli — yo&apos;l xaritasi</CardTitle>
          <p className="text-[12px] text-[var(--fg-muted)]">
            Bosqich 1 davomida quyidagi imkoniyatlar bosqichma-bosqich qo&apos;shiladi
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2.5">
            <RoadmapItem done label="Brendlar (multi-brand)" sprint="1.1" />
            <RoadmapItem done label="Knowledge base + RAG (pgvector)" sprint="1.2" />
            <RoadmapItem done label="Telegram bot integratsiyasi" sprint="1.3" />
            <RoadmapItem done label="Instagram + Facebook" sprint="1.4" />
            <RoadmapItem done label="YouTube" sprint="1.5" />
            <RoadmapItem done label="AI kontent generatsiya (Claude + GPT)" sprint="1.6" />
            <RoadmapItem done label="Postlar workflow (draft → schedule → publish)" sprint="1.7" />
            <RoadmapItem done label="Kontent reja kalendar" sprint="1.8" icon={CalendarDays} />
            <RoadmapItem label="SMM analytics" sprint="1.9" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  hint,
  href,
}: {
  icon: typeof Megaphone;
  label: string;
  value: string | number;
  hint: string;
  href?: string;
}) {
  const inner = (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)] transition-shadow hover:shadow-[var(--shadow-md)]">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        <p className="mt-2 text-[26px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </p>
        <p className="mt-1.5 truncate text-[11px] text-[var(--fg-subtle)]">{hint}</p>
      </div>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
        <Icon className="h-4 w-4" />
      </div>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

function RoadmapItem({
  label,
  sprint,
  done,
  icon: Icon,
}: {
  label: string;
  sprint: string;
  done?: boolean;
  icon?: typeof Megaphone;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-2.5">
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
          done
            ? "bg-[var(--success-soft)] text-[var(--success)]"
            : "bg-[var(--surface-hover)] text-[var(--fg-subtle)]"
        }`}
      >
        {done ? "✓" : sprint}
      </div>
      <div className="flex-1 text-[13px] text-[var(--fg)]">{label}</div>
      {Icon ? <Icon className="h-3.5 w-3.5 text-[var(--fg-subtle)]" /> : null}
      {done ? (
        <Badge variant="success">Tayyor</Badge>
      ) : (
        <Badge variant="default">Sprint {sprint}</Badge>
      )}
    </div>
  );
}

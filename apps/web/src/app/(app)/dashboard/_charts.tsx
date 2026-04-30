"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import {
  Area,
  AreaChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const REVENUE = [
  { month: "Yan", revenue: 86, leads: 42 },
  { month: "Fev", revenue: 92, leads: 51 },
  { month: "Mar", revenue: 105, leads: 65 },
  { month: "Apr", revenue: 118, leads: 72 },
  { month: "May", revenue: 132, leads: 78 },
  { month: "Iyn", revenue: 142, leads: 95 },
];

const SOURCES = [
  { name: "Telegram", value: 38 },
  { name: "Sayt", value: 27 },
  { name: "Instagram", value: 18 },
  { name: "Reklama", value: 12 },
  { name: "Boshqa", value: 5 },
];

const subscribe = () => () => {};
const getSnapshot = () => true;
const getServerSnapshot = () => false;

export function DashboardCharts() {
  const { resolvedTheme } = useTheme();
  const mounted = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  // Read live CSS variables so charts always sync with the active theme
  const isDark = mounted && resolvedTheme === "dark";
  const fgMuted = isDark ? "oklch(70% 0.01 150)" : "oklch(45% 0.012 200)";
  const grid = isDark ? "oklch(28% 0.015 200)" : "oklch(92% 0.008 150)";
  const primary = isDark ? "oklch(72% 0.16 155)" : "oklch(56% 0.14 155)";
  const accent = isDark ? "oklch(75% 0.18 285)" : "oklch(62% 0.18 285)";
  const surface = isDark ? "oklch(19% 0.012 200)" : "oklch(100% 0 0)";
  const fg = isDark ? "oklch(96% 0.005 150)" : "oklch(18% 0.015 200)";

  const COLORS = [primary, accent, "oklch(72% 0.15 70)", "oklch(68% 0.16 25)", fgMuted];

  const tooltipStyle = {
    background: surface,
    border: `1px solid ${grid}`,
    borderRadius: 8,
    fontSize: 12,
    color: fg,
    boxShadow: "var(--shadow-md)",
  };

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Revenue area chart */}
      <Card className="lg:col-span-2">
        <CardHeader className="flex flex-row items-end justify-between">
          <div>
            <CardTitle>Daromad va lead&apos;lar</CardTitle>
            <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">
              Oxirgi 6 oy · mln so&apos;m
            </p>
          </div>
          <div className="flex gap-3 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: primary }} />
              <span className="text-[var(--fg-muted)]">Daromad</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: accent }} />
              <span className="text-[var(--fg-muted)]">Leadlar</span>
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={REVENUE} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="g-revenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={primary} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="g-leads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={accent} stopOpacity={0.25} />
                    <stop offset="100%" stopColor={accent} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="month"
                  stroke={fgMuted}
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis stroke={fgMuted} fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ stroke: grid, strokeWidth: 1 }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke={primary}
                  strokeWidth={2}
                  fill="url(#g-revenue)"
                />
                <Area
                  type="monotone"
                  dataKey="leads"
                  stroke={accent}
                  strokeWidth={2}
                  fill="url(#g-leads)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Sources donut chart */}
      <Card>
        <CardHeader>
          <CardTitle>Mijoz manbalari</CardTitle>
          <p className="mt-0.5 text-[12px] text-[var(--fg-muted)]">Ulush, %</p>
        </CardHeader>
        <CardContent>
          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={SOURCES}
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  stroke={surface}
                  strokeWidth={2}
                >
                  {SOURCES.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend
                  iconType="circle"
                  wrapperStyle={{ fontSize: 11, color: fgMuted, paddingTop: 8 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

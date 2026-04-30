"use client";

import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Minus, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: number; // percentage change, positive or negative
  trendLabel?: string;
  icon?: LucideIcon;
  className?: string;
}

export function StatCard({
  label,
  value,
  trend,
  trendLabel = "o'tgan oydan",
  icon: Icon,
  className,
}: StatCardProps) {
  const direction =
    trend === undefined ? "neutral" : trend > 0 ? "up" : trend < 0 ? "down" : "neutral";
  const TrendIcon =
    direction === "up" ? ArrowUpRight : direction === "down" ? ArrowDownRight : Minus;
  const trendCls = {
    up: "text-[var(--success)] bg-[var(--success-soft)]",
    down: "text-[var(--danger)] bg-[var(--danger-soft)]",
    neutral: "text-[var(--fg-muted)] bg-[var(--surface-hover)]",
  }[direction];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      whileHover={{ y: -2 }}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-xs)] transition-shadow hover:shadow-[var(--shadow-md)]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[13px] font-medium text-[var(--fg-muted)]">{label}</p>
        {Icon ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary-soft-fg)]">
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-[28px] leading-none font-semibold tracking-tight text-[var(--fg)]">
          {value}
        </span>
        {trend !== undefined ? (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-semibold",
              trendCls,
            )}
          >
            <TrendIcon className="h-3 w-3" />
            {Math.abs(trend).toFixed(1)}%
          </span>
        ) : null}
      </div>
      {trend !== undefined ? (
        <p className="mt-1 text-[11px] text-[var(--fg-subtle)]">{trendLabel}</p>
      ) : null}
    </motion.div>
  );
}

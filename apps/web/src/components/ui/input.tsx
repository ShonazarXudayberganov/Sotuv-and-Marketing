"use client";

import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, invalid, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-9 w-full rounded-lg border bg-[var(--surface)] px-3 py-2 text-sm text-[var(--fg)]",
        "placeholder:text-[var(--fg-subtle)]",
        "transition-[border-color,box-shadow] duration-150",
        "focus-visible:border-[var(--primary)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "shadow-[var(--shadow-xs)]",
        invalid
          ? "border-[var(--danger)] focus-visible:ring-[color-mix(in_oklab,var(--danger),transparent_60%)]"
          : "border-[var(--border)]",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

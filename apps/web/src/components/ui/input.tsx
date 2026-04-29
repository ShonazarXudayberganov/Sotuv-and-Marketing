"use client";

import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, invalid, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "bg-cream flex h-11 w-full rounded-md border px-3 py-2 text-sm",
          "placeholder:text-muted file:border-0 file:bg-transparent file:font-medium",
          "focus-visible:ring-gold/60 focus-visible:border-gold focus-visible:ring-2 focus-visible:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "transition-colors",
          invalid
            ? "border-destructive focus-visible:ring-destructive/40"
            : "border-cream-200",
          className,
        )}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

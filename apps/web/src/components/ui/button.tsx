"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        primary: "bg-gold text-charcoal hover:bg-gold-deep shadow-sm hover:shadow-md",
        secondary: "bg-charcoal text-cream hover:bg-charcoal-soft shadow-sm",
        outline: "border border-gold/40 bg-transparent text-charcoal hover:bg-cream-100",
        ghost: "bg-transparent text-charcoal hover:bg-cream-100",
        link: "text-gold-deep underline-offset-4 hover:underline px-0 h-auto",
        destructive: "bg-destructive text-cream hover:bg-destructive/90 shadow-sm",
      },
      size: {
        default: "h-10 px-5 text-sm",
        sm: "h-8 px-3 text-sm",
        lg: "h-12 px-7 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        disabled={loading || disabled}
        {...props}
      >
        {loading ? <Spinner /> : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" />
      <path className="opacity-75" d="M22 12a10 10 0 0 1-10 10" strokeLinecap="round" />
    </svg>
  );
}

export { buttonVariants };

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function maskPhone(phone: string): string {
  if (phone.length < 6) return phone;
  return `${phone.slice(0, 4)}***${phone.slice(-2)}`;
}

export function formatUzPhone(value: string): string {
  // Strip non-digits and leading +
  const digits = value.replace(/\D/g, "");
  // Always start with 998
  const trimmed = digits.startsWith("998") ? digits.slice(3) : digits;
  const parts = [
    trimmed.slice(0, 2),
    trimmed.slice(2, 5),
    trimmed.slice(5, 7),
    trimmed.slice(7, 9),
  ].filter(Boolean);
  if (parts.length === 0) return "+998 ";
  return `+998 ${parts.join(" ")}`.trim();
}

export function uzPhoneToE164(value: string): string {
  const digits = value.replace(/\D/g, "");
  const trimmed = digits.startsWith("998") ? digits : `998${digits}`;
  return `+${trimmed}`;
}

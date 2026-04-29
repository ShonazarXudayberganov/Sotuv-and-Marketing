import Link from "next/link";
import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="bg-cream flex min-h-screen flex-col">
      <header className="border-cream-200 border-b">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="font-display text-charcoal text-2xl tracking-tight">
            NEXUS <span className="text-gold-deep">AI</span>
          </Link>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">{children}</div>
      </main>

      <footer className="text-muted py-4 text-center text-xs">
        © {new Date().getFullYear()} NEXUS AI. Barcha huquqlar himoyalangan.
      </footer>
    </div>
  );
}

import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="from-cream via-cream to-cream-100 flex min-h-screen flex-col items-center justify-center bg-gradient-to-br px-4">
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-gold-deep font-accent mb-6 text-lg italic">
          O&apos;zbekiston biznesi uchun
        </p>
        <h1 className="text-charcoal font-display mb-6 text-6xl tracking-tight md:text-7xl">
          NEXUS <span className="text-gold-deep">AI</span>
        </h1>
        <p className="text-muted mb-10 text-lg leading-relaxed md:text-xl">
          CRM, SMM, Reklama, Inbox, Hisobotlar va Integratsiyalar — bir tizimda. AI har modulda
          — kontent yaratish, mijoz scoring, reklama optimizatsiyasi.
        </p>
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link href="/register">
            <Button size="lg">7 kunlik bepul sinov</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" size="lg">
              Kirish
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}

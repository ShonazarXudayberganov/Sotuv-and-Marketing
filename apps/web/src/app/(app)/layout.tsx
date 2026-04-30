import type { ReactNode } from "react";

import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { GraceBanner } from "@/components/shared/grace-banner";
import { ProtectedRoute } from "@/components/shared/protected-route";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-[var(--bg)]">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Navbar />
          <GraceBanner />
          <main className="flex-1 overflow-y-auto">
            <div className="w-full px-4 py-6 md:px-8 md:py-8 2xl:px-12">{children}</div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

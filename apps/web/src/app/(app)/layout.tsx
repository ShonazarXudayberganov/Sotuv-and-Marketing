import type { ReactNode } from "react";

import { GraceBanner } from "@/components/shared/grace-banner";
import { Header } from "@/components/shared/header";
import { ProtectedRoute } from "@/components/shared/protected-route";
import { Sidebar } from "@/components/shared/sidebar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="bg-cream flex min-h-screen">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          <GraceBanner />
          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-7xl p-6 md:p-8">{children}</div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

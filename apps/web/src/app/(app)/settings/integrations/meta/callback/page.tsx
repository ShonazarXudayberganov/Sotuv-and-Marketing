"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { integrationsApi } from "@/lib/smm-api";
import { extractApiError } from "@/lib/api-client";

type CallbackState = {
  kind: "loading" | "success" | "error";
  message: string;
};

export default function MetaOAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [state, setState] = useState<CallbackState>({
    kind: "loading",
    message: "Meta OAuth yakunlanmoqda...",
  });

  useEffect(() => {
    let active = true;

    async function run() {
      const error = searchParams.get("error");
      const errorReason = searchParams.get("error_description");
      const code = searchParams.get("code");
      const oauthState = searchParams.get("state");
      const redirectUri = `${window.location.origin}/settings/integrations/meta/callback`;

      if (error) {
        if (!active) return;
        setState({
          kind: "error",
          message: errorReason || "Meta OAuth rad etildi yoki tugamadi",
        });
        return;
      }

      if (!code || !oauthState) {
        if (!active) return;
        setState({
          kind: "error",
          message: "Meta OAuth callback parametrlari to'liq emas",
        });
        return;
      }

      try {
        await integrationsApi.finishMetaOAuth({
          code,
          state: oauthState,
          redirect_uri: redirectUri,
        });
      } catch (err) {
        if (!active) return;
        setState({ kind: "error", message: extractApiError(err) });
        return;
      }

      if (!active) return;
      setState({ kind: "success", message: "Meta OAuth yakunlandi. Qaytmoqda..." });
      window.setTimeout(() => {
        router.replace("/settings/integrations?oauth=meta-success");
      }, 900);
    }

    run();
    return () => {
      active = false;
    };
  }, [router, searchParams]);

  return (
    <div className="mx-auto max-w-xl py-12">
      <Card className="space-y-4 p-6">
        <div>
          <h1 className="text-[18px] font-semibold text-[var(--fg)]">Meta OAuth</h1>
          <p className="mt-1 text-[13px] text-[var(--fg-muted)]">{state.message}</p>
        </div>
        {state.kind === "error" ? (
          <div className="flex items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/settings/integrations">Integratsiyalarga qaytish</Link>
            </Button>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

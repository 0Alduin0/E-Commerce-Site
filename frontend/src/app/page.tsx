"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

type Health = {
  status: string;
  service: string;
  environment: string;
};

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: Health }
  | { kind: "error"; message: string };

export default function Home() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!API_URL) {
      setState({ kind: "error", message: "NEXT_PUBLIC_API_URL tanımlı değil (.env.local)." });
      return;
    }

    fetch(`${API_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<Health>;
      })
      .then((data) => setState({ kind: "ok", data }))
      .catch((err) =>
        setState({ kind: "error", message: err instanceof Error ? err.message : String(err) }),
      );
  }, []);

  return (
    <main className="flex min-h-full flex-1 flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-2xl font-semibold">E-Ticaret — Faz 1</h1>
      <p className="text-sm text-foreground/60">Backend bağlantı testi</p>

      <div className="rounded-lg border border-foreground/15 px-6 py-4 text-center">
        {state.kind === "loading" && <span className="text-foreground/60">Bağlanıyor…</span>}

        {state.kind === "ok" && (
          <div className="space-y-1">
            <p className="font-medium text-green-600">✓ Backend&apos;e bağlanıldı</p>
            <p className="text-sm text-foreground/70">
              {state.data.service} · {state.data.environment}
            </p>
          </div>
        )}

        {state.kind === "error" && (
          <div className="space-y-1">
            <p className="font-medium text-red-600">✗ Bağlantı başarısız</p>
            <p className="text-sm text-foreground/70">{state.message}</p>
            <p className="text-xs text-foreground/50">Backend çalışıyor mu? (uvicorn :8000)</p>
          </div>
        )}
      </div>
    </main>
  );
}

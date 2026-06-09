"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/lib/auth";

/**
 * Giriş / kayıt sayfası (tek formda sekme). Başarılı olunca `next` parametresine
 * (varsa, örn. ödeme akışından geldiyse) ya da ana sayfaya döner.
 *
 * useSearchParams() Suspense boundary gerektirir (Next prerender kuralı), bu yüzden
 * form içeriği ayrı bir bileşende ve Suspense ile sarmalı.
 */
export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex-1" />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const { login, register } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/";

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      router.push(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-12">
        <div className="mb-6 flex gap-2 rounded-lg bg-foreground/5 p-1">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => {
                setMode(m);
                setError(null);
              }}
              className={[
                "flex-1 rounded-md py-2 text-sm font-medium transition-colors",
                mode === m ? "bg-background shadow-sm" : "text-foreground/60",
              ].join(" ")}
            >
              {m === "login" ? "Giriş Yap" : "Kayıt Ol"}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="mb-1 block text-sm font-medium">Ad Soyad</label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ad Soyad"
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium">E-posta</label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ornek@eposta.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Şifre</label>
            <Input
              type="password"
              required
              minLength={mode === "register" ? 8 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "En az 8 karakter" : "Şifreniz"}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Lütfen bekleyin…" : mode === "login" ? "Giriş Yap" : "Kayıt Ol"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-foreground/50">
          <Link href="/" className="hover:text-foreground">
            ← Alışverişe dön
          </Link>
        </p>
      </main>
    </>
  );
}

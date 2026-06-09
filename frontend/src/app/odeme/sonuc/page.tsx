"use client";

import Link from "next/link";

import { Navbar } from "@/components/navbar";

/**
 * İyzico ödeme sonrası dönüş (callback) sayfası. Ödemenin GERÇEK onayı webhook'la
 * sunucuda yapılır — bu sayfa yalnızca kullanıcıyı bilgilendirir. Sipariş durumu
 * "Siparişlerim"de görünür (webhook işleyince 'paid' olur).
 */
export default function PaymentResultPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-lg flex-1 px-4 py-16 text-center">
        <div className="rounded-lg border border-foreground/10 p-8">
          <h1 className="text-2xl font-semibold tracking-tight">Ödemeniz alınıyor</h1>
          <p className="mt-3 text-foreground/70">
            Ödeme sonucunuz işleniyor. Onaylanınca siparişiniz “ödendi” durumuna
            geçecektir; bu birkaç saniye sürebilir.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/siparislerim"
              className="rounded-md bg-foreground px-4 py-2 text-sm text-background"
            >
              Siparişlerim
            </Link>
            <Link
              href="/"
              className="rounded-md border border-foreground/15 px-4 py-2 text-sm hover:bg-foreground/5"
            >
              Alışverişe devam
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}

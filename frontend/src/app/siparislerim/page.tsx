"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Navbar } from "@/components/navbar";
import { useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/format";
import { listMyOrders, STATUS_LABELS, type OrderSummary } from "@/lib/orders";

/** Kullanıcının siparişleri. Üyelik zorunlu — giriş yoksa giriş sayfasına yönlendirir. */
export default function MyOrdersPage() {
  const { user, accessToken, loading } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<OrderSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user || !accessToken) {
      router.replace("/giris?next=/siparislerim");
      return;
    }
    listMyOrders(accessToken)
      .then(setOrders)
      .catch((e) => setError(e instanceof Error ? e.message : "Hata"));
  }, [user, accessToken, loading, router]);

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Siparişlerim</h1>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {!orders && !error && <p className="text-foreground/50">Yükleniyor…</p>}

        {orders && orders.length === 0 && (
          <div className="py-16 text-center">
            <p className="text-foreground/60">Henüz siparişiniz yok.</p>
            <Link href="/" className="mt-3 inline-block text-sm underline">
              Alışverişe başla
            </Link>
          </div>
        )}

        {orders && orders.length > 0 && (
          <ul className="divide-y divide-foreground/10">
            {orders.map((o) => (
              <li key={o.id}>
                <Link
                  href={`/siparislerim/${o.id}`}
                  className="flex items-center justify-between py-4 hover:bg-foreground/[0.02]"
                >
                  <div>
                    <p className="font-medium">Sipariş #{o.id}</p>
                    <p className="text-sm text-foreground/50">
                      {new Date(o.created_at).toLocaleDateString("tr-TR")} · {o.item_count} ürün
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatPrice(o.total_amount)}</p>
                    <p className="text-sm text-foreground/60">
                      {STATUS_LABELS[o.status] ?? o.status}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Navbar } from "@/components/navbar";
import { useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/format";
import { getMyOrder, STATUS_LABELS, type Order } from "@/lib/orders";

/** Tek sipariş detayı (sahibi görebilir). Ödeme tamamlanınca buraya yönlenilir. */
export default function OrderDetailPage() {
  const { user, accessToken, loading } = useAuth();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const orderId = Number(params.id);

  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user || !accessToken) {
      router.replace(`/giris?next=/siparislerim/${orderId}`);
      return;
    }
    getMyOrder(accessToken, orderId)
      .then(setOrder)
      .catch((e) => setError(e instanceof Error ? e.message : "Hata"));
  }, [user, accessToken, loading, orderId, router]);

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <Link href="/siparislerim" className="text-sm text-foreground/60 hover:text-foreground">
          ← Siparişlerim
        </Link>

        {error && <p className="mt-6 text-sm text-red-600">{error}</p>}
        {!order && !error && <p className="mt-6 text-foreground/50">Yükleniyor…</p>}

        {order && (
          <div className="mt-6 space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight">Sipariş #{order.id}</h1>
                <p className="text-sm text-foreground/50">
                  {new Date(order.created_at).toLocaleString("tr-TR")}
                </p>
              </div>
              <span className="rounded-full bg-foreground/5 px-3 py-1 text-sm">
                {STATUS_LABELS[order.status] ?? order.status}
              </span>
            </div>

            {order.status === "pending" && (
              <p className="rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">
                Bu sipariş ödeme bekliyor. Ödeme adımı (İyzico) bir sonraki aşamada
                eklenecek; ödeme onaylanınca durum güncellenecektir.
              </p>
            )}

            <div>
              <h2 className="mb-2 text-sm font-medium text-foreground/60">Ürünler</h2>
              <ul className="divide-y divide-foreground/10 rounded-lg border border-foreground/10">
                {order.items.map((i) => (
                  <li key={i.id} className="flex justify-between gap-4 px-4 py-3">
                    <span>
                      {i.product_name}
                      {i.variant_label ? ` · ${i.variant_label}` : ""}
                      <span className="text-foreground/50"> × {i.quantity}</span>
                    </span>
                    <span className="font-medium">
                      {formatPrice(Number(i.unit_price) * i.quantity)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex justify-between border-t border-foreground/10 pt-4 text-lg font-semibold">
              <span>Toplam</span>
              <span>{formatPrice(order.total_amount)}</span>
            </div>

            <div>
              <h2 className="mb-2 text-sm font-medium text-foreground/60">Teslimat</h2>
              <div className="rounded-lg border border-foreground/10 px-4 py-3 text-sm text-foreground/80">
                <p>{order.shipping_full_name}</p>
                <p>{order.shipping_phone}</p>
                <p>{order.shipping_address}</p>
                <p>{order.shipping_city}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}

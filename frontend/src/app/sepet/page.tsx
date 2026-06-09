"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";
import { formatPrice } from "@/lib/format";

/** Sepet sayfası. Kalemleri listeler, adet/silme yönetir, ödemeye geçirir. */
export default function CartPage() {
  const { items, total, setQuantity, removeItem } = useCart();
  const { user } = useAuth();
  const router = useRouter();

  function goCheckout() {
    // Üyelik zorunlu: giriş yoksa önce giriş, sonra ödemeye dön.
    router.push(user ? "/odeme" : "/giris?next=/odeme");
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Sepet</h1>

        {items.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-foreground/60">Sepetiniz boş.</p>
            <Link href="/" className="mt-3 inline-block text-sm underline">
              Alışverişe başla
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            <ul className="divide-y divide-foreground/10">
              {items.map((item) => (
                <li key={item.variantId} className="flex items-center gap-4 py-4">
                  <div className="min-w-0 flex-1">
                    <Link
                      href={`/urun/${item.productSlug}`}
                      className="font-medium hover:underline"
                    >
                      {item.productName}
                    </Link>
                    {item.variantLabel && (
                      <p className="text-sm text-foreground/50">{item.variantLabel}</p>
                    )}
                    <p className="text-sm text-foreground/70">
                      {formatPrice(item.unitPrice)}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="size-8 rounded-md border border-foreground/15 hover:bg-foreground/5"
                      onClick={() => setQuantity(item.variantId, item.quantity - 1)}
                      aria-label="Azalt"
                    >
                      −
                    </button>
                    <span className="w-8 text-center">{item.quantity}</span>
                    <button
                      type="button"
                      className="size-8 rounded-md border border-foreground/15 hover:bg-foreground/5"
                      onClick={() => setQuantity(item.variantId, item.quantity + 1)}
                      aria-label="Artır"
                    >
                      +
                    </button>
                  </div>

                  <div className="w-24 text-right font-medium">
                    {formatPrice(Number(item.unitPrice) * item.quantity)}
                  </div>

                  <button
                    type="button"
                    className="text-sm text-foreground/40 hover:text-red-600"
                    onClick={() => removeItem(item.variantId)}
                    aria-label="Kaldır"
                  >
                    Sil
                  </button>
                </li>
              ))}
            </ul>

            <div className="flex items-center justify-between border-t border-foreground/10 pt-4">
              <span className="text-lg">Toplam</span>
              <span className="text-xl font-semibold">{formatPrice(total)}</span>
            </div>

            <div className="flex justify-end">
              <Button size="lg" onClick={goCheckout}>
                Ödemeye Geç
              </Button>
            </div>
          </div>
        )}
      </main>
    </>
  );
}

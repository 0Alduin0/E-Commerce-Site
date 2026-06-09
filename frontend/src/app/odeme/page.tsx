"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Navbar } from "@/components/navbar";
import { IyzicoCheckout } from "@/components/iyzico-checkout";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";
import { formatPrice } from "@/lib/format";
import { createOrder, type ShippingInput } from "@/lib/orders";
import { initPayment, PaymentsDisabledError } from "@/lib/payment";

/**
 * Ödeme/checkout: adres formu + sipariş oluşturma. Üyelik zorunlu — giriş yoksa
 * giriş sayfasına yönlendirir. Sipariş 'pending' oluşur; gerçek ödeme (İyzico)
 * Faz 8'de bu adıma eklenecek. Başarılı sipariş sonrası sepet temizlenir.
 */
export default function CheckoutPage() {
  const { user, accessToken, loading } = useAuth();
  const { items, total, clear } = useCart();
  const router = useRouter();

  const [shipping, setShipping] = useState<ShippingInput>({
    full_name: "",
    phone: "",
    address: "",
    city: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Ödeme başlatıldıysa İyzico iframe içeriği burada tutulur.
  const [checkoutContent, setCheckoutContent] = useState<string | null>(null);

  // Giriş yoksa (yükleme bitince) giriş sayfasına. Adı varsa forma ön-doldur.
  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/giris?next=/odeme");
      return;
    }
    if (user.full_name) {
      setShipping((s) => (s.full_name ? s : { ...s, full_name: user.full_name! }));
    }
  }, [user, loading, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setError(null);
    setBusy(true);
    try {
      // 1) Siparişi oluştur ('pending'). Stok burada düşmez; ödeme onayında düşer.
      const order = await createOrder(
        accessToken,
        items.map((i) => ({ variant_id: i.variantId, quantity: i.quantity })),
        shipping,
      );

      // 2) İyzico ödeme oturumunu başlat → iframe içeriğini göster.
      try {
        const payment = await initPayment(accessToken, order.id);
        clear(); // sipariş oluştu, sepeti boşalt
        setCheckoutContent(payment.checkout_form_content);
      } catch (payErr) {
        if (payErr instanceof PaymentsDisabledError) {
          // Ödeme yapılandırılmamış (İyzico anahtarı yok): sipariş 'pending' kaldı,
          // kullanıcıyı sipariş özetine götür (gerçek ödeme anahtar girilince çalışır).
          clear();
          router.push(`/siparislerim/${order.id}`);
          return;
        }
        throw payErr;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sipariş oluşturulamadı");
    } finally {
      setBusy(false);
    }
  }

  if (loading || !user) {
    return (
      <>
        <Navbar />
        <main className="flex flex-1 items-center justify-center">
          <p className="text-foreground/50">Yükleniyor…</p>
        </main>
      </>
    );
  }

  // Ödeme başlatıldıysa İyzico iframe'ini göster (sepet boşaltılmış olur).
  if (checkoutContent) {
    return (
      <>
        <Navbar />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
          <h1 className="mb-6 text-2xl font-semibold tracking-tight">Ödeme</h1>
          <p className="mb-4 text-sm text-foreground/60">
            Kart bilgileriniz güvenli İyzico ekranında işlenir; sitemize hiç ulaşmaz.
          </p>
          <IyzicoCheckout content={checkoutContent} />
        </main>
      </>
    );
  }

  if (items.length === 0) {
    return (
      <>
        <Navbar />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-16 text-center">
          <p className="text-foreground/60">Sepetiniz boş, ödeme yapılamaz.</p>
        </main>
      </>
    );
  }

  function field(key: keyof ShippingInput, label: string, opts?: { textarea?: boolean }) {
    return (
      <div>
        <label className="mb-1 block text-sm font-medium">{label}</label>
        {opts?.textarea ? (
          <textarea
            required
            className="w-full rounded-md border border-foreground/15 bg-transparent px-3 py-2 text-sm"
            rows={3}
            value={shipping[key]}
            onChange={(e) => setShipping((s) => ({ ...s, [key]: e.target.value }))}
          />
        ) : (
          <Input
            required
            value={shipping[key]}
            onChange={(e) => setShipping((s) => ({ ...s, [key]: e.target.value }))}
          />
        )}
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto grid w-full max-w-4xl flex-1 gap-8 px-4 py-8 md:grid-cols-2">
        <section>
          <h1 className="mb-6 text-2xl font-semibold tracking-tight">Teslimat Bilgileri</h1>
          <form onSubmit={onSubmit} className="space-y-4">
            {field("full_name", "Ad Soyad")}
            {field("phone", "Telefon")}
            {field("address", "Adres", { textarea: true })}
            {field("city", "Şehir")}

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" size="lg" className="w-full" disabled={busy}>
              {busy ? "Sipariş oluşturuluyor…" : "Siparişi Tamamla"}
            </Button>
            <p className="text-xs text-foreground/50">
              Ödeme adımı (İyzico) bir sonraki aşamada eklenecek. Şimdilik sipariş
              “ödeme bekleniyor” durumunda oluşturulur.
            </p>
          </form>
        </section>

        <section className="md:border-l md:border-foreground/10 md:pl-8">
          <h2 className="mb-4 text-lg font-medium">Sipariş Özeti</h2>
          <ul className="space-y-2 text-sm">
            {items.map((i) => (
              <li key={i.variantId} className="flex justify-between gap-4">
                <span className="text-foreground/70">
                  {i.productName}
                  {i.variantLabel ? ` · ${i.variantLabel}` : ""} × {i.quantity}
                </span>
                <span>{formatPrice(Number(i.unitPrice) * i.quantity)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-between border-t border-foreground/10 pt-4 font-semibold">
            <span>Toplam</span>
            <span>{formatPrice(total)}</span>
          </div>
        </section>
      </main>
    </>
  );
}

"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Variant } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { formatPrice } from "@/lib/format";

/**
 * Varyant seçimi + sepete ekle. Client Component (etkileşim).
 * Seçili varyantı sepete ekler (localStorage). Stok yoksa buton kilitli.
 * Sepetteki fiyat yalnızca gösterim — geçerli fiyat/stok sipariş anında backend'de.
 */
export function AddToCart({
  variants,
  productSlug,
  productName,
  coverImageUrl,
}: {
  variants: Variant[];
  productSlug: string;
  productName: string;
  coverImageUrl: string | null;
}) {
  const { addItem } = useCart();
  // İlk stokta olan varyantı seç; yoksa ilkini (tükendi gösterimi için).
  const initial = variants.find((v) => v.in_stock) ?? variants[0];
  const [selectedId, setSelectedId] = useState<number | null>(initial?.id ?? null);
  const [added, setAdded] = useState(false);

  if (variants.length === 0) {
    return <p className="text-sm text-foreground/60">Bu ürün şu an satışta değil.</p>;
  }

  const selected = variants.find((v) => v.id === selectedId) ?? null;

  function labelFor(v: Variant): string {
    const parts = [v.color, v.size].filter(Boolean);
    return parts.length > 0 ? parts.join(" / ") : "Standart";
  }

  return (
    <div className="space-y-4">
      {/* Varyant birden fazlaysa seçtir. */}
      {variants.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {variants.map((v) => {
            const active = v.id === selectedId;
            return (
              <button
                key={v.id}
                type="button"
                onClick={() => setSelectedId(v.id)}
                disabled={!v.in_stock}
                className={[
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "border-foreground bg-foreground text-background"
                    : "border-foreground/20 hover:border-foreground/40",
                  !v.in_stock && "cursor-not-allowed opacity-40 line-through",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {labelFor(v)}
              </button>
            );
          })}
        </div>
      )}

      {selected && (
        <div className="flex items-center gap-3">
          <span className="text-2xl font-semibold">{formatPrice(selected.price)}</span>
          {!selected.in_stock && <Badge variant="secondary">Tükendi</Badge>}
        </div>
      )}

      <Button
        size="lg"
        className="w-full sm:w-auto"
        disabled={!selected?.in_stock}
        onClick={() => {
          if (!selected) return;
          addItem({
            variantId: selected.id,
            productSlug,
            productName,
            variantLabel:
              labelFor(selected) === "Standart" ? null : labelFor(selected),
            unitPrice: selected.price,
            imageUrl: coverImageUrl,
          });
          setAdded(true);
          setTimeout(() => setAdded(false), 2000);
        }}
      >
        {!selected?.in_stock ? "Stokta Yok" : added ? "Sepete eklendi ✓" : "Sepete Ekle"}
      </Button>
    </div>
  );
}

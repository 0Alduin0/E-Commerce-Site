"use client";

import Image from "next/image";
import { useState } from "react";

import type { ProductImage } from "@/lib/api";

/**
 * Ürün detay galerisi. Büyük görsel + thumbnail şeridi (tıklayınca büyük değişir).
 * Client Component (seçim etkileşimi). Görsel yoksa placeholder.
 */
const IMAGE_HOST = process.env.NEXT_PUBLIC_IMAGE_HOST;

export function ProductGallery({ images, alt }: { images: ProductImage[]; alt: string }) {
  // Backend kapak'ı zaten ilk sıraya koyuyor; yine de güvenli ilk eleman.
  const [activeId, setActiveId] = useState<number | null>(images[0]?.id ?? null);

  if (images.length === 0) {
    return (
      <div className="flex aspect-square items-center justify-center rounded-lg bg-foreground/5">
        <span className="text-sm text-foreground/30">Görsel</span>
      </div>
    );
  }

  const active = images.find((i) => i.id === activeId) ?? images[0];

  return (
    <div className="space-y-3">
      <div className="relative aspect-square overflow-hidden rounded-lg bg-foreground/5">
        <Image
          src={active.url}
          alt={alt}
          fill
          sizes="(max-width: 768px) 100vw, 50vw"
          className="object-cover"
          priority
          unoptimized={!IMAGE_HOST}
        />
      </div>

      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto">
          {images.map((img) => {
            const isActive = img.id === active.id;
            return (
              <button
                key={img.id}
                type="button"
                onClick={() => setActiveId(img.id)}
                className={[
                  "relative size-16 shrink-0 overflow-hidden rounded-md border bg-foreground/5",
                  isActive ? "border-foreground" : "border-transparent hover:border-foreground/30",
                ].join(" ")}
                aria-label="Görseli göster"
              >
                <Image
                  src={img.url}
                  alt=""
                  fill
                  sizes="64px"
                  className="object-cover"
                  unoptimized={!IMAGE_HOST}
                />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

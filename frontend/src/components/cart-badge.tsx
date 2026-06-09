"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";

import { useCart } from "@/lib/cart";

/** Navbar'daki sepet linki + adet rozeti. Client (sepet state'ine bağlı). */
export function CartBadge() {
  const { itemCount } = useCart();

  return (
    <Link
      href="/sepet"
      className="relative flex items-center gap-2 text-sm text-foreground/70 hover:text-foreground"
      aria-label={`Sepet (${itemCount} ürün)`}
    >
      <span className="relative">
        <ShoppingCart className="size-5" />
        {itemCount > 0 && (
          <span className="absolute -right-2 -top-2 flex size-4 items-center justify-center rounded-full bg-foreground text-[10px] font-medium text-background">
            {itemCount > 9 ? "9+" : itemCount}
          </span>
        )}
      </span>
      <span className="hidden sm:inline">Sepet</span>
    </Link>
  );
}

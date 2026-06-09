import Link from "next/link";

import { AuthMenu } from "@/components/auth-menu";
import { CartBadge } from "@/components/cart-badge";

/** Üst menü. Logo + siparişlerim + sepet (adet rozetli) + oturum (giriş/çıkış). */
export function Navbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-foreground/10 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Mağaza
        </Link>
        <nav className="flex items-center gap-5">
          <Link
            href="/siparislerim"
            className="text-sm text-foreground/70 hover:text-foreground"
          >
            Siparişlerim
          </Link>
          <CartBadge />
          <AuthMenu />
        </nav>
      </div>
    </header>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth";

/**
 * Admin paneli koruması (mutlak kural: /admin yalnızca 'admin' rolüne açık).
 * Giriş yoksa /giris'e, admin değilse ana sayfaya yönlendirir. Guard client'ta;
 * gerçek yetki backend'de (require_admin) — burası yalnızca UX.
 */
const NAV = [
  { href: "/admin", label: "Panel" },
  { href: "/admin/urunler", label: "Ürünler" },
  { href: "/admin/siparisler", label: "Siparişler" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/giris?next=/admin");
    } else if (user.role !== "admin") {
      router.replace("/"); // yetkisiz: vitrine
    }
  }, [user, loading, router]);

  if (loading || !user || user.role !== "admin") {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-foreground/50">Yükleniyor…</p>
      </main>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-foreground/10 bg-background">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <span className="font-semibold">Yönetim</span>
            <nav className="flex gap-4 text-sm">
              {NAV.map((n) => {
                const active =
                  n.href === "/admin" ? pathname === "/admin" : pathname.startsWith(n.href);
                return (
                  <Link
                    key={n.href}
                    href={n.href}
                    className={active ? "font-medium" : "text-foreground/60 hover:text-foreground"}
                  >
                    {n.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/" className="text-foreground/60 hover:text-foreground">
              Vitrine dön
            </Link>
            <button onClick={logout} className="text-foreground/60 hover:text-foreground">
              Çıkış
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}

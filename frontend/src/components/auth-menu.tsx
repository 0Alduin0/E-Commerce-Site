"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";

/**
 * Navbar'ın oturum bölümü (client). Misafire "Giriş", girişli kullanıcıya
 * adı + "Çıkış", admin'e ayrıca "Yönetim" linki gösterir. İlk sessiz refresh
 * sürerken (loading) titremeyi önlemek için placeholder bırakılır.
 */
export function AuthMenu() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    // Layout kaymasını önlemek için sabit genişlikte boş alan.
    return <span className="w-16" aria-hidden />;
  }

  if (!user) {
    return (
      <Link
        href="/giris"
        className="text-sm text-foreground/70 hover:text-foreground"
      >
        Giriş
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-4">
      {user.role === "admin" && (
        <Link
          href="/admin"
          className="text-sm text-foreground/70 hover:text-foreground"
        >
          Yönetim
        </Link>
      )}
      <span className="hidden text-sm text-foreground/60 sm:inline">
        {user.full_name || user.email}
      </span>
      <button
        type="button"
        onClick={() => logout()}
        className="text-sm text-foreground/70 hover:text-foreground"
      >
        Çıkış
      </button>
    </div>
  );
}

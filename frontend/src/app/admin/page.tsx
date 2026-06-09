"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth";
import { getStats, type AdminStats } from "@/lib/admin";
import { formatPrice } from "@/lib/format";

/** Admin dashboard — temel metrikler. */
export default function AdminDashboard() {
  const { accessToken } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    getStats(accessToken)
      .then(setStats)
      .catch((e) => setError(e instanceof Error ? e.message : "Hata"));
  }, [accessToken]);

  const cards = stats
    ? [
        { label: "Ciro (ödenmiş)", value: formatPrice(stats.revenue) },
        { label: "Toplam sipariş", value: String(stats.total_orders) },
        { label: "Bekleyen sipariş", value: String(stats.pending_orders) },
        { label: "Bugünkü sipariş", value: String(stats.orders_today) },
        { label: "Ürün sayısı", value: String(stats.product_count) },
      ]
    : [];

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Panel</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {!stats && !error && <p className="text-foreground/50">Yükleniyor…</p>}

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {cards.map((c) => (
            <div key={c.label} className="rounded-lg border border-foreground/10 p-4">
              <p className="text-sm text-foreground/50">{c.label}</p>
              <p className="mt-1 text-xl font-semibold">{c.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

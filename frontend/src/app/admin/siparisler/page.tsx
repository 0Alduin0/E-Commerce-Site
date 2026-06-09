"use client";

import { useCallback, useEffect, useState } from "react";

import {
  listAdminOrders,
  updateOrderStatus,
  type AdminOrderSummary,
} from "@/lib/admin";
import { useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/orders";

/**
 * Admin sipariş yönetimi: tüm siparişler, durum filtresi, durum değiştirme.
 * 'paid' admin tarafından atanamaz (yalnızca ödeme webhook'u) — bu yüzden seçenekte yok.
 */
const ADMIN_STATUS_OPTIONS = ["preparing", "shipped", "delivered", "cancelled"];
const FILTERS = ["", "pending", "paid", "preparing", "shipped", "delivered", "cancelled"];

export default function AdminOrdersPage() {
  const { accessToken } = useAuth();
  const [orders, setOrders] = useState<AdminOrderSummary[] | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!accessToken) return;
    listAdminOrders(accessToken, filter || undefined)
      .then(setOrders)
      .catch((e) => setError(e instanceof Error ? e.message : "Hata"));
  }, [accessToken, filter]);

  useEffect(load, [load]);

  async function onChangeStatus(id: number, status: string) {
    if (!accessToken) return;
    try {
      await updateOrderStatus(accessToken, id, status);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Siparişler</h1>

      <div className="mb-4 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            onClick={() => setFilter(f)}
            className={[
              "rounded-full border px-3 py-1 text-sm",
              filter === f
                ? "border-foreground bg-foreground text-background"
                : "border-foreground/15 hover:bg-foreground/5",
            ].join(" ")}
          >
            {f === "" ? "Tümü" : STATUS_LABELS[f] ?? f}
          </button>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {!orders && !error && <p className="text-foreground/50">Yükleniyor…</p>}

      {orders && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-foreground/10 text-left text-foreground/50">
              <tr>
                <th className="py-2">#</th>
                <th className="py-2">Müşteri</th>
                <th className="py-2">Tarih</th>
                <th className="py-2">Tutar</th>
                <th className="py-2">Durum</th>
                <th className="py-2">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-foreground/5">
              {orders.map((o) => (
                <tr key={o.id}>
                  <td className="py-3 font-medium">#{o.id}</td>
                  <td className="py-3">{o.shipping_full_name}</td>
                  <td className="py-3 text-foreground/60">
                    {new Date(o.created_at).toLocaleDateString("tr-TR")}
                  </td>
                  <td className="py-3">{formatPrice(o.total_amount)}</td>
                  <td className="py-3">{STATUS_LABELS[o.status] ?? o.status}</td>
                  <td className="py-3">
                    {/* pending: ödeme bekliyor, admin değiştiremez (ödeme webhook'u sürer) */}
                    {o.status === "pending" ? (
                      <span className="text-foreground/40">ödeme bekliyor</span>
                    ) : (
                      <select
                        className="rounded-md border border-foreground/15 bg-transparent px-2 py-1 text-sm"
                        value=""
                        onChange={(e) => e.target.value && onChangeStatus(o.id, e.target.value)}
                      >
                        <option value="">Durum değiştir…</option>
                        {ADMIN_STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>
                            {STATUS_LABELS[s]}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {orders.length === 0 && (
            <p className="py-8 text-center text-foreground/50">Sipariş yok.</p>
          )}
        </div>
      )}
    </div>
  );
}

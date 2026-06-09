"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProductDetail } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  createProduct,
  deleteProduct,
  listAdminProducts,
} from "@/lib/admin";
import { formatPrice } from "@/lib/format";

/** Admin ürün listesi: tüm ürünler (pasif dahil), yeni ürün ekleme, silme. */
export default function AdminProductsPage() {
  const { accessToken } = useAuth();
  const [products, setProducts] = useState<ProductDetail[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);

  // Yeni ürün formu (en az bir varyantla oluşturulur).
  const [form, setForm] = useState({
    name: "",
    slug: "",
    description: "",
    sku: "",
    price: "",
    stock: "0",
  });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    if (!accessToken) return;
    listAdminProducts(accessToken)
      .then(setProducts)
      .catch((e) => setError(e instanceof Error ? e.message : "Hata"));
  }, [accessToken]);

  useEffect(load, [load]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setError(null);
    setSaving(true);
    try {
      await createProduct(accessToken, {
        name: form.name,
        slug: form.slug,
        description: form.description || null,
        variants: [
          { sku: form.sku, price: form.price, stock: Number(form.stock) },
        ],
      });
      setForm({ name: "", slug: "", description: "", sku: "", price: "", stock: "0" });
      setShowNew(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eklenemedi");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: number, name: string) {
    if (!accessToken) return;
    if (!confirm(`"${name}" ürünü ve tüm varyant/görselleri silinsin mi?`)) return;
    try {
      await deleteProduct(accessToken, id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Silinemedi");
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Ürünler</h1>
        <Button onClick={() => setShowNew((v) => !v)}>
          {showNew ? "Vazgeç" : "Yeni Ürün"}
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {showNew && (
        <form
          onSubmit={onCreate}
          className="mb-8 grid gap-3 rounded-lg border border-foreground/10 p-4 sm:grid-cols-2"
        >
          <Input
            required
            placeholder="Ürün adı"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Input
            required
            placeholder="slug (örn. basic-tisort)"
            value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
          />
          <Input
            className="sm:col-span-2"
            placeholder="Açıklama (opsiyonel)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <Input
            required
            placeholder="İlk varyant SKU"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              required
              type="number"
              step="0.01"
              placeholder="Fiyat"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
            <Input
              required
              type="number"
              placeholder="Stok"
              value={form.stock}
              onChange={(e) => setForm({ ...form, stock: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Kaydediliyor…" : "Ürünü Oluştur"}
            </Button>
          </div>
        </form>
      )}

      {!products && !error && <p className="text-foreground/50">Yükleniyor…</p>}

      {products && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-foreground/10 text-left text-foreground/50">
              <tr>
                <th className="py-2">Ürün</th>
                <th className="py-2">Varyant</th>
                <th className="py-2">Fiyat</th>
                <th className="py-2">Toplam stok</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-foreground/5">
              {products.map((p) => {
                const totalStock = p.variants.reduce((s, v) => s + v.stock, 0);
                return (
                  <tr key={p.id}>
                    <td className="py-3">
                      <Link href={`/admin/urunler/${p.id}`} className="font-medium hover:underline">
                        {p.name}
                      </Link>
                      <p className="text-xs text-foreground/40">{p.slug}</p>
                    </td>
                    <td className="py-3">{p.variants.length}</td>
                    <td className="py-3">{formatPrice(p.min_price)}</td>
                    <td className={totalStock === 0 ? "py-3 text-red-600" : "py-3"}>
                      {totalStock}
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        href={`/admin/urunler/${p.id}`}
                        className="mr-3 text-foreground/60 hover:text-foreground"
                      >
                        Düzenle
                      </Link>
                      <button
                        onClick={() => onDelete(p.id, p.name)}
                        className="text-foreground/40 hover:text-red-600"
                      >
                        Sil
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {products.length === 0 && (
            <p className="py-8 text-center text-foreground/50">Henüz ürün yok.</p>
          )}
        </div>
      )}
    </div>
  );
}

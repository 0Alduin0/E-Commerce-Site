"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProductDetail } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  addVariant,
  deleteImage,
  deleteVariant,
  listAdminProducts,
  updateProduct,
  updateVariant,
  uploadImage,
} from "@/lib/admin";

/**
 * Ürün düzenleme: üst-bilgi + varyant/stok yönetimi + görsel yükleme.
 * Admin uçlarından beslenir; tek üründe çoklu işlemleri tek ekranda toplar.
 */
export default function AdminProductEditPage() {
  const { accessToken } = useAuth();
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // admin/products listeden tek ürünü çek (ayrı tekil uç yok; liste yeterli).
  const load = useCallback(async () => {
    if (!accessToken) return;
    try {
      const all = await listAdminProducts(accessToken);
      const found = all.find((p) => p.id === productId) ?? null;
      setProduct(found);
      if (!found) setError("Ürün bulunamadı");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }, [accessToken, productId]);

  useEffect(() => {
    load();
  }, [load]);

  function flash(m: string) {
    setMsg(m);
    setTimeout(() => setMsg(null), 2000);
  }

  // --- Ürün üst-bilgi ---
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  useEffect(() => {
    if (product) {
      setName(product.name);
      setDescription(product.description ?? "");
    }
  }, [product]);

  async function saveInfo() {
    if (!accessToken) return;
    try {
      await updateProduct(accessToken, productId, { name, description: description || null });
      flash("Kaydedildi");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  // --- Varyant stok/fiyat ---
  async function saveVariant(variantId: number, price: string, stock: number) {
    if (!accessToken) return;
    try {
      await updateVariant(accessToken, variantId, { price, stock });
      flash("Varyant güncellendi");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  async function removeVariant(variantId: number) {
    if (!accessToken) return;
    try {
      await deleteVariant(accessToken, variantId);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  // --- Yeni varyant ---
  const [nv, setNv] = useState({ sku: "", color: "", size: "", price: "", stock: "0" });
  async function onAddVariant(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    try {
      await addVariant(accessToken, productId, {
        sku: nv.sku,
        color: nv.color || null,
        size: nv.size || null,
        price: nv.price,
        stock: Number(nv.stock),
      });
      setNv({ sku: "", color: "", size: "", price: "", stock: "0" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  // --- Görsel ---
  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !accessToken) return;
    try {
      await uploadImage(accessToken, productId, file);
      flash("Görsel yüklendi");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function onDeleteImage(imageId: number) {
    if (!accessToken) return;
    try {
      await deleteImage(accessToken, productId, imageId);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata");
    }
  }

  if (!product && !error) return <p className="text-foreground/50">Yükleniyor…</p>;
  if (error && !product) return <p className="text-sm text-red-600">{error}</p>;
  if (!product) return null;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/admin/urunler" className="text-sm text-foreground/60 hover:text-foreground">
          ← Ürünler
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">{product.name}</h1>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {msg && <p className="text-sm text-green-600">{msg}</p>}

      {/* Üst bilgi */}
      <section className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <h2 className="font-medium">Bilgiler</h2>
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ürün adı" />
        <textarea
          className="w-full rounded-md border border-foreground/15 bg-transparent px-3 py-2 text-sm"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Açıklama"
        />
        <Button onClick={saveInfo}>Kaydet</Button>
      </section>

      {/* Varyantlar / stok */}
      <section className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <h2 className="font-medium">Varyantlar &amp; Stok</h2>
        <ul className="space-y-2">
          {product.variants.map((v) => (
            <VariantRow
              key={v.id}
              sku={v.sku}
              label={[v.color, v.size].filter(Boolean).join(" / ") || "Standart"}
              price={v.price}
              stock={v.stock}
              onSave={(price, stock) => saveVariant(v.id, price, stock)}
              onDelete={() => removeVariant(v.id)}
            />
          ))}
        </ul>

        <form onSubmit={onAddVariant} className="flex flex-wrap items-end gap-2 border-t border-foreground/10 pt-3">
          <Input className="w-28" placeholder="SKU" required value={nv.sku} onChange={(e) => setNv({ ...nv, sku: e.target.value })} />
          <Input className="w-24" placeholder="Renk" value={nv.color} onChange={(e) => setNv({ ...nv, color: e.target.value })} />
          <Input className="w-20" placeholder="Beden" value={nv.size} onChange={(e) => setNv({ ...nv, size: e.target.value })} />
          <Input className="w-24" type="number" step="0.01" placeholder="Fiyat" required value={nv.price} onChange={(e) => setNv({ ...nv, price: e.target.value })} />
          <Input className="w-20" type="number" placeholder="Stok" value={nv.stock} onChange={(e) => setNv({ ...nv, stock: e.target.value })} />
          <Button type="submit" variant="outline">Varyant Ekle</Button>
        </form>
      </section>

      {/* Görseller */}
      <section className="space-y-3 rounded-lg border border-foreground/10 p-4">
        <h2 className="font-medium">Görseller</h2>
        <div className="flex flex-wrap gap-3">
          {product.images.map((img) => (
            <div key={img.id} className="relative">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={img.url} alt="" className="size-24 rounded-md border border-foreground/10 object-cover" />
              {img.is_cover && (
                <span className="absolute left-1 top-1 rounded bg-foreground px-1 text-[10px] text-background">
                  kapak
                </span>
              )}
              <button
                onClick={() => onDeleteImage(img.id)}
                className="absolute -right-2 -top-2 size-5 rounded-full bg-red-600 text-xs text-white"
                aria-label="Görseli sil"
              >
                ×
              </button>
            </div>
          ))}
          {product.images.length === 0 && (
            <p className="text-sm text-foreground/50">Henüz görsel yok.</p>
          )}
        </div>
        <input ref={fileRef} type="file" accept="image/*" onChange={onUpload} className="text-sm" />
        <p className="text-xs text-foreground/40">
          R2 yapılandırılmamışsa yükleme 503 döner (anahtarlar .env&apos;de).
        </p>
      </section>
    </div>
  );
}

/** Tek varyant satırı — fiyat/stok düzenlenir. */
function VariantRow({
  sku,
  label,
  price,
  stock,
  onSave,
  onDelete,
}: {
  sku: string;
  label: string;
  price: string;
  stock: number;
  onSave: (price: string, stock: number) => void;
  onDelete: () => void;
}) {
  const [p, setP] = useState(price);
  const [s, setS] = useState(String(stock));
  const dirty = p !== price || s !== String(stock);

  return (
    <li className="flex flex-wrap items-center gap-2">
      <span className="w-28 font-mono text-xs text-foreground/50">{sku}</span>
      <span className="w-28 text-sm">{label}</span>
      <Input className="w-24" type="number" step="0.01" value={p} onChange={(e) => setP(e.target.value)} />
      <Input className="w-20" type="number" value={s} onChange={(e) => setS(e.target.value)} />
      <Button size="sm" disabled={!dirty} onClick={() => onSave(p, Number(s))}>
        Kaydet
      </Button>
      <button onClick={onDelete} className="text-sm text-foreground/40 hover:text-red-600">
        Sil
      </button>
    </li>
  );
}

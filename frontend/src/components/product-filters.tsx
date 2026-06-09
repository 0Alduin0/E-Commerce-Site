"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Category } from "@/lib/api";

/**
 * Arama + kategori + sıralama. Client Component: state'i URL query param'larında
 * tutar (paylaşılabilir/SEO-dostu link). URL değişince Server Component liste
 * yeniden render olur — filtreleme backend'de yapılır, frontend sadece parametreyi taşır.
 */

const SORT_OPTIONS = [
  { value: "newest", label: "En yeni" },
  { value: "price_asc", label: "Fiyat: artan" },
  { value: "price_desc", label: "Fiyat: azalan" },
  { value: "name_asc", label: "İsim: A→Z" },
] as const;

const ALL_CATEGORIES = "__all__"; // Select boş değer kabul etmediği için sentinel

export function ProductFilters({ categories }: { categories: Category[] }) {
  const router = useRouter();
  const params = useSearchParams();
  const [search, setSearch] = useState(params.get("q") ?? "");

  /** Tek bir parametreyi günceller, sayfayı 1'e sıfırlar, yeni URL'e gider. */
  function setParam(key: string, value: string | null) {
    const next = new URLSearchParams(params.toString());
    if (value === null || value === "") {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    next.delete("page"); // filtre değişince ilk sayfaya dön
    router.push(`/?${next.toString()}`);
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <form
        className="flex-1"
        onSubmit={(e) => {
          e.preventDefault();
          setParam("q", search.trim() || null);
        }}
      >
        <Input
          type="search"
          placeholder="Ürün ara…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </form>

      <Select
        value={params.get("category") ?? ALL_CATEGORIES}
        onValueChange={(v) => setParam("category", v === ALL_CATEGORIES ? null : v)}
      >
        <SelectTrigger className="sm:w-44">
          <SelectValue placeholder="Kategori" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_CATEGORIES}>Tüm kategoriler</SelectItem>
          {categories.map((c) => (
            <SelectItem key={c.id} value={c.slug}>
              {c.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={params.get("sort") ?? "newest"}
        onValueChange={(v) => setParam("sort", v === "newest" ? null : v)}
      >
        <SelectTrigger className="sm:w-44">
          <SelectValue placeholder="Sırala" />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

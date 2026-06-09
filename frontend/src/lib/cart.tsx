"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/**
 * Sepet: tarayıcıda tutulur (React state + localStorage'da kalıcı). Kapsam kararı:
 * backend'de sepet tablosu YOK. Sipariş anında bu sepetten variant_id + adet
 * backend'e gönderilir; fiyat/stok orada doğrulanır (frontend fiyatına güvenilmez).
 *
 * Sepette gösterim için ürün adı/fiyatı snapshot tutulur (kart/özet için), ama
 * bunlar yalnızca GÖRSEL — sipariş geçerliliği backend'de belirlenir.
 */

export type CartItem = {
  variantId: number;
  productSlug: string;
  productName: string;
  variantLabel: string | null;
  unitPrice: string; // string: kuruş hassasiyeti (backend Decimal'i ile aynı)
  imageUrl: string | null;
  quantity: number;
};

type CartContextValue = {
  items: CartItem[];
  itemCount: number; // toplam adet (rozet için)
  total: number; // gösterim amaçlı toplam (TL)
  addItem: (item: Omit<CartItem, "quantity">, quantity?: number) => void;
  removeItem: (variantId: number) => void;
  setQuantity: (variantId: number, quantity: number) => void;
  clear: () => void;
};

const STORAGE_KEY = "cart:v1";
const CartContext = createContext<CartContextValue | null>(null);

function loadInitial(): CartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CartItem[]) : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [hydrated, setHydrated] = useState(false);

  // İlk yüklemede localStorage'dan oku (SSR/hydration uyumsuzluğunu önlemek için
  // efekt içinde — sunucu boş sepetle render eder, istemci doldurur).
  useEffect(() => {
    setItems(loadInitial());
    setHydrated(true);
  }, []);

  // Her değişimde localStorage'a yaz (hydrate olduktan sonra; yoksa boşla ezeriz).
  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items, hydrated]);

  const value = useMemo<CartContextValue>(() => {
    const itemCount = items.reduce((sum, i) => sum + i.quantity, 0);
    const total = items.reduce((sum, i) => sum + Number(i.unitPrice) * i.quantity, 0);

    return {
      items,
      itemCount,
      total,
      addItem: (item, quantity = 1) =>
        setItems((prev) => {
          const existing = prev.find((i) => i.variantId === item.variantId);
          if (existing) {
            return prev.map((i) =>
              i.variantId === item.variantId
                ? { ...i, quantity: i.quantity + quantity }
                : i,
            );
          }
          return [...prev, { ...item, quantity }];
        }),
      removeItem: (variantId) =>
        setItems((prev) => prev.filter((i) => i.variantId !== variantId)),
      setQuantity: (variantId, quantity) =>
        setItems((prev) =>
          quantity <= 0
            ? prev.filter((i) => i.variantId !== variantId)
            : prev.map((i) => (i.variantId === variantId ? { ...i, quantity } : i)),
        ),
      clear: () => setItems([]),
    };
  }, [items]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart, CartProvider içinde kullanılmalı");
  return ctx;
}

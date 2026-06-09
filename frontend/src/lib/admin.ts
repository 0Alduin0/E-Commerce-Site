/**
 * Admin API çağrıları (hepsi auth'lu, admin rolü gerektirir). Backend /admin/*
 * uçlarına bağlanır. Token çağıran taraftan (useAuth) gelir.
 */

import type { ProductDetail } from "@/lib/api";
import type { Order } from "@/lib/orders";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type AdminOrderSummary = {
  id: number;
  status: string;
  total_amount: string;
  item_count: number;
  created_at: string;
  user_id: number | null;
  shipping_full_name: string;
};

export type AdminStats = {
  total_orders: number;
  pending_orders: number;
  orders_today: number;
  revenue: string;
  product_count: number;
};

export type VariantInput = {
  sku: string;
  color?: string | null;
  size?: string | null;
  price: string;
  stock: number;
};

async function req<T>(token: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    const detail = err?.detail;
    throw new Error(typeof detail === "string" ? detail : "İşlem başarısız");
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- İstatistik ---
export const getStats = (token: string) => req<AdminStats>(token, "/admin/stats");

// --- Ürünler ---
export const listAdminProducts = (token: string, q?: string) =>
  req<ProductDetail[]>(token, `/admin/products${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const createProduct = (
  token: string,
  body: {
    name: string;
    slug: string;
    description?: string | null;
    category_id?: number | null;
    variants: VariantInput[];
  },
) => req<ProductDetail>(token, "/products", { method: "POST", body: JSON.stringify(body) });

export const updateProduct = (
  token: string,
  id: number,
  body: Partial<{
    name: string;
    slug: string;
    description: string | null;
    category_id: number | null;
    is_active: boolean;
  }>,
) => req<ProductDetail>(token, `/products/${id}`, { method: "PATCH", body: JSON.stringify(body) });

export const deleteProduct = (token: string, id: number) =>
  req<void>(token, `/products/${id}`, { method: "DELETE" });

// --- Varyant / stok ---
export const addVariant = (token: string, productId: number, body: VariantInput) =>
  req<unknown>(token, `/admin/products/${productId}/variants`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const updateVariant = (
  token: string,
  variantId: number,
  body: Partial<{ price: string; stock: number; is_active: boolean; color: string | null; size: string | null }>,
) => req<unknown>(token, `/admin/variants/${variantId}`, { method: "PATCH", body: JSON.stringify(body) });

export const deleteVariant = (token: string, variantId: number) =>
  req<void>(token, `/admin/variants/${variantId}`, { method: "DELETE" });

// --- Görsel ---
export async function uploadImage(token: string, productId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/products/${productId}/images`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }, // Content-Type'ı FormData kendi koyar
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(typeof err?.detail === "string" ? err.detail : "Görsel yüklenemedi");
  }
  return res.json();
}

export const deleteImage = (token: string, productId: number, imageId: number) =>
  req<void>(token, `/products/${productId}/images/${imageId}`, { method: "DELETE" });

// --- Siparişler ---
export const listAdminOrders = (token: string, status?: string) =>
  req<AdminOrderSummary[]>(token, `/admin/orders${status ? `?status=${status}` : ""}`);

export const getAdminOrder = (token: string, id: number) =>
  req<Order>(token, `/admin/orders/${id}`);

export const updateOrderStatus = (token: string, id: number, status: string) =>
  req<Order>(token, `/admin/orders/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

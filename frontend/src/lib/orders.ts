/**
 * Sipariş API'si (client tarafı, auth'lu). Server fetch'ler lib/api.ts'te;
 * bunlar kullanıcının access token'ıyla çağrılır.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type OrderItemInput = { variant_id: number; quantity: number };

export type ShippingInput = {
  full_name: string;
  phone: string;
  address: string;
  city: string;
};

export type OrderItem = {
  id: number;
  variant_id: number | null;
  product_name: string;
  variant_label: string | null;
  unit_price: string;
  quantity: number;
};

export type Order = {
  id: number;
  status: string;
  total_amount: string;
  shipping_full_name: string;
  shipping_phone: string;
  shipping_address: string;
  shipping_city: string;
  items: OrderItem[];
  created_at: string;
};

export type OrderSummary = {
  id: number;
  status: string;
  total_amount: string;
  item_count: number;
  created_at: string;
};

/** Sipariş durumu → Türkçe etiket (vitrin gösterimi). */
export const STATUS_LABELS: Record<string, string> = {
  pending: "Ödeme bekleniyor",
  paid: "Ödendi",
  preparing: "Hazırlanıyor",
  shipped: "Kargoda",
  delivered: "Teslim edildi",
  cancelled: "İptal edildi",
};

async function authed(token: string, path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });
}

export async function createOrder(
  token: string,
  items: OrderItemInput[],
  shipping: ShippingInput,
): Promise<Order> {
  const res = await authed(token, "/orders", {
    method: "POST",
    body: JSON.stringify({ items, shipping }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    // Backend 409'da {message, errors[]} döner; kullanıcıya anlaşılır mesaj ver.
    const detail = err?.detail;
    if (detail && typeof detail === "object" && Array.isArray(detail.errors)) {
      throw new Error(detail.errors.join(" "));
    }
    throw new Error(typeof detail === "string" ? detail : "Sipariş oluşturulamadı");
  }
  return res.json();
}

export async function listMyOrders(token: string): Promise<OrderSummary[]> {
  const res = await authed(token, "/orders");
  if (!res.ok) throw new Error("Siparişler alınamadı");
  return res.json();
}

export async function getMyOrder(token: string, id: number): Promise<Order> {
  const res = await authed(token, `/orders/${id}`);
  if (!res.ok) throw new Error("Sipariş bulunamadı");
  return res.json();
}

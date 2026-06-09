/** Ödeme API'si (client, auth'lu). İyzico iframe içeriğini backend'den alır. */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type PaymentInit = {
  checkout_form_content: string; // İyzico'nun iframe'i çizen <script> içeriği
  token: string;
};

export class PaymentsDisabledError extends Error {}

export async function initPayment(token: string, orderId: number): Promise<PaymentInit> {
  const res = await fetch(`${API_URL}/payments/${orderId}/init`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 503) {
    // Ödeme yapılandırılmamış (İyzico anahtarı yok) — çağıran tarafa bildir.
    throw new PaymentsDisabledError("Ödeme şu an yapılandırılmamış.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(typeof err?.detail === "string" ? err.detail : "Ödeme başlatılamadı");
  }
  return res.json();
}

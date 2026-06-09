/** Fiyat biçimlendirme. Backend Decimal'i string olarak döner; burada TL formatına çeviririz. */

const tl = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "TRY",
  minimumFractionDigits: 2,
});

export function formatPrice(value: string | number | null): string {
  if (value === null) return "—";
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return "—";
  return tl.format(num);
}

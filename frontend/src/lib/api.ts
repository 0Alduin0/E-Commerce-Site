/**
 * Backend (FastAPI) ile konuşan tek nokta. Tip tanımları backend şemalarını
 * (app/schemas/product.py) yansıtır. Fetch'ler Server Component'lerde çalışır;
 * API_URL koda gömülmez, .env'den gelir (NEXT_PUBLIC_API_URL).
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// --- Tipler (backend şemalarının aynası) ---

export type Category = {
  id: number;
  name: string;
  slug: string;
};

export type Variant = {
  id: number;
  sku: string;
  color: string | null;
  size: string | null;
  price: string; // backend Decimal'i JSON'da string döner — kuruş hassasiyeti korunur
  stock: number;
  in_stock: boolean;
};

export type ProductImage = {
  id: number;
  url: string;
  sort_order: number;
  is_cover: boolean;
};

export type ProductListItem = {
  id: number;
  name: string;
  slug: string;
  category: Category | null;
  min_price: string | null;
  in_stock: boolean;
  cover_image_url: string | null;
};

export type ProductListResponse = {
  items: ProductListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ProductDetail = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  category: Category | null;
  variants: Variant[];
  images: ProductImage[];
  min_price: string | null;
  in_stock: boolean;
  created_at: string;
};

export type ProductSort = "newest" | "price_asc" | "price_desc" | "name_asc";

export type ProductQuery = {
  q?: string;
  category?: string;
  min_price?: string;
  max_price?: string;
  sort?: ProductSort;
  page?: number;
  page_size?: number;
};

// --- Yardımcı: API tabanı garanti ---

function apiBase(): string {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL tanımlı değil (.env.local).");
  }
  return API_URL;
}

// --- Fetch fonksiyonları (Server Component'lerden çağrılır) ---

/**
 * Ürün listesi. Vitrin sayfası ürünleri sık değiştiği için kısa süreli
 * revalidate (60sn) ile cache'lenir — her istek backend'e gitmez ama veri bayatlamaz.
 */
export async function getProducts(query: ProductQuery = {}): Promise<ProductListResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const url = `${apiBase()}/products?${params.toString()}`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`Ürünler alınamadı (HTTP ${res.status})`);
  return res.json();
}

export async function getCategories(): Promise<Category[]> {
  const res = await fetch(`${apiBase()}/categories`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`Kategoriler alınamadı (HTTP ${res.status})`);
  return res.json();
}

/**
 * Tek ürün (slug ile). Bulunamazsa null döner — sayfa bunu 404'e çevirir.
 */
export async function getProduct(slug: string): Promise<ProductDetail | null> {
  const res = await fetch(`${apiBase()}/products/${encodeURIComponent(slug)}`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Ürün alınamadı (HTTP ${res.status})`);
  return res.json();
}

import { getCategories, getProducts, type ProductSort } from "@/lib/api";
import { Navbar } from "@/components/navbar";
import { ProductCard } from "@/components/product-card";
import { ProductFilters } from "@/components/product-filters";
import { Pagination } from "@/components/pagination";

const PAGE_SIZE = 12;
const VALID_SORTS: ProductSort[] = ["newest", "price_asc", "price_desc", "name_asc"];

/**
 * Vitrin ana sayfası = ürün listesi. Server Component (SEO + ilk yük hızı):
 * veri sunucuda çekilir, HTML hazır gelir. Filtreler URL query param'larında;
 * etkileşimli filtre çubuğu ayrı bir Client Component.
 */
export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const sp = await searchParams;

  const page = Math.max(1, Number(sp.page) || 1);
  const sort: ProductSort =
    sp.sort && VALID_SORTS.includes(sp.sort as ProductSort)
      ? (sp.sort as ProductSort)
      : "newest";

  // Kategoriler ve ürünler paralel çekilir.
  const [categories, data] = await Promise.all([
    getCategories(),
    getProducts({
      q: sp.q,
      category: sp.category,
      min_price: sp.min_price,
      max_price: sp.max_price,
      sort,
      page,
      page_size: PAGE_SIZE,
    }),
  ]);

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Ürünler</h1>

        <div className="mb-8">
          <ProductFilters categories={categories} />
        </div>

        {data.items.length === 0 ? (
          <p className="py-16 text-center text-foreground/60">
            Aramanıza uygun ürün bulunamadı.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {data.items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            <div className="mt-10">
              <Pagination
                page={data.page}
                total={data.total}
                pageSize={data.page_size}
                searchParams={sp}
              />
            </div>
          </>
        )}
      </main>
    </>
  );
}

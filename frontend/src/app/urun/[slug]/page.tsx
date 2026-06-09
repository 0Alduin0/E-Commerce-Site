import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getProduct } from "@/lib/api";
import { Navbar } from "@/components/navbar";
import { AddToCart } from "@/components/add-to-cart";
import { ProductGallery } from "@/components/product-gallery";

/**
 * Ürün detay sayfası. Server Component + dinamik route.
 * Her ürünün KENDİ metadata'sı var (title/description) → Google'da ayrı ayrı
 * çıkar. Ürün yoksa Next'in notFound() ile 404'e düşer.
 */

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) {
    return { title: "Ürün bulunamadı" };
  }
  // description yoksa ada dayalı makul bir özet üret.
  const desc = product.description?.slice(0, 160) ?? `${product.name} — mağazamızda.`;
  return {
    title: product.name,
    description: desc,
    openGraph: { title: product.name, description: desc },
  };
}

export default async function ProductPage({ params }: Props) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Link href="/" className="text-sm text-foreground/60 hover:text-foreground">
          ← Ürünlere dön
        </Link>

        <div className="mt-6 grid gap-8 md:grid-cols-2">
          <ProductGallery images={product.images} alt={product.name} />

          <div className="space-y-5">
            {product.category && (
              <p className="text-sm text-foreground/50">{product.category.name}</p>
            )}
            <h1 className="text-3xl font-semibold tracking-tight">{product.name}</h1>

            {product.description && (
              <p className="leading-relaxed text-foreground/70">{product.description}</p>
            )}

            <AddToCart
              variants={product.variants}
              productSlug={product.slug}
              productName={product.name}
              coverImageUrl={product.images[0]?.url ?? null}
            />
          </div>
        </div>
      </main>
    </>
  );
}

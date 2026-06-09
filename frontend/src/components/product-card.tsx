import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { ProductImage } from "@/components/product-image";
import type { ProductListItem } from "@/lib/api";
import { formatPrice } from "@/lib/format";

/**
 * Ürün listesi kartı. Server Component (etkileşim yok) — SEO ve hız için.
 * Stok bittiğinde ürün listede KALIR, "Tükendi" rozetiyle gösterilir (kapsam kararı).
 */
export function ProductCard({ product }: { product: ProductListItem }) {
  return (
    <Link href={`/urun/${product.slug}`} className="group block">
      <Card className="h-full overflow-hidden transition-shadow hover:shadow-md">
        <div className="relative">
          <ProductImage url={product.cover_image_url} alt={product.name} />
          {!product.in_stock && (
            <Badge variant="secondary" className="absolute right-2 top-2">
              Tükendi
            </Badge>
          )}
        </div>
        <CardContent className="pt-4">
          {product.category && (
            <p className="text-xs text-foreground/50">{product.category.name}</p>
          )}
          <h3 className="mt-1 line-clamp-2 font-medium group-hover:underline">
            {product.name}
          </h3>
        </CardContent>
        <CardFooter className="text-sm text-foreground/70">
          {product.min_price !== null && (
            <span>
              <span className="text-foreground/50">başlayan fiyat </span>
              <span className="font-semibold text-foreground">
                {formatPrice(product.min_price)}
              </span>
            </span>
          )}
        </CardFooter>
      </Card>
    </Link>
  );
}

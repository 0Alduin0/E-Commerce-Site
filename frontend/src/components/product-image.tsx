import Image from "next/image";

/**
 * Ürün görseli + yer tutucu. URL yoksa "Görsel" placeholder'ı gösterir
 * (görsel henüz yüklenmemiş ürünler — Faz 5 öncesi veri).
 *
 * next/image host'u .env'deki NEXT_PUBLIC_IMAGE_HOST ile whitelist'lenir. Host
 * tanımlı değilse unoptimized=true ile yine de gösterilir (build kırılmaz).
 */
const IMAGE_HOST = process.env.NEXT_PUBLIC_IMAGE_HOST;

export function ProductImage({
  url,
  alt,
  priority = false,
}: {
  url: string | null;
  alt: string;
  priority?: boolean;
}) {
  if (!url) {
    return (
      <div className="flex aspect-square items-center justify-center bg-foreground/5">
        <span className="text-xs text-foreground/30">Görsel</span>
      </div>
    );
  }

  return (
    <div className="relative aspect-square overflow-hidden bg-foreground/5">
      <Image
        src={url}
        alt={alt}
        fill
        sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
        className="object-cover"
        priority={priority}
        // Host whitelist'te değilse optimizasyonu atla (yine de gösterilir).
        unoptimized={!IMAGE_HOST}
      />
    </div>
  );
}

import type { NextConfig } from "next";

/**
 * Ürün görselleri R2'den (veya custom domain) gelir. next/image güvenlik için
 * uzak host'ları whitelist ister. Host'u env'den alıyoruz (NEXT_PUBLIC_IMAGE_HOST,
 * örn. "cdn.site.com" veya "<account>.r2.cloudflarestorage.com"). Tanımlı değilse
 * uzak görsel optimizasyonu devre dışı — placeholder akışı yine çalışır.
 */
const imageHost = process.env.NEXT_PUBLIC_IMAGE_HOST;

const nextConfig: NextConfig = {
  images: {
    remotePatterns: imageHost
      ? [{ protocol: "https", hostname: imageHost }]
      : [],
  },
};

export default nextConfig;

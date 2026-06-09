"use client";

import { useEffect, useRef } from "react";

/**
 * İyzico Checkout Form gömücü. İyzico'nun init cevabı bir <script> içerir; React
 * dangerouslySetInnerHTML ile basılan script ÇALIŞMAZ. Bu yüzden HTML'i parse edip
 * script elementlerini yeniden oluşturup DOM'a ekliyoruz (tarayıcı böylece çalıştırır).
 *
 * İyzico script'i, sayfadaki #iyzipay-checkout-form div'ine ödeme iframe'ini çizer.
 */
export function IyzicoCheckout({ content }: { content: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !content) return;

    // İçeriği geçici bir kapta parse et, script'leri yeniden oluştur.
    const temp = document.createElement("div");
    temp.innerHTML = content;

    const added: HTMLScriptElement[] = [];
    temp.querySelectorAll("script").forEach((old) => {
      const script = document.createElement("script");
      // Öznitelikleri kopyala (src, type vb.).
      for (const attr of Array.from(old.attributes)) {
        script.setAttribute(attr.name, attr.value);
      }
      script.text = old.textContent ?? "";
      document.body.appendChild(script);
      added.push(script);
    });

    // Script dışı içerik (varsa) doğrudan basılabilir.
    temp.querySelectorAll("script").forEach((s) => s.remove());
    container.innerHTML = temp.innerHTML;

    return () => {
      // Sayfa değişince eklenen script'leri temizle.
      added.forEach((s) => s.remove());
    };
  }, [content]);

  return (
    <div>
      {/* İyzico iframe'ini buraya çizer. */}
      <div id="iyzipay-checkout-form" className="responsive" ref={containerRef} />
    </div>
  );
}

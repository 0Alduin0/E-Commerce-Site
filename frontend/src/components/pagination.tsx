import Link from "next/link";

/**
 * Basit sayfalama. Server Component: her sayfa ayrı URL (?page=N) → SEO-dostu,
 * crawl edilebilir. Mevcut query param'ları korur.
 */
export function Pagination({
  page,
  total,
  pageSize,
  searchParams,
}: {
  page: number;
  total: number;
  pageSize: number;
  searchParams: Record<string, string | undefined>;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  function hrefFor(target: number): string {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(searchParams)) {
      if (v !== undefined && k !== "page") params.set(k, v);
    }
    params.set("page", String(target));
    return `/?${params.toString()}`;
  }

  const prevDisabled = page <= 1;
  const nextDisabled = page >= totalPages;

  const linkCls =
    "rounded-md border border-foreground/15 px-3 py-1.5 text-sm hover:bg-foreground/5";
  const disabledCls =
    "rounded-md border border-foreground/10 px-3 py-1.5 text-sm text-foreground/30 pointer-events-none";

  return (
    <nav className="flex items-center justify-center gap-3" aria-label="Sayfalama">
      {prevDisabled ? (
        <span className={disabledCls}>← Önceki</span>
      ) : (
        <Link href={hrefFor(page - 1)} className={linkCls}>
          ← Önceki
        </Link>
      )}
      <span className="text-sm text-foreground/60">
        {page} / {totalPages}
      </span>
      {nextDisabled ? (
        <span className={disabledCls}>Sonraki →</span>
      ) : (
        <Link href={hrefFor(page + 1)} className={linkCls}>
          Sonraki →
        </Link>
      )}
    </nav>
  );
}

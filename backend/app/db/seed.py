"""Geliştirme için örnek veri ekler. Idempotent: veri varsa tekrar eklemez.

Çalıştırma (backend/ içinde):
    .\\venv\\Scripts\\python.exe -m app.db.seed
"""

from decimal import Decimal

from sqlmodel import Session, select

from app.db.session import engine
from app.models import Category, Product, ProductVariant


def seed() -> None:
    with Session(engine) as session:
        if session.exec(select(Product)).first():
            print("Veri zaten mevcut, seed atlanıyor.")
            return

        tisort = Category(name="Tişört", slug="tisort")
        ayakkabi = Category(name="Ayakkabı", slug="ayakkabi")
        session.add_all([tisort, ayakkabi])
        session.commit()
        session.refresh(tisort)
        session.refresh(ayakkabi)

        # Varyantlı ürün: aynı tişört, farklı renk/beden → her biri ayrı stok/fiyat.
        basic_tee = Product(
            name="Basic Tişört",
            slug="basic-tisort",
            description="%100 pamuk basic tişört.",
            category_id=tisort.id,
            variants=[
                ProductVariant(sku="TEE-RED-M", color="Kırmızı", size="M",
                               price=Decimal("199.90"), stock=15),
                ProductVariant(sku="TEE-RED-L", color="Kırmızı", size="L",
                               price=Decimal("199.90"), stock=8),
                ProductVariant(sku="TEE-BLK-L", color="Siyah", size="L",
                               price=Decimal("219.90"), stock=0),  # stokta yok senaryosu
            ],
        )

        # "Varyantsız" ürün de tek bir default varyantla satılır.
        sneaker = Product(
            name="Koşu Ayakkabısı",
            slug="kosu-ayakkabisi",
            description="Hafif koşu ayakkabısı.",
            category_id=ayakkabi.id,
            variants=[
                ProductVariant(sku="SNK-DEFAULT", price=Decimal("1499.00"), stock=25),
            ],
        )

        session.add_all([basic_tee, sneaker])
        session.commit()
        print("Seed tamam: 2 kategori, 2 ürün, 4 varyant eklendi.")


def report() -> None:
    """Veriyi geri okuyup ilişkilerin çalıştığını gösterir."""
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        print(f"\n--- Veritabanı raporu ({len(products)} ürün) ---")
        for p in products:
            print(f"[{p.category.name}] {p.name} (slug={p.slug})")
            for v in p.variants:
                etiket = " / ".join(x for x in (v.color, v.size) if x) or "tek tip"
                print(f"    • {v.sku}: {etiket} — {v.price} TL, stok: {v.stock}")


if __name__ == "__main__":
    seed()
    report()

"""Ürün ve kategori endpoint'leri.

Vitrin (public): kategori listesi, ürün listesi (arama/filtre/sıralama/sayfalama),
ürün detayı (slug ile). Yalnızca aktif ürün/varyant gösterilir.

Admin (require_admin): ürün ekle/güncelle/sil. Fiyat ve stok varyantta olduğu
için ürün üst-bilgisi ile varyantlar birlikte oluşturulur.

Fiyat/stok ProductVariant'ta. "Ürün fiyatı" = aktif varyantların min fiyatı;
"stokta" = en az bir aktif varyantın stock > 0 olması. Bu türetilmiş değerleri
SQL tarafında (subquery) hesaplayıp hem filtre/sıralamada hem cevapta kullanıyoruz.
"""

import logging
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import require_admin
from app.core.config import settings
from app.db.session import get_session

logger = logging.getLogger(__name__)
from app.models import Category, Product, ProductVariant, User
from app.schemas.product import (
    CategoryPublic,
    ImagePublic,
    ProductCreate,
    ProductDetail,
    ProductListItem,
    ProductListResponse,
    ProductUpdate,
    VariantPublic,
)


def _sorted_images(product: Product) -> list:
    """Görselleri kapak önce, sonra sort_order'a göre sıralar (deterministik)."""
    return sorted(product.images, key=lambda i: (not i.is_cover, i.sort_order, i.id))


def _cover_url(product: Product) -> str | None:
    """Kapak görseli URL'i: is_cover olan, yoksa ilk görsel, hiç yoksa None."""
    images = _sorted_images(product)
    return images[0].url if images else None

router = APIRouter(tags=["products"])


class ProductSort(str, Enum):
    """Vitrin sıralama seçenekleri."""

    newest = "newest"          # en yeni (varsayılan)
    price_asc = "price_asc"    # fiyat artan
    price_desc = "price_desc"  # fiyat azalan
    name_asc = "name_asc"      # ada göre A→Z


# --- Türetilmiş alan yardımcıları -------------------------------------------

def _product_to_detail(product: Product, only_active: bool = True) -> ProductDetail:
    """Ürünü detay şemasına çevirir. only_active=True (vitrin) yalnızca aktif
    varyantları gösterir; admin (only_active=False) pasif varyantları da görür."""
    shown_variants = [v for v in product.variants if v.is_active or not only_active]
    prices = [v.price for v in shown_variants]
    return ProductDetail(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        category=CategoryPublic.model_validate(product.category) if product.category else None,
        variants=[
            VariantPublic(
                id=v.id, sku=v.sku, color=v.color, size=v.size,
                price=v.price, stock=v.stock, in_stock=v.stock > 0,
            )
            for v in shown_variants
        ],
        images=[
            ImagePublic(id=i.id, url=i.url, sort_order=i.sort_order, is_cover=i.is_cover)
            for i in _sorted_images(product)
        ],
        min_price=min(prices) if prices else None,
        in_stock=any(v.stock > 0 for v in shown_variants),
        created_at=product.created_at,
    )


# --- Kategori ----------------------------------------------------------------

@router.get("/categories", response_model=list[CategoryPublic])
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return session.exec(select(Category).order_by(Category.name)).all()


# --- Ürün listesi (vitrin) ---------------------------------------------------

@router.get("/products", response_model=ProductListResponse)
def list_products(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="İsimde geçen metin"),
    category: str | None = Query(default=None, description="Kategori slug'ı"),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort: ProductSort = Query(default=ProductSort.newest),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
) -> ProductListResponse:
    """Aktif ürünleri sayfalı döner. Fiyat filtresi/sıralaması, aktif varyantların
    min/max fiyatı üzerinden yapılır (stoğu 0 olan ürün de listede kalır — 'Tükendi')."""

    # Her ürün için aktif varyantların fiyat aggregate'i (subquery).
    price_agg = (
        select(
            ProductVariant.product_id.label("pid"),
            func.min(ProductVariant.price).label("min_price"),
            func.max(ProductVariant.price).label("max_price"),
            func.coalesce(func.sum(ProductVariant.stock), 0).label("total_stock"),
        )
        .where(ProductVariant.is_active == True)  # noqa: E712 (SQL boolean)
        .group_by(ProductVariant.product_id)
        .subquery()
    )

    base = (
        select(Product, price_agg.c.min_price, price_agg.c.total_stock)
        .join(price_agg, price_agg.c.pid == Product.id)
        .where(Product.is_active == True)  # noqa: E712
    )

    if q:
        base = base.where(Product.name.ilike(f"%{q}%"))
    if category:
        base = base.join(Category, Category.id == Product.category_id).where(
            Category.slug == category
        )
    if min_price is not None:
        base = base.where(price_agg.c.min_price >= min_price)
    if max_price is not None:
        base = base.where(price_agg.c.min_price <= max_price)

    # Toplam (sayfalamadan önce) — subquery'yi sayarak.
    total = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()

    # Sıralama.
    if sort == ProductSort.price_asc:
        base = base.order_by(price_agg.c.min_price.asc())
    elif sort == ProductSort.price_desc:
        base = base.order_by(price_agg.c.min_price.desc())
    elif sort == ProductSort.name_asc:
        base = base.order_by(Product.name.asc())
    else:  # newest
        base = base.order_by(Product.created_at.desc())

    rows = session.exec(base.offset((page - 1) * page_size).limit(page_size)).all()

    items = [
        ProductListItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            category=CategoryPublic.model_validate(product.category) if product.category else None,
            min_price=min_p,
            in_stock=total_stock > 0,
            cover_image_url=_cover_url(product),
        )
        for product, min_p, total_stock in rows
    ]
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


# --- Ürün detayı (vitrin) ----------------------------------------------------

@router.get("/products/{slug}", response_model=ProductDetail)
def get_product(slug: str, session: Session = Depends(get_session)) -> ProductDetail:
    product = session.exec(
        select(Product).where(Product.slug == slug, Product.is_active == True)  # noqa: E712
    ).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")
    return _product_to_detail(product)


# --- Admin: yazma ------------------------------------------------------------

@router.post(
    "/products",
    response_model=ProductDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> ProductDetail:
    if session.exec(select(Product).where(Product.slug == data.slug)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu slug zaten kullanımda")

    if data.category_id is not None and session.get(Category, data.category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kategori bulunamadı")

    product = Product(
        name=data.name,
        slug=data.slug,
        description=data.description,
        category_id=data.category_id,
        variants=[ProductVariant(**v.model_dump()) for v in data.variants],
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_to_detail(product)


@router.patch("/products/{product_id}", response_model=ProductDetail)
def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> ProductDetail:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")

    fields = data.model_dump(exclude_unset=True)  # yalnızca gönderilen alanlar
    if "slug" in fields:
        clash = session.exec(
            select(Product).where(Product.slug == fields["slug"], Product.id != product_id)
        ).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu slug zaten kullanımda")
    if "category_id" in fields and fields["category_id"] is not None:
        if session.get(Category, fields["category_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kategori bulunamadı")

    for key, value in fields.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_to_detail(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> None:
    """Ürünü siler. Varyant + görsel KAYITLARI cascade ile gider; R2'deki görsel
    dosyaları da temizlenir (çöp birikmesin — mutlak kural).

    Sıra: önce R2'den dosyalar (kayıtlar hâlâ elimizdeyken), sonra DB satırı.
    Bir dosya silinemezse log'lanıp devam edilir — DB tutarlılığı R2'ye takılmasın.
    """
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")

    if settings.images_enabled:
        from app.services import storage  # lazy: R2 yoksa import maliyeti yok

        for image in product.images:
            try:
                storage.delete_object(image.r2_key)
            except Exception:  # noqa: BLE001 — tek bir dosya silinmesi tüm işlemi bozmamalı
                logger.warning("R2 görseli silinemedi: key=%s", image.r2_key)

    session.delete(product)
    session.commit()

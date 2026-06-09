"""Admin yönetim uçları (hepsi require_admin). /admin prefix'i; sadece 'admin'
rolü erişir. Vitrin uçlarından ayrı tutulur çünkü admin pasif ürün/varyantı da
görür ve tüm siparişleri yönetir.
"""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.api.deps import require_admin
from app.db.session import get_session
from app.models import (
    Order,
    OrderStatus,
    Product,
    ProductVariant,
    User,
)
from app.schemas.order import AdminOrderSummary, OrderPublic, OrderStatusUpdate
from app.schemas.product import (
    ProductDetail,
    VariantCreate,
    VariantPublic,
    VariantUpdate,
)

# products.py'deki detay dönüştürücüyü yeniden kullan (tek doğruluk kaynağı).
from app.api.routes.products import _product_to_detail

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- Ürünler (admin görünümü: pasif dahil) ----------------------------------

@router.get("/products", response_model=list[ProductDetail])
def admin_list_products(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None),
) -> list[ProductDetail]:
    """Tüm ürünler (aktif + pasif), tam detayıyla. Vitrin filtresi uygulanmaz."""
    stmt = select(Product).order_by(Product.created_at.desc())
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    products = session.exec(stmt).all()
    return [_product_to_detail(p, only_active=False) for p in products]


# --- Varyant yönetimi (stok/fiyat) ------------------------------------------

@router.post(
    "/products/{product_id}/variants",
    response_model=VariantPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_variant(
    product_id: int,
    data: VariantCreate,
    session: Session = Depends(get_session),
) -> VariantPublic:
    if session.get(Product, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")
    if session.exec(select(ProductVariant).where(ProductVariant.sku == data.sku)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu SKU zaten kullanımda")

    variant = ProductVariant(product_id=product_id, **data.model_dump())
    session.add(variant)
    session.commit()
    session.refresh(variant)
    return VariantPublic(
        id=variant.id, sku=variant.sku, color=variant.color, size=variant.size,
        price=variant.price, stock=variant.stock, in_stock=variant.stock > 0,
    )


@router.patch("/variants/{variant_id}", response_model=VariantPublic)
def update_variant(
    variant_id: int,
    data: VariantUpdate,
    session: Session = Depends(get_session),
) -> VariantPublic:
    """Varyant stok/fiyat/durum güncelle (stok takibi ekranı bunu kullanır)."""
    variant = session.get(ProductVariant, variant_id)
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Varyant bulunamadı")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, key, value)
    session.add(variant)
    session.commit()
    session.refresh(variant)
    return VariantPublic(
        id=variant.id, sku=variant.sku, color=variant.color, size=variant.size,
        price=variant.price, stock=variant.stock, in_stock=variant.stock > 0,
    )


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    variant_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Varyant sil. Son varyantı silmeye izin verilmez — ürün satılamaz hâle gelmesin."""
    variant = session.get(ProductVariant, variant_id)
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Varyant bulunamadı")
    sibling_count = session.exec(
        select(func.count()).select_from(ProductVariant).where(
            ProductVariant.product_id == variant.product_id
        )
    ).one()
    if sibling_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ürünün son varyantı silinemez. Önce ürünü pasifleştirin veya silin.",
        )
    session.delete(variant)
    session.commit()


# --- Sipariş yönetimi -------------------------------------------------------

@router.get("/orders", response_model=list[AdminOrderSummary])
def admin_list_orders(
    session: Session = Depends(get_session),
    order_status: OrderStatus | None = Query(default=None, alias="status"),
) -> list[AdminOrderSummary]:
    """Tüm siparişler (en yeni önce), opsiyonel durum filtresi."""
    stmt = select(Order).order_by(Order.created_at.desc())
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)
    orders = session.exec(stmt).all()
    return [
        AdminOrderSummary(
            id=o.id, status=o.status, total_amount=o.total_amount,
            item_count=sum(i.quantity for i in o.items), created_at=o.created_at,
            user_id=o.user_id, shipping_full_name=o.shipping_full_name,
        )
        for o in orders
    ]


@router.get("/orders/{order_id}", response_model=OrderPublic)
def admin_get_order(order_id: int, session: Session = Depends(get_session)) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sipariş bulunamadı")
    return order


# İzin verilen durum geçişleri. 'paid'e GEÇİŞ admin'e açık DEĞİL — o yalnızca
# İyzico webhook'uyla olur (mutlak kural). Admin operasyonel akışı yönetir.
_ADMIN_ALLOWED_STATUSES = {
    OrderStatus.preparing,
    OrderStatus.shipped,
    OrderStatus.delivered,
    OrderStatus.cancelled,
}


@router.patch("/orders/{order_id}/status", response_model=OrderPublic)
def admin_update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    session: Session = Depends(get_session),
) -> Order:
    """Sipariş durumunu değiştir. 'paid' atanamaz (yalnızca ödeme webhook'u yapar)."""
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sipariş bulunamadı")
    if data.status not in _ADMIN_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{data.status.value}' durumu admin tarafından atanamaz "
            "('paid' yalnızca ödeme onayıyla gelir).",
        )
    order.status = data.status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# --- İstatistik (dashboard) -------------------------------------------------

@router.get("/stats")
def admin_stats(session: Session = Depends(get_session)) -> dict:
    """Temel dashboard metrikleri. 'Ciro' yalnızca ödenmiş+ sonrası siparişlerden
    sayılır (pending ödenmemiştir → ciroya dahil edilmez)."""
    revenue_statuses = [
        OrderStatus.paid, OrderStatus.preparing, OrderStatus.shipped, OrderStatus.delivered,
    ]

    total_orders = session.exec(select(func.count()).select_from(Order)).one()
    pending_orders = session.exec(
        select(func.count()).select_from(Order).where(Order.status == OrderStatus.pending)
    ).one()
    revenue = session.exec(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.status.in_(revenue_statuses)
        )
    ).one()
    product_count = session.exec(select(func.count()).select_from(Product)).one()

    # Bugünün siparişleri (UTC gün başı).
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    orders_today = session.exec(
        select(func.count()).select_from(Order).where(Order.created_at >= today_start)
    ).one()

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "orders_today": orders_today,
        "revenue": str(Decimal(revenue)),  # Decimal → string (kuruş hassasiyeti)
        "product_count": product_count,
    }

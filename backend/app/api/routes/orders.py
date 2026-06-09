"""Sipariş endpoint'leri (auth zorunlu — üyelik zorunlu kararı, Faz 3).

Akış (POST /orders):
1. İstemciden gelen kalemler (variant_id + adet) doğrulanır.
2. Fiyat ve ad SUNUCUDA, DB'den okunur (frontend fiyatına güvenilmez).
3. Stok kontrol edilir — yetersizse TÜM sipariş reddedilir (kararı: hep ya da hiç).
4. Sipariş 'pending' oluşturulur. STOK BURADA DÜŞMEZ — yalnızca İyzico webhook'u
   ödemeyi onaylayınca düşer (Faz 8). Ödenmeyen sipariş stok kilitlemez.
5. Toplam tutar kalemlerden hesaplanıp snapshot olarak sabitlenir.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import Order, OrderItem, OrderStatus, Product, ProductVariant, User
from app.schemas.order import (
    OrderCreate,
    OrderItemPublic,
    OrderPublic,
    OrderSummary,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _variant_label(variant: ProductVariant) -> str | None:
    parts = [p for p in (variant.color, variant.size) if p]
    return " / ".join(parts) if parts else None


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Order:
    # Aynı varyant birden çok kalemde gelebilir → toplam adetle stok kontrolü yap.
    qty_by_variant: dict[int, int] = {}
    for item in data.items:
        qty_by_variant[item.variant_id] = qty_by_variant.get(item.variant_id, 0) + item.quantity

    # Varyantları tek sorguda çek.
    variants = session.exec(
        select(ProductVariant).where(ProductVariant.id.in_(qty_by_variant.keys()))
    ).all()
    variant_by_id = {v.id: v for v in variants}

    # Doğrulama: var mı, aktif mi, stok yeter mi? Hepsini topla, ilk hatada değil
    # sonunda dön ki kullanıcı tüm sorunlu kalemleri görebilsin.
    errors: list[str] = []
    for variant_id, total_qty in qty_by_variant.items():
        variant = variant_by_id.get(variant_id)
        if variant is None or not variant.is_active:
            errors.append(f"Varyant {variant_id} bulunamadı veya satışta değil.")
            continue
        if variant.stock < total_qty:
            errors.append(
                f"'{variant.sku}' için yeterli stok yok (istenen {total_qty}, mevcut {variant.stock})."
            )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Sipariş oluşturulamadı.", "errors": errors},
        )

    # Ürün adlarını snapshot için topluca çek.
    product_ids = {v.product_id for v in variants}
    products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    product_name_by_id = {p.id: p.name for p in products}

    # Kalemleri ve toplamı kur. Fiyat DB'den (snapshot) — istemciden değil.
    order_items: list[OrderItem] = []
    total = Decimal("0.00")
    for item in data.items:
        variant = variant_by_id[item.variant_id]
        line_price = variant.price  # DB'deki güncel fiyat = sipariş anı snapshot'ı
        total += line_price * item.quantity
        order_items.append(
            OrderItem(
                variant_id=variant.id,
                product_name=product_name_by_id.get(variant.product_id, "Ürün"),
                variant_label=_variant_label(variant),
                unit_price=line_price,
                quantity=item.quantity,
            )
        )

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.pending,  # ödeme öncesi; stok henüz düşmedi
        total_amount=total,
        shipping_full_name=data.shipping.full_name,
        shipping_phone=data.shipping.phone,
        shipping_address=data.shipping.address,
        shipping_city=data.shipping.city,
        items=order_items,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.get("", response_model=list[OrderSummary])
def list_my_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[OrderSummary]:
    """Kullanıcının kendi siparişleri (en yeni önce)."""
    orders = session.exec(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).all()
    # item_count'u kalemlerden türet (lazy-load; sipariş sayısı kullanıcı başına az).
    return [
        OrderSummary(
            id=o.id,
            status=o.status,
            total_amount=o.total_amount,
            item_count=sum(i.quantity for i in o.items),
            created_at=o.created_at,
        )
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderPublic)
def get_my_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Order:
    """Tek sipariş — yalnızca sahibi görebilir (admin yönetimi Faz 7'de ayrı)."""
    order = session.get(Order, order_id)
    if order is None or order.user_id != current_user.id:
        # 'Yok' ile 'başkasının' ayırt edilmez — bilgi sızdırmamak için tek tip 404.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sipariş bulunamadı")
    return order

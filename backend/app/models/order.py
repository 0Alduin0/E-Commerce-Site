from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.product import ProductVariant
    from app.models.user import User


class OrderStatus(str, Enum):
    """Sipariş yaşam döngüsü. 'paid'e geçiş YALNIZCA İyzico webhook'uyla yapılır (Faz 8)."""

    pending = "pending"        # beklemede (oluşturuldu, ödenmedi)
    paid = "paid"              # ödendi (webhook doğruladı)
    preparing = "preparing"    # hazırlanıyor
    shipped = "shipped"        # kargoda
    delivered = "delivered"    # teslim edildi
    cancelled = "cancelled"    # iptal


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    # user_id nullable: misafir alışveriş kararı Faz 3'te netleşecek; şimdilik esnek tutuldu.
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    status: OrderStatus = Field(default=OrderStatus.pending, index=True)
    # Toplam tutar — sipariş anındaki kalemlerden hesaplanıp burada sabitlenir (snapshot).
    total_amount: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)

    # Teslimat adresi snapshot'ı (kullanıcı sonradan adresini değiştirse de sipariş sabit kalır).
    shipping_full_name: str = Field(max_length=255)
    shipping_phone: str = Field(max_length=50)
    shipping_address: str
    shipping_city: str = Field(max_length=100)

    # Ödeme izi (Faz 8). payment_token: İyzico checkout oturumu; provider_payment_id:
    # İyzico'daki ödeme kimliği (denetim). Kart verisi ASLA tutulmaz.
    payment_token: str | None = Field(default=None, max_length=255, index=True)
    provider_payment_id: str | None = Field(default=None, max_length=255)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship()
    items: list["OrderItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class OrderItem(SQLModel, table=True):
    """Sipariş kalemi. Ürün adı/varyant/fiyat SNAPSHOT olarak tutulur:
    ürün sonradan değişse/silinse bile geçmiş sipariş bozulmaz."""

    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    # Varyant silinse bile kalem kalsın diye nullable + snapshot alanları tutulur.
    variant_id: int | None = Field(default=None, foreign_key="product_variants.id", index=True)

    product_name: str = Field(max_length=255)          # snapshot
    variant_label: str | None = Field(default=None, max_length=255)  # örn. "Kırmızı / L"
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)      # snapshot (sipariş anı fiyatı)
    quantity: int = Field(ge=1)

    order: "Order" = Relationship(back_populates="items")
    variant: Optional["ProductVariant"] = Relationship(back_populates="order_items")

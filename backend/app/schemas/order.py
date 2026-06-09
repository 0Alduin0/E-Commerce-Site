"""Sipariş şemaları.

Kritik güvenlik kuralı: istemci yalnızca variant_id + adet gönderir. Fiyat ve
ürün/varyant adı SUNUCUDA, DB'den okunarak belirlenir — frontend'in gönderdiği
fiyata ASLA güvenilmez (aksi halde kullanıcı fiyatı manipüle edebilir).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


# --- İstek ------------------------------------------------------------------

class OrderItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1, le=999)


class ShippingAddress(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1)
    city: str = Field(min_length=1, max_length=100)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    shipping: ShippingAddress


# --- Cevap ------------------------------------------------------------------

class OrderItemPublic(BaseModel):
    id: int
    variant_id: int | None
    product_name: str
    variant_label: str | None
    unit_price: Decimal
    quantity: int

    model_config = {"from_attributes": True}


class OrderPublic(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
    shipping_full_name: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    items: list[OrderItemPublic]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderSummary(BaseModel):
    """Sipariş listesi için hafif görünüm (kalemler olmadan)."""

    id: int
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime


# --- Admin ------------------------------------------------------------------

class AdminOrderSummary(OrderSummary):
    """Admin sipariş listesi: müşteri bilgisini de taşır."""

    user_id: int | None
    shipping_full_name: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

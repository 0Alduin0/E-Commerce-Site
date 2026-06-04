from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.order import OrderItem


class Product(SQLModel, table=True):
    """Ürünün ortak/paylaşılan bilgisi. Satılabilir birim (fiyat + stok)
    ProductVariant'tadır — varyantsız ürünler de tek bir 'default' varyantla satılır."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(unique=True, index=True, max_length=255)
    description: str | None = Field(default=None)
    category_id: int | None = Field(default=None, foreign_key="categories.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    category: Optional["Category"] = Relationship(back_populates="products")
    variants: list["ProductVariant"] = Relationship(
        back_populates="product",
        # Ürün silinince varyantları da silinir (yetim kayıt kalmaz).
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ProductVariant(SQLModel, table=True):
    """Satılabilir birim. Stok ve fiyat BURADA tutulur (varyant düzeyi kararı)."""

    __tablename__ = "product_variants"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    sku: str = Field(unique=True, index=True, max_length=100)
    color: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=100)
    # Para: Numeric(10,2) — ASLA float. Yuvarlama hatası ödemede kabul edilemez.
    price: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    product: "Product" = Relationship(back_populates="variants")
    order_items: list["OrderItem"] = Relationship(back_populates="variant")

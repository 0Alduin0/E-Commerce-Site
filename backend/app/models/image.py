from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.product import Product


class ProductImage(SQLModel, table=True):
    """Bir ürünün görseli. DB'de YALNIZCA URL + R2 anahtarı tutulur, görselin
    kendisi R2'dedir (mutlak kural).

    - url: tarayıcının göstereceği tam adres (R2 public/custom domain).
    - r2_key: bucket içindeki nesne anahtarı (uuid'li ad) — silmek için gerekir.
    - sort_order: galeri sırası (küçük önce).
    - is_cover: liste/kart için kapak görseli. Ürün başına en fazla bir tane true.
    """

    __tablename__ = "product_images"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    url: str = Field(max_length=1024)
    r2_key: str = Field(max_length=512, index=True)
    sort_order: int = Field(default=0)
    is_cover: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    product: "Product" = Relationship(back_populates="images")

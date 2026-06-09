"""Ürün ve kategori API şemaları.

Tasarım: fiyat ve stok ProductVariant'ta. Vitrin için "ürünün fiyatı" =
varyantların en düşük fiyatı (min_price); "stokta var mı" = herhangi bir aktif
varyantta stock > 0. Bu türetilmiş alanları response'a koyuyoruz ki frontend
hesaplama yapmasın.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Kategori ---------------------------------------------------------------

class CategoryPublic(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


# --- Görsel -----------------------------------------------------------------

class ImagePublic(BaseModel):
    id: int
    url: str
    sort_order: int
    is_cover: bool

    model_config = {"from_attributes": True}


# --- Varyant ----------------------------------------------------------------

class VariantPublic(BaseModel):
    id: int
    sku: str
    color: str | None
    size: str | None
    price: Decimal
    stock: int
    in_stock: bool  # stock > 0 — frontend "Tükendi" rozetini buna göre koyar

    model_config = {"from_attributes": True}


# --- Ürün: liste (hafif) ----------------------------------------------------

class ProductListItem(BaseModel):
    """Liste kartı için yeterli alanlar. Tüm varyantları taşımaz — sadece özet."""

    id: int
    name: str
    slug: str
    category: CategoryPublic | None
    min_price: Decimal | None   # vitrinde gösterilen "₺X'den başlayan" fiyat
    in_stock: bool              # en az bir varyant stokta mı
    cover_image_url: str | None  # liste kartı için kapak görseli (yoksa None)

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Sayfalı liste cevabı. Toplam sayı ile frontend sayfa sayısını hesaplar."""

    items: list[ProductListItem]
    total: int
    page: int
    page_size: int


# --- Ürün: detay (tam) ------------------------------------------------------

class ProductDetail(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    category: CategoryPublic | None
    variants: list[VariantPublic]
    images: list[ImagePublic]
    min_price: Decimal | None
    in_stock: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Admin: yazma şemaları --------------------------------------------------

class VariantCreate(BaseModel):
    sku: str = Field(max_length=100)
    color: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=100)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)


class ProductCreate(BaseModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: str | None = None
    category_id: int | None = None
    # Ürün en az bir varyantla oluşturulur (varyantsız ürün de tek 'default' varyant).
    variants: list[VariantCreate] = Field(min_length=1)


class ProductUpdate(BaseModel):
    """Kısmi güncelleme — yalnızca gönderilen alanlar değişir. Varyant yönetimi
    ayrı uçlarda yapılır (bu faz kapsamında ürün üst-bilgisi güncellenir)."""

    name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


class VariantUpdate(BaseModel):
    """Varyant kısmi güncelleme (admin stok/fiyat yönetimi)."""

    color: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

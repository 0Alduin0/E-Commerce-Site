"""Tüm SQLModel modelleri buradan import edilir.

Alembic'in autogenerate'i ve SQLModel.metadata'nın eksiksiz olması için
her yeni model bu dosyaya eklenmeli. Tek import noktası = tek doğruluk kaynağı.
"""

from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem, OrderStatus

__all__ = [
    "User",
    "UserRole",
    "Category",
    "Product",
    "ProductVariant",
    "Order",
    "OrderItem",
    "OrderStatus",
]

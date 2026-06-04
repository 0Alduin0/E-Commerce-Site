from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(unique=True, index=True, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    products: list["Product"] = Relationship(back_populates="category")


# İlişkilerin çözülmesi için Product'ın import edilmesi (tip ipucu, döngüsel import güvenli)
from app.models.product import Product  # noqa: E402

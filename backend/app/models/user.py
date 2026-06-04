from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """Kullanıcı rolü. Token içine konur; /admin erişimi 'admin' rolüne bağlanır (Faz 3/7)."""

    user = "user"
    admin = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"  # "user" çoğu DB'de ayrılmış kelime; çoğul ad kullanılır.

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    # Şifre ASLA düz saklanmaz; Faz 3'te passlib + bcrypt ile hash'lenip buraya yazılır.
    hashed_password: str
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.user)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

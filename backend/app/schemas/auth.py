"""Kimlik doğrulama şemaları: kayıt, giriş ve token cevapları."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    """Kayıt isteği. Şifre düz gelir, sunucuda hash'lenir; asla geri dönmez."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Kullanıcının dışarı verilen güvenli görünümü. hashed_password YOK."""

    id: int
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    """Login/refresh cevabı. Refresh token ayrıca httpOnly cookie'ye de yazılır;
    body'deki kopya, cookie kullanmayan istemciler (mobil vb.) için bırakılır."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Cookie'siz istemciler için refresh token'ı body'de göndermeye izin verir.
    Cookie varsa o önceliklidir (route'ta ele alınır)."""

    refresh_token: str | None = None

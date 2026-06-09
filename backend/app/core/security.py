"""Güvenlik çekirdeği: şifre hash'leme ve JWT üretimi/doğrulaması.

Mutlak kural: şifre asla düz saklanmaz (bcrypt). Sırlar koda gömülmez
(settings.JWT_SECRET .env'den gelir). Token üretimi ve doğrulaması tek yerde
toplanır ki access/refresh tutarlı kalsın.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Not: passlib yerine doğrudan bcrypt kullanıyoruz. passlib 1.7.4 bakımsız ve
# yeni bcrypt sürümlerinde (__about__ kaldırıldı) sürekli uyarı/uyumsuzluk üretiyor.
# bcrypt kütüphanesi tek başına salt üretimi + doğrulama için yeterli.

# Token türleri. Refresh token ile access token endpoint'lerine girilememeli;
# bu yüzden payload'a "type" koyuyoruz ve doğrularken bekleneni kontrol ediyoruz.
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


# --- Şifre ---------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """bcrypt ile hash'ler (her çağrıda rastgele salt). Sonuç DB'ye str olarak yazılır.

    bcrypt 72 byte'tan uzun girdileri sessizce kırpar; bu bilinen bir sınırdır ve
    8–128 karakterlik şifre politikamızda pratikte sorun olmaz.
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# --- JWT -----------------------------------------------------------------

def _create_token(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,          # kullanıcı id'si (string)
        "role": role,            # yetki kontrolü için token içinde taşınır
        "type": token_type,      # access | refresh
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    return _create_token(
        subject,
        role,
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str, role: str) -> str:
    return _create_token(
        subject,
        role,
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str) -> dict:
    """Token'ı çöz ve türünü doğrula. Geçersiz/süresi dolmuş/yanlış türse
    JWTError fırlatır (çağıran 401'e çevirir)."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise JWTError(f"Beklenen token türü '{expected_type}', gelen '{payload.get('type')}'")
    return payload

"""Cloudflare R2 dosya depolama servisi (boto3 / S3 uyumlu).

Mutlak kurallar (CLAUDE.md):
- Görsel R2'de, DB'de yalnızca URL/anahtar.
- Yüklenen dosyaya benzersiz ad (uuid) — çakışma olmaz.
- Ürün silinince R2'deki görsel de silinir (çöp birikmez).

Anahtarlar .env'de yoksa servis 'devre dışı' kabul edilir; client oluşturulmaz.
Bu sayede R2 bağlanmadan da backend ayağa kalkar (önce iskelet, sonra gerçek).
"""

import uuid
from functools import lru_cache
from pathlib import PurePosixPath

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.core.config import settings


@lru_cache(maxsize=1)
def get_client() -> BaseClient:
    """R2 S3 client'ı (tek sefer oluşturulup cache'lenir).

    R2 endpoint biçimi: https://<account_id>.r2.cloudflarestorage.com
    region_name 'auto' R2 için zorunludur. Bu fonksiyon yalnızca images_enabled
    iken çağrılmalı; aksi halde anahtarlar boş olur.
    """
    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


# İzin verilen content-type → dosya uzantısı.
_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def build_object_key(content_type: str, original_name: str | None = None) -> str:
    """Çakışmasız nesne anahtarı üretir: products/<uuid4>.<ext>.

    Ad uuid'den gelir; orijinal ad yalnızca uzantı ipucu için (content_type
    önceliklidir). Yol ayracı normalize edilir, dizin taşması engellenir.
    """
    ext = _EXT_BY_TYPE.get(content_type)
    if ext is None and original_name:
        ext = PurePosixPath(original_name).suffix.lower() or ".bin"
    ext = ext or ".bin"
    return f"products/{uuid.uuid4().hex}{ext}"


def upload_bytes(data: bytes, key: str, content_type: str) -> str:
    """Veriyi R2'ye yükler ve public URL'i döner.

    URL = R2_PUBLIC_BASE_URL + '/' + key. Bucket public ya da custom domain
    arkasında olmalı (anahtar bu sayede tarayıcıdan erişilebilir).
    """
    client = get_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    base = settings.R2_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/{key}"


def delete_object(key: str) -> None:
    """R2'den nesneyi siler. Idempotent: olmayan anahtar hata vermez (S3 davranışı)."""
    client = get_client()
    client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)

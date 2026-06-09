"""Ürün görseli yönetimi (admin). Yükleme R2'ye, kayıt DB'ye.

Akış (yükleme):
1. Dosya doğrulanır (tip + boyut).
2. R2'ye benzersiz (uuid) anahtarla yüklenir.
3. DB'ye ProductImage kaydı (url + r2_key) yazılır.
İlk görsel otomatik kapak (is_cover) olur.

R2 anahtarları .env'de yoksa bu uçlar 503 döner (backend yine de ayakta kalır).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.api.deps import require_admin
from app.core.config import settings
from app.db.session import get_session
from app.models import Product, ProductImage, User
from app.schemas.product import ImagePublic
from app.services import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["images"])


def _require_r2() -> None:
    """R2 yapılandırılmamışsa anlamlı bir hata döndür (sessiz başarısızlık olmasın)."""
    if not settings.images_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Görsel yükleme yapılandırılmamış (R2 anahtarları eksik).",
        )


def _to_public(image: ProductImage) -> ImagePublic:
    return ImagePublic(
        id=image.id, url=image.url, sort_order=image.sort_order, is_cover=image.is_cover
    )


@router.post(
    "/{product_id}/images",
    response_model=ImagePublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    product_id: int,
    file: UploadFile,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> ImagePublic:
    _require_r2()

    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")

    # Tip doğrulama (content-type istemciden gelir; kabaca güvenilir, kesin değil —
    # gerçek doğrulama için ileride imza/magic-byte kontrolü eklenebilir).
    content_type = (file.content_type or "").lower()
    if content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Desteklenmeyen dosya türü: {content_type or 'bilinmiyor'}. "
            f"İzin verilen: {', '.join(sorted(settings.allowed_image_types))}",
        )

    data = await file.read()
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Dosya çok büyük (en fazla {settings.MAX_IMAGE_SIZE_MB} MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Boş dosya.")

    key = storage.build_object_key(content_type, file.filename)
    try:
        url = storage.upload_bytes(data, key, content_type)
    except Exception:  # noqa: BLE001
        logger.exception("R2 yükleme başarısız: product_id=%s", product_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Görsel depolama hatası.",
        )

    # Sıra: yeni görsel en sona. İlk görselse kapak yap.
    existing = session.exec(
        select(ProductImage).where(ProductImage.product_id == product_id)
    ).all()
    next_order = max((img.sort_order for img in existing), default=-1) + 1

    image = ProductImage(
        product_id=product_id,
        url=url,
        r2_key=key,
        sort_order=next_order,
        is_cover=len(existing) == 0,  # ilk görsel = kapak
    )
    session.add(image)
    session.commit()
    session.refresh(image)
    return _to_public(image)


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_image(
    product_id: int,
    image_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> None:
    """Görseli R2'den ve DB'den siler. Silinen kapaksa, kalan ilk görsel kapak olur."""
    image = session.get(ProductImage, image_id)
    if image is None or image.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Görsel bulunamadı")

    if settings.images_enabled:
        try:
            storage.delete_object(image.r2_key)
        except Exception:  # noqa: BLE001
            logger.warning("R2 görseli silinemedi: key=%s", image.r2_key)

    was_cover = image.is_cover
    session.delete(image)
    session.commit()

    # Kapak silindiyse, kalan görsellerden ilkini kapak yap (ürün kapaksız kalmasın).
    if was_cover:
        remaining = session.exec(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order, ProductImage.id)
        ).first()
        if remaining:
            remaining.is_cover = True
            session.add(remaining)
            session.commit()


@router.put(
    "/{product_id}/images/{image_id}/cover",
    response_model=ImagePublic,
)
def set_cover(
    product_id: int,
    image_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> ImagePublic:
    """Bir görseli kapak yapar; ürünün diğer görsellerinin kapak işaretini kaldırır."""
    target = session.get(ProductImage, image_id)
    if target is None or target.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Görsel bulunamadı")

    siblings = session.exec(
        select(ProductImage).where(ProductImage.product_id == product_id)
    ).all()
    for img in siblings:
        img.is_cover = img.id == image_id
        session.add(img)
    session.commit()
    session.refresh(target)
    return _to_public(target)

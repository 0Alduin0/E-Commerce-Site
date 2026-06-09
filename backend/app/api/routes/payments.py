"""Ödeme endpoint'leri (Faz 8). En kritik faz — mutlak kurallar burada uygulanır:

- Kart verisi sisteme hiç değmez: init, İyzico hosted iframe içeriğini döndürür;
  ödeme İyzico ekranında yapılır.
- Sipariş onayı YALNIZCA webhook'la: frontend 'ödendi' diyemez. Webhook'ta İyzico
  imzası doğrulanır; sahte bildirim elenir.
- Ödeme onaylanınca: sipariş 'paid' olur ve stok BURADA düşer (idempotent).

Ödeme katmanı modülerdir (services/payment) — bu route sağlayıcıdan habersizdir.
"""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_session
from app.models import Order, OrderStatus, ProductVariant, User
from app.services.payment import get_payment_provider
from app.services.payment.base import BuyerInfo, CartLine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def _require_payments() -> None:
    if not settings.payments_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ödeme yapılandırılmamış (İyzico anahtarları eksik).",
        )


@router.post("/{order_id}/init")
def init_payment(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Bir sipariş için İyzico ödeme oturumu başlatır, iframe içeriğini döndürür.

    Yalnızca siparişin sahibi ve yalnızca 'pending' sipariş için. Tutar/kalemler
    SUNUCUDAKİ siparişten alınır (istemci tutarı belirleyemez)."""
    _require_payments()

    order = session.get(Order, order_id)
    if order is None or order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sipariş bulunamadı")
    if order.status != OrderStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu sipariş zaten ödenmiş veya kapatılmış.",
        )

    # Alıcı adı/soyadı tek alandan (shipping_full_name) bölünür — İyzico ikisini ister.
    full = order.shipping_full_name.strip()
    name, _, surname = full.partition(" ")
    buyer = BuyerInfo(
        name=name or full,
        surname=surname or "-",
        email=current_user.email,
        phone=order.shipping_phone,
        address=order.shipping_address,
        city=order.shipping_city,
    )
    lines = [
        CartLine(
            id=str(item.variant_id or item.id),
            name=f"{item.product_name}"
            + (f" ({item.variant_label})" if item.variant_label else ""),
            price=item.unit_price,
            quantity=item.quantity,
        )
        for item in order.items
    ]

    provider = get_payment_provider()
    try:
        result = provider.init_checkout(
            order_ref=str(order.id),
            amount=order.total_amount,
            lines=lines,
            buyer=buyer,
            callback_url=settings.PAYMENT_CALLBACK_URL,
        )
    except Exception:
        logger.exception("Ödeme başlatma hatası: order_id=%s", order_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ödeme başlatılamadı, lütfen tekrar deneyin.",
        )

    # Token'ı sakla (webhook eşleme/iz için).
    order.payment_token = result.token
    session.add(order)
    session.commit()

    return {"checkout_form_content": result.checkout_form_content, "token": result.token}


def _result_redirect(order_id: int | None) -> RedirectResponse:
    """Kullanıcıyı frontend'in ödeme sonuç sayfasına GET ile yollar.

    303 See Other: POST callback'i GET'e çevirir (tarayıcı sonuç sayfasını GET'ler).
    Sonuç sayfası bilgilendirme amaçlı; gerçek 'paid' onayı webhook'ta yapılır.
    """
    base = settings.PAYMENT_RESULT_URL.rstrip("?")
    sep = "&" if "?" in base else "?"
    url = f"{base}{sep}order={order_id}" if order_id else base
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.api_route("/callback", methods=["GET", "POST"], include_in_schema=False)
async def payment_callback(
    request: Request,
    token: str | None = Form(default=None),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """İyzico hosted form ödeme sonrası TARAYICIYI buraya POST eder (callback).

    Next.js sayfası POST kabul etmez (405) — bu yüzden callback backend'e gelir,
    biz token'dan siparişi bulup kullanıcıyı frontend sonuç sayfasına GET'le
    yönlendiririz. ÖDEME ONAYI BURADA YAPILMAZ (mutlak kural) — sadece UX dönüşü;
    'paid' geçişi yalnızca imzalı webhook'ta olur.
    """
    if not token:
        # Bazı akışlarda token query string'de gelebilir.
        token = request.query_params.get("token")

    order_id: int | None = None
    if token:
        order = session.exec(select(Order).where(Order.payment_token == token)).first()
        if order is not None:
            order_id = order.id

    return _result_redirect(order_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    """İyzico ödeme bildirimi. Auth YOK (İyzico çağırır) — güvenlik İMZA ile sağlanır.

    Akış:
    1. Ham gövdeyi al, sağlayıcıya imza doğrulat. Geçersizse 200 ama hiçbir şey yapma
       (saldırgana bilgi verme; ama İyzico'nun tekrar denemesini de tetikleme).
    2. Geçerli + ödendi ise: siparişi 'paid' yap ve stoğu düş (idempotent).
    """
    _require_payments()

    raw_body = await request.body()
    headers = dict(request.headers)

    provider = get_payment_provider()
    result = provider.verify_webhook(headers, raw_body)

    if not result.is_valid:
        logger.warning("Geçersiz imzalı webhook reddedildi.")
        # 200 dönüyoruz ki İyzico sonsuz retry yapmasın; ama hiçbir değişiklik yok.
        return {"status": "ignored"}

    if not result.order_ref:
        return {"status": "ignored"}

    order = session.get(Order, int(result.order_ref)) if result.order_ref.isdigit() else None
    if order is None:
        logger.warning("Webhook: sipariş bulunamadı ref=%s", result.order_ref)
        return {"status": "ignored"}

    # Idempotency: zaten ödendiyse tekrar stok düşme (İyzico aynı bildirimi yineleyebilir).
    if order.status != OrderStatus.pending:
        return {"status": "already_processed"}

    if not result.is_paid:
        # Ödeme başarısız bildirimi — siparişi pending bırak (kullanıcı tekrar deneyebilir).
        return {"status": "not_paid"}

    # --- Ödeme onaylandı: stok düş + paid (tek transaction) ---
    # Stoğu burada düşürüyoruz çünkü sipariş anında düşmüyorduk (Faz 6 kararı).
    # Aynı varyant birden çok kalemde olabilir → topla.
    qty_by_variant: dict[int, int] = {}
    for item in order.items:
        if item.variant_id is not None:
            qty_by_variant[item.variant_id] = qty_by_variant.get(item.variant_id, 0) + item.quantity

    for variant_id, qty in qty_by_variant.items():
        variant = session.get(ProductVariant, variant_id)
        if variant is not None:
            # Negatife düşmesin (eşzamanlı sipariş olduysa). max(0, ...) ile koru.
            variant.stock = max(0, variant.stock - qty)
            session.add(variant)

    order.status = OrderStatus.paid
    if result.provider_payment_id:
        order.provider_payment_id = result.provider_payment_id
    session.add(order)
    session.commit()

    logger.info("Sipariş ödendi: order_id=%s", order.id)
    return {"status": "ok"}

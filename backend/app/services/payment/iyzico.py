"""İyzico Checkout Form (hosted iframe) sağlayıcısı.

Mutlak kurallar:
- Kart verisi sisteme HİÇ değmez — İyzico'nun hosted iframe ekranında işlenir.
- Ödeme onayı yalnızca webhook'la; webhook'ta İyzico imzası doğrulanır.

İyzico v2 kimlik doğrulama: HMAC-SHA256 imza. İstek imzası ve gelen webhook
imzası aynı sırrı (secret key) kullanır. Resmi SDK yerine httpx ile doğrudan
bağlanıyoruz (async, az bağımlılık, tam kontrol).
"""

import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal

import httpx

from app.core.config import settings
from app.services.payment.base import (
    BuyerInfo,
    CartLine,
    PaymentInitResult,
    PaymentProvider,
    WebhookResult,
)


class IyzicoProvider(PaymentProvider):
    @property
    def enabled(self) -> bool:
        return bool(
            settings.IYZICO_API_KEY
            and settings.IYZICO_SECRET_KEY
            and settings.IYZICO_BASE_URL
        )

    # --- İmza üretimi (v2 HMAC-SHA256) --------------------------------------

    def _auth_header(self, uri_path: str, body: str) -> tuple[str, str]:
        """İyzico v2 Authorization header'ı üretir.

        İmza = HMAC_SHA256(secretKey, randomKey + uriPath + requestBody).
        Authorization: IYZWSv2 base64("apiKey:...&randomKey:...&signature:...")
        """
        random_key = uuid.uuid4().hex
        payload = f"{random_key}{uri_path}{body}"
        signature = hmac.new(
            settings.IYZICO_SECRET_KEY.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        auth_params = (
            f"apiKey:{settings.IYZICO_API_KEY}"
            f"&randomKey:{random_key}"
            f"&signature:{signature}"
        )
        authorization = "IYZWSv2 " + base64.b64encode(auth_params.encode("utf-8")).decode("utf-8")
        return authorization, random_key

    # --- Ödeme başlatma ------------------------------------------------------

    def init_checkout(
        self,
        *,
        order_ref: str,
        amount: Decimal,
        lines: list[CartLine],
        buyer: BuyerInfo,
        callback_url: str,
    ) -> PaymentInitResult:
        uri_path = "/payment/iyzipos/checkoutform/initialize/auth/ecom"

        # İyzico tutarları "1.0" gibi nokta ondalıkla, string ister. basketItems
        # toplamı paymentPrice'a eşit olmalı.
        def money(d: Decimal) -> str:
            return f"{d:.2f}"

        basket_items = [
            {
                "id": line.id,
                "name": line.name[:200],
                "category1": "Genel",
                "itemType": "PHYSICAL",
                "price": money(line.price * line.quantity),
            }
            for line in lines
        ]

        request_body = {
            "locale": "tr",
            "conversationId": order_ref,  # webhook'ta geri döner → siparişi eşleriz
            "price": money(amount),
            "paidPrice": money(amount),
            "currency": "TRY",
            "basketId": order_ref,
            "paymentGroup": "PRODUCT",
            "callbackUrl": callback_url,
            "buyer": {
                "id": f"BY-{order_ref}",
                "name": buyer.name,
                "surname": buyer.surname,
                "email": buyer.email,
                "gsmNumber": buyer.phone,
                "identityNumber": "11111111111",  # sandbox; gerçekte alıcıdan/varsayılan
                "registrationAddress": buyer.address,
                "city": buyer.city,
                "country": "Turkey",
            },
            "shippingAddress": {
                "contactName": f"{buyer.name} {buyer.surname}",
                "city": buyer.city,
                "country": "Turkey",
                "address": buyer.address,
            },
            "billingAddress": {
                "contactName": f"{buyer.name} {buyer.surname}",
                "city": buyer.city,
                "country": "Turkey",
                "address": buyer.address,
            },
            "basketItems": basket_items,
        }

        body_str = json.dumps(request_body)
        authorization, _ = self._auth_header(uri_path, body_str)

        resp = httpx.post(
            f"{settings.IYZICO_BASE_URL}{uri_path}",
            content=body_str,
            headers={"Authorization": authorization, "Content-Type": "application/json"},
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "success":
            raise RuntimeError(f"İyzico ödeme başlatılamadı: {data.get('errorMessage', data)}")

        return PaymentInitResult(
            checkout_form_content=data["checkoutFormContent"],
            token=data["token"],
        )

    # --- Webhook doğrulama ---------------------------------------------------

    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> WebhookResult:
        """İyzico bildirim imzasını doğrular. İyzico, gövdeyi imzalayıp
        'X-Iyz-Signature-V3' (HMAC-SHA256, base64) başlığında gönderir.

        Sahte bildirimler: imza eşleşmezse is_valid=False döner ve sipariş ASLA
        onaylanmaz. Bu, frontend'in 'ödendi' demesine güvenmeme kuralının teknik
        garantisidir.
        """
        # Başlık adı büyük/küçük harf duyarsız gelebilir → normalize et.
        norm = {k.lower(): v for k, v in headers.items()}
        provided_sig = norm.get("x-iyz-signature-v3") or norm.get("x-iyz-signature")

        expected = base64.b64encode(
            hmac.new(
                settings.IYZICO_SECRET_KEY.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        is_valid = bool(provided_sig) and hmac.compare_digest(provided_sig, expected)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return WebhookResult(is_valid=False, order_ref=None, is_paid=False)

        order_ref = payload.get("conversationId") or payload.get("basketId")
        status_str = (payload.get("status") or payload.get("paymentStatus") or "").upper()
        is_paid = status_str in {"SUCCESS", "PAID", "SUCCESSFUL"}

        return WebhookResult(
            is_valid=is_valid,
            order_ref=order_ref,
            is_paid=is_paid,
            provider_payment_id=str(payload.get("paymentId")) if payload.get("paymentId") else None,
        )

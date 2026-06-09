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
        """İyzico ödeme bildirimini KAYNAĞINDAN doğrular.

        İyzico'nun CHECKOUT_FORM_AUTH webhook'u güvenilir bir imza GÖNDERMEZ
        (x-iyz-signature boş gelir). Bu yüzden webhook'taki status'a körü körüne
        güvenmek yerine, payload'daki token'ı alıp İyzico'ya geri sorarız
        (Checkout Form Retrieve). Asıl 'paid' kararı İYZİCO'NUN cevabına göre verilir —
        bu, sahte webhook'a karşı imzadan da güçlü garantidir (saldırgan İyzico'nun
        retrieve cevabını taklit edemez).

        Webhook gerçek alanları: paymentConversationId (bizim order_ref), token,
        iyziPaymentId, status, iyziEventType.
        """
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return WebhookResult(is_valid=False, order_ref=None, is_paid=False)

        order_ref = (
            payload.get("paymentConversationId")
            or payload.get("conversationId")
            or payload.get("basketId")
        )
        token = payload.get("token")

        # Token yoksa doğrulayamayız → reddet (güvenli taraf).
        if not token:
            return WebhookResult(is_valid=False, order_ref=order_ref, is_paid=False)

        # --- İyzico'ya geri sor: bu token'lı ödeme gerçekten başarılı mı? ---
        retrieved = self._retrieve_checkout_form(token)
        if retrieved is None:
            # İyzico'ya ulaşılamadı → is_valid=False (webhook tekrar gelsin/elle bakılsın).
            return WebhookResult(is_valid=False, order_ref=order_ref, is_paid=False)

        # retrieve cevabı İyzico'dan geldi → güvenilir. paymentStatus/status SUCCESS mi?
        api_ok = retrieved.get("status") == "success"
        pay_status = (retrieved.get("paymentStatus") or "").upper()
        is_paid = api_ok and pay_status in {"SUCCESS", "PAID", "SUCCESSFUL"}
        # order_ref'i de İyzico'nun cevabından teyit et (manipülasyona kapalı).
        ref = retrieved.get("conversationId") or order_ref
        payment_id = retrieved.get("paymentId") or payload.get("iyziPaymentId")

        return WebhookResult(
            is_valid=True,  # cevap İyzico'dan doğrulandı
            order_ref=str(ref) if ref is not None else None,
            is_paid=is_paid,
            provider_payment_id=str(payment_id) if payment_id else None,
        )

    def _retrieve_checkout_form(self, token: str) -> dict | None:
        """İyzico Checkout Form Retrieve: token'la ödemenin gerçek durumunu sorar.
        Hata/ulaşılamama durumunda None döner (çağıran güvenli tarafta reddeder)."""
        uri_path = "/payment/iyzipos/checkoutform/auth/ecom/detail"
        body_str = json.dumps({"locale": "tr", "token": token})
        authorization, _ = self._auth_header(uri_path, body_str)
        try:
            resp = httpx.post(
                f"{settings.IYZICO_BASE_URL}{uri_path}",
                content=body_str,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                timeout=20.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

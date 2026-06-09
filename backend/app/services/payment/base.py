"""Ödeme sağlayıcı soyut arayüzü. Tüm sağlayıcılar (İyzico, ileride PayTR) bunu
implemente eder. Çağıran kod yalnızca bu arayüzü bilir — sağlayıcıdan bağımsızdır.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PaymentInitResult:
    """Ödeme başlatma sonucu (sağlayıcıdan bağımsız).

    - checkout_form_content: hosted iframe'i çizen HTML/script (frontend gömecek).
    - token: ödeme oturumu referansı (sonradan durum sorgulamak/eşlemek için).
    """

    checkout_form_content: str
    token: str


@dataclass
class WebhookResult:
    """Webhook (ödeme bildirimi) doğrulama sonucu.

    - is_valid: imza/doğrulama geçti mi (sahte bildirim elendi mi).
    - order_ref: sağlayıcının bizim sipariş referansımıza (conversationId) eşlediği değer.
    - is_paid: ödeme gerçekten başarılı mı.
    - provider_payment_id: sağlayıcıdaki ödeme kimliği (iz/denetim için).
    """

    is_valid: bool
    order_ref: str | None
    is_paid: bool
    provider_payment_id: str | None = None


@dataclass
class CartLine:
    """Ödeme başlatırken sağlayıcıya verilen sepet kalemi (sunucu verisinden üretilir)."""

    id: str
    name: str
    price: Decimal
    quantity: int


@dataclass
class BuyerInfo:
    """Alıcı/teslimat bilgisi. Sağlayıcıların çoğu (İyzico dahil) bunu zorunlu ister."""

    name: str
    surname: str
    email: str
    phone: str
    address: str
    city: str


class PaymentProvider(ABC):
    """Ödeme sağlayıcı sözleşmesi."""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Sağlayıcı kullanılabilir mi (anahtarlar yapılandırılmış mı)?"""

    @abstractmethod
    def init_checkout(
        self,
        *,
        order_ref: str,
        amount: Decimal,
        lines: list[CartLine],
        buyer: BuyerInfo,
        callback_url: str,
    ) -> PaymentInitResult:
        """Hosted ödeme oturumu başlatır, iframe içeriği + token döndürür.

        order_ref: bizim sipariş referansımız (sağlayıcı geri bildirimde döndürür).
        callback_url: sağlayıcının ödeme sonrası yönlendireceği/bildireceği adres.
        """

    @abstractmethod
    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> WebhookResult:
        """Gelen webhook'u doğrular (imza). SAHTE bildirimleri eler. Sipariş onayı
        YALNIZCA bunun is_valid + is_paid sonucuna göre yapılır."""

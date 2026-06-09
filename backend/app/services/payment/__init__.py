"""Ödeme katmanı — modüler sağlayıcı (provider) mimarisi.

CLAUDE.md bağlayıcı kuralı: ödeme katmanı modüler yazılır; ileride İyzico ↔ PayTR
geçişi için soyut bir 'ödeme sağlayıcı' arayüzü olmalı. Bu paket bunu sağlar:

- base.PaymentProvider: tüm sağlayıcıların uyacağı arayüz.
- iyzico.IyzicoProvider: İyzico Checkout Form (hosted iframe) implementasyonu.
- get_payment_provider(): aktif sağlayıcıyı settings'e göre döndürür.

Yeni sağlayıcı (PayTR) eklemek = base'i implemente eden bir sınıf + factory'ye
bir satır. Çağıran kod (routes/payments.py) sağlayıcıdan habersizdir.
"""

from functools import lru_cache

from app.core.config import settings
from app.services.payment.base import PaymentProvider
from app.services.payment.iyzico import IyzicoProvider


@lru_cache(maxsize=1)
def get_payment_provider() -> PaymentProvider:
    """Aktif ödeme sağlayıcısını döndürür. Şimdilik İyzico; PayTR eklenince
    settings.PAYMENT_PROVIDER ile seçilebilir hale gelir."""
    provider = settings.PAYMENT_PROVIDER.lower()
    if provider == "iyzico":
        return IyzicoProvider()
    raise ValueError(f"Bilinmeyen ödeme sağlayıcısı: {settings.PAYMENT_PROVIDER}")


__all__ = ["PaymentProvider", "get_payment_provider"]

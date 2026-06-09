from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları. Değerler .env dosyasından okunur; yoksa buradaki
    varsayılanlar kullanılır. Sırlar (DB, JWT, İyzico, R2) ileride buraya eklenir."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "E-Ticaret API"
    ENVIRONMENT: str = "development"

    # Veritabanı. Geliştirmede SQLite; production'da PostgreSQL (Railway) URL'i .env'den gelir.
    # Örn. PostgreSQL: postgresql+psycopg://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite:///./ecommerce.db"

    # CORS: virgülle ayrılmış izinli origin listesi (geliştirmede sadece localhost:3000)
    FRONTEND_URL: str = "http://localhost:3000"

    # --- JWT auth (Faz 3) ---
    # ÜRETİMDE .env'den gerçek, uzun ve rastgele bir secret gelmeli. Buradaki
    # varsayılan SADECE geliştirme içindir; production'da değiştirilmezse oturumlar
    # tahmin edilebilir olur. Üret: python -c "import secrets;print(secrets.token_hex(32))"
    JWT_SECRET: str = "dev-only-insecure-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15        # access token: kısa ömür
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7           # refresh token: uzun ömür

    # Refresh cookie'nin SameSite politikası. Geliştirmede frontend+backend aynı
    # site (localhost) → "lax" yeter. Production'da Vercel (frontend) ile Railway
    # (backend) FARKLI site olduğundan tarayıcı "lax" cookie'yi cross-site
    # GÖNDERMEZ → sessiz oturum yenileme kırılır. O durumda "none" gerekir.
    # "none" seçilirse cookie zorunlu olarak Secure (HTTPS) işaretlenir (tarayıcı kuralı).
    COOKIE_SAMESITE: str = "lax"  # prod (ayrı domain): "none"

    # --- Cloudflare R2 / görsel yükleme (Faz 5) ---
    # Anahtarlar .env'den gelir; boşsa görsel yükleme devre dışı kalır (geliştirmede
    # backend yine de çalışır — bkz. images_enabled). R2 S3 uyumludur, boto3 ile bağlanılır.
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    # Görsellerin tarayıcıdan erişileceği taban URL (R2 public bucket veya custom domain,
    # örn. https://cdn.site.com). Sonunda '/' olmadan yazılır.
    R2_PUBLIC_BASE_URL: str = ""

    # Yükleme limitleri.
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    # --- Ödeme / İyzico (Faz 8) ---
    # Ödeme katmanı modülerdir (PAYMENT_PROVIDER ile sağlayıcı seçilir). Anahtarlar
    # boşsa ödeme devre dışı (payments_enabled=False) ama backend ayakta kalır.
    # Sandbox base URL: https://sandbox-api.iyzipay.com  | Prod: https://api.iyzipay.com
    PAYMENT_PROVIDER: str = "iyzico"
    IYZICO_API_KEY: str = ""
    IYZICO_SECRET_KEY: str = ""
    IYZICO_BASE_URL: str = "https://sandbox-api.iyzipay.com"
    # İyzico'nun ödeme sonrası tarayıcıyı döndüreceği frontend adresi (sonuç sayfası).
    PAYMENT_CALLBACK_URL: str = "http://localhost:3000/odeme/sonuc"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    @property
    def allowed_image_types(self) -> set[str]:
        return {t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()}

    @property
    def images_enabled(self) -> bool:
        """R2 yüklemesi için gereken tüm anahtarlar dolu mu? Boşsa yükleme uçları
        503 döner ama uygulama ayağa kalkar (önce iskelet, sonra gerçek)."""
        return all(
            [
                self.R2_ACCOUNT_ID,
                self.R2_ACCESS_KEY_ID,
                self.R2_SECRET_ACCESS_KEY,
                self.R2_BUCKET_NAME,
                self.R2_PUBLIC_BASE_URL,
            ]
        )

    @property
    def payments_enabled(self) -> bool:
        """İyzico anahtarları yapılandırılmış mı? Boşsa ödeme uçları 503 döner,
        backend yine ayakta (önce iskelet, sonra gerçek)."""
        return bool(self.IYZICO_API_KEY and self.IYZICO_SECRET_KEY and self.IYZICO_BASE_URL)


settings = Settings()

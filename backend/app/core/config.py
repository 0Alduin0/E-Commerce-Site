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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]


settings = Settings()

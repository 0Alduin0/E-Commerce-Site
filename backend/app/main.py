from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORS: sadece .env'de tanımlı frontend adres(ler)ine izin ver.
# allow_credentials=True → ileride httpOnly refresh cookie için gerekli.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Bağlantı/canlılık testi. Frontend bu endpoint'i çağırarak backend'e
    erişebildiğini doğrular."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }

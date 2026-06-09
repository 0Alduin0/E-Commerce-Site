"""Kimlik doğrulama endpoint'leri: kayıt, giriş, token yenileme, çıkış, /me.

Tasarım kararları (CLAUDE.md kuralları):
- Şifre asla düz saklanmaz (bcrypt).
- Refresh token httpOnly cookie'de tutulur (XSS'e karşı). localStorage'da DEĞİL.
- Access token kısa ömürlü; istemci onu bellekte tutar, biz cookie'ye yazmayız.
- Token üretim/doğrulama core/security.py'de tek noktada.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    TokenPair,
    UserLogin,
    UserPublic,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Refresh cookie adı ve ortak ayarları tek yerde — tutarlı set/clear için.
REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Refresh token'ı httpOnly cookie'ye yazar.

    secure: production'da True (yalnızca HTTPS). Geliştirmede http://localhost
    için False olmalı, yoksa tarayıcı cookie'yi göndermez.
    samesite: geliştirmede 'lax' (aynı site). Production'da frontend (Vercel) ve
    backend (Railway) ayrı domain → 'none' gerekir, yoksa cookie cross-site gitmez.
    'none' ise tarayıcı kuralı gereği Secure ZORUNLU; o yüzden secure'u or'la.
    """
    is_prod = settings.ENVIRONMENT != "development"
    samesite = settings.COOKIE_SAMESITE.lower()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_prod or samesite == "none",
        samesite=samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",  # cookie yalnızca auth endpoint'lerine gider, gereksiz yere sızmaz
    )


def _issue_tokens(response: Response, user: User) -> TokenPair:
    """Bir kullanıcı için access+refresh üretir, refresh'i cookie'ye de yazar."""
    subject = str(user.id)
    access = create_access_token(subject, user.role.value)
    refresh = create_refresh_token(subject, user.role.value)
    _set_refresh_cookie(response, refresh)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, session: Session = Depends(get_session)) -> User:
    """Yeni kullanıcı oluşturur. Email benzersizdir; rol her zaman varsayılan 'user'.
    Admin, ilk admin'i elle (seed/DB) atayarak oluşturulur — kayıt yoluyla admin olunmaz."""
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta zaten kayıtlı",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        # role: modeldeki varsayılan (user). Kayıttan admin atanamaz.
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(
    data: UserLogin,
    response: Response,
    session: Session = Depends(get_session),
) -> TokenPair:
    """E-posta + şifre ile giriş. JSON gövdesi alır (frontend için doğal yol)."""
    user = _authenticate(session, data.email, data.password)
    return _issue_tokens(response, user)


@router.post("/token", response_model=TokenPair, include_in_schema=False)
def login_form(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> TokenPair:
    """Swagger'ın 'Authorize' düğmesi için OAuth2 form-data uyumlu login.
    Alan adı 'username' olsa da e-posta bekleriz (OAuth2 standardı gereği)."""
    user = _authenticate(session, form.username, form.password)
    return _issue_tokens(response, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    response: Response,
    request: Request,
    body: RefreshRequest | None = None,
    session: Session = Depends(get_session),
) -> TokenPair:
    """Refresh token ile yeni access+refresh üretir (token rotasyonu).

    Token önceliği: httpOnly cookie > body. Tarayıcı istemcileri cookie kullanır;
    cookie'siz istemciler (mobil) body'de gönderebilir.
    """
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token is None and body is not None:
        token = body.refresh_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token bulunamadı",
        )

    try:
        payload = decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş refresh token",
        )

    user = session.get(User, int(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı veya pasif",
        )
    return _issue_tokens(response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    """Refresh cookie'sini siler. Access token kısa ömürlü olduğu için istemci
    onu bellekten atınca oturum biter."""
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/auth")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Oturum açmış kullanıcının kendi bilgisi. Token doğrulamasının canlı testi."""
    return current_user


def _authenticate(session: Session, email: str, password: str) -> User:
    """E-posta+şifreyi doğrular. Başarısızsa tek tip 401 döner — 'kullanıcı yok'
    ile 'şifre yanlış' ayırt edilmez (kullanıcı sayımı/enumeration engellenir)."""
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesap pasif durumda",
        )
    return user

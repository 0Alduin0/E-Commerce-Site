"""Ortak API bağımlılıkları: oturum açmış kullanıcıyı çözen ve rol kontrolü
yapan dependency'ler. Korumalı endpoint'ler bunları kullanır.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_session
from app.models.user import User, UserRole

# Swagger'daki "Authorize" düğmesi için. tokenUrl yalnızca dokümantasyon amaçlı;
# asıl login JSON endpoint'i de var (auth.py).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Geçersiz veya süresi dolmuş kimlik bilgisi",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Access token'ı doğrular ve DB'deki kullanıcıyı döner.

    Token'a değil DB'ye güveniyoruz: kullanıcı silinmiş/pasifleştirilmişse
    geçerli bir token bile erişim vermemeli.
    """
    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
        user_id = payload.get("sub")
        if user_id is None:
            raise _credentials_exc
    except JWTError:
        raise _credentials_exc

    user = session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Yalnızca 'admin' rolüne izin verir. /admin ve yönetim endpoint'leri bunu kullanır."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekir",
        )
    return current_user

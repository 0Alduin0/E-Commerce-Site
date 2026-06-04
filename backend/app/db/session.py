from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

# SQLite tek-thread varsayar; FastAPI çok-thread çalıştığı için bu bayrak gerekir.
# PostgreSQL'de bu argüman gerekmez, o yüzden koşullu veriyoruz.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: istek başına bir DB session açar ve sonunda kapatır.

    Kullanım:
        @router.get(...)
        def handler(session: Session = Depends(get_session)): ...
    """
    with Session(engine) as session:
        yield session

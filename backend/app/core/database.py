from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Explícito en vez de confiar en que close() revierta la
        # transacción abierta: si un router/service propaga una excepción
        # con cambios ya hechos vía flush() (no comiteados), esto asegura
        # que no queden pendientes en la conexión antes de devolverla al pool.
        db.rollback()
        raise
    finally:
        db.close()

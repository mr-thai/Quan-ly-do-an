from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Session factory setup
SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

@contextmanager
def transaction_scope(session: Session | None = None) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.
    
    If an existing session is provided, an internal savepoint (begin_nested) is used.
    If no session is provided, a new session is created, committed on success,
    rolled back on exception, and guaranteed to close.
    """
    if session is not None:
        with session.begin_nested():
            yield session
    else:
        new_session: Session = SessionFactory()
        try:
            with new_session.begin():
                yield new_session
        except Exception:
            new_session.rollback()
            raise
        finally:
            new_session.close()

def get_db_session() -> Generator[Session, None, None]:
    """Dependency/utility generator yielding a database session."""
    session: Session = SessionFactory()
    try:
        yield session
    finally:
        session.close()

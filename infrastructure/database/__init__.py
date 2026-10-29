"""Sessao e engine do SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from infrastructure.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia do FastAPI para obter a sessao do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

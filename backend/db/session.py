import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://user:pass@localhost:5432/secureship"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    # No migration tool (Alembic) yet — plain create_all is enough for a
    # schema that's still taking shape. Revisit if/when the schema needs
    # versioned migrations.
    import models  # noqa: F401  (ensures all model classes are registered)

    Base.metadata.create_all(bind=engine)

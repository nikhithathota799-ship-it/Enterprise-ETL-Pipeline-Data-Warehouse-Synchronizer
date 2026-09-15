"""
Database connection module (Member 4).

Sets up the SQLAlchemy engine, session factory, and declarative Base
that all ORM models in database_models.py inherit from.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# LOAD .ENV
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is missing in .env. "
        "Add your PostgreSQL connection string as DATABASE_URL=..."
    )


# ============================================================
# ENGINE + SESSION
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # avoids stale/dropped connections
    echo=False,           # set True temporarily if you need to see raw SQL
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


# ============================================================
# HELPERS
# ============================================================

def get_session():
    """Return a new database session. Caller is responsible for closing it."""

    return SessionLocal()


def create_all_tables():
    """
    Create all tables defined in database_models.py that don't exist yet.
    Safe to run multiple times - it will not drop or overwrite existing tables.
    """

    # Import here (not at top) to avoid circular imports, since
    # database_models.py imports Base from this file.
    import src.models.database_models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    print("All tables created (or already existed).")


def test_connection():
    """Quick sanity check that we can actually reach the database."""

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        print("Database connection successful.")
        return True
    except Exception as error:
        print(f"Database connection FAILED: {error}")
        return False


if __name__ == "__main__":
    test_connection()
    create_all_tables()

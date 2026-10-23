"""Database configuration and session management."""
import logging
import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from omegaconf import DictConfig

logger = logging.getLogger(__name__)

# Create declarative base for models
Base = declarative_base()

# Global variables for database engine and session
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def _load_db_config(config: DictConfig):
    """Return the configured database settings."""
    db_config = config.get("db") if hasattr(config, "get") else config
    if db_config is None:
        raise KeyError("db")
    return db_config


def _validate_db_config(db_config) -> None:
    """Validate the required database configuration keys."""
    required_keys = ("host", "port", "database", "user", "password")
    missing = [key for key in required_keys if not hasattr(db_config, key)]
    if missing:
        raise KeyError(missing[0])


def _build_database_url(db_config) -> str:
    """Build the configured PostgreSQL URL."""
    _validate_db_config(db_config)
    host = db_config.host
    port = db_config.port
    database_name = db_config.database
    username = db_config.user
    password = db_config.password
    return f"postgresql://{username}:{password}@{host}:{port}/{database_name}"


def init_database(config: DictConfig) -> None:
    """
    Initialize database engine and session factory.

    Attempts PostgreSQL first and falls back to SQLite when the PostgreSQL driver or
    service is unavailable, which keeps the app runnable in a local development setup.

    Args:
        config: Hydra configuration object containing database settings

    Raises:
        ValueError: If database configuration is invalid
        Exception: If database connection fails
    """
    global _engine, _SessionLocal

    try:
        db_config = _load_db_config(config)
        _validate_db_config(db_config)
    except KeyError as e:
        error_msg = f"Missing database configuration key: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    postgres_engine = None
    try:
        echo = getattr(db_config, "echo", False)
        database_url = _build_database_url(db_config)
        postgres_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=echo,
        )
        connection = postgres_engine.connect()
        connection.close()

        _engine = postgres_engine
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info("Database initialized successfully")

    except Exception as postgres_error:
        if postgres_engine is not None:
            postgres_engine.dispose()
        fallback_url = os.getenv("SQLITE_DATABASE_URL", "sqlite:///:memory:")
        logger.warning(
            "PostgreSQL initialization failed (%s); trying SQLite fallback.",
            type(postgres_error).__name__,
        )
        try:
            sqlite_engine = create_engine(fallback_url, echo=echo)
            connection = sqlite_engine.connect()
            connection.close()

            _engine = sqlite_engine
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=_engine,
            )
            logger.info("SQLite fallback database initialized successfully")
        except Exception as sqlite_error:
            logger.error(
                "PostgreSQL and SQLite initialization failed (%s).",
                type(sqlite_error).__name__,
            )
            raise RuntimeError(
                "Failed to initialize both PostgreSQL and SQLite databases."
            ) from None


def create_tables() -> None:
    """
    Create all database tables defined in models.

    Raises:
        RuntimeError: If database is not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    try:
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=_engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        error_msg = f"Failed to create database tables: {e}"
        logger.error(error_msg)
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Raises:
        RuntimeError: If database is not initialized
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine() -> object:
    """
    Get the database engine instance.

    Returns:
        Engine: SQLAlchemy engine instance

    Raises:
        RuntimeError: If database is not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def close_database() -> None:
    """Close database connections and cleanup resources."""
    global _engine, _SessionLocal

    if _engine is not None:
        logger.info("Closing database connections")
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("Database connections closed")

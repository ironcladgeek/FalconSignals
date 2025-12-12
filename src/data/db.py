"""Database engine and session management for NordInvest.

Handles SQLite database initialization, schema creation, and session management
for storing historical analyst ratings and performance tracking data.
"""

from pathlib import Path
from typing import Generator

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

# Track initialized databases to avoid redundant initialization logging
_initialized_databases = set()


class DatabaseManager:
    """Manages database connections and initialization."""

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.engine = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize database engine and create tables.

        Creates the SQLite database and all required tables if they don't exist.
        Only logs initialization message once per database path.
        """
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create engine
            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(
                db_url,
                echo=False,  # Set to True for SQL debugging
                connect_args={"check_same_thread": False},  # Required for SQLite
            )

            # Create all tables
            SQLModel.metadata.create_all(self.engine)
            self._initialized = True

            # Only log once per database path to avoid spam
            db_path_str = str(self.db_path)
            if db_path_str not in _initialized_databases:
                logger.info(f"Database initialized at {self.db_path}")
                _initialized_databases.add(db_path_str)
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a database session.

        Returns:
            SQLModel Session for database operations.

        Raises:
            RuntimeError: If database not initialized.
        """
        if not self._initialized or self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        return Session(self.engine)

    def get_session_generator(self) -> Generator[Session, None, None]:
        """Generator for dependency injection of sessions.

        Yields:
            SQLModel Session for database operations.
        """
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")

    def drop_all(self) -> None:
        """Drop all tables (use with caution!).

        WARNING: This will delete all data in the database.
        """
        if not self._initialized or self.engine is None:
            logger.warning("Database not initialized, skipping drop_all()")
            return

        try:
            SQLModel.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager(db_path: Path | str = "data/nordinvest.db") -> DatabaseManager:
    """Get or create global database manager instance.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        DatabaseManager instance.
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
        _db_manager.initialize()

    return _db_manager


def init_db(db_path: Path | str = "data/nordinvest.db") -> None:
    """Initialize the database with default path.

    Args:
        db_path: Path to SQLite database file.
    """
    manager = get_db_manager(db_path)
    if not manager._initialized:
        manager.initialize()

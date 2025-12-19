"""Unit tests for the database module."""

import tempfile
from pathlib import Path

import pytest

from src.data.db import DatabaseManager, get_db_manager, init_db


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test.db"

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create initialized DatabaseManager."""
        manager = DatabaseManager(temp_db_path)
        manager.initialize()
        yield manager
        manager.close()

    def test_initialization(self, temp_db_path):
        """Test DatabaseManager initialization."""
        manager = DatabaseManager(temp_db_path)

        assert manager.db_path == temp_db_path
        assert manager.engine is None
        assert manager._initialized is False

    def test_initialize_creates_database(self, temp_db_path):
        """Test that initialize creates database file."""
        manager = DatabaseManager(temp_db_path)

        manager.initialize()

        assert temp_db_path.exists()
        assert manager._initialized is True
        assert manager.engine is not None

        manager.close()

    def test_initialize_creates_parent_directories(self):
        """Test that initialize creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "test.db"
            manager = DatabaseManager(nested_path)

            manager.initialize()

            assert nested_path.parent.exists()

            manager.close()

    def test_get_session_without_initialize(self, temp_db_path):
        """Test get_session raises error when not initialized."""
        manager = DatabaseManager(temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_session()

    def test_get_session_after_initialize(self, db_manager):
        """Test get_session returns session after initialize."""
        session = db_manager.get_session()

        assert session is not None
        session.close()

    def test_get_session_generator(self, db_manager):
        """Test get_session_generator yields session."""
        gen = db_manager.get_session_generator()
        session = next(gen)

        assert session is not None

        # Cleanup
        try:
            next(gen)
        except StopIteration:
            pass

    def test_close(self, temp_db_path):
        """Test close disposes engine."""
        manager = DatabaseManager(temp_db_path)
        manager.initialize()
        assert manager._initialized is True

        manager.close()

        assert manager._initialized is False

    def test_drop_all_when_not_initialized(self, temp_db_path):
        """Test drop_all does nothing when not initialized."""
        manager = DatabaseManager(temp_db_path)

        # Should not raise, just log warning
        manager.drop_all()

    def test_drop_all_when_initialized(self, db_manager):
        """Test drop_all drops tables."""
        # This should not raise
        db_manager.drop_all()


class TestDatabaseFunctions:
    """Test suite for module-level database functions."""

    @pytest.fixture(autouse=True)
    def reset_global_manager(self):
        """Reset global manager before each test."""
        import src.data.db as db_module

        db_module._db_manager = None
        yield
        if db_module._db_manager:
            db_module._db_manager.close()
        db_module._db_manager = None

    def test_get_db_manager_creates_manager(self):
        """Test get_db_manager creates and initializes manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            manager = get_db_manager(db_path)

            assert manager is not None
            assert manager._initialized is True

    def test_get_db_manager_returns_same_instance(self):
        """Test get_db_manager returns same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            manager1 = get_db_manager(db_path)
            manager2 = get_db_manager(db_path)

            assert manager1 is manager2

    def test_init_db(self):
        """Test init_db initializes database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            init_db(db_path)

            assert db_path.exists()

    def test_db_path_as_string(self):
        """Test DatabaseManager accepts string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            manager = DatabaseManager(db_path)

            assert manager.db_path == Path(db_path)

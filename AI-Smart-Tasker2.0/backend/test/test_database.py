"""
Comprehensive unit tests for database.py module.

This test suite covers database initialization, session management,
table creation, and error handling scenarios.
"""
import logging
from unittest.mock import Mock, patch

import pytest
from omegaconf import OmegaConf
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.utils import database


@pytest.fixture(autouse=True)
def reset_database_globals():
    """Reset global database variables before and after each test."""
    # Store original values
    original_engine = database._engine
    original_session = database._SessionLocal

    # Reset to None before test
    database._engine = None
    database._SessionLocal = None

    yield

    # Restore original values after test
    database._engine = original_engine
    database._SessionLocal = original_session


@pytest.fixture
def valid_db_config():
    """Create a valid database configuration for testing."""
    config_dict = {
        "db": {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
            "echo": False,
        }
    }
    return OmegaConf.create(config_dict)


@pytest.fixture
def invalid_db_config():
    """Create an invalid database configuration missing required keys."""
    config_dict = {
        "db": {
            "host": "localhost",
            # Missing port, database, user, password
        }
    }
    return OmegaConf.create(config_dict)


class TestInitDatabase:
    """Test cases for init_database() function."""

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    def test_init_database_success(
        self, mock_sessionmaker, mock_create_engine, valid_db_config
    ):
        """Test successful database initialization with valid config."""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        # Act
        database.init_database(valid_db_config)

        # Assert
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        mock_create_engine.assert_called_once_with(
            expected_url, pool_pre_ping=True, pool_size=10, max_overflow=20, echo=False
        )
        mock_sessionmaker.assert_called_once_with(
            autocommit=False, autoflush=False, bind=mock_engine
        )
        assert database._engine == mock_engine
        assert database._SessionLocal == mock_session_factory

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    def test_init_database_with_echo_enabled(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test database initialization with SQL echo enabled."""
        # Arrange
        config_dict = {
            "db": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
                "echo": True,
            }
        }
        config = OmegaConf.create(config_dict)
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Act
        database.init_database(config)

        # Assert
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["echo"] is True

    def test_init_database_missing_config_key(self, invalid_db_config):
        """Test init_database raises exception when config keys are missing."""
        # Act & Assert
        # OmegaConf raises ConfigAttributeError which is caught and re-raised
        with pytest.raises(Exception) as exc_info:
            database.init_database(invalid_db_config)

        # The exception message should indicate the missing required database key
        assert "Missing database configuration key" in str(exc_info.value)
        assert "port" in str(exc_info.value)

    @patch("backend.app.utils.database.create_engine")
    def test_init_database_connection_failure(
        self, mock_create_engine, valid_db_config
    ):
        """Test init_database raises exception on connection failure."""
        # Arrange
        mock_create_engine.side_effect = SQLAlchemyError("Connection refused")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            database.init_database(valid_db_config)

        assert "Failed to initialize both" in str(exc_info.value)

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    def test_init_database_multiple_calls(
        self, mock_sessionmaker, mock_create_engine, valid_db_config
    ):
        """Test that init_database can be called multiple times (re-initialization)."""
        # Arrange
        mock_engine1 = Mock()
        mock_engine2 = Mock()
        mock_create_engine.side_effect = [mock_engine1, mock_engine2]

        # Act
        database.init_database(valid_db_config)
        first_engine = database._engine

        database.init_database(valid_db_config)
        second_engine = database._engine

        # Assert
        assert first_engine == mock_engine1
        assert second_engine == mock_engine2
        assert mock_create_engine.call_count == 2

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    def test_init_database_falls_back_to_sqlite_when_postgres_unavailable(
        self, mock_sessionmaker, mock_create_engine, valid_db_config
    ):
        """Test SQLite fallback when the PostgreSQL driver or service is unavailable."""
        # Arrange
        postgres_error = ModuleNotFoundError("No module named 'psycopg2'")
        sqlite_engine = Mock()
        mock_create_engine.side_effect = [postgres_error, sqlite_engine]
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        # Act
        database.init_database(valid_db_config)

        # Assert
        assert mock_create_engine.call_count == 2
        assert database._engine == sqlite_engine
        assert database._SessionLocal == mock_session_factory
        sqlite_call = mock_create_engine.call_args_list[1]
        assert str(sqlite_call.args[0]) == "sqlite:///:memory:"

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    def test_connection_failure_falls_back_without_logging_connection_details(
        self, mock_sessionmaker, mock_create_engine, valid_db_config, caplog
    ):
        postgres_engine = Mock()
        postgres_engine.connect.side_effect = SQLAlchemyError(
            "postgresql://user:private-password@private-host/database"
        )
        sqlite_engine = Mock()
        mock_create_engine.side_effect = [postgres_engine, sqlite_engine]

        with caplog.at_level(logging.WARNING):
            database.init_database(valid_db_config)

        assert database._engine == sqlite_engine
        postgres_engine.dispose.assert_called_once()
        assert "private-password" not in caplog.text
        assert "private-host" not in caplog.text


class TestCreateTables:
    """Test cases for create_tables() function."""

    @patch("backend.app.utils.database.Base")
    def test_create_tables_success(self, mock_base):
        """Test successful table creation."""
        # Arrange
        mock_engine = Mock()
        database._engine = mock_engine
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        # Act
        database.create_tables()

        # Assert
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)

    def test_create_tables_not_initialized(self):
        """Test create_tables raises RuntimeError when database not initialized."""
        # Arrange
        database._engine = None

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            database.create_tables()

        assert "Database not initialized" in str(exc_info.value)
        assert "Call init_database() first" in str(exc_info.value)

    @patch("backend.app.utils.database.Base")
    def test_create_tables_failure(self, mock_base):
        """Test create_tables raises exception on table creation failure."""
        # Arrange
        mock_engine = Mock()
        database._engine = mock_engine
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        mock_metadata.create_all.side_effect = SQLAlchemyError("Table creation failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            database.create_tables()

        assert "Table creation failed" in str(exc_info.value)


class TestGetDb:
    """Test cases for get_db() dependency function."""

    def test_get_db_success(self):
        """Test get_db yields session and closes it properly."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session_factory = Mock(return_value=mock_session)
        database._SessionLocal = mock_session_factory

        # Act
        generator = database.get_db()
        session = next(generator)

        # Assert - session is yielded
        assert session == mock_session
        mock_session_factory.assert_called_once()

        # Act - complete the generator to trigger finally block
        try:
            next(generator)
        except StopIteration:
            pass

        # Assert - session is closed
        mock_session.close.assert_called_once()

    def test_get_db_not_initialized(self):
        """Test get_db raises RuntimeError when database not initialized."""
        # Arrange
        database._SessionLocal = None

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            generator = database.get_db()
            next(generator)

        assert "Database not initialized" in str(exc_info.value)
        assert "Call init_database() first" in str(exc_info.value)

    def test_get_db_closes_on_exception(self):
        """Test get_db closes session even when exception occurs."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session_factory = Mock(return_value=mock_session)
        database._SessionLocal = mock_session_factory

        # Act
        generator = database.get_db()
        _ = next(generator)  # Get session but don't need to check it

        # Simulate exception by calling throw()
        try:
            generator.throw(Exception("Test exception"))
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # Assert - session is still closed despite exception
        mock_session.close.assert_called_once()

    def test_get_db_multiple_sessions(self):
        """Test get_db can create multiple independent sessions."""
        # Arrange
        mock_session1 = Mock(spec=Session)
        mock_session2 = Mock(spec=Session)
        mock_session_factory = Mock(side_effect=[mock_session1, mock_session2])
        database._SessionLocal = mock_session_factory

        # Act
        gen1 = database.get_db()
        session1 = next(gen1)

        gen2 = database.get_db()
        session2 = next(gen2)

        # Assert
        assert session1 == mock_session1
        assert session2 == mock_session2
        assert session1 != session2
        assert mock_session_factory.call_count == 2


class TestGetEngine:
    """Test cases for get_engine() function."""

    def test_get_engine_success(self):
        """Test get_engine returns the engine instance."""
        # Arrange
        mock_engine = Mock()
        database._engine = mock_engine

        # Act
        result = database.get_engine()

        # Assert
        assert result == mock_engine

    def test_get_engine_not_initialized(self):
        """Test get_engine raises RuntimeError when database not initialized."""
        # Arrange
        database._engine = None

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            database.get_engine()

        assert "Database not initialized" in str(exc_info.value)
        assert "Call init_database() first" in str(exc_info.value)


class TestCloseDatabase:
    """Test cases for close_database() function."""

    def test_close_database_success(self):
        """Test successful database closure."""
        # Arrange
        mock_engine = Mock()
        mock_session_factory = Mock()
        database._engine = mock_engine
        database._SessionLocal = mock_session_factory

        # Act
        database.close_database()

        # Assert
        mock_engine.dispose.assert_called_once()
        assert database._engine is None
        assert database._SessionLocal is None

    def test_close_database_when_not_initialized(self):
        """Test close_database handles case when database not initialized."""
        # Arrange
        database._engine = None
        database._SessionLocal = None

        # Act - should not raise exception
        database.close_database()

        # Assert
        assert database._engine is None
        assert database._SessionLocal is None

    def test_close_database_multiple_calls(self):
        """Test close_database can be called multiple times safely."""
        # Arrange
        mock_engine = Mock()
        database._engine = mock_engine
        database._SessionLocal = Mock()

        # Act
        database.close_database()
        database.close_database()  # Second call

        # Assert - dispose called only once (first call)
        mock_engine.dispose.assert_called_once()
        assert database._engine is None

    def test_close_database_dispose_error(self):
        """Test close_database handles dispose errors gracefully."""
        # Arrange
        mock_engine = Mock()
        mock_engine.dispose.side_effect = Exception("Dispose failed")
        database._engine = mock_engine
        database._SessionLocal = Mock()

        # Act & Assert - should raise the exception
        with pytest.raises(Exception) as exc_info:
            database.close_database()

        assert "Dispose failed" in str(exc_info.value)


class TestIntegrationScenarios:
    """Integration tests for database module workflows."""

    @patch("backend.app.utils.database.create_engine")
    @patch("backend.app.utils.database.sessionmaker")
    @patch("backend.app.utils.database.Base")
    def test_full_lifecycle(
        self, mock_base, mock_sessionmaker, mock_create_engine, valid_db_config
    ):
        """Test complete database lifecycle: init -> create_tables -> use -> close."""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory
        mock_session = Mock(spec=Session)
        mock_session_factory.return_value = mock_session
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        # Act - Initialize
        database.init_database(valid_db_config)

        # Act - Create tables
        database.create_tables()

        # Act - Get session
        gen = database.get_db()
        _ = next(gen)  # Get session to verify it works

        # Complete generator
        try:
            next(gen)
        except StopIteration:
            pass

        # Act - Get engine
        engine = database.get_engine()

        # Act - Close
        database.close_database()

        # Assert
        assert engine == mock_engine
        mock_create_engine.assert_called_once()
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
        mock_session.close.assert_called_once()
        mock_engine.dispose.assert_called_once()
        assert database._engine is None
        assert database._SessionLocal is None

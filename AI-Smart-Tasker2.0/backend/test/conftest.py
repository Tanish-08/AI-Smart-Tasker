"""Pytest fixtures for testing."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from omegaconf import OmegaConf

from backend.app.utils.database import Base
from backend.app.models.user import User
from backend.app.models.task import Task
from backend.app.models.analytics import Analytics


@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for testing.

    Yields:
        Session: Database session
    """
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_user(test_db):
    """
    Create a sample user for testing.

    Args:
        test_db: Database session

    Returns:
        User: Sample user instance
    """
    user = User(
        username="testuser",
        email="test@example.com",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_task(test_db, sample_user):
    """
    Create a sample task for testing.

    Args:
        test_db: Database session
        sample_user: Sample user

    Returns:
        Task: Sample task instance
    """
    task = Task(
        title="Test Task",
        description="This is a test task",
        deadline=datetime.utcnow() + timedelta(days=1),
        completed=False,
        user_id=sample_user.id
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


@pytest.fixture
def overdue_task(test_db, sample_user):
    """
    Create an overdue task for testing.

    Args:
        test_db: Database session
        sample_user: Sample user

    Returns:
        Task: Overdue task instance
    """
    task = Task(
        title="Overdue Task",
        description="This task is overdue",
        deadline=datetime.utcnow() - timedelta(days=1),
        completed=False,
        user_id=sample_user.id
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLM client for testing.

    Returns:
        Mock: Mock LLM client
    """
    mock_client = Mock()
    mock_client.generate.return_value = "Test generated response"
    mock_client.generate_with_template.return_value = "Test template response"
    mock_client.health_check.return_value = True
    return mock_client


@pytest.fixture
def mock_config():
    """
    Create a mock Hydra configuration for testing.

    Returns:
        DictConfig: Mock configuration
    """
    config_dict = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_password",
            "echo": False
        },
        "llm": {
            "model_name": "test-model",
            "api_base": "http://localhost:8001/v1",
            "api_key": "test_key",
            "temperature": 0.7,
            "max_tokens": 150
        },
        "prompts": {
            "insults": {
                "system_message": "Generate insults",
                "prompt_template": "Task: {task_title}\nDescription: {task_description}\nDeadline: {deadline}"
            },
            "summaries": {
                "generation": {
                    "system_message": "Generate summaries",
                    "prompt_template": "Title: {task_title}\nDescription: {task_description}"
                },
                "modification": {
                    "system_message": "Modify summaries",
                    "prompt_template": "Current: {current_summary}\nRequest: {modification_prompt}"
                }
            }
        }
    }
    return OmegaConf.create(config_dict)


@pytest.fixture
def sample_analytics_event(test_db, sample_user, sample_task):
    """
    Create a sample analytics event for testing.

    Args:
        test_db: Database session
        sample_user: Sample user
        sample_task: Sample task

    Returns:
        Analytics: Sample analytics event
    """
    event = Analytics(
        user_id=sample_user.id,
        task_id=sample_task.id,
        event_type="created",
        event_timestamp=datetime.utcnow(),
        task_title=sample_task.title,
        deadline=sample_task.deadline
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def mock_fastapi_app():
    """
    Create a mock FastAPI application for testing.

    Returns:
        Mock: Mock FastAPI app
    """
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    return client

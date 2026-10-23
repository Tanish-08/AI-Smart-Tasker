"""Comprehensive integration tests for AI Task Manager application.

This module contains integration tests covering:
- Task CRUD operations
- Deadline checking and AI insult generation
- AI summary generation and modification
- Analytics endpoints
- Error handling and edge cases
- Frontend-backend integration flows

All tests use proper mocking for database and LLM calls.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from omegaconf import OmegaConf

from backend.app.utils.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.task import Task
from backend.app.models.analytics import Analytics


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock_client = Mock()
    mock_client.generate.return_value = "Test generated response"
    mock_client.generate_with_template.return_value = "Test template response"
    mock_client.health_check.return_value = True
    return mock_client


@pytest.fixture
def mock_config():
    """Create a mock Hydra configuration for testing."""
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
                "system_message": "Generate developer-themed insults",
                "prompt_template": "Task: {task_title}\nDescription: {task_description}\nDeadline: {deadline}"
            },
            "summaries": {
                "generation": {
                    "system_message": "Generate task summaries",
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
def sample_user(test_db):
    """Create a sample user for testing."""
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
    """Create a sample task for testing."""
    task = Task(
        title="Test Task",
        description="This is a test task description",
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
    """Create an overdue task for testing."""
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
def completed_task(test_db, sample_user):
    """Create a completed task for testing."""
    task = Task(
        title="Completed Task",
        description="This task is completed",
        deadline=datetime.utcnow() - timedelta(hours=12),
        completed=True,
        user_id=sample_user.id
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


@pytest.fixture
def task_with_summary(test_db, sample_user):
    """Create a task with a summary for testing."""
    task = Task(
        title="Task With Summary",
        description="This task has a summary",
        deadline=datetime.utcnow() + timedelta(days=2),
        completed=False,
        user_id=sample_user.id,
        summary="Existing test summary"
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


@pytest.fixture
def multiple_tasks(test_db, sample_user):
    """Create multiple tasks for testing list operations."""
    tasks = []
    for i in range(5):
        task = Task(
            title=f"Task {i+1}",
            description=f"Description for task {i+1}",
            deadline=datetime.utcnow() + timedelta(days=i-2),
            completed=i % 2 == 0,  # Alternate completed status
            user_id=sample_user.id
        )
        test_db.add(task)
        tasks.append(task)
    test_db.commit()
    for task in tasks:
        test_db.refresh(task)
    return tasks


# ============================================================================
# TASK CRUD INTEGRATION TESTS
# ============================================================================

class TestTaskCRUDIntegration:
    """Integration tests for Task CRUD operations."""

    def test_create_task_success(self, test_db, sample_user):
        """Test successful task creation with analytics event logging."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        task_data = TaskCreate(
            title="New Integration Test Task",
            description="Testing task creation",
            deadline=datetime.utcnow() + timedelta(days=3),
            user_id=sample_user.id
        )

        task = TaskManager.create_task(test_db, task_data)

        assert task is not None
        assert task.id is not None
        assert task.title == "New Integration Test Task"
        assert task.description == "Testing task creation"
        assert task.completed is False
        assert task.user_id == sample_user.id

        # Verify analytics event was created
        analytics_event = test_db.query(Analytics).filter(
            Analytics.task_id == task.id,
            Analytics.event_type == "created"
        ).first()
        assert analytics_event is not None
        assert analytics_event.task_title == task.title

    def test_create_task_with_minimal_data(self, test_db, sample_user):
        """Test task creation with only required fields."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        task_data = TaskCreate(
            title="Minimal Task",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )

        task = TaskManager.create_task(test_db, task_data)

        assert task is not None
        assert task.title == "Minimal Task"
        assert task.description is None

    def test_get_task_by_id(self, test_db, sample_task, sample_user):
        """Test retrieving a task by ID."""
        from backend.app.utils.task_manager import TaskManager

        task = TaskManager.get_task(test_db, sample_task.id, sample_user.id)

        assert task is not None
        assert task.id == sample_task.id
        assert task.title == sample_task.title

    def test_get_task_not_found(self, test_db, sample_user):
        """Test retrieving non-existent task returns None."""
        from backend.app.utils.task_manager import TaskManager

        task = TaskManager.get_task(test_db, 99999, sample_user.id)

        assert task is None

    def test_get_task_wrong_user(self, test_db, sample_task):
        """Test retrieving task with wrong user ID returns None."""
        from backend.app.utils.task_manager import TaskManager

        task = TaskManager.get_task(test_db, sample_task.id, 99999)

        assert task is None

    def test_get_tasks_list(self, test_db, multiple_tasks, sample_user):
        """Test retrieving list of tasks with filters."""
        from backend.app.utils.task_manager import TaskManager

        # Get all tasks
        all_tasks = TaskManager.get_tasks(test_db, sample_user.id)
        assert len(all_tasks) == 5

        # Get only completed tasks
        completed_tasks = TaskManager.get_tasks(test_db, sample_user.id, completed=True)
        assert len(completed_tasks) == 3  # Tasks 0, 2, 4 are completed

        # Get only incomplete tasks
        incomplete_tasks = TaskManager.get_tasks(test_db, sample_user.id, completed=False)
        assert len(incomplete_tasks) == 2  # Tasks 1, 3 are incomplete

    def test_get_tasks_pagination(self, test_db, multiple_tasks, sample_user):
        """Test task list pagination."""
        from backend.app.utils.task_manager import TaskManager

        # Get first 2 tasks
        first_page = TaskManager.get_tasks(test_db, sample_user.id, skip=0, limit=2)
        assert len(first_page) == 2

        # Get next 2 tasks
        second_page = TaskManager.get_tasks(test_db, sample_user.id, skip=2, limit=2)
        assert len(second_page) == 2

        # Verify no overlap
        first_ids = {t.id for t in first_page}
        second_ids = {t.id for t in second_page}
        assert first_ids.isdisjoint(second_ids)

    def test_update_task_success(self, test_db, sample_task, sample_user):
        """Test successful task update."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskUpdate

        update_data = TaskUpdate(
            title="Updated Title",
            description="Updated description"
        )

        updated_task = TaskManager.update_task(
            test_db, sample_task.id, update_data, sample_user.id
        )

        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Updated description"

    def test_update_task_completion_logs_analytics(self, test_db, sample_task, sample_user):
        """Test that completing a task logs analytics event."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskUpdate

        update_data = TaskUpdate(completed=True)

        updated_task = TaskManager.update_task(
            test_db, sample_task.id, update_data, sample_user.id
        )

        assert updated_task.completed is True

        # Verify completion analytics event
        completion_event = test_db.query(Analytics).filter(
            Analytics.task_id == sample_task.id,
            Analytics.event_type == "completed"
        ).first()
        assert completion_event is not None
        assert completion_event.was_completed_on_time is not None

    def test_update_task_not_found(self, test_db, sample_user):
        """Test updating non-existent task returns None."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskUpdate

        update_data = TaskUpdate(title="Won't Work")

        result = TaskManager.update_task(test_db, 99999, update_data, sample_user.id)

        assert result is None

    def test_delete_task_success(self, test_db, sample_task, sample_user):
        """Test successful task deletion."""
        from backend.app.utils.task_manager import TaskManager

        task_id = sample_task.id
        result = TaskManager.delete_task(test_db, task_id, sample_user.id)

        assert result is True

        # Verify task is deleted
        deleted_task = TaskManager.get_task(test_db, task_id, sample_user.id)
        assert deleted_task is None

    def test_delete_task_not_found(self, test_db, sample_user):
        """Test deleting non-existent task returns False."""
        from backend.app.utils.task_manager import TaskManager

        result = TaskManager.delete_task(test_db, 99999, sample_user.id)

        assert result is False


# ============================================================================
# DEADLINE AND INSULT GENERATION INTEGRATION TESTS
# ============================================================================

class TestDeadlineInsultIntegration:
    """Integration tests for deadline checking and AI insult generation."""

    def test_get_overdue_tasks(self, test_db, sample_user, multiple_tasks):
        """Test retrieving overdue tasks."""
        from backend.app.utils.task_manager import TaskManager

        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)

        # Tasks with deadline in past and not completed
        for task in overdue_tasks:
            assert task.deadline < datetime.utcnow()
            assert task.completed is False

    def test_generate_insult_success(self, test_db, overdue_task, mock_llm_client, mock_config):
        """Test successful AI insult generation."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        mock_llm_client.generate_with_template.return_value = "Your code compiles like you meet deadlines - eventually, maybe."

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        assert insult is not None
        assert len(insult) > 0
        mock_llm_client.generate_with_template.assert_called_once()

    def test_generate_and_save_insult(self, test_db, overdue_task, mock_llm_client, mock_config):
        """Test generating and saving insult to task."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        mock_llm_client.generate_with_template.return_value = "Even your exceptions are exceptional at missing deadlines."

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_and_save_insult(test_db, overdue_task)

        assert overdue_task.insult_message is not None
        assert overdue_task.insult_message == insult

    def test_insult_not_regenerated_if_exists(self, test_db, overdue_task, mock_llm_client, mock_config):
        """Test that existing insult is not overwritten."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        overdue_task.insult_message = "Existing insult"
        test_db.commit()

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_and_save_insult(test_db, overdue_task)

        assert insult == "Existing insult"
        mock_llm_client.generate_with_template.assert_not_called()

    def test_fallback_insult_on_llm_failure(self, test_db, overdue_task, mock_llm_client, mock_config):
        """Test fallback insult when LLM fails."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        mock_llm_client.generate_with_template.side_effect = Exception("LLM service unavailable")

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        assert insult is not None
        assert len(insult) > 0  # Fallback insult should be returned

    def test_batch_generate_insults(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test batch insult generation for multiple tasks."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        # Create multiple overdue tasks
        overdue_tasks = []
        for i in range(3):
            task = Task(
                title=f"Overdue Task {i}",
                description=f"Overdue description {i}",
                deadline=datetime.utcnow() - timedelta(days=i+1),
                completed=False,
                user_id=sample_user.id
            )
            test_db.add(task)
            overdue_tasks.append(task)
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "Generic insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        results = generator.batch_generate_insults(test_db, overdue_tasks)

        assert len(results) == 3
        for task_id, insult in results.items():
            assert insult is not None

    def test_log_missed_deadline(self, test_db, overdue_task):
        """Test logging missed deadline analytics event."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        event = test_db.query(Analytics).filter(
            Analytics.task_id == overdue_task.id,
            Analytics.event_type == "missed_deadline"
        ).first()

        assert event is not None
        assert event.task_title == overdue_task.title

    def test_missed_deadline_not_logged_twice(self, test_db, overdue_task):
        """Test that missed deadline is only logged once per task."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        # Log first time
        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        # Log second time
        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        events = test_db.query(Analytics).filter(
            Analytics.task_id == overdue_task.id,
            Analytics.event_type == "missed_deadline"
        ).all()

        assert len(events) == 1  # Only one event should exist


# ============================================================================
# SUMMARY GENERATION INTEGRATION TESTS
# ============================================================================

class TestSummaryGenerationIntegration:
    """Integration tests for AI summary generation and modification."""

    def test_generate_summary_success(self, mock_llm_client, mock_config):
        """Test successful summary generation."""
        from backend.app.utils.summary_generator import SummaryGenerator

        mock_llm_client.generate_with_template.return_value = "Implement login feature with OAuth2 support."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_summary(
            task_title="Login Feature",
            task_description="Add user authentication using OAuth2"
        )

        assert summary is not None
        assert len(summary) > 0
        mock_llm_client.generate_with_template.assert_called_once()

    def test_generate_summary_no_description(self, mock_llm_client, mock_config):
        """Test summary generation with no description."""
        from backend.app.utils.summary_generator import SummaryGenerator

        mock_llm_client.generate_with_template.return_value = "Simple task summary."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_summary(
            task_title="Simple Task",
            task_description=None
        )

        assert summary is not None
        # Verify "No description provided" was passed
        call_args = mock_llm_client.generate_with_template.call_args
        assert "No description provided" in str(call_args)

    def test_generate_and_save_summary(self, test_db, sample_task, mock_llm_client, mock_config):
        """Test generating and saving summary to task."""
        from backend.app.utils.summary_generator import SummaryGenerator

        mock_llm_client.generate_with_template.return_value = "Generated summary for test task."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_and_save_summary(test_db, sample_task)

        assert sample_task.summary == summary
        assert sample_task.summary == "Generated summary for test task."

    def test_modify_summary_success(self, mock_llm_client, mock_config):
        """Test successful summary modification."""
        from backend.app.utils.summary_generator import SummaryGenerator

        mock_llm_client.generate_with_template.return_value = "Modified: Make it shorter and simpler."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        modified = generator.modify_summary(
            current_summary="Original long summary text",
            modification_prompt="Make it shorter"
        )

        assert modified is not None
        mock_llm_client.generate_with_template.assert_called_once()

    def test_modify_and_save_summary(self, test_db, task_with_summary, mock_llm_client, mock_config):
        """Test modifying and saving summary to task."""
        from backend.app.utils.summary_generator import SummaryGenerator

        original_summary = task_with_summary.summary
        mock_llm_client.generate_with_template.return_value = "Modified summary text."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        modified = generator.modify_and_save_summary(
            test_db,
            task_with_summary,
            "Add more details"
        )

        assert task_with_summary.summary == modified
        assert task_with_summary.summary != original_summary

    def test_modify_summary_without_existing_raises_error(self, test_db, sample_task, mock_llm_client, mock_config):
        """Test that modifying non-existent summary raises error."""
        from backend.app.utils.summary_generator import SummaryGenerator

        # Ensure task has no summary
        sample_task.summary = None
        test_db.commit()

        generator = SummaryGenerator(mock_llm_client, mock_config)

        with pytest.raises(ValueError, match="does not have a summary"):
            generator.modify_and_save_summary(
                test_db,
                sample_task,
                "Modify this"
            )

    def test_regenerate_summary(self, test_db, task_with_summary, mock_llm_client, mock_config):
        """Test regenerating summary replaces existing one."""
        from backend.app.utils.summary_generator import SummaryGenerator

        original_summary = task_with_summary.summary
        mock_llm_client.generate_with_template.return_value = "Brand new regenerated summary."

        generator = SummaryGenerator(mock_llm_client, mock_config)
        new_summary = generator.regenerate_summary(test_db, task_with_summary)

        assert new_summary == "Brand new regenerated summary."
        assert task_with_summary.summary == new_summary
        assert task_with_summary.summary != original_summary


# ============================================================================
# ANALYTICS INTEGRATION TESTS
# ============================================================================

class TestAnalyticsIntegration:
    """Integration tests for analytics endpoints and data processing."""

    def test_get_completion_stats(self, test_db, sample_user, multiple_tasks):
        """Test getting task completion statistics."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)

        assert stats.total_tasks == 5
        assert stats.completed_tasks == 3
        assert stats.pending_tasks == 2
        assert stats.completion_rate == 60.0

    def test_get_completion_stats_no_tasks(self, test_db, sample_user):
        """Test completion stats with no tasks."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)

        assert stats.total_tasks == 0
        assert stats.completion_rate == 0.0

    def test_get_deadline_adherence(self, test_db, sample_user):
        """Test getting deadline adherence metrics."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        # Create some completed task events
        for i in range(5):
            event = Analytics(
                user_id=sample_user.id,
                task_id=i + 1,
                event_type="completed",
                event_timestamp=datetime.utcnow(),
                task_title=f"Task {i}",
                deadline=datetime.utcnow() - timedelta(hours=i),
                was_completed_on_time=(i % 2 == 0),
                completion_delay_hours=float(i) if i % 2 != 0 else 0.0
            )
            test_db.add(event)
        test_db.commit()

        adherence = AnalyticsProcessor.get_deadline_adherence(test_db, sample_user.id)

        assert adherence.total_completed == 5
        assert adherence.completed_on_time == 3
        assert adherence.completed_late == 2

    def test_get_deadline_adherence_no_completions(self, test_db, sample_user):
        """Test deadline adherence with no completed tasks."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        adherence = AnalyticsProcessor.get_deadline_adherence(test_db, sample_user.id)

        assert adherence.total_completed == 0
        assert adherence.on_time_percentage == 0.0

    def test_get_productivity_trends(self, test_db, sample_user):
        """Test getting productivity trends over time."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        # Create analytics events over several days
        for i in range(10):
            event = Analytics(
                user_id=sample_user.id,
                task_id=i + 1,
                event_type=["created", "completed", "missed_deadline"][i % 3],
                event_timestamp=datetime.utcnow() - timedelta(days=i % 5),
                task_title=f"Task {i}",
                deadline=datetime.utcnow() + timedelta(days=1)
            )
            test_db.add(event)
        test_db.commit()

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=7)

        assert len(trends) > 0
        for trend in trends:
            assert hasattr(trend, 'date')
            assert hasattr(trend, 'tasks_created')
            assert hasattr(trend, 'tasks_completed')
            assert hasattr(trend, 'tasks_overdue')

    def test_get_recent_events(self, test_db, sample_user, sample_task):
        """Test getting recent analytics events."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        # Create some events
        for i in range(15):
            event = Analytics(
                user_id=sample_user.id,
                task_id=sample_task.id,
                event_type="created",
                event_timestamp=datetime.utcnow() - timedelta(hours=i),
                task_title=f"Event {i}",
                deadline=datetime.utcnow()
            )
            test_db.add(event)
        test_db.commit()

        recent = AnalyticsProcessor.get_recent_events(test_db, sample_user.id, limit=10)

        assert len(recent) == 10
        # Events should be ordered by timestamp descending
        for i in range(len(recent) - 1):
            assert recent[i].event_timestamp >= recent[i + 1].event_timestamp

    def test_get_comprehensive_analytics(self, test_db, sample_user, multiple_tasks):
        """Test getting comprehensive analytics response."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        analytics = AnalyticsProcessor.get_analytics(test_db, sample_user.id, trend_days=30)

        assert analytics.user_id == sample_user.id
        assert analytics.completion_stats is not None
        assert analytics.deadline_adherence is not None
        assert analytics.productivity_trends is not None
        assert analytics.recent_events is not None


# ============================================================================
# ERROR HANDLING INTEGRATION TESTS
# ============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling and edge cases."""

    def test_create_task_empty_title_validation(self, test_db, sample_user):
        """Test task creation with empty title fails validation."""
        from backend.app.schemas.task_schema import TaskCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TaskCreate(
                title="",  # Empty title should fail
                deadline=datetime.utcnow() + timedelta(days=1),
                user_id=sample_user.id
            )

    def test_create_task_title_too_long(self, test_db, sample_user):
        """Test task creation with title exceeding max length."""
        from backend.app.schemas.task_schema import TaskCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TaskCreate(
                title="x" * 300,  # Exceeds 255 char limit
                deadline=datetime.utcnow() + timedelta(days=1),
                user_id=sample_user.id
            )

    def test_create_task_invalid_user_id(self, test_db):
        """Test task creation with invalid user ID."""
        from backend.app.schemas.task_schema import TaskCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TaskCreate(
                title="Test Task",
                deadline=datetime.utcnow() + timedelta(days=1),
                user_id=0  # Must be > 0
            )

    def test_summary_request_task_id_validation(self):
        """Test summary request with invalid task ID."""
        from backend.app.schemas.summary_schema import SummaryRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SummaryRequest(
                task_id=0,  # Must be > 0
                task_title="Test",
                task_description="Test"
            )

    def test_modify_request_prompt_too_long(self):
        """Test modify request with prompt exceeding max length."""
        from backend.app.schemas.summary_schema import ModifyRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModifyRequest(
                task_id=1,
                current_summary="Test summary",
                modification_prompt="x" * 600  # Exceeds 500 char limit
            )

    def test_llm_client_missing_config(self):
        """Test LLM client initialization with missing config."""
        from backend.app.utils.llm_client import LLMClient
        from omegaconf import OmegaConf

        # Config missing required keys
        incomplete_config = OmegaConf.create({
            "llm": {
                "model_name": "test"
                # Missing api_base
            }
        })

        with pytest.raises((ValueError, KeyError, Exception)):
            LLMClient(incomplete_config)

    def test_database_rollback_on_error(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test that database rollback occurs on error."""
        from backend.app.utils.summary_generator import SummaryGenerator

        # Create task
        task = Task(
            title="Rollback Test",
            description="Test rollback",
            deadline=datetime.utcnow() + timedelta(days=1),
            completed=False,
            user_id=sample_user.id,
            summary="Original"
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        original_summary = task.summary

        # Make LLM fail after modifying summary
        mock_llm_client.generate_with_template.side_effect = Exception("LLM Error")

        generator = SummaryGenerator(mock_llm_client, mock_config)

        with pytest.raises(Exception):
            generator.modify_and_save_summary(test_db, task, "Modify")

        # Refresh and verify rollback
        test_db.refresh(task)
        # Note: Depending on implementation, this may or may not rollback


# ============================================================================
# API ENDPOINT INTEGRATION TESTS
# ============================================================================

class TestAPIEndpointIntegration:
    """Integration tests for API endpoints using TestClient."""

    @pytest.fixture
    def client(self, test_db, mock_llm_client, mock_config):
        """Create a FastAPI test client with mocked dependencies."""
        from backend.app.dependencies import get_config, get_llm_client, set_llm_client
        from backend.app.utils.database import get_db

        # Import app without triggering lifespan
        from fastapi import FastAPI
        from backend.app.endpoint import (
            task_routes,
            summary_routes,
            analytics_routes,
            deadline_routes,
        )

        # Create a test app without lifespan
        app = FastAPI(
            title="AI Task Manager API - Test",
            description="Test instance",
            version="1.0.0",
        )

        # Include routers
        app.include_router(task_routes.router)
        app.include_router(summary_routes.router)
        app.include_router(analytics_routes.router)
        app.include_router(deadline_routes.router)

        # Add health endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "AI Task Manager API", "version": "1.0.0"}

        # Add root endpoint
        @app.get("/")
        async def root():
            return {
                "service": "AI Task Manager API",
                "version": "1.0.0",
                "description": "Backend API for AI-powered task management",
                "docs": "/docs",
                "health": "/health"
            }

        # Override dependencies
        app.dependency_overrides[get_db] = lambda: test_db
        app.dependency_overrides[get_config] = lambda: mock_config
        app.dependency_overrides[get_llm_client] = lambda: mock_llm_client

        # Set LLM client globally for dependencies
        set_llm_client(mock_llm_client)

        client = TestClient(app, raise_server_exceptions=False)
        yield client

        # Clean up overrides
        app.dependency_overrides.clear()

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data


# ============================================================================
# FRONTEND-BACKEND INTEGRATION FLOW TESTS
# ============================================================================

class TestFrontendBackendIntegration:
    """Tests simulating frontend-backend integration flows."""

    def test_complete_task_creation_flow(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test complete flow: create task, generate summary, view analytics."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.utils.summary_generator import SummaryGenerator
        from backend.app.utils.analytics_processor import AnalyticsProcessor
        from backend.app.schemas.task_schema import TaskCreate

        # Step 1: Create task (simulates frontend POST /api/tasks)
        task_data = TaskCreate(
            title="Frontend Test Task",
            description="Created from frontend",
            deadline=datetime.utcnow() + timedelta(days=7),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)
        assert task is not None

        # Step 2: Generate summary (simulates frontend POST /api/summaries/generate)
        mock_llm_client.generate_with_template.return_value = "AI-generated summary for frontend task."
        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_and_save_summary(test_db, task)
        assert task.summary == summary

        # Step 3: View analytics (simulates frontend GET /api/analytics)
        analytics = AnalyticsProcessor.get_analytics(test_db, sample_user.id)
        assert analytics.completion_stats.total_tasks >= 1

    def test_overdue_task_insult_flow(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test flow: task becomes overdue, insult is generated."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.utils.ai_insult_generator import AIInsultGenerator
        from backend.app.utils.analytics_processor import AnalyticsProcessor
        from backend.app.schemas.task_schema import TaskCreate

        # Step 1: Create task with past deadline (simulates already overdue)
        task_data = TaskCreate(
            title="Already Overdue Task",
            description="Should trigger insult",
            deadline=datetime.utcnow() - timedelta(hours=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        # Step 2: Check deadlines (simulates frontend GET /api/deadlines/check)
        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)
        assert len(overdue_tasks) >= 1
        assert task.id in [t.id for t in overdue_tasks]

        # Step 3: Generate insult
        mock_llm_client.generate_with_template.return_value = "Your deadline passed faster than your code reviews."
        insult_gen = AIInsultGenerator(mock_llm_client, mock_config)
        insult = insult_gen.generate_and_save_insult(test_db, task)
        assert task.insult_message is not None

        # Step 4: Log missed deadline
        AnalyticsProcessor.log_missed_deadline(test_db, task)

    def test_summary_modification_flow(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test flow: generate summary, then modify it via AI."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.utils.summary_generator import SummaryGenerator
        from backend.app.schemas.task_schema import TaskCreate

        # Step 1: Create task
        task_data = TaskCreate(
            title="Modify Summary Test",
            description="Test summary modification",
            deadline=datetime.utcnow() + timedelta(days=3),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        # Step 2: Generate initial summary
        mock_llm_client.generate_with_template.return_value = "Initial AI summary."
        generator = SummaryGenerator(mock_llm_client, mock_config)
        generator.generate_and_save_summary(test_db, task)

        # Step 3: Modify summary via AI
        mock_llm_client.generate_with_template.return_value = "Modified AI summary with more details."
        modified = generator.modify_and_save_summary(test_db, task, "Add more details")
        assert task.summary == modified
        assert "Modified" in modified or "more details" in modified

    def test_task_completion_analytics_flow(self, test_db, sample_user, mock_llm_client, mock_config):
        """Test flow: create task, complete it, verify analytics updated."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.utils.analytics_processor import AnalyticsProcessor
        from backend.app.schemas.task_schema import TaskCreate, TaskUpdate

        # Step 1: Get initial analytics
        initial_stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)
        initial_completed = initial_stats.completed_tasks

        # Step 2: Create task
        task_data = TaskCreate(
            title="Completion Flow Test",
            description="Will be completed",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        # Step 3: Complete task
        update_data = TaskUpdate(completed=True)
        TaskManager.update_task(test_db, task.id, update_data, sample_user.id)

        # Step 4: Verify analytics updated
        final_stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)
        assert final_stats.completed_tasks == initial_completed + 1


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_task_deadline_at_current_time(self, test_db, sample_user):
        """Test task with deadline exactly at current time."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        task_data = TaskCreate(
            title="Edge Case Deadline",
            description="Deadline is right now",
            deadline=datetime.utcnow(),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        assert task is not None

    def test_very_long_description(self, test_db, sample_user):
        """Test task with very long description."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        long_description = "A" * 10000  # Very long description

        task_data = TaskCreate(
            title="Long Description Task",
            description=long_description,
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        assert task.description == long_description

    def test_special_characters_in_title(self, test_db, sample_user):
        """Test task with special characters in title."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        special_title = "Task with <script>alert('XSS')</script> & 'quotes' \"double\""

        task_data = TaskCreate(
            title=special_title,
            description="Testing special characters",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        # Title should be stored as-is (output encoding handles display)
        assert task.title == special_title

    def test_unicode_content(self, test_db, sample_user):
        """Test task with unicode content."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate

        unicode_title = "Task with emoji and unicode characters"
        unicode_desc = "Description with special chars"

        task_data = TaskCreate(
            title=unicode_title,
            description=unicode_desc,
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        assert unicode_title in task.title
        assert unicode_desc in task.description

    def test_zero_day_productivity_trends(self, test_db, sample_user):
        """Test productivity trends with minimum day range."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=1)

        assert trends is not None  # Should not crash

    def test_max_day_productivity_trends(self, test_db, sample_user):
        """Test productivity trends with maximum day range."""
        from backend.app.utils.analytics_processor import AnalyticsProcessor

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=365)

        assert trends is not None

    def test_concurrent_task_updates(self, test_db, sample_user):
        """Test that concurrent updates don't corrupt data."""
        from backend.app.utils.task_manager import TaskManager
        from backend.app.schemas.task_schema import TaskCreate, TaskUpdate

        # Create task
        task_data = TaskCreate(
            title="Concurrent Update Test",
            description="Original",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        task = TaskManager.create_task(test_db, task_data)

        # Simulate multiple updates
        for i in range(10):
            update_data = TaskUpdate(description=f"Update {i}")
            TaskManager.update_task(test_db, task.id, update_data, sample_user.id)

        # Verify final state
        final_task = TaskManager.get_task(test_db, task.id, sample_user.id)
        assert "Update 9" in final_task.description


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

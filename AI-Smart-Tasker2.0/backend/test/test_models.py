"""Unit tests for database models."""
import pytest
from datetime import datetime, timedelta

from backend.app.models.user import User
from backend.app.models.task import Task
from backend.app.models.analytics import Analytics


class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self, test_db):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_repr(self, test_db):
        """Test user string representation."""
        user = User(
            username="testuser",
            email="test@example.com"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str

    def test_user_unique_username(self, test_db, sample_user):
        """Test that username must be unique."""
        duplicate_user = User(
            username=sample_user.username,
            email="different@example.com"
        )
        test_db.add(duplicate_user)

        with pytest.raises(Exception):
            test_db.commit()

    def test_user_unique_email(self, test_db, sample_user):
        """Test that email must be unique."""
        duplicate_user = User(
            username="differentuser",
            email=sample_user.email
        )
        test_db.add(duplicate_user)

        with pytest.raises(Exception):
            test_db.commit()

    def test_user_tasks_relationship(self, test_db, sample_user, sample_task):
        """Test user-tasks relationship."""
        test_db.refresh(sample_user)
        assert len(sample_user.tasks) == 1
        assert sample_user.tasks[0].id == sample_task.id


class TestTaskModel:
    """Test cases for Task model."""

    def test_create_task(self, test_db, sample_user):
        """Test creating a task."""
        deadline = datetime.utcnow() + timedelta(days=1)
        task = Task(
            title="Test Task",
            description="Test description",
            deadline=deadline,
            user_id=sample_user.id
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.deadline == deadline
        assert task.completed is False
        assert task.user_id == sample_user.id
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_repr(self, test_db, sample_task):
        """Test task string representation."""
        repr_str = repr(sample_task)
        assert "Task" in repr_str
        assert "Test Task" in repr_str
        assert str(sample_task.completed) in repr_str

    def test_task_is_overdue_property_false(self, test_db, sample_task):
        """Test is_overdue property when task is not overdue."""
        # sample_task has deadline in the future
        assert sample_task.is_overdue is False

    def test_task_is_overdue_property_true(self, test_db, overdue_task):
        """Test is_overdue property when task is overdue."""
        assert overdue_task.is_overdue is True

    def test_task_is_overdue_completed_task(self, test_db, overdue_task):
        """Test is_overdue property when task is completed (should be False)."""
        overdue_task.completed = True
        test_db.commit()
        test_db.refresh(overdue_task)

        assert overdue_task.is_overdue is False

    def test_task_optional_fields(self, test_db, sample_task):
        """Test task optional fields."""
        sample_task.summary = "Test summary"
        sample_task.insult_message = "Test insult"
        test_db.commit()
        test_db.refresh(sample_task)

        assert sample_task.summary == "Test summary"
        assert sample_task.insult_message == "Test insult"

    def test_task_cascade_delete(self, test_db, sample_user):
        """Test that tasks are deleted when user is deleted."""
        task = Task(
            title="Cascade Test",
            description="Will be deleted",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )
        test_db.add(task)
        test_db.commit()
        task_id = task.id

        # Delete user
        test_db.delete(sample_user)
        test_db.commit()

        # Task should be deleted too
        deleted_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None


class TestAnalyticsModel:
    """Test cases for Analytics model."""

    def test_create_analytics_event(self, test_db, sample_user, sample_task):
        """Test creating an analytics event."""
        event = Analytics(
            user_id=sample_user.id,
            task_id=sample_task.id,
            event_type="created",
            task_title=sample_task.title,
            deadline=sample_task.deadline
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        assert event.id is not None
        assert event.user_id == sample_user.id
        assert event.task_id == sample_task.id
        assert event.event_type == "created"
        assert event.event_timestamp is not None
        assert event.task_title == sample_task.title
        assert event.deadline == sample_task.deadline

    def test_analytics_repr(self, test_db, sample_analytics_event):
        """Test analytics string representation."""
        repr_str = repr(sample_analytics_event)
        assert "Analytics" in repr_str
        assert "created" in repr_str

    def test_analytics_completion_fields(self, test_db, sample_user, sample_task):
        """Test analytics completion tracking fields."""
        event = Analytics(
            user_id=sample_user.id,
            task_id=sample_task.id,
            event_type="completed",
            task_title=sample_task.title,
            deadline=sample_task.deadline,
            was_completed_on_time=True,
            completion_delay_hours=-2.5
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        assert event.was_completed_on_time is True
        assert event.completion_delay_hours == -2.5

    def test_analytics_missed_deadline_event(self, test_db, sample_user, overdue_task):
        """Test missed deadline analytics event."""
        event = Analytics(
            user_id=sample_user.id,
            task_id=overdue_task.id,
            event_type="missed_deadline",
            task_title=overdue_task.title,
            deadline=overdue_task.deadline
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        assert event.event_type == "missed_deadline"
        assert event.was_completed_on_time is None
        assert event.completion_delay_hours is None

    def test_analytics_user_relationship(self, test_db, sample_analytics_event, sample_user):
        """Test analytics-user relationship."""
        test_db.refresh(sample_analytics_event)
        assert sample_analytics_event.user is not None
        assert sample_analytics_event.user.id == sample_user.id

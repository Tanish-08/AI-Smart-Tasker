"""Unit tests for TaskManager utility class."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.app.utils.task_manager import TaskManager
from backend.app.schemas.task_schema import TaskCreate, TaskUpdate
from backend.app.models.task import Task
from backend.app.models.analytics import Analytics


class TestTaskManagerCreate:
    """Test cases for TaskManager.create_task()."""

    def test_create_task_success(self, test_db, sample_user):
        """Test successful task creation."""
        task_data = TaskCreate(
            title="New Task",
            description="Task description",
            deadline=datetime.utcnow() + timedelta(days=2),
            user_id=sample_user.id
        )

        task = TaskManager.create_task(test_db, task_data)

        assert task.id is not None
        assert task.title == "New Task"
        assert task.description == "Task description"
        assert task.user_id == sample_user.id
        assert task.completed is False

    def test_create_task_creates_analytics_event(self, test_db, sample_user):
        """Test that creating a task also creates an analytics event."""
        task_data = TaskCreate(
            title="Analytics Test",
            description="Test analytics",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )

        task = TaskManager.create_task(test_db, task_data)

        # Check analytics event was created
        event = test_db.query(Analytics).filter(
            Analytics.task_id == task.id,
            Analytics.event_type == "created"
        ).first()

        assert event is not None
        assert event.user_id == sample_user.id
        assert event.task_title == task.title

    def test_create_task_rollback_on_error(self, test_db, sample_user):
        """Test that task creation is rolled back on error."""
        task_data = TaskCreate(
            title="Error Task",
            description="This will fail",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=999999  # Non-existent user
        )

        with pytest.raises(Exception):
            TaskManager.create_task(test_db, task_data)

        # Verify no task was created
        task_count = test_db.query(Task).filter(Task.title == "Error Task").count()
        assert task_count == 0


class TestTaskManagerGet:
    """Test cases for TaskManager.get_task()."""

    def test_get_task_by_id(self, test_db, sample_task):
        """Test getting a task by ID."""
        task = TaskManager.get_task(test_db, sample_task.id)

        assert task is not None
        assert task.id == sample_task.id
        assert task.title == sample_task.title

    def test_get_task_with_user_filter(self, test_db, sample_task, sample_user):
        """Test getting a task with user ID filter."""
        task = TaskManager.get_task(test_db, sample_task.id, sample_user.id)

        assert task is not None
        assert task.id == sample_task.id

    def test_get_task_wrong_user(self, test_db, sample_task):
        """Test getting a task with wrong user ID returns None."""
        task = TaskManager.get_task(test_db, sample_task.id, 999999)

        assert task is None

    def test_get_task_not_found(self, test_db):
        """Test getting a non-existent task returns None."""
        task = TaskManager.get_task(test_db, 999999)

        assert task is None


class TestTaskManagerGetTasks:
    """Test cases for TaskManager.get_tasks()."""

    def test_get_tasks_for_user(self, test_db, sample_user, sample_task):
        """Test getting all tasks for a user."""
        tasks = TaskManager.get_tasks(test_db, user_id=sample_user.id)

        assert len(tasks) >= 1
        assert any(t.id == sample_task.id for t in tasks)

    def test_get_tasks_completed_filter(self, test_db, sample_user, sample_task):
        """Test filtering tasks by completion status."""
        # Create completed task
        completed_task = Task(
            title="Completed Task",
            description="Done",
            deadline=datetime.utcnow() + timedelta(days=1),
            completed=True,
            user_id=sample_user.id
        )
        test_db.add(completed_task)
        test_db.commit()

        # Get only completed tasks
        tasks = TaskManager.get_tasks(test_db, user_id=sample_user.id, completed=True)

        assert all(t.completed for t in tasks)
        assert any(t.id == completed_task.id for t in tasks)

    def test_get_tasks_overdue_only(self, test_db, sample_user, overdue_task):
        """Test getting only overdue tasks."""
        tasks = TaskManager.get_tasks(
            test_db,
            user_id=sample_user.id,
            overdue_only=True
        )

        assert len(tasks) >= 1
        assert all(t.is_overdue for t in tasks)

    def test_get_tasks_pagination(self, test_db, sample_user):
        """Test task pagination with skip and limit."""
        # Create multiple tasks
        for i in range(5):
            task = Task(
                title=f"Task {i}",
                description=f"Description {i}",
                deadline=datetime.utcnow() + timedelta(days=i+1),
                user_id=sample_user.id
            )
            test_db.add(task)
        test_db.commit()

        # Test pagination
        tasks_page1 = TaskManager.get_tasks(test_db, user_id=sample_user.id, skip=0, limit=2)
        tasks_page2 = TaskManager.get_tasks(test_db, user_id=sample_user.id, skip=2, limit=2)

        assert len(tasks_page1) == 2
        assert len(tasks_page2) == 2
        assert tasks_page1[0].id != tasks_page2[0].id

    def test_get_tasks_empty_result(self, test_db, sample_user):
        """Test getting tasks when user has none completed."""
        tasks = TaskManager.get_tasks(test_db, user_id=999999)

        assert len(tasks) == 0


class TestTaskManagerUpdate:
    """Test cases for TaskManager.update_task()."""

    def test_update_task_title(self, test_db, sample_task, sample_user):
        """Test updating task title."""
        update_data = TaskUpdate(title="Updated Title")

        updated_task = TaskManager.update_task(
            test_db,
            sample_task.id,
            update_data,
            sample_user.id
        )

        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.description == sample_task.description

    def test_update_task_completion(self, test_db, sample_task, sample_user):
        """Test updating task completion status."""
        update_data = TaskUpdate(completed=True)

        updated_task = TaskManager.update_task(
            test_db,
            sample_task.id,
            update_data,
            sample_user.id
        )

        assert updated_task.completed is True

    def test_update_task_creates_analytics_on_completion(self, test_db, sample_task, sample_user):
        """Test that completing a task creates an analytics event."""
        update_data = TaskUpdate(completed=True)

        TaskManager.update_task(test_db, sample_task.id, update_data, sample_user.id)

        # Check analytics event was created
        event = test_db.query(Analytics).filter(
            Analytics.task_id == sample_task.id,
            Analytics.event_type == "completed"
        ).first()

        assert event is not None
        assert event.was_completed_on_time is not None
        assert event.completion_delay_hours is not None

    def test_update_task_completion_delay_calculation(self, test_db, sample_user):
        """Test completion delay hours calculation."""
        # Create task with deadline in the past
        past_deadline = datetime.utcnow() - timedelta(hours=5)
        task = Task(
            title="Late Task",
            description="This is late",
            deadline=past_deadline,
            user_id=sample_user.id
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # Complete the task
        update_data = TaskUpdate(completed=True)
        TaskManager.update_task(test_db, task.id, update_data, sample_user.id)

        # Check analytics
        event = test_db.query(Analytics).filter(
            Analytics.task_id == task.id,
            Analytics.event_type == "completed"
        ).first()

        assert event.was_completed_on_time is False
        assert event.completion_delay_hours > 0

    def test_update_task_wrong_user(self, test_db, sample_task):
        """Test updating task with wrong user ID returns None."""
        update_data = TaskUpdate(title="Should Fail")

        result = TaskManager.update_task(
            test_db,
            sample_task.id,
            update_data,
            999999
        )

        assert result is None

    def test_update_task_not_found(self, test_db, sample_user):
        """Test updating non-existent task returns None."""
        update_data = TaskUpdate(title="Should Fail")

        result = TaskManager.update_task(
            test_db,
            999999,
            update_data,
            sample_user.id
        )

        assert result is None

    def test_update_task_multiple_fields(self, test_db, sample_task, sample_user):
        """Test updating multiple fields at once."""
        new_deadline = datetime.utcnow() + timedelta(days=5)
        update_data = TaskUpdate(
            title="Multi Update",
            description="New description",
            deadline=new_deadline,
            completed=True
        )

        updated_task = TaskManager.update_task(
            test_db,
            sample_task.id,
            update_data,
            sample_user.id
        )

        assert updated_task.title == "Multi Update"
        assert updated_task.description == "New description"
        assert updated_task.deadline == new_deadline
        assert updated_task.completed is True


class TestTaskManagerDelete:
    """Test cases for TaskManager.delete_task()."""

    def test_delete_task_success(self, test_db, sample_task, sample_user):
        """Test successful task deletion."""
        task_id = sample_task.id

        result = TaskManager.delete_task(test_db, task_id, sample_user.id)

        assert result is True

        # Verify task is deleted
        deleted_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None

    def test_delete_task_wrong_user(self, test_db, sample_task):
        """Test deleting task with wrong user ID returns False."""
        result = TaskManager.delete_task(test_db, sample_task.id, 999999)

        assert result is False

        # Verify task still exists
        task = test_db.query(Task).filter(Task.id == sample_task.id).first()
        assert task is not None

    def test_delete_task_not_found(self, test_db, sample_user):
        """Test deleting non-existent task returns False."""
        result = TaskManager.delete_task(test_db, 999999, sample_user.id)

        assert result is False


class TestTaskManagerGetOverdue:
    """Test cases for TaskManager.get_overdue_tasks()."""

    def test_get_overdue_tasks(self, test_db, sample_user, overdue_task):
        """Test getting overdue tasks."""
        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)

        assert len(overdue_tasks) >= 1
        assert all(t.is_overdue for t in overdue_tasks)
        assert any(t.id == overdue_task.id for t in overdue_tasks)

    def test_get_overdue_tasks_excludes_completed(self, test_db, sample_user):
        """Test that overdue tasks excludes completed tasks."""
        # Create overdue but completed task
        completed_overdue = Task(
            title="Completed Overdue",
            description="Done but late",
            deadline=datetime.utcnow() - timedelta(days=1),
            completed=True,
            user_id=sample_user.id
        )
        test_db.add(completed_overdue)
        test_db.commit()

        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)

        # Completed task should not be in results
        assert all(not t.completed for t in overdue_tasks)

    def test_get_overdue_tasks_no_user_filter(self, test_db, overdue_task):
        """Test getting all overdue tasks without user filter."""
        overdue_tasks = TaskManager.get_overdue_tasks(test_db)

        assert len(overdue_tasks) >= 1

    def test_get_overdue_tasks_empty_result(self, test_db, sample_user):
        """Test getting overdue tasks when there are none."""
        # Create only future tasks
        future_task = Task(
            title="Future Task",
            description="Not overdue",
            deadline=datetime.utcnow() + timedelta(days=10),
            user_id=sample_user.id
        )
        test_db.add(future_task)
        test_db.commit()

        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)

        # Only get overdue tasks, not future ones
        assert all(t.deadline < datetime.utcnow() for t in overdue_tasks)

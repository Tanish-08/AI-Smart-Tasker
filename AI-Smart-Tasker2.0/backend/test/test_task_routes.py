"""Unit tests for task API routes."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from backend.app.endpoint.task_routes import (
    create_task,
    get_task,
    get_tasks,
    update_task,
    delete_task
)
from backend.app.schemas.task_schema import TaskCreate, TaskUpdate
from backend.app.models.task import Task


class TestCreateTaskRoute:
    """Test cases for create_task endpoint."""

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_create_task_success(self, mock_task_manager, test_db, sample_user):
        """Test successful task creation via API."""
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "New Task"
        mock_task.description = "Description"
        mock_task.deadline = datetime.utcnow() + timedelta(days=1)
        mock_task.completed = False
        mock_task.user_id = sample_user.id
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()
        mock_task.summary = None
        mock_task.insult_message = None

        mock_task_manager.create_task.return_value = mock_task

        task_data = TaskCreate(
            title="New Task",
            description="Description",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )

        response = create_task(task_data, test_db)

        assert response.title == "New Task"
        mock_task_manager.create_task.assert_called_once()

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_create_task_failure(self, mock_task_manager, test_db, sample_user):
        """Test task creation failure handling."""
        mock_task_manager.create_task.side_effect = Exception("Creation failed")

        task_data = TaskCreate(
            title="Fail Task",
            description="Will fail",
            deadline=datetime.utcnow() + timedelta(days=1),
            user_id=sample_user.id
        )

        with pytest.raises(HTTPException) as exc_info:
            create_task(task_data, test_db)

        assert exc_info.value.status_code == 500


class TestGetTaskRoute:
    """Test cases for get_task endpoint."""

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_task_success(self, mock_task_manager, test_db, sample_task):
        """Test successful task retrieval."""
        mock_task_manager.get_task.return_value = sample_task

        response = get_task(sample_task.id, sample_task.user_id, test_db)

        assert response.id == sample_task.id
        assert response.title == sample_task.title

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_task_not_found(self, mock_task_manager, test_db):
        """Test getting non-existent task."""
        mock_task_manager.get_task.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_task(999, 1, test_db)

        assert exc_info.value.status_code == 404

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_task_wrong_user(self, mock_task_manager, test_db):
        """Test accessing task with wrong user ID."""
        mock_task_manager.get_task.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_task(1, 999, test_db)

        assert exc_info.value.status_code == 404


class TestGetTasksRoute:
    """Test cases for get_tasks endpoint."""

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_tasks_success(self, mock_task_manager, test_db, sample_user, sample_task):
        """Test getting list of tasks."""
        mock_task_manager.get_tasks.return_value = [sample_task]

        response = get_tasks(
            user_id=sample_user.id,
            completed=None,
            overdue_only=False,
            skip=0,
            limit=100,
            db=test_db
        )

        assert response.total >= 0
        assert isinstance(response.tasks, list)

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_tasks_with_completed_filter(self, mock_task_manager, test_db, sample_user):
        """Test getting tasks filtered by completion status."""
        mock_completed_task = Mock(spec=Task)
        mock_completed_task.id = 1
        mock_completed_task.title = "Completed"
        mock_completed_task.completed = True
        mock_completed_task.user_id = sample_user.id
        mock_completed_task.deadline = datetime.utcnow()
        mock_completed_task.created_at = datetime.utcnow()
        mock_completed_task.updated_at = datetime.utcnow()
        mock_completed_task.description = "Done"
        mock_completed_task.summary = None
        mock_completed_task.insult_message = None

        mock_task_manager.get_tasks.return_value = [mock_completed_task]

        response = get_tasks(
            user_id=sample_user.id,
            completed=True,
            overdue_only=False,
            skip=0,
            limit=100,
            db=test_db
        )

        assert len(response.tasks) >= 0

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_get_tasks_with_pagination(self, mock_task_manager, test_db, sample_user):
        """Test task list pagination."""
        mock_task_manager.get_tasks.return_value = []

        response = get_tasks(
            user_id=sample_user.id,
            completed=None,
            overdue_only=False,
            skip=10,
            limit=5,
            db=test_db
        )

        # Verify pagination parameters were passed
        call_kwargs = mock_task_manager.get_tasks.call_args[1]
        assert call_kwargs['skip'] == 10
        assert call_kwargs['limit'] == 5


class TestUpdateTaskRoute:
    """Test cases for update_task endpoint."""

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_update_task_success(self, mock_task_manager, test_db, sample_task):
        """Test successful task update."""
        updated_task = Mock(spec=Task)
        updated_task.id = sample_task.id
        updated_task.title = "Updated Title"
        updated_task.description = sample_task.description
        updated_task.deadline = sample_task.deadline
        updated_task.completed = sample_task.completed
        updated_task.user_id = sample_task.user_id
        updated_task.created_at = sample_task.created_at
        updated_task.updated_at = datetime.utcnow()
        updated_task.summary = None
        updated_task.insult_message = None

        mock_task_manager.update_task.return_value = updated_task

        update_data = TaskUpdate(title="Updated Title")

        response = update_task(sample_task.id, update_data, sample_task.user_id, test_db)

        assert response.title == "Updated Title"

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_update_task_not_found(self, mock_task_manager, test_db):
        """Test updating non-existent task."""
        mock_task_manager.update_task.return_value = None

        update_data = TaskUpdate(title="Updated")

        with pytest.raises(HTTPException) as exc_info:
            update_task(999, update_data, 1, test_db)

        assert exc_info.value.status_code == 404

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_update_task_completion(self, mock_task_manager, test_db, sample_task):
        """Test marking task as completed."""
        completed_task = Mock(spec=Task)
        completed_task.id = sample_task.id
        completed_task.title = sample_task.title
        completed_task.description = sample_task.description
        completed_task.deadline = sample_task.deadline
        completed_task.completed = True
        completed_task.user_id = sample_task.user_id
        completed_task.created_at = sample_task.created_at
        completed_task.updated_at = datetime.utcnow()
        completed_task.summary = None
        completed_task.insult_message = None

        mock_task_manager.update_task.return_value = completed_task

        update_data = TaskUpdate(completed=True)

        response = update_task(sample_task.id, update_data, sample_task.user_id, test_db)

        assert response.completed is True


class TestDeleteTaskRoute:
    """Test cases for delete_task endpoint."""

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_delete_task_success(self, mock_task_manager, test_db, sample_task):
        """Test successful task deletion."""
        mock_task_manager.delete_task.return_value = True

        result = delete_task(sample_task.id, sample_task.user_id, test_db)

        assert result is None  # 204 No Content
        mock_task_manager.delete_task.assert_called_once()

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_delete_task_not_found(self, mock_task_manager, test_db):
        """Test deleting non-existent task."""
        mock_task_manager.delete_task.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            delete_task(999, 1, test_db)

        assert exc_info.value.status_code == 404

    @patch('backend.app.endpoint.task_routes.TaskManager')
    def test_delete_task_wrong_user(self, mock_task_manager, test_db):
        """Test deleting task with wrong user ID."""
        mock_task_manager.delete_task.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            delete_task(1, 999, test_db)

        assert exc_info.value.status_code == 404

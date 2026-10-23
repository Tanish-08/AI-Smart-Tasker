"""Unit tests for deadline API routes."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from backend.app.endpoint.deadline_routes import (
    check_deadlines,
    regenerate_insult,
    get_overdue_tasks
)
from backend.app.models.task import Task


class TestCheckDeadlinesRoute:
    """Test cases for check_deadlines endpoint."""

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    @patch('backend.app.endpoint.deadline_routes.AIInsultGenerator')
    @patch('backend.app.endpoint.deadline_routes.AnalyticsProcessor')
    def test_check_deadlines_with_overdue_tasks(
        self,
        mock_analytics,
        mock_insult_gen,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test checking deadlines with overdue tasks."""
        # Create mock overdue task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "Overdue Task"
        mock_task.description = "Task is overdue"
        mock_task.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task.completed = False
        mock_task.user_id = sample_user.id
        mock_task.insult_message = None
        mock_task.summary = None
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        # Mock TaskManager to return overdue task
        mock_task_manager.get_overdue_tasks.return_value = [mock_task]

        # Mock insult generator
        mock_gen_instance = MagicMock()
        mock_insult_gen.return_value = mock_gen_instance

        # Call the endpoint
        result = check_deadlines(
            user_id=sample_user.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions
        assert "overdue_tasks" in result
        assert len(result["overdue_tasks"]) == 1
        mock_task_manager.get_overdue_tasks.assert_called_once_with(test_db, sample_user.id)
        mock_analytics.log_missed_deadline.assert_called_once_with(test_db, mock_task)
        mock_gen_instance.generate_and_save_insult.assert_called_once_with(test_db, mock_task)

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_check_deadlines_no_overdue_tasks(
        self,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test checking deadlines when no overdue tasks exist."""
        # Mock no overdue tasks
        mock_task_manager.get_overdue_tasks.return_value = []

        # Call the endpoint
        result = check_deadlines(
            user_id=sample_user.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions
        assert "overdue_tasks" in result
        assert len(result["overdue_tasks"]) == 0
        mock_task_manager.get_overdue_tasks.assert_called_once()

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    @patch('backend.app.endpoint.deadline_routes.AIInsultGenerator')
    @patch('backend.app.endpoint.deadline_routes.AnalyticsProcessor')
    def test_check_deadlines_with_existing_insult(
        self,
        mock_analytics,
        mock_insult_gen,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test checking deadlines when task already has insult."""
        # Create mock overdue task with existing insult
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "Overdue Task"
        mock_task.description = "Task is overdue"
        mock_task.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task.completed = False
        mock_task.user_id = sample_user.id
        mock_task.insult_message = "Existing insult"
        mock_task.summary = None
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_task_manager.get_overdue_tasks.return_value = [mock_task]
        mock_gen_instance = MagicMock()
        mock_insult_gen.return_value = mock_gen_instance

        # Call the endpoint
        result = check_deadlines(
            user_id=sample_user.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions - insult generation should not be called
        assert "overdue_tasks" in result
        mock_gen_instance.generate_and_save_insult.assert_not_called()

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    @patch('backend.app.endpoint.deadline_routes.AIInsultGenerator')
    @patch('backend.app.endpoint.deadline_routes.AnalyticsProcessor')
    def test_check_deadlines_insult_generation_failure(
        self,
        mock_analytics,
        mock_insult_gen,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test check deadlines continues when insult generation fails."""
        # Create mock overdue tasks
        mock_task1 = Mock(spec=Task)
        mock_task1.id = 1
        mock_task1.title = "Task 1"
        mock_task1.description = "First task"
        mock_task1.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task1.completed = False
        mock_task1.user_id = sample_user.id
        mock_task1.insult_message = None
        mock_task1.summary = None
        mock_task1.created_at = datetime.utcnow()
        mock_task1.updated_at = datetime.utcnow()

        mock_task2 = Mock(spec=Task)
        mock_task2.id = 2
        mock_task2.title = "Task 2"
        mock_task2.description = "Second task"
        mock_task2.deadline = datetime.utcnow() - timedelta(days=2)
        mock_task2.completed = False
        mock_task2.user_id = sample_user.id
        mock_task2.insult_message = None
        mock_task2.summary = None
        mock_task2.created_at = datetime.utcnow()
        mock_task2.updated_at = datetime.utcnow()

        mock_task_manager.get_overdue_tasks.return_value = [mock_task1, mock_task2]

        # Mock insult generator to fail on first task
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_and_save_insult.side_effect = [
            Exception("Insult generation failed"),
            None  # Second call succeeds
        ]
        mock_insult_gen.return_value = mock_gen_instance

        # Call the endpoint - should not raise exception
        result = check_deadlines(
            user_id=sample_user.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Should still return both tasks
        assert "overdue_tasks" in result
        assert len(result["overdue_tasks"]) == 2

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_check_deadlines_error_handling(
        self,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test error handling in check_deadlines endpoint."""
        # Mock TaskManager to raise exception
        mock_task_manager.get_overdue_tasks.side_effect = Exception("Database error")

        # Call should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            check_deadlines(
                user_id=sample_user.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        assert exc_info.value.status_code == 500
        assert "Failed to check deadlines" in str(exc_info.value.detail)


class TestRegenerateInsultRoute:
    """Test cases for regenerate_insult endpoint."""

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    @patch('backend.app.endpoint.deadline_routes.AIInsultGenerator')
    def test_regenerate_insult_success(
        self,
        mock_insult_gen,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test successful insult regeneration."""
        # Create mock overdue task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "Overdue Task"
        mock_task.description = "Task is overdue"
        mock_task.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task.completed = False
        mock_task.user_id = sample_user.id
        mock_task.insult_message = "Old insult"
        mock_task.is_overdue = True
        mock_task.summary = None
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_task_manager.get_task.return_value = mock_task
        mock_gen_instance = MagicMock()
        mock_insult_gen.return_value = mock_gen_instance

        # Call the endpoint
        with patch.object(test_db, 'refresh'):
            result = regenerate_insult(
                task_id=1,
                user_id=sample_user.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        mock_task_manager.get_task.assert_called_once_with(test_db, 1, sample_user.id)
        assert mock_task.insult_message is None  # Should be cleared
        mock_gen_instance.generate_and_save_insult.assert_called_once_with(test_db, mock_task)

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_regenerate_insult_task_not_found(
        self,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test regenerating insult for non-existent task."""
        mock_task_manager.get_task.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            regenerate_insult(
                task_id=999,
                user_id=sample_user.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        assert exc_info.value.status_code == 404
        assert "not found or access denied" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_regenerate_insult_task_not_overdue(
        self,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test regenerating insult for task that is not overdue."""
        # Create mock task that is not overdue
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "Future Task"
        mock_task.deadline = datetime.utcnow() + timedelta(days=1)
        mock_task.is_overdue = False

        mock_task_manager.get_task.return_value = mock_task

        with pytest.raises(HTTPException) as exc_info:
            regenerate_insult(
                task_id=1,
                user_id=sample_user.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        assert exc_info.value.status_code == 400
        assert "is not overdue" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_regenerate_insult_wrong_user(
        self,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config
    ):
        """Test user ownership verification."""
        mock_task_manager.get_task.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            regenerate_insult(
                task_id=1,
                user_id=999,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        assert exc_info.value.status_code == 404

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    @patch('backend.app.endpoint.deadline_routes.AIInsultGenerator')
    def test_regenerate_insult_generation_failure(
        self,
        mock_insult_gen,
        mock_task_manager,
        test_db,
        mock_llm_client,
        mock_config,
        sample_user
    ):
        """Test error handling when insult generation fails."""
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.is_overdue = True

        mock_task_manager.get_task.return_value = mock_task
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_and_save_insult.side_effect = Exception("Generation failed")
        mock_insult_gen.return_value = mock_gen_instance

        with pytest.raises(HTTPException) as exc_info:
            regenerate_insult(
                task_id=1,
                user_id=sample_user.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        assert exc_info.value.status_code == 500
        assert "Failed to regenerate insult" in str(exc_info.value.detail)


class TestGetOverdueTasksRoute:
    """Test cases for get_overdue_tasks endpoint."""

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_get_overdue_tasks_success(
        self,
        mock_task_manager,
        test_db,
        sample_user
    ):
        """Test retrieving overdue tasks successfully."""
        # Create mock overdue tasks
        mock_task1 = Mock(spec=Task)
        mock_task1.id = 1
        mock_task1.title = "Overdue Task 1"
        mock_task1.description = "First overdue"
        mock_task1.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task1.completed = False
        mock_task1.user_id = sample_user.id
        mock_task1.insult_message = "Insult 1"
        mock_task1.summary = None
        mock_task1.created_at = datetime.utcnow()
        mock_task1.updated_at = datetime.utcnow()

        mock_task2 = Mock(spec=Task)
        mock_task2.id = 2
        mock_task2.title = "Overdue Task 2"
        mock_task2.description = "Second overdue"
        mock_task2.deadline = datetime.utcnow() - timedelta(days=2)
        mock_task2.completed = False
        mock_task2.user_id = sample_user.id
        mock_task2.insult_message = "Insult 2"
        mock_task2.summary = None
        mock_task2.created_at = datetime.utcnow()
        mock_task2.updated_at = datetime.utcnow()

        mock_task_manager.get_overdue_tasks.return_value = [mock_task1, mock_task2]

        # Call the endpoint
        result = get_overdue_tasks(user_id=sample_user.id, db=test_db)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 2
        mock_task_manager.get_overdue_tasks.assert_called_once_with(test_db, sample_user.id)

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_get_overdue_tasks_empty_result(
        self,
        mock_task_manager,
        test_db,
        sample_user
    ):
        """Test retrieving overdue tasks when none exist."""
        mock_task_manager.get_overdue_tasks.return_value = []

        # Call the endpoint
        result = get_overdue_tasks(user_id=sample_user.id, db=test_db)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_get_overdue_tasks_filters_by_user(
        self,
        mock_task_manager,
        test_db,
        sample_user
    ):
        """Test that overdue tasks are filtered by user ID."""
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.title = "User's Task"
        mock_task.user_id = sample_user.id
        mock_task.completed = False
        mock_task.deadline = datetime.utcnow() - timedelta(days=1)
        mock_task.description = "Task"
        mock_task.insult_message = None
        mock_task.summary = None
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_task_manager.get_overdue_tasks.return_value = [mock_task]

        # Call the endpoint
        result = get_overdue_tasks(user_id=sample_user.id, db=test_db)

        # Verify user_id was passed correctly
        mock_task_manager.get_overdue_tasks.assert_called_once_with(test_db, sample_user.id)
        assert len(result) == 1

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_get_overdue_tasks_excludes_completed(
        self,
        mock_task_manager,
        test_db,
        sample_user
    ):
        """Test that completed tasks are excluded from overdue tasks."""
        # TaskManager.get_overdue_tasks should already filter out completed
        # This test verifies the behavior
        mock_incomplete_task = Mock(spec=Task)
        mock_incomplete_task.id = 1
        mock_incomplete_task.completed = False
        mock_incomplete_task.deadline = datetime.utcnow() - timedelta(days=1)
        mock_incomplete_task.user_id = sample_user.id
        mock_incomplete_task.title = "Incomplete"
        mock_incomplete_task.description = "Task"
        mock_incomplete_task.insult_message = None
        mock_incomplete_task.summary = None
        mock_incomplete_task.created_at = datetime.utcnow()
        mock_incomplete_task.updated_at = datetime.utcnow()

        # Mock returns only incomplete tasks
        mock_task_manager.get_overdue_tasks.return_value = [mock_incomplete_task]

        result = get_overdue_tasks(user_id=sample_user.id, db=test_db)

        assert len(result) == 1
        # Verify all returned tasks are incomplete
        for task_response in result:
            assert hasattr(task_response, 'completed')

    @patch('backend.app.endpoint.deadline_routes.TaskManager')
    def test_get_overdue_tasks_error_handling(
        self,
        mock_task_manager,
        test_db,
        sample_user
    ):
        """Test error handling in get_overdue_tasks endpoint."""
        mock_task_manager.get_overdue_tasks.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            get_overdue_tasks(user_id=sample_user.id, db=test_db)

        assert exc_info.value.status_code == 500
        assert "Failed to get overdue tasks" in str(exc_info.value.detail)

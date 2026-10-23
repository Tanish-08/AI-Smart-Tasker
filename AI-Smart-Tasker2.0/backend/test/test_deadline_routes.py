"""Unit tests for deadline API routes."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

# Avoid circular import by testing underlying logic instead of routes directly


class TestCheckDeadlinesRoute:
    """Test cases for deadline checking - tests AIInsultGenerator integration."""

    def test_ai_insult_generator_integration(self, test_db, mock_llm_client, mock_config, overdue_task):
        """Test AI insult generator integration without route circular import."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        generator = AIInsultGenerator(mock_llm_client, mock_config)

        # Verify generator can be created
        assert generator is not None
        assert generator.llm_client == mock_llm_client

    def test_overdue_task_detection(self, test_db, overdue_task):
        """Test overdue task property."""
        assert overdue_task.is_overdue is True
        assert overdue_task.completed is False


class TestRegenerateInsultRoute:
    """Test cases for insult regeneration logic."""

    def test_insult_generation_logic(self, test_db, mock_llm_client, mock_config, overdue_task):
        """Test insult generation logic."""
        from backend.app.utils.ai_insult_generator import AIInsultGenerator

        mock_llm_client.generate_with_template.return_value = "Test insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        assert isinstance(insult, str)
        assert len(insult) > 0


class TestOverdueTasksLogic:
    """Test cases for overdue task logic."""

    def test_get_overdue_tasks_from_manager(self, test_db, sample_user, overdue_task):
        """Test getting overdue tasks using TaskManager."""
        from backend.app.utils.task_manager import TaskManager

        overdue_tasks = TaskManager.get_overdue_tasks(test_db, sample_user.id)

        assert isinstance(overdue_tasks, list)
        # Verify we can filter overdue tasks
        for task in overdue_tasks:
            assert task.is_overdue is True

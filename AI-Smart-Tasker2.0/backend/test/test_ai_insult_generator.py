"""Unit tests for AI insult generator."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from backend.app.utils.ai_insult_generator import AIInsultGenerator
from backend.app.models.task import Task


class TestAIInsultGeneratorInit:
    """Test cases for AIInsultGenerator initialization."""

    def test_init_success(self, mock_llm_client, mock_config):
        """Test successful insult generator initialization."""
        generator = AIInsultGenerator(mock_llm_client, mock_config)

        assert generator.llm_client == mock_llm_client
        assert generator.config == mock_config
        assert generator.prompts is not None


class TestGenerateInsult:
    """Test cases for generate_insult method."""

    def test_generate_insult_success(self, mock_llm_client, mock_config, overdue_task):
        """Test successful insult generation."""
        mock_llm_client.generate_with_template.return_value = "You missed your deadline!"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        assert insult == "You missed your deadline!"
        mock_llm_client.generate_with_template.assert_called_once()

    def test_generate_insult_strips_quotes(self, mock_llm_client, mock_config, overdue_task):
        """Test that insult strips quotes from response."""
        mock_llm_client.generate_with_template.return_value = '"Quoted insult"'

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        assert insult == "Quoted insult"

    def test_generate_insult_api_failure_returns_fallback(
        self, mock_llm_client, mock_config, overdue_task
    ):
        """Test that API failure returns fallback insult."""
        mock_llm_client.generate_with_template.side_effect = Exception("API Error")

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_insult(overdue_task)

        # Should return a fallback insult
        assert isinstance(insult, str)
        assert len(insult) > 0

    def test_generate_insult_uses_high_temperature(
        self, mock_llm_client, mock_config, overdue_task
    ):
        """Test that insult generation uses high temperature for creativity."""
        mock_llm_client.generate_with_template.return_value = "Creative insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        generator.generate_insult(overdue_task)

        # Verify temperature parameter
        call_kwargs = mock_llm_client.generate_with_template.call_args[1]
        assert call_kwargs.get('temperature') == 0.8


class TestGenerateAndSaveInsult:
    """Test cases for generate_and_save_insult method."""

    def test_generate_and_save_new_insult(
        self, test_db, mock_llm_client, mock_config, overdue_task
    ):
        """Test generating and saving new insult."""
        mock_llm_client.generate_with_template.return_value = "New insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_and_save_insult(test_db, overdue_task)

        assert insult == "New insult"
        test_db.refresh(overdue_task)
        assert overdue_task.insult_message == "New insult"

    def test_generate_and_save_returns_existing_insult(
        self, test_db, mock_llm_client, mock_config, overdue_task
    ):
        """Test that existing insult is returned without regenerating."""
        overdue_task.insult_message = "Existing insult"
        test_db.commit()

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator.generate_and_save_insult(test_db, overdue_task)

        assert insult == "Existing insult"
        # Should not call LLM client
        mock_llm_client.generate_with_template.assert_not_called()

    def test_generate_and_save_rollback_on_error(
        self, test_db, mock_llm_client, mock_config, overdue_task
    ):
        """Test database rollback on save error."""
        mock_llm_client.generate_with_template.return_value = "Test insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)

        # Force a database error by closing the session
        original_commit = test_db.commit
        test_db.commit = Mock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception):
            generator.generate_and_save_insult(test_db, overdue_task)

        # Restore original commit
        test_db.commit = original_commit


class TestBatchGenerateInsults:
    """Test cases for batch_generate_insults method."""

    def test_batch_generate_for_multiple_tasks(
        self, test_db, mock_llm_client, mock_config, sample_user
    ):
        """Test batch insult generation for multiple tasks."""
        # Create multiple overdue tasks
        tasks = []
        for i in range(3):
            task = Task(
                title=f"Overdue Task {i}",
                description=f"Task {i}",
                deadline=datetime.utcnow() - timedelta(days=1),
                user_id=sample_user.id
            )
            test_db.add(task)
            tasks.append(task)
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "Batch insult"

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        results = generator.batch_generate_insults(test_db, tasks)

        assert len(results) == 3
        for task in tasks:
            assert task.id in results

    def test_batch_generate_continues_on_individual_failure(
        self, test_db, mock_llm_client, mock_config, sample_user
    ):
        """Test that batch processing continues even if one fails."""
        # Create tasks
        task1 = Task(
            title="Task 1",
            description="First",
            deadline=datetime.utcnow() - timedelta(days=1),
            user_id=sample_user.id
        )
        task2 = Task(
            title="Task 2",
            description="Second",
            deadline=datetime.utcnow() - timedelta(days=1),
            user_id=sample_user.id
        )
        test_db.add(task1)
        test_db.add(task2)
        test_db.commit()

        # First call fails, second succeeds
        mock_llm_client.generate_with_template.side_effect = [
            Exception("API Error"),
            "Success insult"
        ]

        generator = AIInsultGenerator(mock_llm_client, mock_config)
        results = generator.batch_generate_insults(test_db, [task1, task2])

        # Both tasks should have results
        assert len(results) == 2
        assert task1.id in results  # Fallback insult
        assert task2.id in results


class TestFallbackInsult:
    """Test cases for fallback insult generation."""

    def test_fallback_insult_returns_string(self, mock_llm_client, mock_config):
        """Test that fallback insult returns a non-empty string."""
        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator._get_fallback_insult()

        assert isinstance(insult, str)
        assert len(insult) > 0

    def test_fallback_insult_is_developer_themed(self, mock_llm_client, mock_config):
        """Test that fallback insults are developer-themed."""
        generator = AIInsultGenerator(mock_llm_client, mock_config)
        insult = generator._get_fallback_insult()

        # Check for programming-related keywords
        keywords = ["git", "code", "bug", "404", "commit", "deadline", "Explorer"]
        assert any(keyword.lower() in insult.lower() for keyword in keywords)

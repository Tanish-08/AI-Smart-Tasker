"""Unit tests for summary generator."""
import pytest
from unittest.mock import Mock, MagicMock

from backend.app.utils.summary_generator import SummaryGenerator
from backend.app.models.task import Task


class TestSummaryGeneratorInit:
    """Test cases for SummaryGenerator initialization."""

    def test_init_success(self, mock_llm_client, mock_config):
        """Test successful summary generator initialization."""
        generator = SummaryGenerator(mock_llm_client, mock_config)

        assert generator.llm_client == mock_llm_client
        assert generator.config == mock_config
        assert generator.prompts is not None


class TestGenerateSummary:
    """Test cases for generate_summary method."""

    def test_generate_summary_with_description(self, mock_llm_client, mock_config):
        """Test summary generation with task description."""
        mock_llm_client.generate_with_template.return_value = "Generated summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_summary(
            "Test Task",
            "Task description here"
        )

        assert summary == "Generated summary"
        mock_llm_client.generate_with_template.assert_called_once()

    def test_generate_summary_without_description(self, mock_llm_client, mock_config):
        """Test summary generation without task description."""
        mock_llm_client.generate_with_template.return_value = "Summary without desc"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_summary("Test Task", None)

        assert summary == "Summary without desc"

        # Verify "No description provided" was used
        call_args = mock_llm_client.generate_with_template.call_args
        variables = call_args[1]['variables']
        assert variables['task_description'] == "No description provided"

    def test_generate_summary_strips_quotes(self, mock_llm_client, mock_config):
        """Test that summary strips quotes from response."""
        mock_llm_client.generate_with_template.return_value = '"Quoted summary"'

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_summary("Test", "Description")

        assert summary == "Quoted summary"

    def test_generate_summary_error_propagates(self, mock_llm_client, mock_config):
        """Test that errors during generation are propagated."""
        mock_llm_client.generate_with_template.side_effect = Exception("API Error")

        generator = SummaryGenerator(mock_llm_client, mock_config)

        with pytest.raises(Exception):
            generator.generate_summary("Test", "Description")


class TestModifySummary:
    """Test cases for modify_summary method."""

    def test_modify_summary_success(self, mock_llm_client, mock_config):
        """Test successful summary modification."""
        mock_llm_client.generate_with_template.return_value = "Modified summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        modified = generator.modify_summary(
            "Original summary",
            "Make it shorter"
        )

        assert modified == "Modified summary"
        mock_llm_client.generate_with_template.assert_called_once()

    def test_modify_summary_uses_correct_prompt(self, mock_llm_client, mock_config):
        """Test that modification uses correct prompt template."""
        mock_llm_client.generate_with_template.return_value = "Modified"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        generator.modify_summary("Current", "Change request")

        call_args = mock_llm_client.generate_with_template.call_args
        variables = call_args[1]['variables']

        assert variables['current_summary'] == "Current"
        assert variables['modification_prompt'] == "Change request"

    def test_modify_summary_error_propagates(self, mock_llm_client, mock_config):
        """Test that modification errors are propagated."""
        mock_llm_client.generate_with_template.side_effect = Exception("Modification error")

        generator = SummaryGenerator(mock_llm_client, mock_config)

        with pytest.raises(Exception):
            generator.modify_summary("Current", "Change")


class TestGenerateAndSaveSummary:
    """Test cases for generate_and_save_summary method."""

    def test_generate_and_save_success(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test generating and saving summary."""
        mock_llm_client.generate_with_template.return_value = "Saved summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.generate_and_save_summary(test_db, sample_task)

        assert summary == "Saved summary"
        test_db.refresh(sample_task)
        assert sample_task.summary == "Saved summary"

    def test_generate_and_save_rollback_on_error(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test database rollback on save error."""
        mock_llm_client.generate_with_template.return_value = "Test summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)

        # Force a database error
        original_commit = test_db.commit
        test_db.commit = Mock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception):
            generator.generate_and_save_summary(test_db, sample_task)

        # Restore commit
        test_db.commit = original_commit


class TestModifyAndSaveSummary:
    """Test cases for modify_and_save_summary method."""

    def test_modify_and_save_success(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test modifying and saving summary."""
        sample_task.summary = "Original"
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "Modified summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        modified = generator.modify_and_save_summary(
            test_db,
            sample_task,
            "Make changes"
        )

        assert modified == "Modified summary"
        test_db.refresh(sample_task)
        assert sample_task.summary == "Modified summary"

    def test_modify_and_save_no_existing_summary_error(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test error when modifying task without summary."""
        sample_task.summary = None
        test_db.commit()

        generator = SummaryGenerator(mock_llm_client, mock_config)

        with pytest.raises(ValueError, match="does not have a summary"):
            generator.modify_and_save_summary(test_db, sample_task, "Change")

    def test_modify_and_save_rollback_on_error(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test database rollback on modification error."""
        sample_task.summary = "Original"
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "Modified"

        generator = SummaryGenerator(mock_llm_client, mock_config)

        # Force database error
        original_commit = test_db.commit
        test_db.commit = Mock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception):
            generator.modify_and_save_summary(test_db, sample_task, "Change")

        test_db.commit = original_commit


class TestRegenerateSummary:
    """Test cases for regenerate_summary method."""

    def test_regenerate_summary_replaces_existing(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test that regeneration replaces existing summary."""
        sample_task.summary = "Old summary"
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "New summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.regenerate_summary(test_db, sample_task)

        assert summary == "New summary"
        test_db.refresh(sample_task)
        assert sample_task.summary == "New summary"

    def test_regenerate_summary_creates_if_none_exists(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test regeneration when no summary exists."""
        sample_task.summary = None
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "First summary"

        generator = SummaryGenerator(mock_llm_client, mock_config)
        summary = generator.regenerate_summary(test_db, sample_task)

        assert summary == "First summary"
        test_db.refresh(sample_task)
        assert sample_task.summary == "First summary"

    def test_regenerate_summary_rollback_on_error(
        self, test_db, mock_llm_client, mock_config, sample_task
    ):
        """Test database rollback on regeneration error."""
        sample_task.summary = "Original"
        test_db.commit()

        mock_llm_client.generate_with_template.return_value = "New"

        generator = SummaryGenerator(mock_llm_client, mock_config)

        # Force database error
        original_commit = test_db.commit
        test_db.commit = Mock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception):
            generator.regenerate_summary(test_db, sample_task)

        test_db.commit = original_commit

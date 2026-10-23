"""Unit tests for summary API routes."""
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

# Import schemas without importing routes to avoid circular dependency
from backend.app.schemas.summary_schema import SummaryRequest, ModifyRequest


class TestGenerateSummaryEndpoint:
    """Comprehensive test cases for /api/summaries/generate endpoint."""

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_generate_summary_success(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test successful summary generation."""
        from backend.app.endpoint.summary_routes import generate_summary

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance and methods
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_and_save_summary.return_value = "Generated summary text"
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = SummaryRequest(
            task_id=sample_task.id,
            task_title=sample_task.title,
            task_description=sample_task.description
        )

        # Call endpoint
        response = generate_summary(
            request=request,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions
        assert response.task_id == sample_task.id
        assert response.summary == "Generated summary text"
        assert response.success is True
        mock_task_manager.get_task.assert_called_once_with(test_db, sample_task.id)
        mock_generator_instance.generate_and_save_summary.assert_called_once()

    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_generate_summary_task_not_found(
        self, mock_task_manager, test_db, mock_llm_client, mock_config
    ):
        """Test error when task is not found."""
        from backend.app.endpoint.summary_routes import generate_summary

        # Mock TaskManager.get_task to return None
        mock_task_manager.get_task.return_value = None

        # Create request
        request = SummaryRequest(
            task_id=999,
            task_title="Non-existent task",
            task_description="This task does not exist"
        )

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            generate_summary(
                request=request,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 404
        assert "Task 999 not found" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_generate_summary_llm_failure(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test error handling when LLM generation fails."""
        from backend.app.endpoint.summary_routes import generate_summary

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator to raise exception
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_and_save_summary.side_effect = Exception("LLM API error")
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = SummaryRequest(
            task_id=sample_task.id,
            task_title=sample_task.title,
            task_description=sample_task.description
        )

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            generate_summary(
                request=request,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 500
        assert "Failed to generate summary" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_generate_summary_database_save(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that summary is saved to database."""
        from backend.app.endpoint.summary_routes import generate_summary

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        generated_summary = "Saved summary in database"
        mock_generator_instance.generate_and_save_summary.return_value = generated_summary
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = SummaryRequest(
            task_id=sample_task.id,
            task_title=sample_task.title,
            task_description=sample_task.description
        )

        # Call endpoint
        response = generate_summary(
            request=request,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify the database session was passed to generator
        call_args = mock_generator_instance.generate_and_save_summary.call_args
        assert call_args[0][0] == test_db  # First arg should be db session
        assert response.summary == generated_summary


class TestModifySummaryEndpoint:
    """Comprehensive test cases for /api/summaries/modify endpoint."""

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_success(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test successful summary modification."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Set existing summary on task
        sample_task.summary = "Original summary text"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        mock_generator_instance.modify_and_save_summary.return_value = "Modified summary text"
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = ModifyRequest(
            task_id=sample_task.id,
            current_summary="Original summary text",
            modification_prompt="Make it more concise"
        )

        # Call endpoint
        response = modify_summary(
            request=request,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions
        assert response.task_id == sample_task.id
        assert response.original_summary == "Original summary text"
        assert response.modified_summary == "Modified summary text"
        assert response.success is True
        mock_generator_instance.modify_and_save_summary.assert_called_once()

    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_task_not_found(
        self, mock_task_manager, test_db, mock_llm_client, mock_config
    ):
        """Test error when task is not found."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Mock TaskManager.get_task to return None
        mock_task_manager.get_task.return_value = None

        # Create request
        request = ModifyRequest(
            task_id=999,
            current_summary="Original summary",
            modification_prompt="Make it shorter"
        )

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            modify_summary(
                request=request,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 404
        assert "Task 999 not found" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_no_existing_summary(
        self, mock_task_manager, test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test error when task has no existing summary."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Ensure task has no summary
        sample_task.summary = None

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Create request
        request = ModifyRequest(
            task_id=sample_task.id,
            current_summary="Some summary",
            modification_prompt="Make it shorter"
        )

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            modify_summary(
                request=request,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 400
        assert "does not have a summary to modify" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_with_query_application(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that modification prompt is correctly applied."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Set existing summary on task
        sample_task.summary = "Long detailed summary with lots of information"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        mock_generator_instance.modify_and_save_summary.return_value = "Brief summary"
        mock_summary_generator.return_value = mock_generator_instance

        # Create request with specific modification
        modification_prompt = "Make it much shorter and more concise"
        request = ModifyRequest(
            task_id=sample_task.id,
            current_summary=sample_task.summary,
            modification_prompt=modification_prompt
        )

        # Call endpoint
        response = modify_summary(
            request=request,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify modification prompt was passed correctly
        call_args = mock_generator_instance.modify_and_save_summary.call_args
        assert call_args[0][2] == modification_prompt  # Third arg is modification_prompt
        assert len(response.modified_summary) < len(response.original_summary)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_database_update(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that modified summary is saved to database."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Set existing summary
        sample_task.summary = "Original summary"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        mock_generator_instance.modify_and_save_summary.return_value = "Updated in DB"
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = ModifyRequest(
            task_id=sample_task.id,
            current_summary="Original summary",
            modification_prompt="Update it"
        )

        # Call endpoint
        response = modify_summary(
            request=request,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify database session was passed
        call_args = mock_generator_instance.modify_and_save_summary.call_args
        assert call_args[0][0] == test_db  # First arg should be db session
        assert response.modified_summary == "Updated in DB"

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_modify_summary_llm_failure(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test error handling when LLM modification fails."""
        from backend.app.endpoint.summary_routes import modify_summary

        # Set existing summary
        sample_task.summary = "Original summary"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator to raise exception
        mock_generator_instance = MagicMock()
        error_msg = "LLM connection error"
        mock_generator_instance.modify_and_save_summary.side_effect = Exception(error_msg)
        mock_summary_generator.return_value = mock_generator_instance

        # Create request
        request = ModifyRequest(
            task_id=sample_task.id,
            current_summary="Original summary",
            modification_prompt="Update it"
        )

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            modify_summary(
                request=request,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 500
        assert "Failed to modify summary" in str(exc_info.value.detail)


class TestRegenerateSummaryEndpoint:
    """Comprehensive test cases for /api/summaries/regenerate/{task_id} endpoint."""

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_success(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test successful summary regeneration."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Set existing summary on task
        sample_task.summary = "Old summary"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        mock_generator_instance.regenerate_summary.return_value = "Regenerated summary text"
        mock_summary_generator.return_value = mock_generator_instance

        # Call endpoint
        response = regenerate_summary(
            task_id=sample_task.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Assertions
        assert response.task_id == sample_task.id
        assert response.summary == "Regenerated summary text"
        assert response.success is True
        mock_task_manager.get_task.assert_called_once_with(test_db, sample_task.id)
        mock_generator_instance.regenerate_summary.assert_called_once()

    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_task_not_found(
        self, mock_task_manager, test_db, mock_llm_client, mock_config
    ):
        """Test error when task is not found."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Mock TaskManager.get_task to return None
        mock_task_manager.get_task.return_value = None

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            regenerate_summary(
                task_id=999,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 404
        assert "Task 999 not found" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_produces_new_output(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that regeneration produces different output."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Set existing summary
        original_summary = "Original summary content"
        sample_task.summary = original_summary

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator to return different summary
        mock_generator_instance = MagicMock()
        new_summary = "Completely new regenerated summary"
        mock_generator_instance.regenerate_summary.return_value = new_summary
        mock_summary_generator.return_value = mock_generator_instance

        # Call endpoint
        response = regenerate_summary(
            task_id=sample_task.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify new summary is different
        assert response.summary == new_summary
        assert response.summary != original_summary

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_database_persistence(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that regenerated summary persists to database."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Set existing summary
        sample_task.summary = "Old summary"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        regenerated_summary = "New persistent summary"
        mock_generator_instance.regenerate_summary.return_value = regenerated_summary
        mock_summary_generator.return_value = mock_generator_instance

        # Call endpoint
        response = regenerate_summary(
            task_id=sample_task.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify database session was passed
        call_args = mock_generator_instance.regenerate_summary.call_args
        assert call_args[0][0] == test_db  # First arg should be db session
        assert response.summary == regenerated_summary

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_llm_failure(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test error handling when regeneration fails."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator to raise exception
        mock_generator_instance = MagicMock()
        mock_generator_instance.regenerate_summary.side_effect = Exception("Regeneration failed")
        mock_summary_generator.return_value = mock_generator_instance

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            regenerate_summary(
                task_id=sample_task.id,
                db=test_db,
                llm_client=mock_llm_client,
                config=mock_config
            )

        # Assertions
        assert exc_info.value.status_code == 500
        assert "Failed to regenerate summary" in str(exc_info.value.detail)

    @patch('backend.app.endpoint.summary_routes.SummaryGenerator')
    @patch('backend.app.endpoint.summary_routes.TaskManager')
    def test_regenerate_summary_replaces_existing(
        self, mock_task_manager, mock_summary_generator,
        test_db, sample_task, mock_llm_client, mock_config
    ):
        """Test that regeneration replaces existing summary."""
        from backend.app.endpoint.summary_routes import regenerate_summary

        # Set existing summary
        sample_task.summary = "Existing summary to be replaced"

        # Mock TaskManager.get_task to return sample task
        mock_task_manager.get_task.return_value = sample_task

        # Mock SummaryGenerator instance
        mock_generator_instance = MagicMock()
        mock_generator_instance.regenerate_summary.return_value = "Brand new summary"
        mock_summary_generator.return_value = mock_generator_instance

        # Call endpoint
        response = regenerate_summary(
            task_id=sample_task.id,
            db=test_db,
            llm_client=mock_llm_client,
            config=mock_config
        )

        # Verify regenerate_summary was called (not generate_and_save_summary)
        mock_generator_instance.regenerate_summary.assert_called_once()
        assert response.summary == "Brand new summary"


class TestSummaryRouteSchemas:
    """Test cases for summary route schemas."""

    def test_summary_response_schema(self):
        """Test summary response schema."""
        from backend.app.schemas.summary_schema import SummaryResponse

        response = SummaryResponse(
            task_id=1,
            summary="Test summary",
            success=True
        )

        assert response.task_id == 1
        assert response.summary == "Test summary"
        assert response.success is True

    def test_modify_response_schema(self):
        """Test modify response schema."""
        from backend.app.schemas.summary_schema import ModifyResponse

        response = ModifyResponse(
            task_id=1,
            original_summary="Original",
            modified_summary="Modified",
            success=True
        )

        assert response.task_id == 1
        assert response.original_summary == "Original"
        assert response.modified_summary == "Modified"

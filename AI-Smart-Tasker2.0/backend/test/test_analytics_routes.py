"""Unit tests for analytics API routes."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from backend.app.endpoint.analytics_routes import (
    get_analytics,
    get_completion_stats,
    get_deadline_adherence,
    get_productivity_trends
)


class TestGetAnalyticsRoute:
    """Test cases for get_analytics endpoint."""

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_analytics_success(self, mock_processor, test_db, sample_user):
        """Test successful analytics retrieval."""
        mock_response = MagicMock()
        mock_response.user_id = sample_user.id
        mock_processor.get_analytics.return_value = mock_response

        response = get_analytics(user_id=sample_user.id, trend_days=30, db=test_db)

        assert response.user_id == sample_user.id
        mock_processor.get_analytics.assert_called_once_with(test_db, sample_user.id, 30)

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_analytics_custom_trend_days(self, mock_processor, test_db, sample_user):
        """Test analytics with custom trend days."""
        mock_response = MagicMock()
        mock_response.user_id = sample_user.id
        mock_processor.get_analytics.return_value = mock_response

        response = get_analytics(user_id=sample_user.id, trend_days=7, db=test_db)

        call_args = mock_processor.get_analytics.call_args[0]
        assert call_args[2] == 7  # trend_days parameter


class TestGetCompletionStatsRoute:
    """Test cases for get_completion_stats endpoint."""

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_completion_stats_success(self, mock_processor, test_db, sample_user):
        """Test successful completion stats retrieval."""
        mock_stats = MagicMock()
        mock_stats.total_tasks = 10
        mock_stats.completed_tasks = 7
        mock_processor.get_completion_stats.return_value = mock_stats

        response = get_completion_stats(user_id=sample_user.id, db=test_db)

        assert response is not None
        mock_processor.get_completion_stats.assert_called_once()


class TestGetDeadlineAdherenceRoute:
    """Test cases for get_deadline_adherence endpoint."""

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_deadline_adherence_success(self, mock_processor, test_db, sample_user):
        """Test successful deadline adherence retrieval."""
        mock_adherence = MagicMock()
        mock_adherence.total_completed = 10
        mock_adherence.completed_on_time = 8
        mock_processor.get_deadline_adherence.return_value = mock_adherence

        response = get_deadline_adherence(user_id=sample_user.id, db=test_db)

        assert response is not None
        mock_processor.get_deadline_adherence.assert_called_once()


class TestGetProductivityTrendsRoute:
    """Test cases for get_productivity_trends endpoint."""

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_productivity_trends_success(self, mock_processor, test_db, sample_user):
        """Test successful productivity trends retrieval."""
        mock_trends = [MagicMock(), MagicMock()]
        mock_processor.get_productivity_trends.return_value = mock_trends

        response = get_productivity_trends(user_id=sample_user.id, days=30, db=test_db)

        assert isinstance(response, list)
        mock_processor.get_productivity_trends.assert_called_once()

    @patch('backend.app.endpoint.analytics_routes.AnalyticsProcessor')
    def test_get_productivity_trends_custom_days(self, mock_processor, test_db, sample_user):
        """Test productivity trends with custom days parameter."""
        mock_processor.get_productivity_trends.return_value = []

        response = get_productivity_trends(user_id=sample_user.id, days=7, db=test_db)

        call_args = mock_processor.get_productivity_trends.call_args[0]
        assert call_args[2] == 7  # days parameter

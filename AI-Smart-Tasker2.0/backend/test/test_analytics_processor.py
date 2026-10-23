"""Unit tests for analytics processor."""
import pytest
from datetime import datetime, timedelta

from backend.app.utils.analytics_processor import AnalyticsProcessor
from backend.app.models.task import Task
from backend.app.models.analytics import Analytics


class TestGetCompletionStats:
    """Test cases for get_completion_stats method."""

    def test_completion_stats_no_tasks(self, test_db, sample_user):
        """Test completion stats with no tasks."""
        # Delete existing tasks
        test_db.query(Task).filter(Task.user_id == sample_user.id).delete()
        test_db.commit()

        stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)

        assert stats.total_tasks == 0
        assert stats.completed_tasks == 0
        assert stats.pending_tasks == 0
        assert stats.overdue_tasks == 0
        assert stats.completion_rate == 0.0

    def test_completion_stats_with_mixed_tasks(self, test_db, sample_user):
        """Test completion stats with various task types."""
        # Create tasks with different statuses
        completed_task = Task(
            title="Completed",
            description="Done",
            deadline=datetime.utcnow() + timedelta(days=1),
            completed=True,
            user_id=sample_user.id
        )
        pending_task = Task(
            title="Pending",
            description="Not done",
            deadline=datetime.utcnow() + timedelta(days=2),
            completed=False,
            user_id=sample_user.id
        )
        overdue_task = Task(
            title="Overdue",
            description="Late",
            deadline=datetime.utcnow() - timedelta(days=1),
            completed=False,
            user_id=sample_user.id
        )
        test_db.add_all([completed_task, pending_task, overdue_task])
        test_db.commit()

        stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)

        assert stats.total_tasks >= 3
        assert stats.completed_tasks >= 1
        assert stats.pending_tasks >= 2
        assert stats.overdue_tasks >= 1
        assert 0 <= stats.completion_rate <= 100

    def test_completion_stats_on_time_rate(self, test_db, sample_user):
        """Test on-time completion rate calculation."""
        task = Task(
            title="On-time task",
            description="Will complete on time",
            deadline=datetime.utcnow() + timedelta(hours=5),
            user_id=sample_user.id
        )
        test_db.add(task)
        test_db.commit()

        # Mark as completed
        task.completed = True
        test_db.commit()

        # Create analytics event
        event = Analytics(
            user_id=sample_user.id,
            task_id=task.id,
            event_type="completed",
            task_title=task.title,
            deadline=task.deadline,
            was_completed_on_time=True,
            completion_delay_hours=-5.0
        )
        test_db.add(event)
        test_db.commit()

        stats = AnalyticsProcessor.get_completion_stats(test_db, sample_user.id)

        assert stats.on_time_completion_rate > 0


class TestGetDeadlineAdherence:
    """Test cases for get_deadline_adherence method."""

    def test_deadline_adherence_no_completed_tasks(self, test_db, sample_user):
        """Test deadline adherence with no completed tasks."""
        # Delete any completed analytics events
        test_db.query(Analytics).filter(
            Analytics.user_id == sample_user.id,
            Analytics.event_type == "completed"
        ).delete()
        test_db.commit()

        adherence = AnalyticsProcessor.get_deadline_adherence(test_db, sample_user.id)

        assert adherence.total_completed == 0
        assert adherence.completed_on_time == 0
        assert adherence.completed_late == 0
        assert adherence.average_delay_hours == 0.0
        assert adherence.on_time_percentage == 0.0

    def test_deadline_adherence_all_on_time(self, test_db, sample_user):
        """Test deadline adherence with all on-time completions."""
        task = Task(
            title="Early task",
            description="Completed early",
            deadline=datetime.utcnow() + timedelta(hours=10),
            completed=True,
            user_id=sample_user.id
        )
        test_db.add(task)
        test_db.commit()

        event = Analytics(
            user_id=sample_user.id,
            task_id=task.id,
            event_type="completed",
            task_title=task.title,
            deadline=task.deadline,
            was_completed_on_time=True,
            completion_delay_hours=-3.0
        )
        test_db.add(event)
        test_db.commit()

        adherence = AnalyticsProcessor.get_deadline_adherence(test_db, sample_user.id)

        assert adherence.total_completed >= 1
        assert adherence.completed_on_time >= 1
        assert adherence.on_time_percentage > 0

    def test_deadline_adherence_with_late_tasks(self, test_db, sample_user):
        """Test deadline adherence with late completions."""
        late_task = Task(
            title="Late task",
            description="Completed late",
            deadline=datetime.utcnow() - timedelta(hours=10),
            completed=True,
            user_id=sample_user.id
        )
        test_db.add(late_task)
        test_db.commit()

        event = Analytics(
            user_id=sample_user.id,
            task_id=late_task.id,
            event_type="completed",
            task_title=late_task.title,
            deadline=late_task.deadline,
            was_completed_on_time=False,
            completion_delay_hours=5.5
        )
        test_db.add(event)
        test_db.commit()

        adherence = AnalyticsProcessor.get_deadline_adherence(test_db, sample_user.id)

        assert adherence.completed_late >= 1
        assert adherence.average_delay_hours > 0


class TestGetProductivityTrends:
    """Test cases for get_productivity_trends method."""

    def test_productivity_trends_no_events(self, test_db, sample_user):
        """Test productivity trends with no events."""
        # Clean all analytics for this user
        test_db.query(Analytics).filter(Analytics.user_id == sample_user.id).delete()
        test_db.commit()

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=7)

        assert isinstance(trends, list)

    def test_productivity_trends_with_events(self, test_db, sample_user):
        """Test productivity trends with various events."""
        # Create events over multiple days
        for i in range(3):
            event_date = datetime.utcnow() - timedelta(days=i)
            event = Analytics(
                user_id=sample_user.id,
                task_id=100 + i,
                event_type="created",
                event_timestamp=event_date,
                task_title=f"Task {i}",
                deadline=event_date + timedelta(days=1)
            )
            test_db.add(event)
        test_db.commit()

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=7)

        assert isinstance(trends, list)
        assert len(trends) > 0

    def test_productivity_trends_groups_by_date(self, test_db, sample_user):
        """Test that trends are grouped by date."""
        today = datetime.utcnow()

        # Create multiple events on same day
        for i in range(3):
            event = Analytics(
                user_id=sample_user.id,
                task_id=200 + i,
                event_type="created",
                event_timestamp=today,
                task_title=f"Same day task {i}",
                deadline=today + timedelta(days=1)
            )
            test_db.add(event)
        test_db.commit()

        trends = AnalyticsProcessor.get_productivity_trends(test_db, sample_user.id, days=1)

        # Events should be grouped by date
        for trend in trends:
            assert hasattr(trend, 'date')
            assert hasattr(trend, 'tasks_created')


class TestGetRecentEvents:
    """Test cases for get_recent_events method."""

    def test_get_recent_events_default_limit(self, test_db, sample_user):
        """Test getting recent events with default limit."""
        events = AnalyticsProcessor.get_recent_events(test_db, sample_user.id)

        assert isinstance(events, list)
        assert len(events) <= 10  # Default limit

    def test_get_recent_events_custom_limit(self, test_db, sample_user):
        """Test getting recent events with custom limit."""
        # Create multiple events
        for i in range(15):
            event = Analytics(
                user_id=sample_user.id,
                task_id=300 + i,
                event_type="created",
                task_title=f"Event task {i}",
                deadline=datetime.utcnow() + timedelta(days=1)
            )
            test_db.add(event)
        test_db.commit()

        events = AnalyticsProcessor.get_recent_events(test_db, sample_user.id, limit=5)

        assert len(events) <= 5

    def test_get_recent_events_ordered_by_timestamp(self, test_db, sample_user):
        """Test that recent events are ordered by timestamp (newest first)."""
        # Create events with different timestamps
        timestamps = [
            datetime.utcnow() - timedelta(hours=3),
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow()
        ]

        for i, ts in enumerate(timestamps):
            event = Analytics(
                user_id=sample_user.id,
                task_id=400 + i,
                event_type="created",
                event_timestamp=ts,
                task_title=f"Ordered task {i}",
                deadline=ts + timedelta(days=1)
            )
            test_db.add(event)
        test_db.commit()

        events = AnalyticsProcessor.get_recent_events(test_db, sample_user.id, limit=3)

        # Verify ordering (newest first)
        if len(events) >= 2:
            assert events[0].event_timestamp >= events[1].event_timestamp


class TestLogMissedDeadline:
    """Test cases for log_missed_deadline method."""

    def test_log_missed_deadline_creates_event(self, test_db, overdue_task):
        """Test logging a missed deadline creates analytics event."""
        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        event = test_db.query(Analytics).filter(
            Analytics.task_id == overdue_task.id,
            Analytics.event_type == "missed_deadline"
        ).first()

        assert event is not None
        assert event.task_title == overdue_task.title
        assert event.deadline == overdue_task.deadline

    def test_log_missed_deadline_not_duplicate(self, test_db, overdue_task):
        """Test that missed deadline is not logged twice."""
        # Log once
        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        # Try to log again
        AnalyticsProcessor.log_missed_deadline(test_db, overdue_task)

        # Count events
        event_count = test_db.query(Analytics).filter(
            Analytics.task_id == overdue_task.id,
            Analytics.event_type == "missed_deadline"
        ).count()

        assert event_count == 1  # Should only have one event


class TestGetAnalytics:
    """Test cases for get_analytics comprehensive method."""

    def test_get_analytics_returns_all_data(self, test_db, sample_user):
        """Test that get_analytics returns complete analytics response."""
        analytics = AnalyticsProcessor.get_analytics(test_db, sample_user.id, trend_days=7)

        assert analytics is not None
        assert analytics.user_id == sample_user.id
        assert hasattr(analytics, 'completion_stats')
        assert hasattr(analytics, 'deadline_adherence')
        assert hasattr(analytics, 'productivity_trends')
        assert hasattr(analytics, 'recent_events')

    def test_get_analytics_with_custom_trend_days(self, test_db, sample_user):
        """Test get_analytics with custom trend period."""
        analytics = AnalyticsProcessor.get_analytics(test_db, sample_user.id, trend_days=30)

        assert analytics is not None
        assert isinstance(analytics.productivity_trends, list)

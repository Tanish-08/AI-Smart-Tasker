"""Analytics data processing and aggregation."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.app.models.task import Task
from backend.app.models.analytics import Analytics
from backend.app.schemas.analytics_schema import (
    TaskCompletionStats,
    ProductivityTrend,
    DeadlineAdherence,
    AnalyticsResponse,
    AnalyticsEvent,
)

logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    """Processor for task analytics and metrics."""

    @staticmethod
    def get_completion_stats(db: Session, user_id: int) -> TaskCompletionStats:
        """
        Get task completion statistics for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Task completion statistics
        """
        try:
            # Get total tasks
            total_tasks = db.query(Task).filter(Task.user_id == user_id).count()

            # Get completed tasks
            completed_tasks = (
                db.query(Task)
                .filter(and_(Task.user_id == user_id, Task.completed == True))
                .count()
            )

            # Get pending tasks
            pending_tasks = (
                db.query(Task)
                .filter(and_(Task.user_id == user_id, Task.completed == False))
                .count()
            )

            # Get overdue tasks
            overdue_tasks = (
                db.query(Task)
                .filter(
                    and_(
                        Task.user_id == user_id,
                        Task.completed == False,
                        Task.deadline < datetime.utcnow(),
                    )
                )
                .count()
            )

            # Calculate rates
            completion_rate = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            )

            # Get on-time completion rate
            on_time_completed = (
                db.query(Analytics)
                .filter(
                    and_(
                        Analytics.user_id == user_id,
                        Analytics.event_type == "completed",
                        Analytics.was_completed_on_time == True,
                    )
                )
                .count()
            )

            on_time_completion_rate = (
                (on_time_completed / completed_tasks * 100)
                if completed_tasks > 0
                else 0.0
            )

            return TaskCompletionStats(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                pending_tasks=pending_tasks,
                overdue_tasks=overdue_tasks,
                completion_rate=round(completion_rate, 2),
                on_time_completion_rate=round(on_time_completion_rate, 2),
            )

        except Exception as e:
            logger.error(f"Failed to get completion stats for user {user_id}: {e}")
            raise

    @staticmethod
    def get_deadline_adherence(db: Session, user_id: int) -> DeadlineAdherence:
        """
        Get deadline adherence metrics for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Deadline adherence metrics
        """
        try:
            # Get all completed task events
            completed_events = (
                db.query(Analytics)
                .filter(
                    and_(
                        Analytics.user_id == user_id,
                        Analytics.event_type == "completed",
                    )
                )
                .all()
            )

            total_completed = len(completed_events)

            if total_completed == 0:
                return DeadlineAdherence(
                    total_completed=0,
                    completed_on_time=0,
                    completed_late=0,
                    average_delay_hours=0.0,
                    on_time_percentage=0.0,
                )

            # Count on-time and late completions
            completed_on_time = sum(
                1 for event in completed_events if event.was_completed_on_time
            )
            completed_late = total_completed - completed_on_time

            # Calculate average delay for late tasks
            late_delays = [
                event.completion_delay_hours
                for event in completed_events
                if event.completion_delay_hours and event.completion_delay_hours > 0
            ]
            average_delay_hours = (
                sum(late_delays) / len(late_delays) if late_delays else 0.0
            )

            # Calculate on-time percentage
            on_time_percentage = completed_on_time / total_completed * 100

            return DeadlineAdherence(
                total_completed=total_completed,
                completed_on_time=completed_on_time,
                completed_late=completed_late,
                average_delay_hours=round(average_delay_hours, 2),
                on_time_percentage=round(on_time_percentage, 2),
            )

        except Exception as e:
            logger.error(f"Failed to get deadline adherence for user {user_id}: {e}")
            raise

    @staticmethod
    def get_productivity_trends(
        db: Session, user_id: int, days: int = 30
    ) -> List[ProductivityTrend]:
        """
        Get productivity trends over time.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of productivity trend data points
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get analytics events in date range
            events = (
                db.query(Analytics)
                .filter(
                    and_(
                        Analytics.user_id == user_id,
                        Analytics.event_timestamp >= start_date,
                        Analytics.event_timestamp <= end_date,
                    )
                )
                .all()
            )

            # Group events by date
            trends_dict: Dict[str, Dict[str, int]] = {}

            for event in events:
                date_str = event.event_timestamp.strftime("%Y-%m-%d")

                if date_str not in trends_dict:
                    trends_dict[date_str] = {
                        "tasks_created": 0,
                        "tasks_completed": 0,
                        "tasks_overdue": 0,
                    }

                if event.event_type == "created":
                    trends_dict[date_str]["tasks_created"] += 1
                elif event.event_type == "completed":
                    trends_dict[date_str]["tasks_completed"] += 1
                elif event.event_type == "missed_deadline":
                    trends_dict[date_str]["tasks_overdue"] += 1

            # Convert to list of ProductivityTrend objects
            trends = [
                ProductivityTrend(
                    date=date_str,
                    tasks_created=data["tasks_created"],
                    tasks_completed=data["tasks_completed"],
                    tasks_overdue=data["tasks_overdue"],
                )
                for date_str, data in sorted(trends_dict.items())
            ]

            return trends

        except Exception as e:
            logger.error(f"Failed to get productivity trends for user {user_id}: {e}")
            raise

    @staticmethod
    def get_recent_events(
        db: Session, user_id: int, limit: int = 10
    ) -> List[AnalyticsEvent]:
        """
        Get recent analytics events for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of events to return

        Returns:
            List of recent analytics events
        """
        try:
            events = (
                db.query(Analytics)
                .filter(Analytics.user_id == user_id)
                .order_by(Analytics.event_timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                AnalyticsEvent(
                    id=event.id,
                    user_id=event.user_id,
                    task_id=event.task_id,
                    event_type=event.event_type,
                    event_timestamp=event.event_timestamp,
                    task_title=event.task_title,
                    deadline=event.deadline,
                    was_completed_on_time=event.was_completed_on_time,
                    completion_delay_hours=event.completion_delay_hours,
                )
                for event in events
            ]

        except Exception as e:
            logger.error(f"Failed to get recent events for user {user_id}: {e}")
            raise

    @staticmethod
    def get_analytics(
        db: Session, user_id: int, trend_days: int = 30
    ) -> AnalyticsResponse:
        """
        Get comprehensive analytics for a user.

        Args:
            db: Database session
            user_id: User ID
            trend_days: Number of days for productivity trends

        Returns:
            Comprehensive analytics response
        """
        try:
            completion_stats = AnalyticsProcessor.get_completion_stats(db, user_id)
            deadline_adherence = AnalyticsProcessor.get_deadline_adherence(db, user_id)
            productivity_trends = AnalyticsProcessor.get_productivity_trends(
                db, user_id, trend_days
            )
            recent_events = AnalyticsProcessor.get_recent_events(db, user_id, limit=10)

            return AnalyticsResponse(
                user_id=user_id,
                completion_stats=completion_stats,
                deadline_adherence=deadline_adherence,
                productivity_trends=productivity_trends,
                recent_events=recent_events,
            )

        except Exception as e:
            logger.error(f"Failed to get analytics for user {user_id}: {e}")
            raise

    @staticmethod
    def log_missed_deadline(db: Session, task: Task) -> None:
        """
        Log a missed deadline event.

        Args:
            db: Database session
            task: Task with missed deadline
        """
        try:
            # Check if event already logged
            existing_event = (
                db.query(Analytics)
                .filter(
                    and_(
                        Analytics.task_id == task.id,
                        Analytics.event_type == "missed_deadline",
                    )
                )
                .first()
            )

            if existing_event:
                logger.debug(f"Missed deadline already logged for task {task.id}")
                return

            # Log new event
            event = Analytics(
                user_id=task.user_id,
                task_id=task.id,
                event_type="missed_deadline",
                event_timestamp=datetime.utcnow(),
                task_title=task.title,
                deadline=task.deadline,
            )
            db.add(event)
            db.commit()

            logger.info(f"Logged missed deadline for task {task.id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log missed deadline for task {task.id}: {e}")
            raise

"""Pydantic schemas for analytics operations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    """Schema for a single analytics event."""

    id: int = Field(..., description="Event ID")
    user_id: int = Field(..., description="User ID")
    task_id: int = Field(..., description="Task ID")
    event_type: str = Field(..., description="Event type")
    event_timestamp: datetime = Field(..., description="Event timestamp")
    task_title: str = Field(..., description="Task title")
    deadline: datetime = Field(..., description="Task deadline")
    was_completed_on_time: Optional[bool] = Field(None, description="Completed on time")
    completion_delay_hours: Optional[float] = Field(None, description="Delay in hours")


class TaskCompletionStats(BaseModel):
    """Schema for task completion statistics."""

    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    completion_rate: float = Field(..., description="Completion rate percentage")
    on_time_completion_rate: float = Field(
        ..., description="On-time completion rate percentage"
    )


class ProductivityTrend(BaseModel):
    """Schema for productivity trend data point."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    tasks_created: int = Field(..., description="Tasks created on this date")
    tasks_completed: int = Field(..., description="Tasks completed on this date")
    tasks_overdue: int = Field(
        ..., description="Tasks that became overdue on this date"
    )


class DeadlineAdherence(BaseModel):
    """Schema for deadline adherence metrics."""

    total_completed: int = Field(..., description="Total completed tasks")
    completed_on_time: int = Field(..., description="Tasks completed on time")
    completed_late: int = Field(..., description="Tasks completed late")
    average_delay_hours: float = Field(
        ..., description="Average delay in hours for late tasks"
    )
    on_time_percentage: float = Field(..., description="On-time completion percentage")


class AnalyticsResponse(BaseModel):
    """Schema for comprehensive analytics response."""

    user_id: int = Field(..., description="User ID")
    completion_stats: TaskCompletionStats = Field(
        ..., description="Task completion statistics"
    )
    deadline_adherence: DeadlineAdherence = Field(
        ..., description="Deadline adherence metrics"
    )
    productivity_trends: list[ProductivityTrend] = Field(
        ..., description="Productivity trends over time"
    )
    recent_events: list[AnalyticsEvent] = Field(
        ..., description="Recent analytics events"
    )

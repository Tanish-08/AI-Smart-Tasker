"""Analytics database model."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from backend.app.utils.database import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class Analytics(Base):
    """Analytics model for tracking task completion metrics."""

    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id = Column(
        Integer, nullable=False, index=True
    )  # Reference to task (soft reference)

    # Event tracking
    event_type = Column(
        String(50), nullable=False, index=True
    )  # "created", "completed", "missed_deadline", "overdue"
    event_timestamp = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Task metadata at time of event
    task_title = Column(String(255), nullable=False)
    deadline = Column(DateTime, nullable=False)
    was_completed_on_time = Column(
        Boolean, nullable=True
    )  # True if completed before deadline
    completion_delay_hours = Column(
        Float, nullable=True
    )  # Hours late (positive) or early (negative)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        """String representation of Analytics."""
        return (
            f"<Analytics(id={self.id}, user_id={self.user_id}, "
            f"event_type='{self.event_type}', event_timestamp={self.event_timestamp})>"
        )

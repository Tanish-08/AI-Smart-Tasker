"""Task database model."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.utils.database import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class Task(Base):
    """Task model for storing task information."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=False, index=True)
    completed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Optional fields for AI features
    summary = Column(Text, nullable=True)
    insult_message = Column(Text, nullable=True)

    category = Column(String, default="General")
    priority = Column(String, default="Medium")

    # Relationships
    user = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        """String representation of Task."""
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"deadline={self.deadline}, completed={self.completed})>"
        )

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue and not completed."""
        return not self.completed and datetime.utcnow() > self.deadline

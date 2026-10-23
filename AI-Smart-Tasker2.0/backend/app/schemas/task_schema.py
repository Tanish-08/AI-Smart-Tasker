"""Pydantic schemas for Task operations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """Base schema for task with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    deadline: datetime = Field(..., description="Task deadline")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    category: Optional[str] = "General"
    priority: Optional[str] = "Medium"

    user_id: int = Field(..., gt=0, description="User ID who owns the task")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Task title"
    )
    description: Optional[str] = Field(None, description="Task description")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    completed: Optional[bool] = Field(None, description="Task completion status")
    summary: Optional[str] = Field(None, description="AI-generated task summary")


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: int = Field(..., description="Task ID")
    completed: bool = Field(..., description="Task completion status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")
    user_id: int = Field(..., description="User ID who owns the task")
    summary: Optional[str] = Field(None, description="AI-generated task summary")
    insult_message: Optional[str] = Field(
        None, description="AI-generated insult for missed deadline"
    )

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Schema for list of tasks response."""

    tasks: list[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")

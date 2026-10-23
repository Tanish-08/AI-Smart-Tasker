"""Pydantic schemas for AI summary operations."""
from typing import Optional

from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    """Schema for requesting AI summary generation."""

    task_id: int = Field(..., gt=0, description="Task ID to generate summary for")
    task_title: str = Field(..., min_length=1, description="Task title")
    task_description: Optional[str] = Field(None, description="Task description")


class SummaryResponse(BaseModel):
    """Schema for AI summary response."""

    task_id: int = Field(..., description="Task ID")
    summary: str = Field(..., description="AI-generated summary")
    success: bool = Field(
        default=True, description="Whether summary generation was successful"
    )


class ModifyRequest(BaseModel):
    """Schema for modifying AI summary with natural language prompt."""

    task_id: int = Field(..., gt=0, description="Task ID")
    current_summary: str = Field(..., min_length=1, description="Current task summary")
    modification_prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language prompt for summary modification",
    )


class ModifyResponse(BaseModel):
    """Schema for modified summary response."""

    task_id: int = Field(..., description="Task ID")
    original_summary: str = Field(..., description="Original summary")
    modified_summary: str = Field(..., description="Modified summary")
    success: bool = Field(
        default=True, description="Whether modification was successful"
    )

"""API endpoints for AI summary generation and modification."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.utils.database import get_db
from backend.app.utils.task_manager import TaskManager
from backend.app.utils.summary_generator import SummaryGenerator
from backend.app.utils.llm_client import LLMClient
from backend.app.schemas.summary_schema import (
    SummaryRequest,
    SummaryResponse,
    ModifyRequest,
    ModifyResponse,
)
from backend.app.dependencies import get_llm_client, get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.post(
    "/generate",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI summary for a task",
)
def generate_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    config=Depends(get_config),
) -> SummaryResponse:
    """
    Generate an AI-powered summary for a task.

    Args:
        request: Summary generation request
        db: Database session
        llm_client: LLM client
        config: Application configuration

    Returns:
        Generated summary

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Get the task
        task = TaskManager.get_task(db, request.task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {request.task_id} not found",
            )

        # Generate summary
        generator = SummaryGenerator(llm_client, config)
        summary = generator.generate_and_save_summary(db, task)

        return SummaryResponse(task_id=task.id, summary=summary, success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.post(
    "/modify",
    response_model=ModifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify task summary using natural language",
)
def modify_summary(
    request: ModifyRequest,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    config=Depends(get_config),
) -> ModifyResponse:
    """
    Modify an existing task summary using a natural language prompt.

    Args:
        request: Summary modification request
        db: Database session
        llm_client: LLM client
        config: Application configuration

    Returns:
        Modified summary

    Raises:
        HTTPException: If modification fails
    """
    try:
        # Get the task
        task = TaskManager.get_task(db, request.task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {request.task_id} not found",
            )

        if not task.summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task {request.task_id} does not have a summary to modify",
            )

        # Store original summary
        original_summary = task.summary

        # Modify summary
        generator = SummaryGenerator(llm_client, config)
        modified_summary = generator.modify_and_save_summary(
            db, task, request.modification_prompt
        )

        return ModifyResponse(
            task_id=task.id,
            original_summary=original_summary,
            modified_summary=modified_summary,
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to modify summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify summary: {str(e)}",
        )


@router.post(
    "/regenerate/{task_id}",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate task summary",
)
def regenerate_summary(
    task_id: int,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    config=Depends(get_config),
) -> SummaryResponse:
    """
    Regenerate summary for a task (replaces existing).

    Args:
        task_id: Task ID
        db: Database session
        llm_client: LLM client
        config: Application configuration

    Returns:
        New generated summary

    Raises:
        HTTPException: If regeneration fails
    """
    try:
        # Get the task
        task = TaskManager.get_task(db, task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        # Regenerate summary
        generator = SummaryGenerator(llm_client, config)
        summary = generator.regenerate_summary(db, task)

        return SummaryResponse(task_id=task.id, summary=summary, success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate summary: {str(e)}",
        )

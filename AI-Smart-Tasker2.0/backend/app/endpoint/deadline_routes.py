"""API endpoints for deadline monitoring and insult generation."""
import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.utils.database import get_db
from backend.app.utils.task_manager import TaskManager
from backend.app.utils.ai_insult_generator import AIInsultGenerator
from backend.app.utils.analytics_processor import AnalyticsProcessor
from backend.app.utils.llm_client import LLMClient
from backend.app.schemas.task_schema import TaskResponse
from backend.app.dependencies import get_llm_client, get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deadlines", tags=["deadlines"])


@router.get(
    "/check",
    response_model=Dict[str, List[TaskResponse]],
    status_code=status.HTTP_200_OK,
    summary="Check for missed deadlines and generate insults",
)
def check_deadlines(
    user_id: int = Query(..., description="User ID to check deadlines for"),
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    config=Depends(get_config),
) -> Dict[str, List[TaskResponse]]:
    """
    Check for tasks with missed deadlines and generate AI insults.

    This endpoint:
    1. Finds all overdue tasks for the user
    2. Generates funny developer-themed insults for tasks without insults
    3. Logs missed deadline events to analytics
    4. Returns the overdue tasks with their insults

    Args:
        user_id: User ID to check deadlines for
        db: Database session
        llm_client: LLM client
        config: Application configuration

    Returns:
        Dictionary with overdue tasks

    Raises:
        HTTPException: If check fails
    """
    try:
        # Get overdue tasks
        overdue_tasks = TaskManager.get_overdue_tasks(db, user_id)

        if not overdue_tasks:
            return {"overdue_tasks": []}

        # Initialize insult generator
        insult_generator = AIInsultGenerator(llm_client, config)

        # Process each overdue task
        for task in overdue_tasks:
            # Log missed deadline event (only once)
            AnalyticsProcessor.log_missed_deadline(db, task)

            # Generate insult if not already present
            if not task.insult_message:
                try:
                    insult_generator.generate_and_save_insult(db, task)
                except Exception as e:
                    logger.error(f"Failed to generate insult for task {task.id}: {e}")
                    # Continue with other tasks even if one fails

        # Convert to response models
        task_responses = [TaskResponse.model_validate(task) for task in overdue_tasks]

        return {"overdue_tasks": task_responses}

    except Exception as e:
        logger.error(f"Failed to check deadlines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check deadlines: {str(e)}",
        )


@router.post(
    "/regenerate-insult/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate insult for a task",
)
def regenerate_insult(
    task_id: int,
    user_id: int = Query(..., description="User ID for ownership verification"),
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    config=Depends(get_config),
) -> TaskResponse:
    """
    Regenerate the insult message for a task with a missed deadline.

    Args:
        task_id: Task ID
        user_id: User ID for ownership verification
        db: Database session
        llm_client: LLM client
        config: Application configuration

    Returns:
        Updated task with new insult

    Raises:
        HTTPException: If task not found or not overdue
    """
    try:
        # Get the task
        task = TaskManager.get_task(db, task_id, user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or access denied",
            )

        if not task.is_overdue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task {task_id} is not overdue",
            )

        # Clear existing insult and regenerate
        task.insult_message = None
        db.commit()

        insult_generator = AIInsultGenerator(llm_client, config)
        insult_generator.generate_and_save_insult(db, task)

        db.refresh(task)
        return TaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate insult: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate insult: {str(e)}",
        )


@router.get(
    "/overdue",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all overdue tasks for a user",
)
def get_overdue_tasks(
    user_id: int = Query(..., description="User ID"), db: Session = Depends(get_db)
) -> List[TaskResponse]:
    """
    Get all overdue tasks for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of overdue tasks

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        overdue_tasks = TaskManager.get_overdue_tasks(db, user_id)
        return [TaskResponse.model_validate(task) for task in overdue_tasks]

    except Exception as e:
        logger.error(f"Failed to get overdue tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overdue tasks: {str(e)}",
        )

"""API endpoints for task CRUD operations."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.ai_helper import auto_categorize_task
from backend.app.utils.database import get_db
from backend.app.utils.task_manager import TaskManager
from backend.app.schemas.task_schema import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    """
    Create a new task.

    Args:
        task_data: Task creation data
        db: Database session

    Returns:
        Created task

    Raises:
        HTTPException: If task creation fails
    """
    try:
        # --- AI logic: auto-categorize the task ---
        ai_result = auto_categorize_task(task_data.description or task_data.title)
        task_data.category = ai_result.get("category", "General")
        task_data.priority = ai_result.get("priority", "Medium")
        # ------------------------------------------

        task = TaskManager.create_task(db, task_data)
        return TaskResponse.model_validate(task)

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
def get_task(
    task_id: int,
    user_id: int = Query(..., description="User ID for ownership verification"),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    Get a task by ID.

    Args:
        task_id: Task ID
        user_id: User ID for ownership verification
        db: Database session

    Returns:
        Task details

    Raises:
        HTTPException: If task not found or access denied
    """
    try:
        task = TaskManager.get_task(db, task_id, user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or access denied",
            )

        return TaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}",
        )


@router.get("", response_model=TaskListResponse, summary="Get tasks with filters")
def get_tasks(
    user_id: int = Query(..., description="User ID to filter tasks"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    overdue_only: bool = Query(False, description="Show only overdue tasks"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """
    Get tasks with optional filters.

    Args:
        user_id: User ID to filter tasks
        completed: Optional filter by completion status
        overdue_only: Show only overdue tasks
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of tasks

    Raises:
        HTTPException: If query fails
    """
    try:
        tasks = TaskManager.get_tasks(
            db,
            user_id=user_id,
            completed=completed,
            overdue_only=overdue_only,
            skip=skip,
            limit=limit,
        )

        task_responses = [TaskResponse.model_validate(task) for task in tasks]

        return TaskListResponse(tasks=task_responses, total=len(task_responses))

    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}",
        )


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: int = Query(..., description="User ID for ownership verification"),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    Update a task.

    Args:
        task_id: Task ID
        task_data: Task update data
        user_id: User ID for ownership verification
        db: Database session

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found or update fails
    """
    try:
        task = TaskManager.update_task(db, task_id, task_data, user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or access denied",
            )

        return TaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task"
)
def delete_task(
    task_id: int,
    user_id: int = Query(..., description="User ID for ownership verification"),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a task.

    Args:
        task_id: Task ID
        user_id: User ID for ownership verification
        db: Database session

    Raises:
        HTTPException: If task not found or deletion fails
    """
    try:
        deleted = TaskManager.delete_task(db, task_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or access denied",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )

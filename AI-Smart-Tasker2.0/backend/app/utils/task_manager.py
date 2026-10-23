"""Core task management logic and CRUD operations."""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.app.models.task import Task
from backend.app.models.analytics import Analytics
from backend.app.schemas.task_schema import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskManager:
    """Manager class for task CRUD operations."""

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """
        Create a new task.

        Args:
            db: Database session
            task_data: Task creation data

        Returns:
            Created task instance

        Raises:
            Exception: If task creation fails
        """
        try:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                deadline=task_data.deadline,
                user_id=task_data.user_id,
            )

            db.add(task)
            db.commit()
            db.refresh(task)

            # Log analytics event
            analytics_event = Analytics(
                user_id=task.user_id,
                task_id=task.id,
                event_type="created",
                event_timestamp=datetime.utcnow(),
                task_title=task.title,
                deadline=task.deadline,
            )
            db.add(analytics_event)
            db.commit()

            logger.info(f"Created task ID: {task.id} for user: {task.user_id}")
            return task

        except Exception as e:
            db.rollback()
            error_msg = f"Failed to create task: {e}"
            logger.error(error_msg)
            raise

    @staticmethod
    def get_task(
        db: Session, task_id: int, user_id: Optional[int] = None
    ) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            db: Database session
            task_id: Task ID
            user_id: Optional user ID to filter by ownership

        Returns:
            Task instance or None if not found
        """
        try:
            query = db.query(Task).filter(Task.id == task_id)
            if user_id is not None:
                query = query.filter(Task.user_id == user_id)

            task = query.first()
            return task

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise

    @staticmethod
    def get_tasks(
        db: Session,
        user_id: int,
        completed: Optional[bool] = None,
        overdue_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        Get tasks with optional filters.

        Args:
            db: Database session
            user_id: User ID to filter tasks
            completed: Optional filter by completion status
            overdue_only: Filter for overdue tasks only
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tasks
        """
        try:
            query = db.query(Task).filter(Task.user_id == user_id)

            if completed is not None:
                query = query.filter(Task.completed == completed)

            if overdue_only:
                query = query.filter(
                    and_(Task.completed == False, Task.deadline < datetime.utcnow())
                )

            tasks = query.order_by(Task.deadline.asc()).offset(skip).limit(limit).all()
            return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks for user {user_id}: {e}")
            raise

    @staticmethod
    def update_task(
        db: Session, task_id: int, task_data: TaskUpdate, user_id: int
    ) -> Optional[Task]:
        """
        Update a task.

        Args:
            db: Database session
            task_id: Task ID
            task_data: Task update data
            user_id: User ID for ownership verification

        Returns:
            Updated task instance or None if not found

        Raises:
            Exception: If update fails
        """
        try:
            task = TaskManager.get_task(db, task_id, user_id)
            if not task:
                return None

            # Track if task was just completed
            was_completed = task.completed
            update_data = task_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(task, field, value)

            task.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task)

            # Log analytics event if task was completed
            if not was_completed and task.completed:
                completion_time = datetime.utcnow()
                delay_hours = (completion_time - task.deadline).total_seconds() / 3600

                analytics_event = Analytics(
                    user_id=task.user_id,
                    task_id=task.id,
                    event_type="completed",
                    event_timestamp=completion_time,
                    task_title=task.title,
                    deadline=task.deadline,
                    was_completed_on_time=delay_hours <= 0,
                    completion_delay_hours=delay_hours,
                )
                db.add(analytics_event)
                db.commit()

            logger.info(f"Updated task ID: {task_id}")
            return task

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update task {task_id}: {e}")
            raise

    @staticmethod
    def delete_task(db: Session, task_id: int, user_id: int) -> bool:
        """
        Delete a task.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User ID for ownership verification

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If deletion fails
        """
        try:
            task = TaskManager.get_task(db, task_id, user_id)
            if not task:
                return False

            db.delete(task)
            db.commit()

            logger.info(f"Deleted task ID: {task_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise

    @staticmethod
    def get_overdue_tasks(db: Session, user_id: Optional[int] = None) -> List[Task]:
        """
        Get all overdue and incomplete tasks.

        Args:
            db: Database session
            user_id: Optional user ID to filter by

        Returns:
            List of overdue tasks
        """
        try:
            query = db.query(Task).filter(
                and_(Task.completed == False, Task.deadline < datetime.utcnow())
            )

            if user_id is not None:
                query = query.filter(Task.user_id == user_id)

            tasks = query.order_by(Task.deadline.asc()).all()
            return tasks

        except Exception as e:
            logger.error(f"Failed to get overdue tasks: {e}")
            raise

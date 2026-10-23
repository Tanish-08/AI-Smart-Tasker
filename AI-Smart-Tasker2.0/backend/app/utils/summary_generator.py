"""AI-powered task summary generation and modification."""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from omegaconf import DictConfig

from backend.app.models.task import Task
from backend.app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Generator for AI-powered task summaries.

    Provides functionality to generate concise single-line summaries
    and modify them using natural language prompts.
    """

    def __init__(self, llm_client: LLMClient, config: DictConfig):
        """
        Initialize summary generator.

        Args:
            llm_client: LLM client for text generation
            config: Hydra configuration object
        """
        self.llm_client = llm_client
        self.config = config
        self.prompts = config.prompts.summaries

    def generate_summary(
        self, task_title: str, task_description: Optional[str] = None
    ) -> str:
        """
        Generate a concise single-line task summary.

        Args:
            task_title: Task title
            task_description: Optional task description

        Returns:
            Generated summary

        Raises:
            Exception: If generation fails
        """
        try:
            # Build context
            context = {
                "task_title": task_title,
                "task_description": task_description or "No description provided",
            }

            # Get prompt template from config
            system_message = self.prompts.generation.system_message
            prompt_template = self.prompts.generation.prompt_template

            # Generate summary
            summary = self.llm_client.generate_with_template(
                template=prompt_template,
                variables=context,
                system_message=system_message,
                temperature=0.7,
                max_tokens=100,
            )

            # Clean up the response
            summary = summary.strip().strip('"').strip("'")

            logger.info(f"Generated summary: {summary[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise

    def modify_summary(self, current_summary: str, modification_prompt: str) -> str:
        """
        Modify an existing summary using natural language prompt.

        Args:
            current_summary: Current task summary
            modification_prompt: User's modification request

        Returns:
            Modified summary

        Raises:
            Exception: If modification fails
        """
        try:
            # Build context
            context = {
                "current_summary": current_summary,
                "modification_prompt": modification_prompt,
            }

            # Get prompt template from config
            system_message = self.prompts.modification.system_message
            prompt_template = self.prompts.modification.prompt_template

            # Generate modified summary
            modified_summary = self.llm_client.generate_with_template(
                template=prompt_template,
                variables=context,
                system_message=system_message,
                temperature=0.7,
                max_tokens=100,
            )

            # Clean up the response
            modified_summary = modified_summary.strip().strip('"').strip("'")

            logger.info(f"Modified summary: {modified_summary[:50]}...")
            return modified_summary

        except Exception as e:
            logger.error(f"Failed to modify summary: {e}")
            raise

    def generate_and_save_summary(self, db: Session, task: Task) -> str:
        """
        Generate summary and save it to the task.

        Args:
            db: Database session
            task: Task instance

        Returns:
            Generated summary

        Raises:
            Exception: If generation or save fails
        """
        try:
            # Generate summary
            summary = self.generate_summary(
                task_title=task.title, task_description=task.description
            )

            # Save to task
            task.summary = summary
            db.commit()
            db.refresh(task)

            logger.info(f"Saved summary for task {task.id}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save summary for task {task.id}: {e}")
            raise

    def modify_and_save_summary(
        self, db: Session, task: Task, modification_prompt: str
    ) -> str:
        """
        Modify summary and save it to the task.

        Args:
            db: Database session
            task: Task instance
            modification_prompt: User's modification request

        Returns:
            Modified summary

        Raises:
            Exception: If modification or save fails
        """
        try:
            if not task.summary:
                raise ValueError("Task does not have a summary to modify")

            # Modify summary
            modified_summary = self.modify_summary(
                current_summary=task.summary, modification_prompt=modification_prompt
            )

            # Save to task
            task.summary = modified_summary
            db.commit()
            db.refresh(task)

            logger.info(f"Modified and saved summary for task {task.id}")
            return modified_summary

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to modify and save summary for task {task.id}: {e}")
            raise

    def regenerate_summary(self, db: Session, task: Task) -> str:
        """
        Regenerate summary for a task (replaces existing).

        Args:
            db: Database session
            task: Task instance

        Returns:
            New generated summary

        Raises:
            Exception: If generation or save fails
        """
        try:
            # Generate new summary
            summary = self.generate_summary(
                task_title=task.title, task_description=task.description
            )

            # Replace existing summary
            task.summary = summary
            db.commit()
            db.refresh(task)

            logger.info(f"Regenerated summary for task {task.id}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to regenerate summary for task {task.id}: {e}")
            raise

"""AI-powered insult generator for missed deadlines."""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from omegaconf import DictConfig

from backend.app.models.task import Task
from backend.app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AIInsultGenerator:
    """
    Generator for funny, developer-themed insults when deadlines are missed.

    Uses LLM to generate witty, single-line motivational insults tailored
    to the specific task context.
    """

    def __init__(self, llm_client: LLMClient, config: DictConfig):
        """
        Initialize insult generator.

        Args:
            llm_client: LLM client for text generation
            config: Hydra configuration object
        """
        self.llm_client = llm_client
        self.config = config
        self.prompts = config.prompts.insults

    def generate_insult(self, task: Task) -> str:
        """
        Generate a funny developer-themed insult for a missed deadline.

        Args:
            task: Task instance with missed deadline

        Returns:
            Generated insult message

        Raises:
            Exception: If generation fails
        """
        try:
            # Build context about the task
            task_context = {
                "task_title": task.title,
                "task_description": task.description or "No description",
                "deadline": task.deadline.strftime("%Y-%m-%d %H:%M"),
            }

            # Get prompt template from config
            system_message = self.prompts.system_message
            prompt_template = self.prompts.prompt_template

            # Generate insult
            insult = self.llm_client.generate_with_template(
                template=prompt_template,
                variables=task_context,
                system_message=system_message,
                temperature=0.8,  # Higher temperature for more creative insults
                max_tokens=100,
            )

            # Clean up the response
            insult = insult.strip().strip('"').strip("'")

            logger.info(f"Generated insult for task {task.id}: {insult[:50]}...")
            return insult

        except Exception as e:
            logger.error(f"Failed to generate insult for task {task.id}: {e}")
            # Return fallback insult
            return self._get_fallback_insult()

    def generate_and_save_insult(self, db: Session, task: Task) -> str:
        """
        Generate insult and save it to the task.

        Args:
            db: Database session
            task: Task instance with missed deadline

        Returns:
            Generated insult message

        Raises:
            Exception: If generation or save fails
        """
        try:
            # Check if insult already exists
            if task.insult_message:
                logger.info(f"Task {task.id} already has insult message")
                return task.insult_message

            # Generate new insult
            insult = self.generate_insult(task)

            # Save to task
            task.insult_message = insult
            db.commit()
            db.refresh(task)

            logger.info(f"Saved insult for task {task.id}")
            return insult

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save insult for task {task.id}: {e}")
            raise

    def _get_fallback_insult(self) -> str:
        """
        Get a fallback insult when generation fails.

        Returns:
            Fallback insult message
        """
        fallback_insults = [
            "Even Internet Explorer would have finished this task by now.",
            "This deadline has more bugs than your last code review.",
            "404: Motivation not found. Please try again later.",
            "Your procrastination skills are more advanced than your code skills.",
            "Git commit -m 'Added deadline. Will fix later. (Narrator: They did not fix it later)'",
        ]

        # Use secrets module for cryptographically secure random selection
        # Although not strictly necessary for insults, it's a security best practice
        import secrets

        return secrets.choice(fallback_insults)

    def batch_generate_insults(self, db: Session, tasks: list[Task]) -> dict[int, str]:
        """
        Generate insults for multiple tasks.

        Args:
            db: Database session
            tasks: List of tasks with missed deadlines

        Returns:
            Dictionary mapping task IDs to insult messages
        """
        results = {}

        for task in tasks:
            try:
                insult = self.generate_and_save_insult(db, task)
                results[task.id] = insult
            except Exception as e:
                logger.error(f"Failed to generate insult for task {task.id}: {e}")
                results[task.id] = self._get_fallback_insult()

        return results

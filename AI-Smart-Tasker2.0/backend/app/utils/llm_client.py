"""LLM client wrapper using LangChain for external API calls."""
import logging
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM client for interacting with external language models via LangChain.

    This client uses LangChain to call external APIs (like OpenAI-compatible endpoints)
    for generating text responses.
    """

    def __init__(self, config: DictConfig):
        """
        Initialize LLM client with configuration.

        Args:
            config: Hydra configuration object containing LLM settings

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            self.config = config.llm

            # Validate required configuration keys
            if "model_name" not in self.config:
                raise ValueError("Missing LLM configuration key: 'model_name'")
            if "api_base" not in self.config:
                raise ValueError("Missing LLM configuration key: 'api_base'")

            self.model_name = self.config.model_name
            self.api_base = self.config.api_base
            self.api_key = self.config.get(
                "api_key", "EMPTY"
            )  # vLLM often doesn't need a real key
            self.temperature = self.config.get("temperature", 0.7)
            self.max_tokens = self.config.get("max_tokens", 150)
            self.request_timeout = self.config.get("request_timeout", 30)
            self.max_retries = self.config.get("max_retries", 3)

            # Initialize LangChain ChatOpenAI client
            # This works with OpenAI-compatible APIs including vLLM
            self._client = ChatOpenAI(
                model=self.model_name,
                base_url=self.api_base,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            logger.info(f"Initialized LLM client with model: {self.model_name}")

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            error_msg = f"Failed to initialize LLM client: {e}"
            logger.error(error_msg)
            raise

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: User prompt/question
            system_message: Optional system message to set context
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails
        """
        try:
            # Build messages
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))

            # Override parameters if provided
            kwargs: Dict[str, Any] = {}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens

            # Generate response
            if kwargs:
                # Create temporary client with overridden parameters
                temp_client = ChatOpenAI(
                    model=self.model_name,
                    base_url=self.api_base,
                    api_key=self.api_key,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                )
                response = temp_client.invoke(messages)
            else:
                response = self._client.invoke(messages)

            generated_text = response.content.strip()
            logger.debug(f"Generated response: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            error_msg = f"Failed to generate text: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    def generate_with_template(
        self,
        template: str,
        variables: Dict[str, str],
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using a prompt template with variables.

        Args:
            template: Prompt template with {variable_name} placeholders
            variables: Dictionary of variable names to values
            system_message: Optional system message to set context
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails
        """
        try:
            # Format template with variables
            prompt = template.format(**variables)
            logger.debug(f"Formatted prompt: {prompt[:100]}...")

            # Generate response
            return self.generate(
                prompt=prompt,
                system_message=system_message,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except KeyError as e:
            error_msg = f"Missing template variable: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate text with template: {e}"
            logger.error(error_msg)
            raise

    def health_check(self) -> bool:
        """
        Check if LLM service is accessible.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Try a simple generation
            self.generate(
                prompt="Hello",
                system_message="Respond with 'OK' only.",
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

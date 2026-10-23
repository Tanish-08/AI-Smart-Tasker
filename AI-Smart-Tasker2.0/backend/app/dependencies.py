"""Dependency injection functions for FastAPI."""
import logging
from typing import Optional

from dotenv import load_dotenv
from omegaconf import DictConfig
from hydra import compose, initialize

from backend.app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Global configuration and LLM client
_config: Optional[DictConfig] = None
_llm_client: Optional[LLMClient] = None


def load_config() -> DictConfig:
    """
    Load Hydra configuration.

    Returns:
        Hydra configuration object

    Raises:
        Exception: If configuration loading fails
    """
    global _config

    if _config is not None:
        return _config

    try:
        load_dotenv()
        # Initialize Hydra with config path
        with initialize(version_base=None, config_path="../config"):
            cfg = compose(config_name="config")
            _config = cfg
            logger.info("Configuration loaded successfully")
            return cfg

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def get_config() -> DictConfig:
    """
    Dependency function to get configuration.

    Returns:
        Configuration object
    """
    return load_config()


def get_llm_client() -> LLMClient:
    """
    Dependency function to get LLM client.

    Returns:
        LLM client instance

    Raises:
        RuntimeError: If LLM client is not initialized
    """
    if _llm_client is None:
        raise RuntimeError("LLM client not initialized")
    return _llm_client


def set_llm_client(client: LLMClient) -> None:
    """
    Set the global LLM client instance.

    Args:
        client: LLM client instance
    """
    global _llm_client
    _llm_client = client

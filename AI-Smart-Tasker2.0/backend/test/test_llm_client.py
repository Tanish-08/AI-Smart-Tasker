"""Unit tests for LLM client wrapper."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from omegaconf import OmegaConf

from backend.app.utils.llm_client import LLMClient


class TestLLMClientInit:
    """Test cases for LLMClient initialization."""

    def test_init_success(self, mock_config):
        """Test successful LLM client initialization."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_chat.return_value = MagicMock()

            client = LLMClient(mock_config)

            assert client.model_name == "test-model"
            assert client.api_base == "http://localhost:8001/v1"
            assert client.api_key == "test_key"
            assert client.temperature == 0.7
            assert client.max_tokens == 150

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config_dict = {
            "llm": {
                "model_name": "test-model",
                "api_base": "http://localhost:8001/v1",
            }
        }
        config = OmegaConf.create(config_dict)

        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_chat.return_value = MagicMock()

            client = LLMClient(config)

            assert client.api_key == "EMPTY"
            assert client.temperature == 0.7
            assert client.max_tokens == 150

    def test_init_missing_config_key(self):
        """Test initialization fails with missing config key."""
        config_dict = {
            "llm": {
                "model_name": "test-model"
                # Missing api_base
            }
        }
        config = OmegaConf.create(config_dict)

        with pytest.raises(ValueError, match="Missing LLM configuration key"):
            LLMClient(config)

    def test_init_chatgpt_client_creation(self, mock_config):
        """Test that ChatOpenAI client is created with correct parameters."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_instance = MagicMock()
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)

            mock_chat.assert_called_once_with(
                model="test-model",
                base_url="http://localhost:8001/v1",
                api_key="test_key",
                temperature=0.7,
                max_tokens=150,
            )


class TestLLMClientGenerate:
    """Test cases for LLMClient.generate()."""

    def test_generate_simple_prompt(self, mock_config):
        """Test generating text with a simple prompt."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "Generated response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.generate("Test prompt")

            assert result == "Generated response"
            mock_instance.invoke.assert_called_once()

    def test_generate_with_system_message(self, mock_config):
        """Test generating text with system message."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "System-guided response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.generate(
                "User prompt",
                system_message="You are a helpful assistant"
            )

            assert result == "System-guided response"

    def test_generate_with_temperature_override(self, mock_config):
        """Test generating text with temperature override."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "High temp response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.generate("Test prompt", temperature=1.0)

            # Should create new client with overridden temperature
            assert mock_chat.call_count == 2  # Once for init, once for override
            assert result == "High temp response"

    def test_generate_with_max_tokens_override(self, mock_config):
        """Test generating text with max tokens override."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "Limited tokens response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.generate("Test prompt", max_tokens=50)

            assert result == "Limited tokens response"

    def test_generate_strips_whitespace(self, mock_config):
        """Test that generated text is stripped of whitespace."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "  Response with spaces  \n"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.generate("Test prompt")

            assert result == "Response with spaces"

    def test_generate_error_handling(self, mock_config):
        """Test error handling during generation."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = Exception("API Error")
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)

            with pytest.raises(Exception, match="Failed to generate text"):
                client.generate("Test prompt")


class TestLLMClientGenerateWithTemplate:
    """Test cases for LLMClient.generate_with_template()."""

    def test_generate_with_template_success(self, mock_config):
        """Test generating text with template and variables."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "Template response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            template = "Task: {task_name}, Status: {status}"
            variables = {"task_name": "Test Task", "status": "Complete"}

            result = client.generate_with_template(template, variables)

            assert result == "Template response"

    def test_generate_with_template_missing_variable(self, mock_config):
        """Test error when template variable is missing."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_chat.return_value = MagicMock()

            client = LLMClient(mock_config)
            template = "Task: {task_name}, Status: {status}"
            variables = {"task_name": "Test Task"}  # Missing 'status'

            with pytest.raises(ValueError, match="Missing template variable"):
                client.generate_with_template(template, variables)

    def test_generate_with_template_with_system_message(self, mock_config):
        """Test template generation with system message."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "Guided template response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            template = "Hello {name}"
            variables = {"name": "World"}

            result = client.generate_with_template(
                template,
                variables,
                system_message="Be friendly"
            )

            assert result == "Guided template response"

    def test_generate_with_template_parameter_overrides(self, mock_config):
        """Test template generation with parameter overrides."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "Override response"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            template = "Task: {task}"
            variables = {"task": "Test"}

            result = client.generate_with_template(
                template,
                variables,
                temperature=0.9,
                max_tokens=200
            )

            assert result == "Override response"


class TestLLMClientHealthCheck:
    """Test cases for LLMClient.health_check()."""

    def test_health_check_success(self, mock_config):
        """Test successful health check."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_response = MagicMock()
            mock_response.content = "OK"
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.health_check()

            assert result is True

    def test_health_check_failure(self, mock_config):
        """Test health check failure."""
        with patch('backend.app.utils.llm_client.ChatOpenAI') as mock_chat:
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = Exception("Connection failed")
            mock_chat.return_value = mock_instance

            client = LLMClient(mock_config)
            result = client.health_check()

            assert result is False

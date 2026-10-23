"""Tests for optional AI task categorisation and its local fallback."""
import logging
from unittest.mock import Mock

from backend.app import ai_helper


def test_auto_categorize_uses_heuristic_when_model_is_not_configured(monkeypatch):
    monkeypatch.setattr(ai_helper, "_MODEL", None)

    result = ai_helper.auto_categorize_task("Urgent client project")

    assert result == {"category": "Work", "priority": "High"}


def test_auto_categorize_logs_and_falls_back_when_response_is_invalid(
    monkeypatch, caplog
):
    model = Mock()
    model.generate_content.return_value.text = "not JSON"
    monkeypatch.setattr(ai_helper, "_MODEL", model)

    with caplog.at_level(logging.WARNING):
        result = ai_helper.auto_categorize_task("Study for an exam")

    assert result == {"category": "Study", "priority": "Low"}
    assert "using heuristic fallback" in caplog.text

"""Optional Gemini-assisted task categorisation with a local fallback."""

import json
import logging
import os

from dotenv import load_dotenv

try:
    import google.generativeai as genai
    from google.api_core.exceptions import GoogleAPIError
except ImportError:  # pragma: no cover - optional dependency for local AI features
    genai = None
    _API_ERRORS = ()
else:
    _API_ERRORS = (GoogleAPIError,)

load_dotenv()

logger = logging.getLogger(__name__)
_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_MODEL = None

if genai is not None and _API_KEY:
    genai.configure(api_key=_API_KEY)
    _MODEL = genai.GenerativeModel("gemini-1.5-flash")


def _fallback_category(task_text: str) -> dict[str, str]:
    """Simple heuristic fallback when no AI API key or LLM is available."""
    text = (task_text or "").lower()

    if any(
        word in text
        for word in [
            "code",
            "build",
            "bug",
            "client",
            "project",
            "deploy",
            "api",
            "work",
            "meeting",
        ]
    ):
        category = "Work"
    elif any(
        word in text
        for word in ["study", "learn", "read", "practice", "course", "exam", "homework"]
    ):
        category = "Study"
    elif any(
        word in text
        for word in [
            "run",
            "gym",
            "workout",
            "fitness",
            "exercise",
            "training",
            "walk",
            "swim",
        ]
    ):
        category = "Fitness"
    else:
        category = "Personal"

    if any(
        word in text for word in ["urgent", "deadline", "today", "asap", "immediate"]
    ):
        priority = "High"
    elif any(word in text for word in ["later", "soon", "this week", "next"]):
        priority = "Medium"
    else:
        priority = "Low"

    return {"category": category, "priority": priority}


def auto_categorize_task(task_text: str | None) -> dict[str, str]:
    """Categorize task text into a predefined bucket with safe fallback behavior."""
    if not task_text or not isinstance(task_text, str):
        return {"category": "Personal", "priority": "Medium"}

    prompt = f"""
    Task: "{task_text}"
    Categorize this task strictly into one of these: 'Work', 'Personal', 'Study', 'Fitness'.
    Assign priority strictly into one of these: 'High', 'Medium', 'Low'.
    Return ONLY a valid JSON object. No markdown formatting, no backticks.
    Example: {{"category": "Work", "priority": "High"}}
    """

    if _MODEL is None:
        return _fallback_category(task_text)

    try:
        response = _MODEL.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except _API_ERRORS + (AttributeError, ValueError) as exc:
        logger.warning(
            "Gemini task categorisation failed (%s); using heuristic fallback.",
            type(exc).__name__,
        )
        return _fallback_category(task_text)

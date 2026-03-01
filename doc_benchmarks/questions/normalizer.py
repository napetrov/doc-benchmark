"""Normalize question records to a canonical schema.

Canonical schema:
    {
        "id":               str,
        "question":         str,   # canonical field (was "text" in legacy format)
        "persona":          str,
        "category":         str,
        "difficulty":       str,   # "beginner" | "intermediate" | "advanced"
        "expected_topics":  list[str],
    }

Usage::

    from doc_benchmarks.questions.normalizer import normalize_questions
    questions = normalize_questions(raw_list)
"""

from __future__ import annotations

from typing import Any, Dict, List

_DIFFICULTY_MAP: Dict[Any, str] = {
    1: "beginner",   "1": "beginner",  "beginner": "beginner",
    2: "intermediate", "2": "intermediate", "intermediate": "intermediate",
    3: "advanced",   "3": "advanced",  "advanced": "advanced",
    # common aliases
    "easy":   "beginner",
    "medium": "intermediate",
    "hard":   "advanced",
    "expert": "advanced",
}


def _normalize_difficulty(value: Any) -> str:
    """Map numeric or string difficulty to canonical label."""
    if value is None:
        return "intermediate"
    normalized = _DIFFICULTY_MAP.get(value)
    if normalized:
        return normalized
    # fallback: lowercase string match
    s = str(value).strip().lower()
    return _DIFFICULTY_MAP.get(s, "intermediate")


def normalize_question(q: Dict[str, Any], idx: int = 0) -> Dict[str, Any]:
    """Normalize a single question record to canonical schema."""
    return {
        "id":              q.get("id") or q.get("question_id") or f"q{idx:04d}",
        "question":        q.get("question") or q.get("text") or "",
        "persona":         q.get("persona") or "",
        "category":        q.get("category") or "",
        "difficulty":      _normalize_difficulty(q.get("difficulty")),
        "expected_topics": q.get("expected_topics") or [],
    }


def normalize_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of question records."""
    return [normalize_question(q, i) for i, q in enumerate(questions)]

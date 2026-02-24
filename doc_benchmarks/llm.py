"""Thin LLM wrapper using litellm — one interface for all providers.

Usage:
    from doc_benchmarks.llm import llm_call
    text = llm_call("Your prompt", model="gpt-4o-mini", provider="openai")
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def llm_call(
    prompt: str,
    model: str,
    provider: str = "openai",
    api_key: Optional[str] = None,
) -> str:
    """Call any LLM via litellm with a plain string API key (no async issues)."""
    from litellm import completion

    # Always resolve key as plain string from env — never async
    if not api_key:
        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "")

    # Build litellm model string
    if "/" in model:
        litellm_model = model          # already prefixed, e.g. "anthropic/claude-3"
    elif provider == "anthropic":
        litellm_model = f"anthropic/{model}"
    else:
        litellm_model = model          # openai models work as-is

    resp = completion(
        model=litellm_model,
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key or None,
    )
    return resp.choices[0].message.content

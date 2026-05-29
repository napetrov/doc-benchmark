"""Core treatment-arm abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    """The agent setup produced by a treatment for one question.

    Attributes:
        system_prompt: Optional system prompt (agent persona). ``None`` keeps
            the model's default behavior.
        injected_context: Retrieved/loaded chunks to prepend to the prompt.
            Each chunk is a dict with at least a ``content`` key, matching the
            shape returned by ``MCPClient.get_library_docs``.
        metadata: Free-form provenance for the report (retrieval stats, profile
            id, skill name, …).
    """

    system_prompt: Optional[str] = None
    injected_context: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_context(self) -> bool:
        return bool(self.injected_context)


class Treatment(ABC):
    """One arm of an N-way evaluation.

    Subclasses implement :meth:`prepare`, returning the :class:`AgentConfig`
    used to answer a single question. Treatments must be safe to reuse across
    questions (any per-question state lives in the returned config).
    """

    #: Stable arm identifier used as the key in result/report tables.
    name: str = "treatment"

    @abstractmethod
    def prepare(
        self,
        question_text: str,
        library_name: str,
        library_id: Optional[str] = None,
    ) -> AgentConfig:
        """Build the agent config for *question_text*."""
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} name={self.name!r}>"

"""Treatment arms: pluggable context-augmentation strategies under test.

A *treatment* is anything that modifies the answering agent's setup before it
answers: the system prompt, the context injected into the prompt, and (in the
agentic track) the tools/skills it can call. Each treatment is one **arm** of an
N-way comparison, generalizing the original binary ``with_docs``/``without_docs``
experiment.

The four supported arm kinds map onto the evaluation scenarios:

==================  ====================================================
Arm spec            Scenario
==================  ====================================================
``baseline``        No augmentation (the control / ``without_docs``).
``docs[:source]``   Documentation injection (the original ``with_docs``).
``mcp:<ref>``       Documentation retrieved via a real MCP server.
``profile:<path>``  Agent persona prompt (answering-agent system prompt).
``skill:<path>``    Agent skill injected as context.
==================  ====================================================
"""

from .base import AgentConfig, Treatment
from .arms import (
    BaselineTreatment,
    DocTreatment,
    AgentProfileTreatment,
    SkillTreatment,
)
from .factory import create_treatment, create_treatments

__all__ = [
    "AgentConfig",
    "Treatment",
    "BaselineTreatment",
    "DocTreatment",
    "AgentProfileTreatment",
    "SkillTreatment",
    "create_treatment",
    "create_treatments",
]

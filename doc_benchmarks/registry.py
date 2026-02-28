"""Library registry — load and query known products from libraries.yaml."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Default registry bundled with the package
_DEFAULT_REGISTRY = Path(__file__).parent.parent / "libraries.yaml"


@dataclass
class LibraryEntry:
    key: str                          # registry key, e.g. "onetbb"
    name: str                         # human name, e.g. "oneTBB"
    description: str
    repo: Optional[str] = None
    context7_id: Optional[str] = None
    doc_sources: List[str] = field(default_factory=lambda: ["context7"])


class LibraryRegistry:
    """Load and query the libraries.yaml registry."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or _DEFAULT_REGISTRY
        self._entries: Dict[str, LibraryEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            logger.warning(f"Registry not found: {self._path}")
            return
        data = yaml.safe_load(self._path.read_text()) or {}
        for key, cfg in data.get("libraries", {}).items():
            self._entries[key.lower()] = LibraryEntry(
                key=key,
                name=cfg.get("name", key),
                description=cfg.get("description", "").strip(),
                repo=cfg.get("repo"),
                context7_id=cfg.get("context7_id"),
                doc_sources=cfg.get("doc_sources", ["context7"]),
            )
        logger.info(f"Loaded {len(self._entries)} libraries from {self._path}")

    def get(self, key: str) -> LibraryEntry:
        """Return entry by key (case-insensitive). Raises KeyError if not found."""
        entry = self._entries.get(key.lower())
        if entry is None:
            available = ", ".join(sorted(self._entries))
            raise KeyError(f"Library '{key}' not found in registry. Available: {available}")
        return entry

    def list(self) -> List[LibraryEntry]:
        return list(self._entries.values())

    def keys(self) -> List[str]:
        return sorted(self._entries.keys())

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._entries

from pathlib import Path
from typing import Iterable


def discover_markdown(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_docs(paths: Iterable[Path]) -> dict[str, str]:
    return {str(p): load_text(p) for p in sorted(paths)}

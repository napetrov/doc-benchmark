"""Snapshot comparison logic."""

from __future__ import annotations

import json
from pathlib import Path


def compare_snapshots(base_path: Path, cand_path: Path) -> dict:
    """Compare two run snapshots and return summary and metric deltas."""
    base = json.loads(base_path.read_text(encoding="utf-8"))
    cand = json.loads(cand_path.read_text(encoding="utf-8"))

    diff = {
        "docs": cand["summary"]["docs"] - base["summary"]["docs"],
        "score": round(cand["summary"]["score"] - base["summary"]["score"], 4),
        "coverage": round(cand["summary"]["coverage"] - base["summary"]["coverage"], 4),
        "freshness_lite": round(cand["summary"]["freshness_lite"] - base["summary"]["freshness_lite"], 4),
        "readability": round(cand["summary"]["readability"] - base["summary"]["readability"], 4),
    }
    return {"base": base["summary"], "candidate": cand["summary"], "diff": diff}

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import subprocess

from doc_benchmarks.ingest.chunker import chunk_text
from doc_benchmarks.ingest.loader import discover_markdown, load_docs
from doc_benchmarks.metrics import coverage, freshness_lite, readability


@dataclass
class DocMetrics:
    path: str
    chunks: int
    coverage: float
    freshness_lite: float
    readability: float
    score: float


def _weighted_score(doc: dict, weights: dict[str, float]) -> float:
    return round(
        doc["coverage"] * weights["coverage"]
        + doc["freshness_lite"] * weights["freshness_lite"]
        + doc["readability"] * weights["readability"],
        4,
    )


def _load_spec(spec_path: Path) -> dict:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except Exception:
        proc = subprocess.run(
            ["yq", "eval", "-o=json", str(spec_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)


def run_benchmark(root: Path, spec_path: Path) -> dict:
    spec = _load_spec(spec_path)
    weights = spec["weights"]

    docs = discover_markdown(root / "docs")
    loaded = load_docs(docs)

    results: list[DocMetrics] = []
    for p in docs:
        text = loaded[str(p)]
        row = {
            "path": str(p.relative_to(root)),
            "chunks": len(chunk_text(text)),
            "coverage": coverage.score(text),
            "freshness_lite": freshness_lite.score(p, spec["metrics"]["freshness_lite"]["max_age_days"]),
            "readability": readability.score(text, spec["metrics"]["readability"]["grade_max"]),
        }
        row["score"] = _weighted_score(row, weights)
        results.append(DocMetrics(**row))

    agg = {
        "coverage": round(sum(r.coverage for r in results) / max(1, len(results)), 4),
        "freshness_lite": round(sum(r.freshness_lite for r in results) / max(1, len(results)), 4),
        "readability": round(sum(r.readability for r in results) / max(1, len(results)), 4),
    }
    total_score = round(sum(r.score for r in results) / max(1, len(results)), 4)

    return {
        "summary": {
            "docs": len(results),
            "score": total_score,
            **agg,
        },
        "docs": [asdict(r) for r in results],
    }


def save_snapshot(data: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

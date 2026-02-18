from __future__ import annotations

from pathlib import Path


def _summary_lines(summary: dict) -> list[str]:
    return [
        f"- docs: {summary['docs']}",
        f"- total_score: {summary['score']}",
        f"- coverage: {summary['coverage']}",
        f"- freshness_lite: {summary['freshness_lite']}",
        f"- readability: {summary['readability']}",
    ]


def write_run_report(run_data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Doc Benchmark Run", "", "## Summary", *(_summary_lines(run_data["summary"])), "", "## Docs"]
    for d in run_data["docs"]:
        lines.append(f"- {d['path']}: score={d['score']} cov={d['coverage']} fresh={d['freshness_lite']} read={d['readability']} chunks={d['chunks']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compare_report(compare_data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    d = compare_data["diff"]
    lines = [
        "# Doc Benchmark Compare",
        "",
        "## Diff",
        f"- score: {d['score']:+.4f}",
        f"- coverage: {d['coverage']:+.4f}",
        f"- freshness_lite: {d['freshness_lite']:+.4f}",
        f"- readability: {d['readability']:+.4f}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

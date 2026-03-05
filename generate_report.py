#!/usr/bin/env python3
"""
generate_report.py — Generate a documentation quality report from eval JSON.

Usage:
    python generate_report.py --eval results/onedal_final/eval/oneDAL.json \
                              --out results/onedal_final/reports/oneDAL_full.md

    python generate_report.py --eval results/onetbb_final/eval/oneTBB.json \
                              --out results/onetbb_final/reports/oneTBB_full.md
"""

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Los_Angeles")
except ImportError:
    _TZ = None


def avg(lst):
    return round(sum(lst) / len(lst), 1) if lst else 0.0


def has_scores(e):
    return (
        e.get("with_docs") and e["with_docs"].get("aggregate") is not None
        and e.get("without_docs") and e["without_docs"].get("aggregate") is not None
    )


def stats(qs):
    valid = [e for e in qs if has_scores(e)]
    with_s = [e["with_docs"]["aggregate"] for e in valid]
    without_s = [e["without_docs"]["aggregate"] for e in valid]
    deltas = [e["delta"] for e in valid if e.get("delta") is not None]
    return {
        "count": len(qs),
        "valid": len(valid),
        "with_avg": avg(with_s),
        "without_avg": avg(without_s),
        "delta_avg": round(avg(with_s) - avg(without_s), 1),
        "improvements": sum(1 for d in deltas if d > 0),
        "degradations": sum(1 for d in deltas if d < 0),
        "neutral": sum(1 for d in deltas if d == 0),
    }


def fmt_delta(d):
    if d is None:
        return "N/A"
    if isinstance(d, float):
        d = round(d, 1)
    return f"+{d}" if d > 0 else str(d)


def detect_static_prefix(evals):
    """Detect the prefix used for static/golden questions (e.g. 'onedal-Q', 'onetbb-Q')."""
    for e in evals:
        qid = e["question_id"]
        # Static questions typically look like 'onedal-Q001', 'onetbb-Q001', etc.
        import re
        m = re.match(r"^([a-zA-Z]+-Q)\d+$", qid)
        if m:
            return m.group(1)
    return None


DIAG_MAP = {
    "docs_helped": "✅ Docs helped",
    "knowledge_sufficient": "🔵 Model knowledge sufficient",
    "empty_retrieval": "🔴 Empty retrieval",
    "low_relevance": "🟡 Low relevance",
    "below_rerank_threshold": "🟠 Below rerank threshold",
    "insufficient_data": "⚪ Insufficient data",
}

DIFFICULTY_ORDER = ["easy", "beginner", "intermediate", "medium", "advanced", "hard"]


def generate_report(eval_path: str, out_path: str):
    with open(eval_path) as f:
        data = json.load(f)

    evals = data["evaluations"]
    meta = data.get("run_metadata", {})
    library = os.path.basename(eval_path).replace(".json", "")

    static_prefix = detect_static_prefix(evals)
    static_qs = [e for e in evals if static_prefix and e["question_id"].startswith(static_prefix)]
    dynamic_qs = [e for e in evals if not (static_prefix and e["question_id"].startswith(static_prefix))]

    all_stats = stats(evals)
    static_stats = stats(static_qs)
    dyn_stats = stats(dynamic_qs)

    diff_groups = defaultdict(list)
    for e in evals:
        diff_groups[e.get("difficulty", "unknown")].append(e)

    valid_all = [
        e for e in evals
        if has_scores(e) and isinstance(e.get("delta"), (int, float)) and not math.isnan(e["delta"])
    ]

    lines = []

    # Header
    lines += [
        f"# {library} Documentation Quality Report",
        f"_Generated: {datetime.now(tz=_TZ).strftime('%Y-%m-%d %H:%M %Z') if _TZ else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## Run Configuration",
        "| | |",
        "|---|---|",
        f'| Answer model | {meta.get("answer_model", "—")} ({meta.get("answer_provider", "—")}) |',
        f'| Judge model | {data.get("judge_model", "—")} ({data.get("judge_provider", "—")}) |',
        f'| Total questions | {all_stats["count"]} ({dyn_stats["count"]} dynamic + {static_stats["count"]} golden static) |',
        "",
    ]

    # Summary
    lines += [
        "## Summary",
        "| Set | Count | WITH docs | WITHOUT docs | Delta |",
        "|---|---:|---:|---:|---:|",
        f'| **All** | {all_stats["count"]} | {all_stats["with_avg"]} | {all_stats["without_avg"]} | **{all_stats["delta_avg"]:+}** |',
        f'| Generated (dynamic) | {dyn_stats["count"]} | {dyn_stats["with_avg"]} | {dyn_stats["without_avg"]} | **{dyn_stats["delta_avg"]:+}** |',
        f'| Golden (static) | {static_stats["count"]} | {static_stats["with_avg"]} | {static_stats["without_avg"]} | **{static_stats["delta_avg"]:+}** |',
        "",
    ]

    # Dynamic vs Static breakdown
    lines += [
        "## Breakdown: Dynamic vs Static",
        "| Set | Count | WITH | WITHOUT | Delta | Improved | Degraded | Neutral |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, s in [
        ("Dynamic (generated)", dyn_stats),
        ("Golden (static)", static_stats),
        ("**Total**", all_stats),
    ]:
        lines.append(
            f'| {label} | {s["count"]} | {s["with_avg"]} | {s["without_avg"]} '
            f'| **{s["delta_avg"]:+}** | {s["improvements"]} | {s["degradations"]} | {s["neutral"]} |'
        )
    lines.append("")

    # Difficulty breakdown
    lines += [
        "## Breakdown by Difficulty",
        "| Difficulty | Count | WITH | WITHOUT | Delta | Improved | Degraded |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in DIFFICULTY_ORDER:
        if d in diff_groups:
            s = stats(diff_groups[d])
            lines.append(
                f'| {d} | {s["count"]} | {s["with_avg"]} | {s["without_avg"]} '
                f'| **{s["delta_avg"]:+}** | {s["improvements"]} | {s["degradations"]} |'
            )
    lines.append("")

    # Diagnosis
    diag = Counter(
        e["diagnosis"]["label"]
        for e in evals
        if isinstance(e.get("diagnosis"), dict) and "label" in e["diagnosis"]
    )
    total_diag = sum(diag.values())
    lines += [
        "## Diagnosis",
        "| Diagnosis | Count | Rate |",
        "|---|---:|---:|",
    ]
    for label, count in sorted(diag.items(), key=lambda x: -x[1]):
        name = DIAG_MAP.get(label, label)
        rate = round(count / total_diag * 100) if total_diag else 0
        lines.append(f"| {name} | {count} | {rate}% |")
    missing = all_stats["count"] - total_diag
    if missing > 0:
        lines.append(f"| ⚪ Insufficient data | {missing} | {round(missing/all_stats['count']*100)}% |")
    lines.append("")

    # Top 15 helped
    lines += [
        "## Top 15 — Docs Helped Most",
        "| QID | Source | Delta | WITH | WITHOUT | Difficulty | Question |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for e in sorted(valid_all, key=lambda x: x["delta"], reverse=True)[:15]:
        src = "🔵 static" if static_prefix and e["question_id"].startswith(static_prefix) else "🟡 gen"
        q = e["question_text"][:70] + "..."
        delta = round(e["delta"], 1) if isinstance(e["delta"], float) else e["delta"]
        lines.append(
            f'| {e["question_id"]} | {src} | **{fmt_delta(delta)}** '
            f'| {e["with_docs"]["aggregate"]} | {e["without_docs"]["aggregate"]} '
            f'| {e.get("difficulty", "—")} | {q} |'
        )
    lines.append("")

    # Bottom 15 degradations
    lines += [
        "## Bottom 15 — Biggest Degradations",
        "| QID | Source | Delta | WITH | WITHOUT | Difficulty | Question |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for e in sorted(valid_all, key=lambda x: x["delta"])[:15]:
        src = "🔵 static" if static_prefix and e["question_id"].startswith(static_prefix) else "🟡 gen"
        q = e["question_text"][:70] + "..."
        delta = round(e["delta"], 1) if isinstance(e["delta"], float) else e["delta"]
        lines.append(
            f'| {e["question_id"]} | {src} | **{fmt_delta(delta)}** '
            f'| {e["with_docs"]["aggregate"]} | {e["without_docs"]["aggregate"]} '
            f'| {e.get("difficulty", "—")} | {q} |'
        )
    lines.append("")

    # Full Q&A — Static
    lines += [
        "## Full Q&A Table — Golden Static Questions",
        "| QID | Difficulty | WITH | WITHOUT | Delta | Question |",
        "|---|---|---:|---:|---:|---|",
    ]
    for e in sorted(static_qs, key=lambda x: (x.get("difficulty", ""), x["question_id"])):
        wd = e["with_docs"]["aggregate"] if e.get("with_docs") and e["with_docs"].get("aggregate") is not None else "N/A"
        wod = e["without_docs"]["aggregate"] if e.get("without_docs") and e["without_docs"].get("aggregate") is not None else "N/A"
        delta = e.get("delta")
        d = round(delta, 1) if isinstance(delta, float) else delta
        lines.append(
            f'| {e["question_id"]} | {e.get("difficulty", "—")} | {wd} | {wod} '
            f'| {fmt_delta(d)} | {e["question_text"][:70]}... |'
        )
    lines.append("")

    # Full Q&A — Dynamic
    lines += [
        "## Full Q&A Table — Dynamic Generated Questions",
        "| QID | Difficulty | WITH | WITHOUT | Delta | Question |",
        "|---|---|---:|---:|---:|---|",
    ]
    for e in sorted(dynamic_qs, key=lambda x: (x.get("difficulty", ""), x["question_id"])):
        wd = e["with_docs"]["aggregate"] if e.get("with_docs") and e["with_docs"].get("aggregate") is not None else "N/A"
        wod = e["without_docs"]["aggregate"] if e.get("without_docs") and e["without_docs"].get("aggregate") is not None else "N/A"
        delta = e.get("delta")
        d = round(delta, 1) if isinstance(delta, float) else delta
        lines.append(
            f'| {e["question_id"]} | {e.get("difficulty", "—")} | {wd} | {wod} '
            f'| {fmt_delta(d)} | {e["question_text"][:70]}... |'
        )
    lines.append("")

    # Recommendations
    lines += [
        "## Key Observations & Recommendations",
        "",
        f'- **Overall delta: {all_stats["delta_avg"]:+}** — '
        + ("documentation is helping." if all_stats["delta_avg"] > 2 else
           "documentation is neutral or slightly harmful."),
        f'- **Dynamic vs Static agreement:** {dyn_stats["delta_avg"]:+} vs {static_stats["delta_avg"]:+} — '
        + ("good consistency, benchmark is stable." if abs(dyn_stats["delta_avg"] - static_stats["delta_avg"]) < 3
           else "notable gap — investigate question quality."),
        f'- **Win rate:** {round(all_stats["improvements"]/all_stats["count"]*100) if all_stats["count"] else 0}% questions improved with docs '
        f'({all_stats["improvements"]}/{all_stats["count"]}).',
        f'- **Degradations:** {all_stats["degradations"]} questions '
        f'({round(all_stats["degradations"]/all_stats["count"]*100) if all_stats["count"] else 0}%).',
        "",
    ]

    report = "\n".join(lines)

    dir_path = os.path.dirname(out_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(report)

    print(f"✅ Report written to: {out_path}")
    print(f"   Questions: {all_stats['count']} ({dyn_stats['count']} dynamic + {static_stats['count']} static)")
    print(f"   Delta: {all_stats['delta_avg']:+} (with={all_stats['with_avg']}, without={all_stats['without_avg']})")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate documentation quality report from eval JSON.")
    parser.add_argument("--eval", required=True, help="Path to eval JSON file")
    parser.add_argument("--out", required=True, help="Output path for the markdown report")
    args = parser.parse_args()
    generate_report(args.eval, args.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Multi-model comparison script for doc-benchmark results.

Usage:
    # Compare models on regular questions only
    python scripts/compare_models.py \
        --regular-runs results/arms/dpnp_regular_sonnet46.json results/arms/dpnp_regular_opus48.json \
        --run-ids sonnet46,opus48 \
        --out results/dpnp_compare.md

    # Compare models on golden questions only
    python scripts/compare_models.py \
        --golden-runs results/arms/dpnp_golden_sonnet46.json results/arms/dpnp_golden_opus48.json \
        --run-ids sonnet46,opus48 \
        --out results/dpnp_compare.md

    # Compare models on both regular AND golden questions
    python scripts/compare_models.py \
        --regular-runs results/arms/dpnp_regular_sonnet46.json results/arms/dpnp_regular_opus48.json \
        --golden-runs results/arms/dpnp_golden_sonnet46.json results/arms/dpnp_golden_opus48.json \
        --run-ids sonnet46,opus48 \
        --out results/dpnp_compare.md

Generates a comprehensive report with:
- Overall summary (WITH/WITHOUT docs, delta)
- Statistical significance (t-test, Wilcoxon, Cohen's d)
- Static vs Dynamic breakdown (if both types present)
- Difficulty analysis
- Head-to-Head comparison
- Per-model weak spots
"""

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed. Statistical tests will be skipped.")

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Los_Angeles")
except ImportError:
    _TZ = None


def load_run(path: str) -> dict[str, Any]:
    """Load a judged results JSON file."""
    with open(path) as f:
        return json.load(f)


def extract_scores(run_data: dict) -> list[dict]:
    """Extract question-level scores from a run."""
    scores = []

    # Check if scores are in evaluations field (new format)
    if "evaluations" in run_data:
        baseline_arm = run_data["baseline_arm"]

        for evaluation in run_data["evaluations"]:
            qid = evaluation["question_id"]
            eval_scores = evaluation.get("scores", {})

            if not eval_scores:
                continue

            baseline_data = eval_scores.get(baseline_arm, {})
            if baseline_data is None:
                continue
            baseline_score = baseline_data.get("aggregate")

            # Find treatment arm (not baseline)
            treatment_score = None
            for arm_name, arm_scores in eval_scores.items():
                if arm_name != baseline_arm and arm_scores is not None:
                    treatment_score = arm_scores.get("aggregate")
                    break

            if baseline_score is not None and treatment_score is not None:
                scores.append({
                    "question_id": qid,
                    "question_text": evaluation.get("question_text", ""),
                    "category": evaluation.get("category", ""),
                    "difficulty": evaluation.get("difficulty", "unknown"),
                    "persona": evaluation.get("persona", ""),
                    "without_docs": baseline_score,
                    "with_docs": treatment_score,
                    "delta": treatment_score - baseline_score,
                })

    # Fallback to old format (evaluation inside arms)
    else:
        for answer in run_data.get("answers", []):
            qid = answer["question_id"]
            arms = answer.get("arms", {})

            baseline_eval = arms.get(run_data["baseline_arm"], {}).get("evaluation", {})

            # Find treatment arm (not baseline)
            treatment_arm = None
            for arm_name in arms.keys():
                if arm_name != run_data["baseline_arm"]:
                    treatment_arm = arm_name
                    break

            treatment_eval = arms.get(treatment_arm, {}).get("evaluation", {}) if treatment_arm else {}

            baseline_score = baseline_eval.get("aggregate_score")
            treatment_score = treatment_eval.get("aggregate_score")

            if baseline_score is not None and treatment_score is not None:
                scores.append({
                    "question_id": qid,
                    "question_text": answer.get("question_text", ""),
                    "category": answer.get("category", ""),
                    "difficulty": answer.get("difficulty", "unknown"),
                    "persona": answer.get("persona", ""),
                    "without_docs": baseline_score,
                    "with_docs": treatment_score,
                    "delta": treatment_score - baseline_score,
                })

    return scores


def avg(lst):
    """Calculate average, handling empty lists."""
    return round(sum(lst) / len(lst), 1) if lst else 0.0


def significance_test(with_scores: list[float], without_scores: list[float]) -> dict | None:
    """Compute paired t-test, Wilcoxon, and Cohen's d."""
    if len(with_scores) < 5 or not HAS_SCIPY:
        return None

    deltas = [w - wo for w, wo in zip(with_scores, without_scores)]
    d_mean = sum(deltas) / len(deltas)
    d_std = (sum((x - d_mean) ** 2 for x in deltas) / len(deltas)) ** 0.5

    result = {
        "n": len(with_scores),
        "delta_mean": round(d_mean, 2),
        "delta_std": round(d_std, 2),
    }

    t_stat, p_ttest = sp_stats.ttest_rel(with_scores, without_scores)
    result["t_stat"] = round(t_stat, 3)
    result["p_ttest"] = round(p_ttest, 4)

    try:
        _, p_wilcox = sp_stats.wilcoxon(deltas)
        result["p_wilcoxon"] = round(p_wilcox, 4)
    except Exception:
        result["p_wilcoxon"] = None

    result["cohens_d"] = round(d_mean / d_std, 3) if d_std > 0 else 0.0
    result["significant"] = bool(p_ttest < 0.05)

    # Effect size interpretation
    abs_d = abs(result["cohens_d"])
    if abs_d < 0.2:
        result["effect"] = "negligible"
    elif abs_d < 0.5:
        result["effect"] = "small"
    elif abs_d < 0.8:
        result["effect"] = "medium"
    else:
        result["effect"] = "large"

    return result


def fmt_delta(d):
    """Format delta with + sign for positive values."""
    if d is None:
        return "N/A"
    if isinstance(d, float):
        d = round(d, 1)
    return f"+{d}" if d > 0 else str(d)


def generate_combined_report(regular_runs: list[tuple[str, dict]], golden_runs: list[tuple[str, dict]], run_ids: list[str], out_path: str):
    """Generate combined report for regular and/or golden questions."""

    lines = []

    # Header
    lines += [
        "#  Model Comparison Report",
        f"_Generated: {datetime.now(tz=_TZ).strftime('%Y-%m-%d %H:%M %Z') if _TZ else datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]

    # Generate separate sections for regular and golden if both are present
    if regular_runs and golden_runs:
        lines += [
            "## Overview",
            "",
            "This report compares models across two question sets:",
            "- **Regular Questions**: 12 standard questions covering getting started, compatibility, performance, and troubleshooting",
            "- **Golden Questions**: 7 scenario-based questions derived from real GitHub issues",
            "",
        ]

        # Regular questions section
        lines += [
            "---",
            "",
            "# Regular Questions Analysis",
            "",
        ]
        section_lines = generate_section_report(regular_runs, run_ids, "Regular")
        lines += section_lines

        # Golden questions section
        lines += [
            "",
            "---",
            "",
            "# Golden Questions Analysis",
            "",
        ]
        section_lines = generate_section_report(golden_runs, run_ids, "Golden")
        lines += section_lines

    elif regular_runs:
        # Only regular questions
        section_lines = generate_section_report(regular_runs, run_ids, "Regular")
        lines += section_lines

    elif golden_runs:
        # Only golden questions
        section_lines = generate_section_report(golden_runs, run_ids, "Golden")
        lines += section_lines

    # Write output
    output = "\n".join(lines)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(output, encoding="utf-8")
    print(f"✅ Report written to {out_path}")


def generate_section_report(runs: list[tuple[str, dict]], run_ids: list[str], section_name: str) -> list[str]:
    """Generate report section for a set of runs (regular or golden)."""
    """Generate multi-model comparison report."""

    # Extract scores for each run
    all_run_scores = {}
    for run_id, run_data in runs:
        all_run_scores[run_id] = extract_scores(run_data)

    # Find common questions across all runs
    question_sets = [set(s["question_id"] for s in scores) for scores in all_run_scores.values()]
    common_questions = set.intersection(*question_sets) if question_sets else set()

    lines = []

    # Header
    lines += [
        "#  Model Comparison Report",
        f"_Generated: {datetime.now(tz=_TZ).strftime('%Y-%m-%d %H:%M %Z') if _TZ else datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## Models Compared",
        "| Run ID | Answer model | Judge model |",
        "|---|---|---|",
    ]

    for run_id, run_data in runs:
        model = run_data.get("model", "unknown")
        provider = run_data.get("provider", "unknown")
        judge_model = run_data.get("judge_model", "same")
        judge_provider = run_data.get("judge_provider", provider)
        lines.append(f'| **{run_id}** | {model} ({provider}) | {judge_model} ({judge_provider}) |')

    lines += [
        "",
        f"Common questions evaluated: **{len(common_questions)}**",
        "",
    ]

    # Overall Summary
    lines += [
        "## Overall Summary",
        "| Run | N | WITH docs | WITHOUT docs | Delta | Improved | Degraded |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    summary_stats = {}
    for run_id in run_ids:
        scores = all_run_scores[run_id]
        with_avg = avg([s["with_docs"] for s in scores])
        without_avg = avg([s["without_docs"] for s in scores])
        delta_avg = round(with_avg - without_avg, 1)
        improved = sum(1 for s in scores if s["delta"] > 0)
        degraded = sum(1 for s in scores if s["delta"] < 0)

        summary_stats[run_id] = {
            "n": len(scores),
            "with_avg": with_avg,
            "without_avg": without_avg,
            "delta_avg": delta_avg,
            "improved": improved,
            "degraded": degraded,
        }

        lines.append(
            f'| **{run_id}** | {len(scores)} | {with_avg} | {without_avg} | '
            f'**{fmt_delta(delta_avg)}** | {improved} | {degraded} |'
        )

    lines += [""]

    # Statistical Significance
    if HAS_SCIPY:
        lines += [
            "## Statistical Significance of Delta (α = 0.05)",
            "_Is each model's delta (WITH − WITHOUT) statistically meaningful?_",
            "",
            "| Run | Delta | p (t-test) | p (Wilcoxon) | Cohen's d | Effect | Significant? |",
            "|---|---:|---:|---:|---:|---|---|",
        ]

        for run_id in run_ids:
            scores = all_run_scores[run_id]
            with_scores = [s["with_docs"] for s in scores]
            without_scores = [s["without_docs"] for s in scores]

            sig = significance_test(with_scores, without_scores)
            if sig:
                sig_mark = "✅ Yes" if sig["significant"] else "❌ No"
                p_wilcox = sig["p_wilcoxon"] if sig["p_wilcoxon"] else "N/A"
                lines.append(
                    f'| **{run_id}** | {fmt_delta(sig["delta_mean"])} | {sig["p_ttest"]} | '
                    f'{p_wilcox} | {fmt_delta(sig["cohens_d"])} | {sig["effect"]} | {sig_mark} |'
                )

        lines += [""]

    # Static vs Dynamic (if applicable)
    static_prefix = None
    for scores in all_run_scores.values():
        for s in scores:
            qid = s["question_id"]
            # Detect pattern like "dpnp-Q001" for static questions
            if "-Q" in qid and qid.split("-Q")[1].isdigit():
                static_prefix = qid.split("-Q")[0] + "-Q"
                break
        if static_prefix:
            break

    if static_prefix:
        lines += [
            "## Static (Golden) vs Dynamic",
            "| Run | Type | N | WITH | WITHOUT | Delta |",
            "|---|---|---:|---:|---:|---:|",
        ]

        for run_id in run_ids:
            scores = all_run_scores[run_id]
            static = [s for s in scores if s["question_id"].startswith(static_prefix)]
            dynamic = [s for s in scores if not s["question_id"].startswith(static_prefix)]

            if static:
                with_avg = avg([s["with_docs"] for s in static])
                without_avg = avg([s["without_docs"] for s in static])
                delta = round(with_avg - without_avg, 1)
                lines.append(f'| **{run_id}** | 🔵 static | {len(static)} | {with_avg} | {without_avg} | **{fmt_delta(delta)}** |')

            if dynamic:
                with_avg = avg([s["with_docs"] for s in dynamic])
                without_avg = avg([s["without_docs"] for s in dynamic])
                delta = round(with_avg - without_avg, 1)
                lines.append(f'| **{run_id}** | 🟡 dynamic | {len(dynamic)} | {with_avg} | {without_avg} | **{fmt_delta(delta)}** |')

        lines += [""]

    # By Difficulty (common questions only)
    difficulty_groups = defaultdict(lambda: defaultdict(list))
    for run_id in run_ids:
        scores = all_run_scores[run_id]
        for s in scores:
            if s["question_id"] in common_questions:
                difficulty_groups[s["difficulty"]][run_id].append(s)

    if difficulty_groups:
        lines += [
            "## By Difficulty (common questions only)",
            "| Difficulty | N |",
        ]

        # Build header dynamically
        header_parts = ["| Difficulty | N |"]
        for run_id in run_ids:
            header_parts.append(f" {run_id} WITH | {run_id} Δ |")
        lines[-1] = "".join(header_parts)
        lines.append("|---|---:|" + "|---:|---:|" * len(run_ids))

        difficulty_order = ["easy", "beginner", "intermediate", "medium", "advanced", "hard"]
        for diff in difficulty_order:
            if diff not in difficulty_groups:
                continue

            run_data = difficulty_groups[diff]
            n = len(next(iter(run_data.values())))

            row = f"| {diff} | {n} |"
            for run_id in run_ids:
                scores = run_data.get(run_id, [])
                if scores:
                    with_avg = avg([s["with_docs"] for s in scores])
                    without_avg = avg([s["without_docs"] for s in scores])
                    delta = round(with_avg - without_avg, 1)
                    row += f" {with_avg} | {fmt_delta(delta)} |"
                else:
                    row += " — | — |"

            lines.append(row)

        lines += [""]

    # Head-to-Head (WITH docs, common questions)
    lines += [
        "## Head-to-Head (WITH docs, common questions)",
        "| Winner | Count | % |",
        "|---|---:|---:|",
    ]

    winner_counts = defaultdict(int)
    for qid in common_questions:
        question_scores = {}
        for run_id in run_ids:
            for s in all_run_scores[run_id]:
                if s["question_id"] == qid:
                    question_scores[run_id] = s["with_docs"]
                    break

        if question_scores:
            max_score = max(question_scores.values())
            winners = [rid for rid, score in question_scores.items() if score == max_score]

            if len(winners) == 1:
                winner_counts[winners[0]] += 1
            else:
                winner_counts["tie"] += 1

    total_questions = len(common_questions)
    for run_id in run_ids:
        count = winner_counts.get(run_id, 0)
        pct = round(100 * count / total_questions) if total_questions > 0 else 0
        lines.append(f"| **{run_id}** | {count} | {pct}% |")

    tie_count = winner_counts.get("tie", 0)
    tie_pct = round(100 * tie_count / total_questions) if total_questions > 0 else 0
    lines.append(f"| tie | {tie_count} | {tie_pct}% |")

    lines += [""]

    # Doc Retrieval Benefit — Delta Comparison
    lines += [
        "## Doc Retrieval Benefit — Delta Comparison",
        "_Which model benefits more from documentation context?_",
        "",
        "| Run | Avg Delta | Questions docs helped | Questions docs hurt |",
        "|---|---:|---:|---:|",
    ]

    for run_id in run_ids:
        stats = summary_stats[run_id]
        helped = stats["improved"]
        hurt = stats["degraded"]
        n = stats["n"]
        helped_pct = round(100 * helped / n) if n > 0 else 0
        hurt_pct = round(100 * hurt / n) if n > 0 else 0

        lines.append(
            f'| **{run_id}** | **{fmt_delta(stats["delta_avg"])}** | '
            f'{helped} ({helped_pct}%) | {hurt} ({hurt_pct}%) |'
        )

    lines += [""]

    # Model Ranking
    lines += [
        "## Model Ranking",
        "",
        "### By absolute quality (WITH docs)",
        "| Rank | Run | WITH docs avg |",
        "|---:|---|---:|",
    ]

    sorted_by_quality = sorted(summary_stats.items(), key=lambda x: x[1]["with_avg"], reverse=True)
    for rank, (run_id, stats) in enumerate(sorted_by_quality, 1):
        lines.append(f"| {rank} | **{run_id}** | {stats['with_avg']} |")

    lines += [
        "",
        "### By retrieval utilisation (Delta)",
        "| Rank | Run | Delta |",
        "|---:|---|---:|",
    ]

    sorted_by_delta = sorted(summary_stats.items(), key=lambda x: x[1]["delta_avg"], reverse=True)
    for rank, (run_id, stats) in enumerate(sorted_by_delta, 1):
        lines.append(f"| {rank} | **{run_id}** | {fmt_delta(stats['delta_avg'])} |")

    lines += [""]

    return lines


def main():
    parser = argparse.ArgumentParser(description="Compare multiple model runs")
    parser.add_argument("--regular-runs", nargs="+", help="Paths to regular questions judged JSON files")
    parser.add_argument("--golden-runs", nargs="+", help="Paths to golden questions judged JSON files")
    parser.add_argument("--run-ids", required=True, help="Comma-separated run IDs (e.g., sonnet46,opus48)")
    parser.add_argument("--out", required=True, help="Output markdown file path")

    args = parser.parse_args()

    # Validate: at least one of regular-runs or golden-runs must be provided
    if not args.regular_runs and not args.golden_runs:
        print("Error: Must provide at least --regular-runs or --golden-runs")
        return 1

    run_ids = [rid.strip() for rid in args.run_ids.split(",")]

    # Validate run counts
    if args.regular_runs and len(args.regular_runs) != len(run_ids):
        print(f"Error: Number of regular runs ({len(args.regular_runs)}) must match number of run IDs ({len(run_ids)})")
        return 1

    if args.golden_runs and len(args.golden_runs) != len(run_ids):
        print(f"Error: Number of golden runs ({len(args.golden_runs)}) must match number of run IDs ({len(run_ids)})")
        return 1

    # Load regular runs if provided
    regular_runs = []
    if args.regular_runs:
        for run_id, run_path in zip(run_ids, args.regular_runs):
            print(f"Loading {run_id} (regular): {run_path}")
            run_data = load_run(run_path)
            regular_runs.append((run_id, run_data))

    # Load golden runs if provided
    golden_runs = []
    if args.golden_runs:
        for run_id, run_path in zip(run_ids, args.golden_runs):
            print(f"Loading {run_id} (golden): {run_path}")
            run_data = load_run(run_path)
            golden_runs.append((run_id, run_data))

    # Generate combined report
    generate_combined_report(regular_runs, golden_runs, run_ids, args.out)

    return 0


if __name__ == "__main__":
    exit(main())

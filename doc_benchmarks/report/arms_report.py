"""Render an N-arm treatment comparison as Markdown."""

from typing import Any, Dict, List


def render_arms_report(data: Dict[str, Any]) -> str:
    """Render the artifact produced by ``ArmRunner.build_output`` as Markdown."""
    lines: List[str] = []
    lib = data.get("library_name", "?")
    arms = data.get("arms", [])
    baseline = data.get("baseline_arm", "baseline")

    lines.append(f"# Treatment-arm comparison — {lib}")
    lines.append("")
    lines.append(f"- Model: `{data.get('provider', '?')}/{data.get('model', '?')}`")
    lines.append(f"- Arms: {', '.join(f'`{a}`' for a in arms)}")
    lines.append(f"- Baseline arm: `{baseline}`")
    lines.append(f"- Questions: {data.get('total_questions', 0)}")
    lines.append("")

    summary = data.get("summary")
    if summary and summary.get("per_arm"):
        lines.append("## Summary (avg aggregate score, 0–100)")
        lines.append("")
        lines.append("| Arm | Avg | Δ vs baseline | n |")
        lines.append("| --- | ---: | ---: | ---: |")
        for arm in arms:
            stats = summary["per_arm"].get(arm, {})
            avg = stats.get("avg_aggregate")
            delta = stats.get("delta_vs_baseline")
            avg_s = "—" if avg is None else f"{avg:.1f}"
            if arm == baseline:
                delta_s = "(baseline)"
            elif delta is None:
                delta_s = "—"
            else:
                delta_s = f"{delta:+.1f}"
            lines.append(f"| `{arm}` | {avg_s} | {delta_s} | {stats.get('n', 0)} |")
        lines.append("")
    else:
        lines.append("_No evaluations available (answers were not judged)._")
        lines.append("")

    evaluations = data.get("evaluations")
    if evaluations:
        lines.append("## Per-question scores")
        lines.append("")
        header = "| Question | " + " | ".join(f"`{a}`" for a in arms) + " |"
        sep = "| --- | " + " | ".join("---:" for _ in arms) + " |"
        lines.append(header)
        lines.append(sep)
        for ev in evaluations:
            q = ev.get("question_text", "")
            q_short = (q[:60] + "…") if len(q) > 60 else q
            cells = []
            for arm in arms:
                s = ev.get("scores", {}).get(arm)
                if isinstance(s, dict) and isinstance(s.get("aggregate"), (int, float)):
                    cells.append(f"{s['aggregate']:.0f}")
                else:
                    cells.append("—")
            lines.append(f"| {q_short} | " + " | ".join(cells) + " |")
        lines.append("")

    return "\n".join(lines)

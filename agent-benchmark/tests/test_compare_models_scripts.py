"""Tests for multi-model comparison scripts."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import compare_models
from scripts import compare_models_combined


def _run(question_ids):
    evaluations = []
    for idx, qid in enumerate(question_ids, start=1):
        evaluations.append(
            {
                "question_id": qid,
                "question_text": f"Question {qid}",
                "difficulty": "medium",
                "scores": {
                    "baseline": {"aggregate": 50 + idx},
                    "skill:dpnp": {"aggregate": 60 + idx},
                },
            }
        )
    return {
        "model": "m",
        "provider": "p",
        "baseline_arm": "baseline",
        "evaluations": evaluations,
    }


def test_extract_scores_skips_invalid_arm_shapes():
    assert compare_models.extract_scores({"evaluations": []}) == []
    assert compare_models.extract_scores({"baseline_arm": 123, "evaluations": []}) == []
    assert (
        compare_models.extract_scores(
            {
                "baseline_arm": "baseline",
                "evaluations": [{"question_id": "q1", "scores": {"skill": {"aggregate": 1}}}],
            }
        )
        == []
    )


def test_generate_section_report_uses_common_questions_and_context_labels():
    lines = compare_models.generate_section_report(
        [("run-a", _run(["q1", "q2"])), ("run-b", _run(["q1"]))],
        ["run-a", "run-b"],
        "Regular",
    )
    text = "\n".join(lines)

    assert "Common questions evaluated: **1**" in text
    assert "| **run-a** | 1 |" in text
    assert "## Context-Arm Benefit — Delta Comparison" in text
    assert "Delta Comparison" in text
    assert "Baseline vs treatment" not in text


def test_load_run_reports_missing_file():
    with pytest.raises(SystemExit, match="File not found"):
        compare_models.load_run("does-not-exist.json")


def test_combined_runner_uses_absolute_script_and_typed_run_flag(monkeypatch, tmp_path):
    out = tmp_path / "sub.md"
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        out.write_text("## Models Compared\nbody", encoding="utf-8")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(compare_models_combined.subprocess, "run", fake_run)

    content = compare_models_combined.run_compare_models(["a.json"], "a", out, "golden")

    assert content.startswith("## Models Compared")
    assert captured["cmd"][1] == str(compare_models_combined.COMPARE_MODELS_SCRIPT)
    assert Path(captured["cmd"][1]).is_absolute()
    assert "--golden-runs" in captured["cmd"]
    assert "--runs" not in captured["cmd"]


def test_combined_runner_raises_on_subprocess_failure(monkeypatch, tmp_path):
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=2, stderr="bad args")

    monkeypatch.setattr(compare_models_combined.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="exit code 2"):
        compare_models_combined.run_compare_models(["a.json"], "a", tmp_path / "out.md", "regular")


# ---------------------------------------------------------------------------
# check_run_consistency
# ---------------------------------------------------------------------------

def _make_run(run_id, *, baseline_arm="baseline", model="model-a", provider="prov", q_hash=None):
    data = {"baseline_arm": baseline_arm, "model": model, "provider": provider}
    if q_hash is not None:
        data["question_set_hash"] = q_hash
    return (run_id, data)


def test_consistency_ok_different_models():
    runs = [
        _make_run("run-a", model="model-a"),
        _make_run("run-b", model="model-b"),
    ]
    warnings = compare_models.check_run_consistency(runs, "regular")
    assert warnings == []


def test_consistency_baseline_mismatch_raises():
    runs = [
        _make_run("run-a", baseline_arm="no-context"),
        _make_run("run-b", baseline_arm="baseline"),
    ]
    with pytest.raises(SystemExit, match="different baseline_arm"):
        compare_models.check_run_consistency(runs, "regular")


def test_consistency_hash_mismatch_warns():
    runs = [
        _make_run("run-a", model="model-a", q_hash="aaaa1111"),
        _make_run("run-b", model="model-b", q_hash="bbbb2222"),
    ]
    warnings = compare_models.check_run_consistency(runs, "golden")
    assert any("question_set_hash" in w for w in warnings)


def test_consistency_identical_models_warns():
    runs = [
        _make_run("run-a", model="same-model", provider="prov"),
        _make_run("run-b", model="same-model", provider="prov"),
    ]
    warnings = compare_models.check_run_consistency(runs, "regular")
    assert any("same model" in w for w in warnings)


def test_consistency_single_run_no_warnings():
    runs = [_make_run("run-a")]
    assert compare_models.check_run_consistency(runs, "regular") == []


# ---------------------------------------------------------------------------
# extract_scores: treatment arm selection
# ---------------------------------------------------------------------------

def _make_run_data(arms, baseline="baseline", q_hash=None):
    """Build a minimal arms JSON with the new 'evaluations' format."""
    evaluations = [
        {
            "question_id": "Q1",
            "question_text": "test?",
            "category": "c",
            "difficulty": "easy",
            "persona": "user",
            "scores": {
                arm: {"aggregate": score} for arm, score in arms.items()
            },
        }
    ]
    data = {"baseline_arm": baseline, "evaluations": evaluations}
    if q_hash:
        data["question_set_hash"] = q_hash
    return data


def test_extract_scores_auto_selects_single_treatment():
    data = _make_run_data({"baseline": 60, "with-docs": 80})
    scores = compare_models.extract_scores(data)
    assert len(scores) == 1
    assert scores[0]["treatment_arm"] == "with-docs"
    assert scores[0]["with_docs"] == 80
    assert scores[0]["without_docs"] == 60


def test_extract_scores_force_treatment_arm():
    data = _make_run_data({"baseline": 60, "arm-a": 70, "arm-b": 80})
    scores = compare_models.extract_scores(data, force_treatment_arm="arm-b")
    assert scores[0]["treatment_arm"] == "arm-b"
    assert scores[0]["with_docs"] == 80


def test_extract_scores_ambiguous_raises_without_force():
    data = _make_run_data({"baseline": 60, "arm-a": 70, "arm-b": 80})
    with pytest.raises(SystemExit, match="multiple non-baseline arms"):
        compare_models.extract_scores(data)


def test_extract_scores_force_arm_missing_raises():
    data = _make_run_data({"baseline": 60, "arm-a": 70})
    with pytest.raises(SystemExit, match="not found"):
        compare_models.extract_scores(data, force_treatment_arm="nonexistent")

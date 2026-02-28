"""Tests for JudgePanel multi-evaluator."""
import json
from unittest.mock import patch

import pytest

from doc_benchmarks.eval.panel import (
    DEFAULT_PANEL,
    JudgeConfig,
    JudgePanel,
    JudgeVote,
    PanelVerdict,
    _verdict_to_dict,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _llm_response(aggregate=80, correctness=80, completeness=80,
                  specificity=80, code_quality=80, actionability=80):
    return json.dumps({
        "correctness": correctness,
        "completeness": completeness,
        "specificity": specificity,
        "code_quality": code_quality,
        "actionability": actionability,
        "aggregate": aggregate,
        "reasoning": "test reasoning",
    })


def _patch_llm(responses):
    """Patch llm_call to return responses in sequence."""
    it = iter(responses)
    return patch("doc_benchmarks.eval.panel.llm_call", side_effect=lambda *a, **kw: next(it))


# ── JudgePanel._call_judge ────────────────────────────────────────────────────

def test_call_judge_success():
    cfg = JudgeConfig(role="technical_expert", model="gpt-4o-mini", provider="openai")
    panel = JudgePanel(judges=[cfg])
    with _patch_llm([_llm_response(aggregate=85)]):
        vote = panel._call_judge(cfg, "Q?", "A.", "oneTBB", "ctx")
    assert vote.aggregate == 85.0
    assert vote.error is None
    assert vote.role == "technical_expert"


def test_call_judge_strips_markdown():
    cfg = JudgeConfig(role="technical_expert", model="gpt-4o-mini", provider="openai")
    panel = JudgePanel(judges=[cfg])
    raw = "```json\n" + _llm_response(aggregate=70) + "\n```"
    with _patch_llm([raw]):
        vote = panel._call_judge(cfg, "Q?", "A.", "oneTBB", "")
    assert vote.aggregate == 70.0


def test_call_judge_llm_error():
    cfg = JudgeConfig(role="technical_expert", model="gpt-4o-mini", provider="openai")
    panel = JudgePanel(judges=[cfg])
    with patch("doc_benchmarks.eval.panel.llm_call", side_effect=RuntimeError("boom")):
        vote = panel._call_judge(cfg, "Q?", "A.", "oneTBB", "")
    assert vote.aggregate is None
    assert vote.error is not None


def test_call_judge_bad_json():
    cfg = JudgeConfig(role="technical_expert", model="gpt-4o-mini", provider="openai")
    panel = JudgePanel(judges=[cfg])
    with _patch_llm(["not json"]):
        vote = panel._call_judge(cfg, "Q?", "A.", "oneTBB", "")
    assert vote.error is not None


# ── JudgePanel._aggregate ─────────────────────────────────────────────────────

def test_aggregate_mean_and_std():
    votes = [
        JudgeVote("technical_expert", "m", "p", {"aggregate": 80}, "r"),
        JudgeVote("developer_advocate", "m", "p", {"aggregate": 60}, "r"),
        JudgeVote("doc_reviewer", "m", "p", {"aggregate": 70}, "r"),
    ]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.mean_aggregate == 70.0
    assert verdict.std_aggregate is not None
    assert 0 <= verdict.agreement_score <= 1


def test_aggregate_perfect_agreement():
    votes = [
        JudgeVote("technical_expert", "m", "p", {"aggregate": 75}, "r"),
        JudgeVote("developer_advocate", "m", "p", {"aggregate": 75}, "r"),
    ]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.std_aggregate == 0.0
    assert verdict.agreement_score == 1.0
    assert not verdict.disagreement_flag


def test_aggregate_high_disagreement():
    votes = [
        JudgeVote("technical_expert", "m", "p", {"aggregate": 20}, "r"),
        JudgeVote("developer_advocate", "m", "p", {"aggregate": 90}, "r"),
    ]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.disagreement_flag  # std > 15


def test_aggregate_all_errors():
    votes = [
        JudgeVote("technical_expert", "m", "p", {}, "", error="boom"),
        JudgeVote("developer_advocate", "m", "p", {}, "", error="boom"),
    ]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.mean_aggregate is None
    assert verdict.agreement_score is None


def test_aggregate_single_vote():
    votes = [JudgeVote("technical_expert", "m", "p", {"aggregate": 80}, "r")]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.mean_aggregate == 80.0
    assert verdict.std_aggregate == 0.0


def test_aggregate_dimensions():
    votes = [
        JudgeVote("a", "m", "p", {"aggregate": 80, "correctness": 90, "completeness": 70}, "r"),
        JudgeVote("b", "m", "p", {"aggregate": 60, "correctness": 50, "completeness": 70}, "r"),
    ]
    panel = JudgePanel()
    verdict = panel._aggregate(votes)
    assert verdict.mean_dimensions["correctness"] == 70.0
    assert verdict.mean_dimensions["completeness"] == 70.0


# ── JudgePanel.evaluate ───────────────────────────────────────────────────────

def test_evaluate_full_panel():
    judges = [
        JudgeConfig("technical_expert", "gpt-4o-mini", "openai"),
        JudgeConfig("developer_advocate", "gpt-4o-mini", "openai"),
        JudgeConfig("doc_reviewer", "gpt-4o-mini", "openai"),
    ]
    panel = JudgePanel(judges=judges, concurrency=3)
    responses = [_llm_response(aggregate=80), _llm_response(aggregate=75), _llm_response(aggregate=85)]
    with _patch_llm(responses):
        verdict = panel.evaluate("Q?", "A.", "oneTBB", "ctx")
    assert verdict.mean_aggregate == 80.0
    assert len(verdict.votes) == 3
    assert len(verdict.valid_votes) == 3


def test_evaluate_partial_failure():
    judges = [
        JudgeConfig("technical_expert", "gpt-4o-mini", "openai"),
        JudgeConfig("developer_advocate", "gpt-4o-mini", "openai"),
    ]
    panel = JudgePanel(judges=judges, concurrency=2)
    it = iter([_llm_response(aggregate=80), "bad json"])
    with patch("doc_benchmarks.eval.panel.llm_call", side_effect=lambda *a, **kw: next(it)):
        verdict = panel.evaluate("Q?", "A.", "oneTBB", "")
    assert len(verdict.valid_votes) == 1
    assert verdict.mean_aggregate == 80.0


# ── DEFAULT_PANEL & roles ─────────────────────────────────────────────────────

def test_default_panel_has_three_roles():
    assert len(DEFAULT_PANEL) == 3
    assert "technical_expert" in DEFAULT_PANEL
    assert "developer_advocate" in DEFAULT_PANEL
    assert "doc_reviewer" in DEFAULT_PANEL


def test_default_judges_created_without_config():
    panel = JudgePanel(default_model="gpt-4o-mini", default_provider="openai")
    assert len(panel.judges) == 3
    roles = {j.role for j in panel.judges}
    assert roles == set(DEFAULT_PANEL)


# ── _verdict_to_dict ──────────────────────────────────────────────────────────

def test_verdict_to_dict_none():
    assert _verdict_to_dict(None) is None


def test_verdict_to_dict_structure():
    votes = [JudgeVote("technical_expert", "m", "p", {"aggregate": 80}, "reason")]
    verdict = PanelVerdict(votes=votes, mean_aggregate=80.0, std_aggregate=0.0,
                           agreement_score=1.0, mean_dimensions={"correctness": 80.0})
    d = _verdict_to_dict(verdict)
    assert d["aggregate"] == 80.0
    assert d["agreement_score"] == 1.0
    assert not d["disagreement_flag"]
    assert len(d["votes"]) == 1
    assert d["votes"][0]["role"] == "technical_expert"

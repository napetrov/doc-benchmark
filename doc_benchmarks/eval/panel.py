"""Multi-evaluator (LLM Judge Panel) for doc-benchmark.

Runs N judges with different roles in parallel and computes:
- Per-judge scores
- Mean aggregate score across judges
- Standard deviation (spread)
- Inter-rater agreement score (1 - normalized_std, 0-1)

Each judge role weights dimensions differently, ensuring genuine diversity:
- technical_expert:    correctness × 2, specificity × 1.5
- developer_advocate:  actionability × 2, code_quality × 1.5
- doc_reviewer:        completeness × 2, specificity × 1.5
"""

from __future__ import annotations

import json
import logging
import math
import os
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from doc_benchmarks.llm import llm_call

logger = logging.getLogger(__name__)

# ── Judge role prompts ────────────────────────────────────────────────────────

# Use string Template to avoid .format() conflicts with user content
_ROLE_INTROS: Dict[str, str] = {
    "technical_expert": (
        "You are a STRICT TECHNICAL EXPERT evaluating documentation answers. "
        "Your primary concern is FACTUAL ACCURACY and TECHNICAL DEPTH. "
        "Penalize vague, hand-wavy, or technically wrong answers heavily — "
        "even if they sound helpful. A wrong answer scores < 40 on correctness "
        "regardless of how well-written it is."
    ),
    "developer_advocate": (
        "You are a DEVELOPER ADVOCATE evaluating documentation answers. "
        "Your primary concern is PRACTICAL USEFULNESS: would a developer be "
        "unblocked by this answer right now? Prioritize working code examples "
        "and clear actionable steps. A theoretically correct but hard-to-apply "
        "answer scores < 50 on actionability."
    ),
    "doc_reviewer": (
        "You are a DOCUMENTATION QUALITY REVIEWER. "
        "Your primary concern is COMPLETENESS and FIDELITY TO THE DOCS. "
        "Check whether the answer covers all aspects of the question and stays "
        "within the scope of the provided context. An answer that ignores key "
        "parts of the question scores < 40 on completeness."
    ),
}

_WEIGHTED_AGGREGATE: Dict[str, str] = {
    "technical_expert": (
        "Compute aggregate as: (correctness×2 + completeness + specificity×1.5 + "
        "code_quality + actionability) / 6.5, rounded to nearest integer."
    ),
    "developer_advocate": (
        "Compute aggregate as: (correctness + completeness + specificity + "
        "code_quality×1.5 + actionability×2) / 6.5, rounded to nearest integer."
    ),
    "doc_reviewer": (
        "Compute aggregate as: (correctness + completeness×2 + specificity×1.5 + "
        "code_quality + actionability) / 6.5, rounded to nearest integer."
    ),
}

_CRITERIA = """
Rate each dimension 0-100:
1. correctness   — Is the answer factually accurate?
2. completeness  — Does it fully address all parts of the question?
3. specificity   — Is it specific to THIS library (not generic advice)?
4. code_quality  — If code is included: is it correct, runnable, idiomatic?
5. actionability — Can the user directly apply this to their problem?

{weighted_aggregate}

Output ONLY a JSON object. No markdown, no explanation:
{json_schema}
"""

_JSON_SCHEMA = ('{"correctness": 0-100, "completeness": 0-100, "specificity": 0-100, '
                '"code_quality": 0-100, "actionability": 0-100, "aggregate": 0-100, '
                '"reasoning": "one sentence explaining the main strength or weakness"}')

JUDGE_ROLES: Dict[str, str] = {
    role: (
        _ROLE_INTROS[role] + "\n\n"
        "Library: __LIBRARY__\n"
        "Question: __QUESTION__\n"
        "Answer: __ANSWER__\n"
        "Context (from docs): __CONTEXT__\n"
        + _CRITERIA.format(
            weighted_aggregate=_WEIGHTED_AGGREGATE[role],
            json_schema=_JSON_SCHEMA,
        )
    )
    for role in _ROLE_INTROS
}

DEFAULT_PANEL = ["technical_expert", "developer_advocate", "doc_reviewer"]

SCORE_FIELDS = ("correctness", "completeness", "specificity", "code_quality", "actionability", "aggregate")


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class JudgeVote:
    role: str
    model: str
    provider: str
    scores: Dict[str, float]
    reasoning: str
    error: Optional[str] = None

    @property
    def aggregate(self) -> Optional[float]:
        return self.scores.get("aggregate") if not self.error else None


@dataclass
class PanelVerdict:
    """Aggregated verdict from all judges."""
    votes: List[JudgeVote]
    mean_aggregate: Optional[float]
    std_aggregate: Optional[float]
    agreement_score: Optional[float]   # 0–1; 1.0 = perfect agreement
    mean_dimensions: Dict[str, float] = field(default_factory=dict)

    @property
    def valid_votes(self) -> List[JudgeVote]:
        return [v for v in self.votes if v.aggregate is not None]

    @property
    def disagreement_flag(self) -> bool:
        """True when judges disagree significantly (std > 15 points)."""
        return self.std_aggregate is not None and self.std_aggregate > 15.0


@dataclass
class JudgeConfig:
    role: str
    model: str
    provider: str


# ── Panel ─────────────────────────────────────────────────────────────────────

class JudgePanel:
    """Run multiple LLM judges in parallel and aggregate their verdicts."""

    def __init__(
        self,
        judges: Optional[List[JudgeConfig]] = None,
        default_model: str = "gpt-4o-mini",
        default_provider: str = "openai",
        concurrency: int = 6,
    ):
        self.judges = judges or [
            JudgeConfig(role=role, model=default_model, provider=default_provider)
            for role in DEFAULT_PANEL
        ]
        self.concurrency = concurrency

    def _build_prompt(self, role: str, question: str, answer: str,
                      library_name: str, context: str) -> str:
        template = JUDGE_ROLES.get(role, JUDGE_ROLES["technical_expert"])
        return (
            template
            .replace("__LIBRARY__", library_name)
            .replace("__QUESTION__", question)
            .replace("__ANSWER__", answer)
            .replace("__CONTEXT__", context or "(No documentation provided)")
        )

    def _call_judge(
        self,
        config: JudgeConfig,
        question: str,
        answer: str,
        library_name: str,
        context: str,
    ) -> JudgeVote:
        prompt = self._build_prompt(config.role, question, answer, library_name, context)
        try:
            raw = llm_call(prompt, model=config.model, provider=config.provider)
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            scores = {}
            for k in SCORE_FIELDS:
                if k in data:
                    val = float(data[k])
                    # Clamp to valid range
                    scores[k] = max(0.0, min(100.0, val))
            return JudgeVote(
                role=config.role,
                model=config.model,
                provider=config.provider,
                scores=scores,
                reasoning=str(data.get("reasoning", "")),
            )
        except Exception as exc:
            logger.warning(f"Judge '{config.role}' ({config.model}) failed: {exc}")
            return JudgeVote(
                role=config.role,
                model=config.model,
                provider=config.provider,
                scores={},
                reasoning="",
                error=str(exc),
            )

    def evaluate(
        self,
        question: str,
        answer: str,
        library_name: str,
        context: str = "",
    ) -> PanelVerdict:
        """Run all judges concurrently and return aggregated verdict."""
        votes: List[JudgeVote] = []
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(self._call_judge, cfg, question, answer, library_name, context): cfg
                for cfg in self.judges
            }
            for future in as_completed(futures):
                votes.append(future.result())
        return self._aggregate(votes)

    def _aggregate(self, votes: List[JudgeVote]) -> PanelVerdict:
        valid = [v for v in votes if v.aggregate is not None]
        if not valid:
            return PanelVerdict(votes=votes, mean_aggregate=None,
                                std_aggregate=None, agreement_score=None)

        aggs = [v.aggregate for v in valid]
        mean_agg = round(statistics.mean(aggs), 1)
        std_agg = round(statistics.stdev(aggs), 1) if len(aggs) > 1 else 0.0
        agreement = round(max(0.0, 1.0 - std_agg / 50.0), 3)

        dims = ("correctness", "completeness", "specificity", "code_quality", "actionability")
        mean_dims: Dict[str, float] = {}
        for dim in dims:
            vals = [v.scores[dim] for v in valid if dim in v.scores]
            if vals:
                mean_dims[dim] = round(statistics.mean(vals), 1)

        return PanelVerdict(
            votes=votes,
            mean_aggregate=mean_agg,
            std_aggregate=std_agg,
            agreement_score=agreement,
            mean_dimensions=mean_dims,
        )

    def evaluate_answers(
        self,
        answers: List[Dict[str, Any]],
        library_name: str,
        output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate a full answers list with panel scoring."""
        results = []
        n = len(answers)

        for i, answer in enumerate(answers, 1):
            q_id = answer.get("question_id", f"q{i}")
            question = answer.get("question", "")
            print(f"[{i}/{n}] Panel: {q_id}…", flush=True)

            with_verdict = self._score_answer_entry(answer.get("with_docs"), question, library_name)
            without_verdict = self._score_answer_entry(answer.get("without_docs"), question, library_name)

            delta = None
            if (with_verdict and with_verdict.mean_aggregate is not None
                    and without_verdict and without_verdict.mean_aggregate is not None):
                delta = round(with_verdict.mean_aggregate - without_verdict.mean_aggregate, 1)

            result = {
                "question_id": q_id,
                "question": question,
                "panel_size": len(self.judges),
                "with_docs": _verdict_to_dict(with_verdict),
                "without_docs": _verdict_to_dict(without_verdict),
                "delta": delta,
            }
            results.append(result)

            if output_path:
                _save_incremental(results, output_path, library_name, self)

        return results

    def _score_answer_entry(
        self,
        ans_data: Optional[Dict[str, Any]],
        question: str,
        library_name: str,
    ) -> Optional[PanelVerdict]:
        if not ans_data or not ans_data.get("answer"):
            return None
        ctx = "\n".join(d.get("content", "") for d in ans_data.get("retrieved_docs", []))
        return self.evaluate(question, ans_data["answer"], library_name, ctx)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verdict_to_dict(v: Optional[PanelVerdict]) -> Optional[Dict[str, Any]]:
    if v is None:
        return None
    return {
        "aggregate": v.mean_aggregate,
        "std": v.std_aggregate,
        "agreement_score": v.agreement_score,
        "disagreement_flag": v.disagreement_flag,
        "dimensions": v.mean_dimensions,
        "votes": [
            {
                "role": vote.role,
                "model": vote.model,
                "aggregate": vote.aggregate,
                "scores": vote.scores,
                "reasoning": vote.reasoning,
                "error": vote.error,
            }
            for vote in v.votes
        ],
    }


def _save_incremental(results: List[Dict], path: Path, library_name: str, panel: JudgePanel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    output = {
        "evaluated_at": _timestamp(),
        "judge_model": f"panel({len(panel.judges)})",
        "library_name": library_name,
        "total_evaluations": len(results),
        "evaluations": results,
    }
    with open(tmp, "w") as f:
        json.dump(output, f, indent=2)
    os.replace(tmp, path)


def _timestamp() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

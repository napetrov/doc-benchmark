#!/usr/bin/env python3
"""CLI for doc-benchmark: thin compatibility shim.

The implementation now lives in the ``doc_benchmarks`` package. This module
keeps ``python cli.py ...`` working and re-exports the public names that were
historically importable from ``cli``.
"""

from __future__ import annotations

from doc_benchmarks.cli import build_parser, main

# Re-export command functions and helpers for backward compatibility.
from doc_benchmarks.commands.run import cmd_run, cmd_compare
from doc_benchmarks.commands.orchestrate import cmd_evaluate
from doc_benchmarks.commands.baseline import (
    BASELINES_DIR,
    cmd_baseline_save,
    cmd_baseline_list,
    cmd_baseline_compare,
    _baseline_manifest,
    _save_manifest,
    _compute_summary,
)
from doc_benchmarks.commands.report import (
    cmd_report,
    cmd_report_eval,
    cmd_report_generate,
)
from doc_benchmarks.commands.personas import (
    cmd_personas_discover,
    cmd_personas_approve,
)
from doc_benchmarks.commands.questions import (
    cmd_questions_generate,
    cmd_questions_analyze,
    cmd_questions_refine,
    cmd_questions_panel_review,
)
from doc_benchmarks.commands.answers import cmd_answers_generate
from doc_benchmarks.commands.evaluate import (
    cmd_eval_score,
    cmd_eval_ragas,
    cmd_eval_panel_score,
    _run_ragas_eval,
    _warn_judge_independence,
)
from doc_benchmarks.commands.library import (
    cmd_library_list,
    cmd_library_show,
    _load_registry,
)
from doc_benchmarks.commands.benchmark import (
    cmd_benchmark_run,
    cmd_benchmark_batch,
    _run_single_library,
)
from doc_benchmarks.commands.dashboard import cmd_dashboard_generate
from doc_benchmarks.commands.arms import cmd_arms_run

if __name__ == "__main__":
    main()

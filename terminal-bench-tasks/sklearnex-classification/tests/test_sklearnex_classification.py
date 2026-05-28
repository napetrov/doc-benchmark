#!/usr/bin/env python3
"""Verifier for sklearnex-classification."""
import re
import subprocess
from pathlib import Path

SOLUTION = Path("/app/solution.py")
REFERENCE = Path("/app/reference.py")
TIMEOUT_SEC = 100.0
KEYWORDS = ["sklearnex", "patch_sklearn"]


def _run(script):
    result = subprocess.run(
        ["python3", str(script)], capture_output=True, text=True, timeout=TIMEOUT_SEC
    )
    assert result.returncode == 0, (
        f"{script} exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "VALID" in result.stdout, f"expected VALID in stdout, got {result.stdout!r}"
    return result.stdout


def _acc(text):
    m = re.search(r"acc=([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text)
    assert m, f"no acc=<value> found in {text!r}"
    return float(m.group(1))


def test_files_exist():
    assert SOLUTION.exists(), f"{SOLUTION} not found; create the sklearnex solution"
    assert REFERENCE.exists(), f"{REFERENCE} not found; stock reference is required"


def test_solution_uses_sklearnex():
    text = SOLUTION.read_text(errors="replace")
    missing = [kw for kw in KEYWORDS if kw not in text]
    assert not missing, f"missing required sklearnex markers {missing} in {SOLUTION}"


def test_accuracy_matches_reference():
    ref_acc = _acc(_run(REFERENCE))
    sol_acc = _acc(_run(SOLUTION))
    assert sol_acc >= 0.60, f"accuracy {sol_acc} unexpectedly low"
    assert sol_acc >= ref_acc - 0.02, (
        f"sklearnex accuracy {sol_acc} is more than 0.02 below stock reference {ref_acc}"
    )

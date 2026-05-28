#!/usr/bin/env python3
"""Verifier for oneccl-allreduce: multi-rank sum allreduce."""
import os
import re
import subprocess
from pathlib import Path

BINARY = Path("/app/ccl_allreduce")
TARGET_SOURCE = Path("/app/ccl_allreduce.cpp")
RANKS = 4
KEYWORDS = ["oneapi/ccl.hpp", "allreduce"]
TIMEOUT_SEC = 90.0


def _run_mpi():
    cmd = ["mpirun", "-n", str(RANKS), str(BINARY)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SEC)
    assert result.returncode == 0, (
        f"{cmd} exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "VALID" in result.stdout, f"expected VALID in stdout, got {result.stdout!r}"
    return result.stdout


def _field(text, name):
    m = re.search(name + r"=([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text)
    assert m, f"no {name}=<value> found in {text!r}"
    return float(m.group(1))


def test_binary_exists():
    assert BINARY.exists(), f"{BINARY} not found; compile the oneCCL binary"
    assert os.access(BINARY, os.X_OK), f"{BINARY} is not executable"


def test_allreduce_result():
    out = _run_mpi()
    expected = RANKS * (RANKS + 1) / 2.0
    assert _field(out, "value") == expected, f"allreduce value != {expected}"
    assert _field(out, "expected") == expected, "reported expected value is wrong"


def test_source_uses_required_ccl_api():
    assert TARGET_SOURCE.exists(), f"{TARGET_SOURCE} not found"
    text = TARGET_SOURCE.read_text(errors="replace")
    missing = [kw for kw in KEYWORDS if kw not in text]
    assert not missing, f"missing required oneCCL markers {missing} in {TARGET_SOURCE}"

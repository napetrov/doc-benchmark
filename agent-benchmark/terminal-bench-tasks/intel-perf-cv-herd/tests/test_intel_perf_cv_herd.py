#!/usr/bin/env python3
import os
import re
import subprocess
import time
from pathlib import Path

BINARY = Path("/app/herd_fixed")
SOURCE = Path("/app/herd_fixed.cpp")
TIMEOUT = 60.0


def _run(workers, njobs):
    cmd = [str(BINARY), str(workers), str(njobs)]
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, f"{cmd} exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    pm = re.search(r"processed=(\d+)", result.stdout)
    cm = re.search(r"checksum=(\d+)", result.stdout)
    assert pm and cm, f"missing processed/checksum in {result.stdout!r}"
    return int(pm.group(1)), int(cm.group(1)), elapsed


def test_binary_exists():
    assert SOURCE.exists(), "write /app/herd_fixed.cpp"
    assert BINARY.exists(), "compile /app/herd_fixed"
    assert os.access(BINARY, os.X_OK), "/app/herd_fixed is not executable"


def test_every_job_processed_exactly_once():
    # exact job accounting at several worker counts; run a few times each to
    # catch lost or duplicate wakeups
    for workers, njobs in [(4, 150000), (16, 150000), (64, 80000)]:
        expected_sum = njobs * (njobs + 1) // 2
        for _ in range(2):
            processed, checksum, _ = _run(workers, njobs)
            assert processed == njobs, f"processed={processed} expected={njobs} (workers={workers})"
            assert checksum == expected_sum, f"checksum={checksum} expected={expected_sum} (workers={workers})"


def test_terminates_no_deadlock():
    # large pool must still drain and terminate well within the limit
    _, _, elapsed = _run(64, 100000)
    assert elapsed < 30.0, f"run took {elapsed:.1f}s; possible deadlock or lost wakeup"


def test_source_reduces_per_job_wakeups():
    text = SOURCE.read_text(errors="replace")
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    src = re.sub(r"//.*", "", no_block)
    assert re.search(r"notify_one\b", src), "wake a single worker per job with notify_one"
    # at most one notify_all is acceptable (shutdown); a per-job notify_all is the bug
    notify_all_count = len(re.findall(r"notify_all\b", src))
    assert notify_all_count <= 1, (
        f"found {notify_all_count} notify_all calls; the per-job path must not broadcast"
    )

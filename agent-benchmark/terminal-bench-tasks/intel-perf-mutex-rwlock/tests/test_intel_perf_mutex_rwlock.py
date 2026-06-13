#!/usr/bin/env python3
import os
import re
import subprocess
import time
from pathlib import Path

BINARY = Path("/app/rwlock_fixed")
SOURCE = Path("/app/rwlock_fixed.cpp")
REFERENCE = Path("/app/rwlock_bad")
TIMEOUT = 60.0


def _run(binary, threads, ops):
    cmd = [str(binary), str(threads), str(ops)]
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, f"{cmd} exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    match = re.search(r"checksum=(\d+)", result.stdout)
    assert match, f"missing checksum=<value> in {result.stdout!r}"
    return int(match.group(1)), elapsed


def test_binary_exists():
    assert SOURCE.exists(), "write /app/rwlock_fixed.cpp"
    assert BINARY.exists(), "compile /app/rwlock_fixed"
    assert os.access(BINARY, os.X_OK), "/app/rwlock_fixed is not executable"


def test_checksum_matches_reference():
    # write path must stay correct: the array checksum (driven only by writes)
    # must equal the reference build's at several thread counts
    for threads, ops in [(2, 300000), (4, 300000), (8, 200000)]:
        ref_sum, _ = _run(REFERENCE, threads, ops)
        fix_sum, _ = _run(BINARY, threads, ops)
        assert fix_sum == ref_sum, (
            f"checksum mismatch at threads={threads} ops={ops}: ref={ref_sum} fixed={fix_sum}"
        )


def test_terminates_under_load():
    # rwlock must not deadlock/starve to the point of timing out under read load
    _, elapsed = _run(BINARY, 8, 400000)
    assert elapsed < 30.0, f"run took {elapsed:.1f}s; possible deadlock/starvation"


def test_source_uses_reader_writer_lock():
    text = SOURCE.read_text(errors="replace")
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    src = re.sub(r"//.*", "", no_block)
    has_shared_mutex = bool(re.search(r"shared_mutex", src))
    has_shared_lock = bool(re.search(r"shared_lock", src))
    has_unique_lock = bool(re.search(r"unique_lock|lock_guard", src))
    assert has_shared_mutex, "use std::shared_mutex for the reader-writer lock"
    assert has_shared_lock, "readers must take a std::shared_lock (shared access)"
    assert has_unique_lock, "writers must still take an exclusive lock"

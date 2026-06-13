#!/usr/bin/env python3
import os
import re
import subprocess
import time
from pathlib import Path

BINARY = Path("/app/crc_fast")
SOURCE = Path("/app/crc_fast.cpp")
REFERENCE = Path("/app/crc_bad")
BIG = "67108864"   # 64 MiB throughput run
TIMEOUT = 60.0

# Known reference value for length 1000003 (computed from the reflected
# 0x82F63B78 polynomial over the deterministic buffer fill). A hardware CRC32C
# implementation must reproduce this exactly.
KNOWN_LEN = "1000003"
KNOWN_CRC = 3160327329


def _run(cmd):
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, f"{cmd} exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    match = re.search(r"crc=(\d+)", result.stdout)
    assert match, f"missing crc=<value> in {result.stdout!r}"
    return int(match.group(1)), elapsed


def _best_time(cmd, rounds=3):
    _run(cmd)  # warmup
    times = []
    val = None
    for _ in range(rounds):
        val, sec = _run(cmd)
        times.append(sec)
    return val, min(times)


def test_binary_exists():
    assert SOURCE.exists(), "write /app/crc_fast.cpp"
    assert BINARY.exists(), "compile /app/crc_fast"
    assert os.access(BINARY, os.X_OK), "/app/crc_fast is not executable"


def test_matches_known_vector():
    value, _ = _run([str(BINARY), KNOWN_LEN])
    assert value == KNOWN_CRC, f"crc mismatch vs known vector: got {value} expected {KNOWN_CRC}"


def test_matches_reference_and_is_faster():
    ref_value, ref_time = _best_time([str(REFERENCE), BIG])
    fast_value, fast_time = _best_time([str(BINARY), BIG])
    assert fast_value == ref_value, f"crc mismatch vs reference: ref={ref_value} fast={fast_value}"
    # hardware CRC32C is dramatically faster than bit-at-a-time; require >=4x.
    # The measured margin is ~14x, so this threshold is conservative.
    assert fast_time < ref_time / 4.0, (
        f"expected >=4x speedup; reference={ref_time:.4f}s fast={fast_time:.4f}s"
    )


def test_source_uses_hw_crc_with_dispatch():
    text = SOURCE.read_text(errors="replace")
    has_hw = bool(re.search(r"_mm_crc32_u(8|16|32|64)", text))
    has_dispatch = bool(
        re.search(r"__get_cpuid|__builtin_cpu_supports|getauxval|cpuid", text)
        or re.search(r'target\s*\(\s*"sse4', text)
    )
    has_fallback = bool(re.search(r"0x82F63B78", text))
    assert has_hw, "use the hardware CRC32C intrinsic (_mm_crc32_u64/_u8)"
    assert has_dispatch, "use runtime CPU dispatch or a target-attributed hardware path"
    assert has_fallback, "keep a portable scalar fallback (reflected 0x82F63B78 polynomial)"

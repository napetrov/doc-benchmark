#!/usr/bin/env python3
"""CLI for doc-benchmark: thin compatibility shim.

The implementation now lives in the ``doc_benchmarks`` package. This module
keeps ``python cli.py ...`` working and re-exports the public names that were
historically importable from ``cli``.
"""

from __future__ import annotations

from doc_benchmarks.cli import main

# Re-export command functions and helpers for backward compatibility.

if __name__ == "__main__":
    main()

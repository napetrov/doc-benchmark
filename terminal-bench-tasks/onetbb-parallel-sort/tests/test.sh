#!/bin/bash
# Test runner for onetbb-parallel-sort task.
# Installs pytest and runs the test suite, writing reward.txt.

set -euo pipefail

REWARD_FILE="/logs/verifier/reward.txt"
mkdir -p /logs/verifier

pip install pytest --quiet

pytest /tests/test_parallel_sort.py -v 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo 1 > "$REWARD_FILE"
else
    echo 0 > "$REWARD_FILE"
fi

exit $EXIT_CODE

#!/bin/bash
set -e

cd /home/openclaw/.openclaw/workspace/projects/intel/intel-doc-benchmark
source venv/bin/activate

echo "=========================================="
echo "Starting all benchmarks..."
echo "=========================================="

# Create result directories
mkdir -p results/onedal results/onetbb_full

# 1. oneDAL Baseline
echo ""
echo "1/4: Running oneDAL baseline..."
python -u benchmark.py scan \
    -q questions/onedal.json \
    --source baseline \
    --scorer-model deepseek-chat \
    2>&1 | tee results/onedal/baseline_run.log

# Copy latest results
LATEST_DIR=$(ls -td results/run_* | head -1)
cp -r "$LATEST_DIR" results/onedal/baseline
echo "✓ oneDAL baseline complete: results/onedal/baseline"

# 2. oneDAL Context7
echo ""
echo "2/4: Running oneDAL context7..."
python -u benchmark.py scan \
    -q questions/onedal.json \
    --source context7:oneapi-src/onedal \
    --scorer-model deepseek-chat \
    2>&1 | tee results/onedal/context7_run.log

LATEST_DIR=$(ls -td results/run_* | head -1)
cp -r "$LATEST_DIR" results/onedal/context7
echo "✓ oneDAL context7 complete: results/onedal/context7"

# 3. oneTBB Baseline (full 27 questions)
echo ""
echo "3/4: Running oneTBB baseline (full)..."
python -u benchmark.py scan \
    -q questions/onetbb.json \
    --source baseline \
    --scorer-model deepseek-chat \
    2>&1 | tee results/onetbb_full/baseline_run.log

LATEST_DIR=$(ls -td results/run_* | head -1)
cp -r "$LATEST_DIR" results/onetbb_full/baseline
echo "✓ oneTBB baseline complete: results/onetbb_full/baseline"

# 4. oneTBB Context7 (full 27 questions)
echo ""
echo "4/4: Running oneTBB context7 (full)..."
python -u benchmark.py scan \
    -q questions/onetbb.json \
    --source context7:uxlfoundation/onetbb \
    --scorer-model deepseek-chat \
    2>&1 | tee results/onetbb_full/context7_run.log

LATEST_DIR=$(ls -td results/run_* | head -1)
cp -r "$LATEST_DIR" results/onetbb_full/context7
echo "✓ oneTBB context7 complete: results/onetbb_full/context7"

echo ""
echo "=========================================="
echo "All benchmarks complete!"
echo "=========================================="
echo ""
echo "Results:"
echo "  oneDAL:  results/onedal/{baseline,context7}"
echo "  oneTBB:  results/onetbb_full/{baseline,context7}"
echo ""
echo "Reports:"
echo "  results/onedal/baseline/report.md"
echo "  results/onedal/context7/report.md"
echo "  results/onetbb_full/baseline/report.md"
echo "  results/onetbb_full/context7/report.md"

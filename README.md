# doc-benchmark

`doc-benchmark` is a toolkit for measuring whether documentation and other agent-facing context improve model performance. It started as a technical documentation quality benchmark and now supports a broader evaluation pattern: compare a model or coding agent with and without a controlled context layer.

Current context layers include product documentation, local Markdown/URL sources, Context7-backed docs, curated golden question sets, and executable task environments. The same harness can be extended to evaluate skills, agent profiles, prompt packs, retrieval settings, and other artifacts that may affect agent behavior.

It supports three complementary workflows:

1. **Static documentation quality checks** over Markdown/code examples: coverage, freshness, readability, example execution, gates, and regression detection.
2. **LLM-assisted context evaluation**: persona and question generation, answer generation with/without context, LLM-as-judge scoring, multi-judge panels, RAGAS meta-evaluation, trust gates, baselines, dashboards, and reproducibility metadata.
3. **Executable agent tasks**: Terminal-Bench/Harbor-style tasks that require an agent to edit code, compile, run, and pass correctness/performance verifiers.

The repository is currently focused on Intel library documentation quality experiments, especially oneTBB, oneDAL, and oneMKL.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

Run the static documentation benchmark:

```bash
python cli.py run \
  --root . \
  --spec benchmarks/spec.v1.yaml \
  --out-json baselines/current.json \
  --out-md reports/current.md
```

Compare a candidate snapshot with a baseline:

```bash
python cli.py compare \
  --base baselines/baseline.json \
  --candidate baselines/current.json \
  --spec benchmarks/spec.v1.yaml \
  --out-json reports/compare.json \
  --out-md reports/compare.md
```

Run the test suite:

```bash
python -m pytest -q
```

Run the same coverage command used by CI:

```bash
python -m pytest --cov=doc_benchmarks --cov-report=term --cov-report=xml
```

## Main CLI areas

The top-level CLI is `python cli.py`. The main command groups are:

```text
run                 Run the static docs-quality benchmark
compare             Compare benchmark snapshots
report              Render JSON reports to Markdown
evaluate            Run the full evaluation pipeline
personas            Discover and approve target user personas
questions           Generate, analyze, refine, and panel-review questions
answers             Generate answers with and without documentation context
eval                Score answers, run RAGAS, or use a multi-judge panel
library             List/show registered libraries
benchmark           Run registered library benchmarks
dashboard           Generate dashboard Markdown/JSON
```

Use `--help` on any command for detailed options, for example:

```bash
python cli.py questions --help
python cli.py eval --help
python cli.py dashboard generate --help
```

## Static benchmark metrics

The default static benchmark is configured in `benchmarks/spec.v1.yaml` and currently uses four active metrics:

| Metric | Purpose |
| --- | --- |
| `coverage` | Checks Markdown structure: headings, code blocks, and body content. |
| `freshness_lite` | Scores files by modification age. |
| `readability` | Estimates text readability with a Flesch-Kincaid-style score. |
| `example_pass_rate` | Executes supported fenced code examples in isolation. |

Weights are normalized across enabled metrics. The benchmark also supports soft gates, hard gates, critical bands, and regression thresholds. Hard gates and critical bands are enforced only when `--strict` is passed.

## LLM evaluation workflow

The LLM workflow is designed to answer a practical question: does documentation improve model answers for real developer tasks?

A typical one-command flow is:

```bash
python cli.py benchmark run \
  --library onetbb \
  --model gpt-4o-mini \
  --judge-model claude-sonnet-4 \
  --judge-provider anthropic \
  --multi-run 3
```

The pipeline:

1. Discovers or loads user personas for the target product.
2. Generates or reuses questions from persona/topic signals, golden sets, and optionally doc chunks.
3. Generates two answers per question using the same answer model:
   - `with_docs`: retrieve context from the configured doc source, rerank it, then answer using only that context.
   - `without_docs`: answer from the model's parametric knowledge only.
4. Evaluates both answers with a separate judge model and reports the delta.
5. Writes artifacts under `results/<library>/` and includes `question_set_hash`, model metadata, token usage, retrieval metadata when requested, and trust-gate signals.

For fair multi-model comparisons, generate one question set and reuse it:

```bash
python cli.py benchmark run --library onedal --output-dir results/onedal_seed
python cli.py benchmark run --library onedal --questions-from results/onedal_seed --model gpt-4o
python cli.py benchmark run --library onedal --questions-from results/onedal_seed --model claude-sonnet-4 --provider anthropic
```

Generated artifacts should normally go under `results/`, `reports/`, or `baselines/current.json` for temporary runs; those paths are ignored by default. Curated fixtures under `answers/`, `eval/`, `baselines/`, `personas/`, and `questions/` may be committed intentionally when they are part of a reproducible benchmark.

See [docs/benchmark-methodology.md](docs/benchmark-methodology.md) for the detailed model roles, question types, difficulty levels, task workflow, and trust checks.

## Executable oneTBB tasks

The repository includes terminal-bench-style tasks under `terminal-bench-tasks/`. These tasks validate not just text answers but working code and measurable behavior. Current CI builds every included oneTBB task container and verifies the oracle solution with network disabled.

Included oneTBB tasks cover `parallel_sort`, `parallel_for`/`parallel_reduce` streaming kernels, tiled stencil and transpose, `parallel_reduce`, `parallel_scan`, and `flow::graph`. These tasks are the executable side of the benchmark: they can test whether docs, skills, or an agent profile actually improve an agent's ability to produce correct and performant code.

## Repository layout

```text
benchmarks/              Static benchmark spec and schema
config/                  Product/library configuration
doc_benchmarks/          Main Python package
  dashboard/             Dashboard aggregation/rendering
  eval/                  Answer generation, judges, panels, RAGAS
  gate/                  Soft/hard gates and regression classification
  ingest/                Markdown loading and chunking
  mcp/                   Documentation source clients
  metrics/               Static documentation metrics
  personas/              Persona generation/analysis
  questions/             Question generation, validation, refinement
  report/                JSON/Markdown report generation
  runner/                Benchmark orchestration
terminal-bench-tasks/    Executable task definitions and verifiers
tests/                   Pytest suite
```

## CI

GitHub Actions runs three checks on pull requests:

1. `test` — installs `requirements-test.txt` and runs pytest with coverage.
2. `benchmark` — runs the static docs-quality benchmark and uploads artifacts.
3. `Verify terminal-bench-tasks` — builds task containers and verifies oracle solutions.

Manual workflow dispatch supports strict mode for blocking quality gates.

## Repository hygiene

Do not commit generated logs, coverage databases, tarballs, local caches, or one-off experiment outputs. Keep generated benchmark artifacts either ignored locally or explicitly curated as fixtures. Use pull requests for all changes to `main`.

## License

Internal Intel use.

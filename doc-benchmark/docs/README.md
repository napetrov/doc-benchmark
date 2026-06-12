# doc-benchmark: measuring what actually helps an agent

> **TL;DR** — Everyone ships context for AI agents: documentation, skills, MCP
> servers, agent persona prompts, plugins. Almost nobody *measures* whether any
> of it helps. This project treats every such artifact as a **treatment** in a
> controlled experiment: same model, same questions/tasks, same judge — only the
> artifact changes — and reports the score delta **with statistical
> significance**, so "it feels better" becomes "it is +9.5 points, p = 0.0024".

## The idea

An agent's ability to solve a problem is shaped by far more than the base
model. It is the *sum* of:

- the **base model** (and the harness/CLI it runs in),
- the **documentation** it can retrieve (local files, URLs, Context7, MCP
  doc servers),
- the **skills** it is given (reusable `SKILL.md` procedures and playbooks),
- the **agent profile** (the system prompt / persona it operates under),
- **runtime plugins** that modify behavior (e.g. brevity instructions),
- and the **way** the artifact is delivered (injected up-front vs. fetched by
  the agent through a tool call).

Each of these is cheap to author and easy to over-claim. The hard question is
always the same: **does this artifact measurably improve the agent's answers
and task outcomes — for this model, on this product — or is it just adding
tokens?**

doc-benchmark answers that with the standard tool for the job: a controlled
A/B (in fact N-way) comparison. Every artifact becomes an **arm**:

| Arm | What is being evaluated |
|---|---|
| `baseline` | the bare model — the control |
| `docs:` / `mcp:` | documentation injection (local, URL, Context7, real MCP server) |
| `skill:` | a skill's instructions injected as context |
| `profile:` | an agent persona system prompt |
| `agent:` / `skill-agent:` | **agentic** use — the model gets a tool and *decides* whether to fetch docs / load the skill |
| `plugin:` | runtime behavior modifiers, reported as a separate run dimension |

Everything else is held fixed: the answer model, the question set (hashed so
reuse can be proven), temperature, and an **independent LLM judge** (a
different model/provider than the one answering, to avoid self-judging
inflation). What remains is the marginal value of the artifact itself.

## Example: what the results look like

A skill evaluated across four models, on the same golden question set:

| Model | WITH skill | WITHOUT skill | Delta | p-value | Significant? |
|---|---|---|---|---|---|
| Haiku 4.5 | 66.3 | 56.8 | **+9.5** | 0.0024 | ✅ yes |
| Opus 4.7 | 78.5 | 73.6 | +4.9 | 0.0842 | ❌ |
| Sonnet 4.6 | 74.3 | 69.9 | +4.4 | 0.1797 | ❌ |
| Opus 4.8 | 80.8 | 78.1 | +2.7 | 0.1530 | ❌ |

This single table demonstrates the core lessons of the methodology:

1. **Impact depends on the model.** The same skill is worth +9.5 points to a
   small model and +2.7 to a frontier one. Stronger models already "know" more,
   so the artifact's marginal value shrinks — a delta is only meaningful inside
   its `(model, harness)` cell, never as a universal number.
2. **A positive delta is not a result until it survives a significance test.**
   Three of the four deltas are positive but *not* statistically significant
   (paired t-test on per-question score pairs, p ≥ 0.05) — with this sample
   size they are indistinguishable from judge noise. Reporting "+4.9, helps!"
   would be exactly the over-claiming this project exists to prevent.
3. **The actionable conclusion is targeted.** Ship this skill to agents running
   on smaller/cheaper models, where it provably closes the gap; for frontier
   models, collect more samples or accept that it may not pay for its tokens.

Beyond the headline p-value, reports include Wilcoxon signed-rank tests,
Cohen's d effect size, bootstrap confidence intervals, per-dimension scores
(correctness, completeness, specificity, code quality, actionability), and
trust-gate checks.

## How the evaluation flows

```text
        WHAT WE EVALUATE (the treatments / subjects)
  docs sources · MCP servers · skills · agent profiles · plugins
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│ 1. BUILD THE PROBE SET                                         │
│    personas (synthetic users from real GitHub activity)        │
│      → topic extraction → question generation                  │
│    or curated golden question sets (regression-stable)         │
│    questions span conceptual / how-to / troubleshooting /      │
│    comparison / performance × beginner / intermediate / adv.   │
├────────────────────────────────────────────────────────────────┤
│ 2. RUN EVERY ARM                                               │
│    same model answers every question once per arm:             │
│      baseline | +docs | +skill | +profile | agentic tool use   │
│    agentic arms record whether the model actually used the     │
│    tool — usability, not just relevance                        │
├────────────────────────────────────────────────────────────────┤
│ 3. JUDGE INDEPENDENTLY                                         │
│    a different model/provider scores all answers blind on      │
│    5 dimensions (0–100); optional 3-role judge panel and       │
│    RAGAS meta-evaluation as cross-checks                       │
├────────────────────────────────────────────────────────────────┤
│ 4. ANALYZE & GATE                                              │
│    per-arm delta vs baseline · paired t-test / Wilcoxon /      │
│    Cohen's d · per (model × harness × plugin) cell ·           │
│    trust checks, baselines, regression gates, dashboards       │
└────────────────────────────┬───────────────────────────────────┘
                             ▼
        scorecard: "this artifact is worth +X on model M
              (p = …)" — the evidence to ship or cut it
```

Two complementary tracks back this up:

- **Static track** — fast, LLM-free quality checks on the documentation itself
  (structure coverage, freshness, readability, whether code examples actually
  execute), with hard/soft gates and regression detection for CI.
- **Executable task track** — Terminal-Bench/Harbor-style tasks
  ([`terminal-bench-tasks/`](../terminal-bench-tasks/)) where an agent must
  edit code, compile, and pass tests in Docker. Judge prose can be fooled;
  a pytest verifier cannot. This is where the *procedural* value of skills
  and profiles (which single-answer judging under-measures) shows up.

## Why this matters

Marketplaces and registries rank agent artifacts by popularity and trend —
which structurally buries niche, expert tooling (the current focus here is
Intel performance libraries: oneTBB, oneDAL, oneMKL, …). The alternative this
repo pursues: every shipped skill, doc source, or agent profile carries the
**scorecard that earned it**, and the scorecard stays alive as models, docs,
and harnesses change. Measurement is the gate, not an afterthought. See the
[umbrella README](../../README.md) for how this feeds the broader
author → build → **measure** → package → discover → serve cycle.

## Explore

- Run a treatment comparison yourself:
  [evaluating-treatments.md](evaluating-treatments.md) — `cli.py arms run`
  with any mix of `baseline,docs,mcp:…,skill:…,profile:…,agent:…`.
- Full pipeline in one command:
  [quickstart.md](quickstart.md) — personas → questions → answers → judge →
  report, with cost estimates.
- The reasoning behind the design:
  [decisions/benchmark-methodology.md](decisions/benchmark-methodology.md)
  (model roles, question taxonomy, judging, trust checks) and
  [decisions/2026-05-29-evaluating-mcp-skills-personas.md](decisions/2026-05-29-evaluating-mcp-skills-personas.md)
  (why skills/MCP/profiles became first-class arms).

---

# Documentation index

Start with the top-level [README](../README.md) for the project overview and
CLI surface. The files in this directory go deeper:

## Using doc-benchmark

- [quickstart.md](quickstart.md) — end-to-end LLM evaluation pipeline:
  personas → questions → answers → judge → report. Includes troubleshooting
  and a cost estimate.
- [benchmarking-and-comparison.md](benchmarking-and-comparison.md) — how to
  run static benchmarks, LLM context benchmarks, fair multi-model comparisons,
  treatment-arm comparisons, dashboards, baselines, and PR #60 comparison
  scripts.
- [adding-doc-source.md](adding-doc-source.md) — point the pipeline at local
  files, a single URL, a real MCP server, or a custom client.
- [evaluating-treatments.md](evaluating-treatments.md) — compare
  context-augmentation arms (docs, MCP, skills, agent persona prompts) with
  `cli.py arms run`.

## Extending doc-benchmark

- [architecture.md](architecture.md) — module map and data flow across the
  static, LLM, and executable-task tracks.
- [contributing-metric.md](contributing-metric.md) — add a new static
  documentation metric (module + spec + tests + docs).
- [contributing-terminal-bench-task.md](contributing-terminal-bench-task.md)
  — add an executable oneTBB / oneAPI task with Docker, oracle, and pytest
  verifier.

## Historical decisions

The `decisions/` directory keeps point-in-time design reviews and
investigations. They reflect the state of the project at their dated time
and may have been partially superseded — each file's header notes its
current status.

- [decisions/2026-02-12-review-devils-advocate.md](decisions/2026-02-12-review-devils-advocate.md)
- [decisions/2026-02-12-review-intel-product.md](decisions/2026-02-12-review-intel-product.md)
- [decisions/2026-02-14-context7-http-vs-mcp.md](decisions/2026-02-14-context7-http-vs-mcp.md)
- [decisions/2026-05-29-evaluating-mcp-skills-personas.md](decisions/2026-05-29-evaluating-mcp-skills-personas.md)
  — assessment + proposal for evaluating MCP docs, skills, and agent persona
  prompts as first-class treatment arms.
- [decisions/2026-06-10-evaluation-beyond-mcp-docs.md](decisions/2026-06-10-evaluation-beyond-mcp-docs.md)
  — **umbrella / index** for extending evaluation beyond MCP docs; states the
  shared motivation and sequences the ADRs below.
  - [decisions/2026-06-10-questions-and-tasks-coverage-contract.md](decisions/2026-06-10-questions-and-tasks-coverage-contract.md)
    — pair every project's question set (awareness) with an executable task set
    (work); surface the gap as a checked matrix. *(Phase A.)*
  - [decisions/2026-06-10-model-harness-dimension.md](decisions/2026-06-10-model-harness-dimension.md)
    — make base model × harness an explicit, swept, reported dimension; deltas
    only comparable within a `(model, harness)` cell. *(Phase B.)*
  - [decisions/2026-06-11-plugin-and-harness-aware-benchmarks.md](decisions/2026-06-11-plugin-and-harness-aware-benchmarks.md)
    — add plugins such as Caveman as explicit runtime behavior modifiers and
    report token/cost gains separately from quality or task-success loss.
    *(Phase C.)*
  - [decisions/2026-06-10-artifacts-as-evaluation-subjects.md](decisions/2026-06-10-artifacts-as-evaluation-subjects.md)
    — promote skills/profiles/bundles from arms to first-class evaluation
    *subjects* emitting a per-subject scorecard. *(Phase D.)*
- [decisions/benchmark-methodology.md](decisions/benchmark-methodology.md)
  — current operational methodology for model roles, question types,
  difficulty levels, answer generation, judging, trust checks, and executable
  agent tasks.

# Evaluation beyond MCP docs: artifacts as subjects, model × harness as a dimension, tasks for every project

**Status:** PROPOSED. This extends the treatment-arm framework already shipped in
[2026-05-29-evaluating-mcp-skills-personas.md](2026-05-29-evaluating-mcp-skills-personas.md)
(`doc_benchmarks/treatments/`, `eval/arm_runner.py`, `cli.py arms run`) and the
executable [terminal-bench track](../contributing-terminal-bench-task.md). No
code lands with this document; it is the design we will phase in. Tracked as
BACKLOG #59.

**Date:** 2026-06-10

---

## 1. Where we are

The benchmark today answers a doc-centric question — *does retrieved
documentation improve a model's answer?* — and the treatment-arm framework
generalized it so skills, agent profiles, and MCP servers can each be toggled as
an **arm** layered on a fixed product question set. Skills/profiles/MCP are, in
the current design, *levers we vary on top of a doc-evaluation question*. The
outcome is an LLM-as-judge delta vs a baseline arm; behavioral signal comes from
the separate terminal-bench tasks (oneTBB/oneMKL/IPP/…).

This is the right substrate, but it is still organized around **documentation as
the thing under test**. Three gaps follow from that framing.

## 2. The three gaps

### 2.1 Skills and agent profiles are levers, not subjects

When the goal becomes *packaging a summonable Intel expert* (umbrella #58), the
artifact we want to certify is the **skill** or the **agent profile** itself —
the thing that ships. Today an artifact only appears as a column in one product's
arm report. There is no first-class object that says "*this* skill, measured
across *this* portfolio of products/questions/tasks, earns *this* scorecard."

The inversion we want: make the **artifact the subject** and a curated set of
products/questions/tasks its **test bed**. The arm machinery stays; what changes
is the unit of reporting and aggregation — from "product X, with vs without
arm" to "artifact A, scored over its declared evaluation suite." This is the
object packaging (#58d, scorecard-as-credential) needs to serialize.

### 2.2 No base-model or harness dimension

For coding work the **base model** and the **agent harness** (the loop that
drives tool calls, retries, edits, and execution — e.g. terminus / oracle /
Claude Code / a bespoke runner) usually dominate the doc-or-skill delta. A skill
that adds +0.3 under a weak model+harness can be invisible under a strong one,
and vice-versa. Right now both are effectively fixed: one answer model, and for
tasks whatever agent Harbor is invoked with, set outside the benchmark.

We cannot interpret an artifact's delta without holding model and harness fixed
*and* sweeping them deliberately. Today we do neither in a first-class way.

### 2.3 Awareness is measured everywhere; work is measured only for oneTBB-ish C++

Every product has (or can have) a golden **question** set — that measures
*awareness*: can the model talk about the API correctly. Only a handful of
oneAPI components have executable **tasks** — that measure *work*: can the model
produce code that compiles, runs, and passes a verifier. The two signals diverge
(a model can describe `parallel_reduce` perfectly and still write a racy loop),
and the artifacts we most want to certify (skills, setup guides) prove their
value in *work*, not *talk*. Every project in scope should carry **both**.

## 3. Proposal

Three changes, each independently shippable, each reusing existing seams.

### 3.1 Promote the artifact to a first-class evaluation subject

Introduce an **evaluation subject** descriptor — the artifact under test plus the
suite it is measured against:

```yaml
# subjects/onetbb-quickstart.yaml  (illustrative)
subject:
  kind: skill                       # skill | profile | mcp | doc-source | bundle
  ref: data/skills/onetbb-quickstart
suite:
  products: [oneTBB]
  questions: [data/questions/onetbb_golden.json]
  tasks: [terminal-bench-tasks/onetbb-*]   # behavioral arm, optional
baseline: baseline                   # arm to delta against
matrix:                              # see 3.2
  models: [<model-a>, <model-b>]
  harnesses: [single-shot, agent, terminus]
```

A `bundle` subject is several artifacts shipped together (profile + skills + MCP)
— i.e. exactly the `AgentConfig` a package serializes (#58a). The runner expands
a subject into the arms it already knows (`skill:`, `profile:`, `mcp:`, `agent:`,
`skill-agent:`) and aggregates **per subject**, not per product. Output is a
**scorecard** keyed by `(subject, model, harness)` with Q&A deltas and task
pass-rate deltas side by side — the credential #58d ships.

Concretely this is a new `subjects/` loader + a `cli.py subjects run` that wraps
`arm_runner` and the task verifier, plus a `report/subject_report.py`. The
existing `arms run` stays as the low-level, product-centric entry point.

### 3.2 Make base model × harness an explicit matrix

Add two axes the runner sweeps and the report holds fixed:

- **Model** — already plumbed through `llm.py`; lift it from a single flag to a
  list and stamp it on every result row (most rows carry the answer model
  already; make it a reported dimension, not a run-wide constant).
- **Harness** — name the loop that produces the answer/transcript:
  `single-shot` (today's one completion), `agent` (the in-process tool-calling
  loop in `eval/agent_runner.py`), and `terminal-bench:<agent>` (Harbor drives a
  real coding agent against a task). The harness is a property of a *run*, not a
  treatment; an arm's delta is only comparable within one `(model, harness)`
  cell.

The report becomes a small cube: rows = arms/subjects, and each cell is a
`(model, harness)` pair. This lets us answer the question that motivates the
whole exercise — *for coding tasks, how large is the model/harness effect
relative to the doc/skill effect?* — by reading variance down the model/harness
axes against variance across arms. Practically: a `matrix:` block in config, a
`(model, harness)` key threaded into result rows and the dashboard, and CI cost
guards (the matrix is multiplicative — gate it behind opt-in and small default
cells).

### 3.3 A questions-and-tasks contract for every project

Define a per-product **coverage contract**: each product in `libraries.yaml` /
`config/products.yaml` should declare both a golden question set (awareness) and
at least one executable task (work), with a documented validation strategy
(serial-reference signature, analytic value, round-trip invariant, drop-in
comparison — the patterns already used in #54). Surface the gap as a checked
matrix (extend `terminal-bench-tasks/COVERAGE.md` into a product × {questions,
tasks} table) so an un-tasked product is visible, and let the dashboard report
**awareness score** and **work pass-rate** as two columns per product.

This does not require a task for all 22 registered libraries on day one; it
requires the *contract to be explicit* and the gaps tracked, so "we only judge
text for product X" is a visible TODO rather than a silent default. Skills and
setup-guide artifacts (#58e/#58f) then have a behavioral bar to clear, not just a
judge score.

## 4. How it maps onto existing seams

| Need | Reuse | New |
|---|---|---|
| Artifact-as-subject | `treatments/` arms, `arm_runner.py` | `subjects/` loader + `subjects run` + `report/subject_report.py` |
| Q&A outcome | `eval/judge.py`, `panel.py` | aggregate per subject, not per product |
| Work outcome | `terminal-bench-tasks/` + Harbor | a `terminal-bench` harness adapter that returns pass-rate as an arm outcome |
| Model axis | `llm.py` model arg | promote to a reported dimension + `matrix.models` |
| Harness axis | `agent_runner.py`, Harbor | name + record the harness; `matrix.harnesses` |
| Coverage contract | `COVERAGE.md`, `config/products.yaml`, `libraries.yaml` | product × {questions, tasks} matrix + dashboard columns |
| Scorecard object | `artifacts.py` (`schema_version`), `runner/manifest.py`, `question_set_hash` | a versioned per-subject scorecard schema (feeds #58d) |

## 5. Methodology caveats (carried forward and added)

- **Confounders multiply fast.** Subjects × models × harnesses × arms is a
  combinatorial space; every comparison must hold all but one axis fixed. Keep
  `question_set_hash` and add a `harness`/`model` stamp to every row so the
  report can refuse to delta across incomparable cells.
- **Cost.** The matrix is multiplicative and agentic/task cells are the
  expensive ones. Default to a single `(model, harness)` cell; gate sweeps and
  the terminal-bench harness behind opt-in flags and CI labels.
- **Q&A still under-measures skills/profiles** (their value is procedural). The
  questions-and-tasks contract (3.3) is the structural fix: when a subject has a
  task suite, treat the **task pass-rate delta as authoritative** and the judge
  delta as a weak proxy.
- **Faithful skill execution still needs the sandbox.** Running a skill's
  bundled scripts stays on the terminal-bench Docker track (`--network none`),
  never in-process — unchanged from #56 Phase 4.
- **Harness fairness.** Comparing harnesses is comparing *our* integrations;
  document each harness's version/config so a "harness effect" is not really a
  mis-configuration artifact.

## 6. Suggested phasing

- **Phase A — Coverage contract (cheap, high-leverage).** Product × {questions,
  tasks} matrix in `COVERAGE.md`; dashboard gains awareness vs work columns;
  declare the per-product contract in config. No new eval machinery — just makes
  the existing gap legible and gives 3.1/3.2 a target portfolio.
- **Phase B — Model × harness dimension.** Promote model to a reported axis;
  name and record the harness; add a `matrix:` block and a `(model, harness)`
  key through `arm_runner`, the report, and the dashboard; add a
  `terminal-bench` harness adapter so task pass-rate is an arm outcome.
- **Phase C — Subjects.** `subjects/` descriptor + loader, `subjects run`
  wrapping `arm_runner` + the task adapter, `report/subject_report.py`, and the
  versioned per-subject scorecard schema. This is the object #58d/#58i serialize
  and sign.

Each phase leaves the existing two-arm doc flow and `arms run` working, and each
is useful on its own: A makes gaps visible, B explains variance, C produces the
shippable credential.

## 7. Open decisions

1. **Harness boundary.** Is `terminal-bench:<agent>` invoked in-process via a
   thin Harbor adapter, or out-of-band with results imported? (Leaning adapter,
   to keep one report.)
2. **Subject vs package overlap.** A `bundle` subject and a #58 `package.yaml`
   manifest describe nearly the same thing. Should `subjects/` *be* the
   pre-package form, or a separate eval-only descriptor that a package
   references? (Leaning: subject is the eval view; package embeds the resulting
   scorecard.)
3. **Default matrix size.** Which `(model, harness)` cells are the committed
   default so CI cost stays bounded while the variance question stays answerable?
4. **Coverage contract enforcement.** Soft (reported gap) or hard (CI fails a
   product that declares a task suite but ships none)? Start soft.

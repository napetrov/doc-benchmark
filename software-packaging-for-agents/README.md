# Software Packaging for Agents — framing & architecture

This directory holds the **vision and architecture** for packaging software so
that *agentic AI consumers* — not just human developers — can discover, install,
and use it effectively. The companion [`../doc-benchmark/`](../doc-benchmark/)
provides the measurement engine that decides whether a packaged artifact is
actually worth shipping.

> **Status:** Bootstrapping. This is the skeleton; the design documents below
> are being written on the `packaging-distribution-vision` branch. See the
> umbrella [README](../README.md) for the project loop and the architecture
> mainline being explored.

## Why this exists

Software distribution is reorganizing around agents. The artifacts that matter
are no longer only binaries and packages, but **agent-facing capabilities**:

- **Agent profiles** — the system prompt that turns a general model into, e.g.,
  an Intel HPC expert.
- **Skills** — packaged, triggerable know-how (`SKILL.md` + idioms + BKMs +
  optional scripts).
- **MCP doc sources** — on-demand access to the relevant slice of documentation.

The mainline hypothesis: *documentation behaves as a general skill, and MCP (or
an equivalent) is how an agent asks for the relevant part on demand* — a thin,
always-available skill that knows when to reach for a thick doc source.

## Planned contents

| File | Purpose | Status |
|---|---|---|
| `architecture.md` | The package/distribute/discover tracks and how they compose with the measurement engine. | Skeleton |
| `decisions/` | Design docs: agent-package format, per-runtime distribution, discovery graph. | Planned |

## The discovery problem

Marketplaces rank by popularity / "what's trending." That structurally buries
niche HPC and numerical-accuracy tools, which will never trend among average
developers. The planned discovery layer replaces keyword/trend ranking with a
**capability/intent graph + semantic search**, using the benchmark scorecard as
a *vetted* ranking signal. Design doc to follow.

## Relationship to `doc-benchmark/`

`doc-benchmark/` already contains the primitives this framing packages —
treatment arms for `agent_profile`, `skill`, and `mcp` (see
[`../doc-benchmark/docs/evaluating-treatments.md`](../doc-benchmark/docs/evaluating-treatments.md)).
Here those primitives are treated as **deliverables to ship**, not just
benchmark inputs to score.

# Software Packaging for Agents

Usage is shifting from human developers to **agentic AI consumers**. Software —
especially expert, high-performance, and numerically-sensitive libraries — needs
to be packaged for *that* audience: reachable by an agent, practical to apply,
and carrying its own best-known-methods (BKMs), setup guidance, and idioms.

This repository pursues that mission in two complementary halves:

| Directory | Role | Status |
|---|---|---|
| [`software-packaging-for-agents/`](software-packaging-for-agents/) | **Framing & architecture** — the vision, the agent-package format, per-runtime distribution (Claude, Hermes, …), and the discovery layer. | Bootstrapping |
| [`doc-benchmark/`](doc-benchmark/) | **Measurement engine** — evaluates whether a given skill / MCP doc source / agent profile actually improves agent answers and task outcomes. The evidence that justifies shipping an artifact. | Established |

## The loop

```text
        build ─────────► measure ─────────► package ─────────► publish
   (agent_profile +    (doc-benchmark:     (manifest +       (discoverable
    skills + MCP)       arms, judges,       per-runtime        catalog, not
                        terminal-bench)     adapters)          trend-ranked)
        ▲                                                          │
        └──────────────────  feedback / scorecard  ◄───────────────┘
```

Measurement is the **gate**, not the product: a packaged agent ships with the
scorecard that earned it — a deliberate contrast to popularity/trend-ranked
marketplaces, which structurally bury niche HPC and numerical-accuracy tools.

## Architecture mainline being explored

> Intel expert persona → system prompt, skills, and MCP, distributed as an
> agent for Claude, Hermes, et al. Documentation behaves as a *general skill*;
> MCP (or equivalent) is how the agent asks for the relevant part on demand.

See [`software-packaging-for-agents/`](software-packaging-for-agents/) for the
full framing and architecture.

## Repository layout

```text
README.md                          This umbrella overview
Makefile                           Delegates targets into each area
software-packaging-for-agents/     Framing, architecture, packaging & discovery design
doc-benchmark/                     The measurement engine (self-contained Python project)
LICENSE  NOTICE                    Apache-2.0 + attribution (repo-wide)
.github/workflows/                 CI (runs inside doc-benchmark/)
```

## Getting started

The runnable project today is the benchmark:

```bash
make benchmark        # delegates into doc-benchmark/ (see its README)
make test             # runs the doc-benchmark test suite
```

For the benchmark's own quickstart, CLI surface, and architecture, see
[`doc-benchmark/README.md`](doc-benchmark/README.md).

## License

Licensed under the [Apache License, Version 2.0](LICENSE); see [NOTICE](NOTICE)
for attribution.

# Review: from a measurement engine to a packaging-for-agents project

> **Status:** DRAFT for annotation by Emmanuel & Nikolay. This is the review
> that motivates the `software-packaging-for-agents/` track and the two design
> docs beside it. Leave inline comments / replies; unresolved points feed the
> open questions at the end.
> **Date:** 2026-06-02

## 0. The brief

Usage is shifting from human developers to **agentic AI consumers**. Software —
especially expert, high-performance, numerically-sensitive Intel libraries —
must be packaged for that audience: reachable by an agent, practical to apply,
carrying its own BKMs and setup guidance. Emmanuel's architecture mainline:

> Intel expert persona → system prompt, skills, and MCP.
> Distribute as an agent for Claude, Hermes, et al.
> Documentation behaves as a general skill; MCP (or equivalent) is how the agent
> asks for the relevant part on demand.

Reference points shared: [intel/intel-performance-skills](https://github.com/intel/intel-performance-skills)
(shipped skill catalog), [intel-xpu-backend-for-triton.claude-plugins](https://github.com/intel-sandbox/applications.python.intel-xpu-backend-for-triton.claude-plugins)
(packaged plugins), [cursor.directory](https://cursor.directory/) (a listing —
"81.4k+ developers, ranked by what's trending").

## 1. Core tension: this repo *measures*; the vision *ships*

The repository as inherited is written end-to-end as a **measurement toolkit**
("a toolkit for measuring and improving technical documentation quality";
"does documentation improve model answers?"). The vision is a **production &
distribution pipeline**: build Intel expert agents and distribute them.

Tellingly, all three shared references sit on the *distribution* end (a catalog,
plugins, a marketplace) — none is a benchmark. The treatment-arm framework
already speaks the right vocabulary (`agent_profile`, `skill`, `mcp`), but it
**consumes** those artifacts as benchmark inputs rather than **producing** them
as deliverables.

Resolution taken on this branch: keep the measurement engine (it is the
*evidence* that a given skill/MCP/persona is worth shipping) and add the missing
half — packaging + discovery — as new tracks under one umbrella repo. Measurement
becomes the **gate**, not the product.

## 2. Findings

**F1 — Two whole layers were absent from the architecture.** The inherited
architecture had three tracks (static / LLM-eval / executable-task). The vision
needs a fourth (**package/distribute**) and a fifth (**discover/serve**). Neither
appeared in the README, architecture, or backlog. *Addressed* by the umbrella
README's build→measure→package→publish loop and
[`../architecture.md`](../architecture.md).

**F2 — "Doc is a general skill, then MCP for the relevant part" is a design
principle, not an aside.** It describes two-tier progressive disclosure: a thin
always-on skill that knows *when* to reach for a thick on-demand doc source. The
mechanism already exists in `doc-benchmark` (`skill-agent:` + `agent:`/`mcp:`
arms) but only as *arms to compare*. *Addressed* by elevating it to the
prescribed packaging pattern in
[`agent-package-format.md` §3](agent-package-format.md).

**F3 — The "trending" remark is a real architecture constraint.** Popularity
ranking structurally buries niche HPC / numerical-accuracy tools. The fix is a
capability/intent graph + semantic search, ranked by *vetted scorecard* not
install count. The repo already holds the seed data (`libraries.yaml`,
`COVERAGE.md`, fixtures), just not as one queryable structure. *Addressed* by
[`discovery-graph.md`](discovery-graph.md).

**F4 — `AgentConfig` is already an agent package.** `treatments/base.py`'s
`AgentConfig` = `system_prompt + injected_context + tools + metadata` — literally
a shippable agent. Packaging is serializing/adapting this, not inventing a new
representation. This one observation connects eval and packaging cheaply.

**F5 — The eval→ship gap.** The inherited decision docs stop at *scoring* a
treatment; none asks "how do we ship the winner?" The package format closes this:
the benchmark's per-arm report becomes the package's embedded `scorecard`, and
distribution is gated on it — the differentiator vs unvetted, trend-ranked
listings.

## 3. Naming / risk flags (carried into the design docs)

- **Use `agent_profile`, not `persona`, for the shipped Intel expert.** The team
  just closed the persona(asker)/agent_profile(answerer) collision; the vision's
  "persona" is the answerer's system prompt = `agent_profile`.
- **Shipped skills re-open the execution surface** the eval side deferred to the
  sandboxed terminal-bench track (`Skill.resources` are recorded but not run).
  Handled in [`agent-package-format.md` §6](agent-package-format.md).
- **MCP client vs server.** `doc-benchmark` only *consumes* MCP today. Shipping
  an Intel MCP *server* is a different artifact/lifecycle (open question Q6).

## 4. What this branch delivers (docs-only, Phase A–E)

- Umbrella restructure: `doc-benchmark/` (engine, moved intact) +
  `software-packaging-for-agents/` (this framing) + root README/Makefile.
- This review + two design drafts (package format, discovery graph) +
  architecture skeleton.
- Backlog epics for the package/discover tracks (in `doc-benchmark/BACKLOG.md`).
- **No packaging code yet** — deferred to a follow-up PR pending the decisions
  below.

## 5. Open questions for Emmanuel & Nikolay

- **Q1 — repo shape.** RESOLVED: single umbrella repo, two subdirs, no submodule.
- **Q2 — PR scope.** RESOLVED: docs/framing first; code follow-up.
- **Q3 — first runtimes.** Which exporter ships first — Anthropic Agent Skills,
  Claude plugin, Hermes, a cursor.directory-style listing? (Suggest Agent Skills,
  since `SKILL.md` already conforms.)
- **Q4 — graph & embedding stack.** Property graph vs RDF vs lightweight in-repo
  graph; reuse the existing `embeddings` extra? (See discovery doc.)
- **Q5 — layout alignment.** Adopt `intel/intel-performance-skills`' package
  layout, or define our own + an adapter?
- **Q6 — MCP server.** Ship an Intel MCP doc server, or only consume third-party?

## 6. Suggested next steps once decisions land

1. Resolve Q3–Q6 inline here.
2. Build the first real package from existing fixtures (`concise_expert` +
   `onetbb-quickstart` + Context7 MCP) as a proof, with its scorecard.
3. Implement one exporter (per Q3) and a thin `package build` command.
4. Stand up the discovery graph seed from `libraries.yaml` + `COVERAGE.md`.

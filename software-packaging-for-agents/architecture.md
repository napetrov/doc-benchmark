# Architecture (framing skeleton)

> **Status:** Skeleton. Detailed design docs land under `decisions/` per the
> branch plan. This file fixes the shape so contributors know where each piece
> goes.

The project is a closed loop with four conceptual tracks. The first
(**measure**) is built today as [`../doc-benchmark/`](../doc-benchmark/); the
other three are the subject of this directory.

```text
   ┌─────────── build ───────────┐     ┌────────── measure ──────────┐
   │ agent_profile (system prompt)│     │ doc-benchmark:              │
   │ skills (SKILL.md + BKMs)     │────►│  treatment arms, judges,    │
   │ mcp doc sources              │     │  terminal-bench outcomes    │
   └──────────────────────────────┘     └──────────────┬──────────────┘
                                                        │ scorecard (gate)
                                                        ▼
   ┌────────── package ──────────┐     ┌────────── discover ─────────┐
   │ manifest = profile + skills │     │ capability/intent graph     │
   │  + mcp refs + provenance    │────►│  + semantic search          │
   │ per-runtime adapters:       │     │  ranked by vetted scorecard,│
   │  Claude, Hermes, generic    │     │  not popularity/trend       │
   └──────────────────────────────┘     └─────────────────────────────┘
```

## Tracks

1. **Build** — author the agent-facing artifacts. Today these exist as
   benchmark fixtures (`../doc-benchmark/data/agent_profiles/`,
   `../doc-benchmark/data/skills/`).
2. **Measure** — `doc-benchmark/`. The scorecard is the gate: only artifacts
   that demonstrably improve answers/task outcomes get packaged.
3. **Package** — serialize an agent configuration (system prompt + skills +
   MCP references + provenance + scorecard) into a manifest, then export it per
   runtime (Claude plugin, Anthropic Agent Skills layout, Hermes, generic).
   *Design doc: `decisions/` (planned).*
4. **Discover** — a capability/intent graph with semantic search so niche tools
   surface by *fit*, not popularity. *Design doc: `decisions/` (planned).*

## Key idea: AgentConfig is already a package

`doc-benchmark`'s `Treatment` → `AgentConfig` abstraction
(`../doc-benchmark/doc_benchmarks/treatments/base.py`) is
`system_prompt + skills + tools + injected_context` — which is exactly a
shippable agent. Packaging is largely *serializing and adapting* this existing
representation, not inventing a new one.

## Open architectural questions

Tracked in the branch plan; to be resolved with design docs:

- Package manifest schema and how the scorecard is embedded.
- Which runtimes to target first and how their adapters differ.
- Graph technology and the intent/capability taxonomy.
- Whether to ship an Intel **MCP server** or only consume third-party ones
  (today `doc-benchmark` is an MCP *client*).

# Doc-Benchmark Pipeline: Overview and Architecture

**Repository:** https://github.com/napetrov/doc-benchmark  
**Date:** 2026-03-04

---

## Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DOC-BENCHMARK PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────┘

  GitHub Repo
  (uxlfoundation/oneTBB)
       │
       ▼
┌─────────────────┐
│   1. PERSONAS   │  LLM analyzes the repo and creates user profiles:
│                 │  who writes code, who optimizes, who integrates
│ Output:         │
│ personas/       │  Example personas:
│ oneTBB.json     │  • HPC Engineer — advanced, cares about NUMA/throughput
└────────┬────────┘  • ML Framework Dev — intermediate, flow graph & latency
         │           • Systems Integrator — beginner, CMake/build config
         │
         ▼
┌─────────────────┐
│  2. QUESTIONS   │  For each persona × seed topics → questions
│                 │
│  Internally:    │  a) Context7 → extracts seed topics from library docs
│  • LLM generates│  b) LLM generates questions (by difficulty: basic/advanced)
│  • Validation   │  c) LLM validator filters weak questions (threshold 60)
│  • Deduplication│  d) Embedding similarity → dedup (cosine > 0.85)
│                 │  e) Merge personas for near-duplicate questions
│ Output:         │
│ questions/      │  Question types: how-to, scenario, explain, compare
│ oneTBB.json     │  Difficulty: basic / intermediate / advanced
└────────┬────────┘  Total: 30–80 unique questions
         │
         ├────────────────────────────────────┐
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│  3a. ANSWERS    │                │  3b. ANSWERS    │
│  WITH DOCS      │                │  WITHOUT DOCS   │
│                 │                │                 │
│ Context7 →      │                │ LLM answers     │
│ retrieves       │                │ from built-in   │
│ relevant doc    │                │ knowledge only  │
│ snippets →      │                │ (baseline)      │
│ LLM answers     │                │                 │
│ with context    │                │                 │
└────────┬────────┘                └────────┬────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ answers/        │  Each entry:
              │ oneTBB.json     │  { with_docs: {answer, retrieved_docs},
              └────────┬────────┘    without_docs: {answer} }
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 4. EVALUATION                        │
│              (LLM-as-Judge)                          │
│                                                     │
│  Judge: separate model (claude-sonnet-4-6)          │
│  NOT the same model that generated the answers      │
│                                                     │
│  Scores each answer on 5 dimensions (0–100):        │
│                                                     │
│  ┌─────────────────┬────────────────────────────┐   │
│  │ Dimension       │ What it measures            │   │
│  ├─────────────────┼────────────────────────────┤   │
│  │ Correctness     │ Factual accuracy            │   │
│  │ Completeness    │ Coverage of the topic       │   │
│  │ Specificity     │ Relevance to the library    │   │
│  │ Code Quality    │ Correctness of code samples │   │
│  │ Actionability   │ Can be applied immediately  │   │
│  └─────────────────┴────────────────────────────┘   │
│                                                     │
│  Aggregate = avg(5 dims)                            │
│  Delta = with_docs.aggregate − without_docs.agg     │
│                                                     │
│  Diagnosis:                                         │
│  • docs_helped          (delta > 0)                 │
│  • knowledge_sufficient (delta ≤ 0)                 │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ eval/           │
              │ oneTBB.json     │
              └────────┬────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 5. REPORT                            │
│                                                     │
│  • Aggregated metrics                               │
│  • Top / bottom questions by score                  │
│  • Delta analysis (where docs helped / hurt)        │
│  • Prioritized documentation fix recommendations    │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
              reports/oneTBB.md
              reports/oneTBB_low_scores_analysis.md
```

---

## Models Used

| Step | Role | Model (current run) |
|------|------|---------------------|
| Personas | Generator | gpt-4o |
| Questions | Generator + validator | gpt-4o |
| Answers with_docs | Answers with context | gpt-4o |
| Answers without_docs | Baseline answerer | gpt-4o |
| Evaluation | Judge | claude-sonnet-4-6 |
| Embeddings (dedup) | Similarity | text-embedding-3-small |

> **Key principle:** Judge ≠ Answerer. Different models for generation and evaluation — avoids self-serving bias.

---

## Context7 — Role in the Pipeline

Context7 is a documentation retrieval service that provides:
1. **Topic discovery** — extracts key topics from library documentation (by repo slug)
2. **Retrieval (RAG)** — for each question, returns relevant documentation snippets

```
Question → Context7.resolve_library("oneTBB")
         → Context7.search(question_text, max_tokens=8000)
         → retrieved_docs (list of snippets)
         → LLM(question + retrieved_docs) → answer_with_docs
```

---

## File Structure

```
results/onetbb_final/
├── personas/
│   └── oneTBB.json          # 5–8 user personas with profiles
├── questions/
│   └── oneTBB.json          # 80 questions with metadata
├── answers/
│   └── oneTBB.json          # Answers: with_docs + without_docs
├── eval/
│   └── oneTBB.json          # Scores per 5 dims + delta + diagnosis
└── reports/
    ├── oneTBB.md                          # Main report
    └── oneTBB_low_scores_analysis.md      # Low score analysis & fix priorities
```

---

## Run Configuration — oneTBB (2026-03-04)

Static parameters used for this evaluation run:

### Product
| Parameter | Value |
|-----------|-------|
| Library | Intel oneAPI Threading Building Blocks (oneTBB) |
| GitHub repo | `uxlfoundation/oneTBB` |
| Context7 library slug | `oneTBB` |

### Personas (7 total)
| ID | Description |
|----|-------------|
| `hpc_developer` | HPC Developer — advanced, NUMA, throughput, task scheduling |
| `scientific_computing_researcher` | Scientific Computing Researcher — parallel algorithms, correctness |
| `embedded_systems_engineer` | Embedded Systems Engineer — resource constraints, static linking |
| `enterprise_software_engineer` | Enterprise Software Engineer — reliability, CMake, integration |
| `systems_architect` | Systems Architect — design decisions, performance trade-offs |
| `graphics_programming_expert` | Graphics Programming Expert — latency, flow graph, pipelines |
| `beginner_parallel_programmer` | Beginner Parallel Programmer — basic APIs, getting started |

### Questions
| Parameter | Value |
|-----------|-------|
| Total questions | 80 |
| Generated by LLM | 56 |
| Manual (golden set) | 24 |
| Difficulty: advanced | 32 |
| Difficulty: intermediate | 16 |
| Difficulty: beginner/easy | 16 |
| Difficulty: medium/hard | 16 |
| Validation threshold | 60 / 100 |
| Dedup similarity threshold | cosine > 0.85 |
| Generator model | gpt-4o (openai) |

### Answers
| Parameter | Value |
|-----------|-------|
| Generated at | 2026-03-04T19:19:54Z |
| Answerer model | gpt-4o (openai) |
| Doc retrieval source | Context7 (cached) |
| Retrieved snippets per question | 1 (relevance-ranked) |

### Evaluation
| Parameter | Value |
|-----------|-------|
| Judge model | claude-sonnet-4-6 (anthropic) |
| Dimensions | 5 (correctness, completeness, specificity, code_quality, actionability) |
| Scale | 0 – 100 per dimension |
| Aggregate | mean of 5 dimensions |
| Gap threshold (flag for review) | < 70 |
| docs_helped | delta > 0 |
| knowledge_sufficient | delta ≤ 0 |

---

## CLI Usage

```bash
# 1. Generate personas
python cli.py personas discover --product oneTBB --repo uxlfoundation/oneTBB --count 5

# 2. Generate questions
python cli.py questions generate --product oneTBB --personas personas/oneTBB.json --count 2

# 3. Generate answers (with and without docs)
python cli.py answers generate --product oneTBB --questions questions/oneTBB.json --model gpt-4o

# 4. Run evaluation
python cli.py eval score --product oneTBB --answers answers/oneTBB.json \
  --judge-model claude-sonnet-4 --judge-provider anthropic

# 5. Generate report
python cli.py report generate --product oneTBB --eval eval/oneTBB.json
```

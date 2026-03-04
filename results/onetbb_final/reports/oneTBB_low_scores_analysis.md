# oneTBB Doc Quality — Low Score Analysis

**Date:** 2026-03-04  
**Dataset:** `results/onetbb_final` (80 questions)  
**Judge model:** claude-sonnet-4-6

---

## Summary Statistics

| Mode | Min | Avg | Max |
|------|-----|-----|-----|
| Without docs (`without_docs`) | 42 | 84.4 | 100 |
| With docs (`with_docs`) | 24 | 84.3 | 100 |

- **docs_helped:** 50 questions (62.5%) — documentation improved the answer
- **knowledge_sufficient:** 30 questions (37.5%) — model answered well without docs

---

## 1. Lowest-Rated Questions — WITHOUT Documentation

_Areas where LLM answers poorly from built-in knowledge alone. Documentation can make a significant difference here._

| # | Score (no→with) | Δ | Question ID | Topic |
|---|----------------|---|-------------|-------|
| 1 | 42 → 54 | +12 | q_026 | Preprocessor macros / CMake options to disable dynamic memory allocation and use a custom allocator |
| 2 | 51 → 67 | +16 | onetbb-Q005 | Reader-writer mutex: `spin_rw_mutex` vs `speculative_spin_rw_mutex` in read-mostly workloads |
| 3 | 55 → **94** | **+39** | q_008 | Performance of `tbb::feeder` vs `parallel_for` with lazy evaluation |
| 4 | 56 → 63 | +7 | q_018 | CMake configuration: arena observers + `tbb::feeder` for scheduling debug |
| 5 | 61 → **92** | **+31** | onetbb-Q001 | Data race when incrementing a member counter inside `parallel_for` body |
| 6 | 64 → **93** | **+29** | q_016 | Task stealing: `tbb::task` vs custom work queue with explicit task affinity |
| 7 | 67 → 76 | +9 | onetbb-Q013 | Iterator safety on `concurrent_vector` during concurrent appends |
| 8 | 73 → 87 | +14 | q_036 | `std::move` with concurrent containers — moved-from object state |
| 9 | 73 → 88 | +15 | onetbb-Q021 | NUMA/hybrid CPU: locality via `task_arena` + `constraints` |
| 10 | 76 → 87 | +11 | q_013 | `task_group` vs `task_arena` — thread participation control |

### Key weaknesses (without docs):

| Issue | Questions |
|-------|-----------|
| **Incorrect / broken code** (`code_quality` < 50) | q_026, q_008, onetbb-Q001, q_016 |
| **Factually wrong** (`correctness` < 50) | q_026, onetbb-Q005, q_008, q_018, onetbb-Q013 |
| **Not actionable** (`actionability` < 30) | onetbb-Q005 |

### Documentation improvements needed:

1. **CMake custom allocator** — the `TBBmalloc_proxy` / `TBBMALLOC_SCALABLE_PROXY` section lacks working end-to-end examples
2. **`spin_rw_mutex` vs `speculative_spin_rw_mutex`** — missing read-heavy vs write-heavy performance comparison with code
3. **`tbb::feeder` performance** — no benchmark comparison with `parallel_for`
4. **Arena observers** — no combined CMake + observer API example
5. **Data race anti-patterns in `parallel_for`** — needs an explicit anti-pattern section with race-free counter patterns
6. **NUMA `task_arena::constraints`** — examples exist but are scattered; consolidate into a single how-to guide

---

## 2. Lowest-Rated Questions — WITH Documentation

_Areas where documentation actively misleads or is insufficient — critical to fix._

| # | Score (no→with) | Δ | Question ID | Topic |
|---|----------------|---|-------------|-------|
| 1 | **94 → 24** | **-70** | q_044 | Iterator/reference invalidation in `concurrent_vector` on segment expansion |
| 2 | **77 → 38** | **-39** | q_019 | CMake: install only flow graph components without full task scheduler |
| 3 | **81 → 55** | **-26** | q_020 | Thread pinning for flow graph nodes (inference latency) |
| 4 | **84 → 57** | **-27** | q_032 | `tbb::flow` dynamic allocation for nodes — compile-time alternatives |
| 5 | **86 → 63** | **-23** | q_035 | CMake linking + `std::move` with `concurrent_vector` without data races |
| 6 | **86 → 63** | **-23** | q_052 | Blocking inside `parallel_for` on `std::cout` — thread utilization impact |
| 7 | **87 → 67** | **-20** | q_049 | `parallel_do_feeder` non-blocking push — cache coherence implications |
| 8 | **100 → 73** | **-27** | onetbb-Q011 | Exception handling inside parallel algorithms |

### Specific documentation errors (require fixes):

#### 🔴 Critical — documentation actively misleads:

**q_044 — `concurrent_vector` iterator invalidation (Δ -70)**
> Documentation contains an **incorrect claim**: element references in `concurrent_vector` may become invalid on expansion. In fact, `concurrent_vector` **guarantees reference stability**. This must be corrected — the current text will cause users to add unnecessary defensive code.

**q_019 — CMake component install (Δ -39)**
> Documentation describes flags that either don't exist or don't work as described. Users follow the instructions and cannot find the expected component. Needs an up-to-date example using `find_package(TBB COMPONENTS tbb)`.

**q_032 — flow graph node allocation (Δ -27)**
> Code sample has a **semantic error**: nodes are created on the stack, but `graph` takes ownership and expects heap allocation. The code compiles but causes undefined behavior at runtime.

#### 🟡 Significant — documentation is incomplete or misleading:

**q_020 — Thread pinning (Δ -26)**
> Documentation recommends low-level OS pinning (`pthread_setaffinity`) without mentioning `task_arena::constraints` — the correct TBB-native approach.

**onetbb-Q005 — Reader-writer mutex default (Δ -16 with docs)**
> Documentation contains an **error in the default value**: `scoped_lock(mutex, bool write=?)` — incorrect default is documented. Needs verification and correction.

---

## 3. Prioritized Fix List

| Priority | Topic | Action |
|----------|-------|--------|
| 🔴 P0 | `concurrent_vector` reference/iterator stability | Fix incorrect claim — references do NOT invalidate |
| 🔴 P0 | `tbb::flow` node stack allocation pattern | Fix code example (UB on heap ownership) |
| 🔴 P0 | `scoped_lock` default write flag | Verify and correct documented default |
| 🔴 P1 | CMake component install for flow graph | Update with working `find_package` example |
| 🟡 P1 | `task_arena::constraints` for thread pinning | Add as primary recommended approach |
| 🟡 P2 | CMake custom allocator / `TBBmalloc_proxy` | Expand with end-to-end example |
| 🟡 P2 | NUMA + constraints how-to guide | Consolidate scattered examples into one page |
| 🟢 P3 | Data race anti-patterns in `parallel_for` | Add anti-pattern section with race-free examples |
| 🟢 P3 | `tbb::feeder` vs `parallel_for` performance | Add benchmark comparison |

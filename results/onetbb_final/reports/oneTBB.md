# oneTBB Documentation Quality Report
_Generated: 2026-03-04 12:44 PST_
## Run Configuration
| | |
|---|---|
| Answer model | gpt-4o (openai) |
| Judge model | gemini-2.5-pro (google-vertex) |
| Retrieval | Semantic (all-MiniLM-L6-v2), k=3 |
| Doc source | context7 MCP |
| Total questions | 80 (56 dynamic + 24 golden static) |

## Summary
| Set | Count | WITH docs | WITHOUT docs | Delta |
|---|---:|---:|---:|---:|
| **All** | 80 | 84.3 | 84.4 | **-0.1** |
| Generated (dynamic) | 56 | 82.5 | 84.0 | **-1.5** |
| Golden (static) | 24 | 88.5 | 85.5 | **+3.0** |

## Retrieval Method Comparison (all oneTBB runs)
| Method | k | WITH | WITHOUT | Delta |
|---|---:|---:|---:|---:|
| Ablation (keyword) | 1 | 82.1 | 85.5 | **-3.5** |
| Ablation (keyword) | 3 | 51.8 | 84.9 | **-33.1** |
| Ablation (keyword) | 5 | 45.1 | 84.7 | **-39.6** |
| Semantic | 1 | 83.5 | 83.4 | **+0.0** |
| Semantic | 3 | 83.1 | 83.5 | **-0.4** |
| **Semantic + golden** | 3 | 84.3 | 84.4 | **-0.1** |

## Top 10 — docs helped most
| QID | Source | Delta | WITH | WITHOUT | Question |
|---|---|---:|---:|---:|---|
| q_008 | 🟡 gen | **+39.0** | 94 | 55 | How does oneTBB's task_scheduler handle std::pair in a NUMA environment compared... |
| onetbb-Q001 | 🔵 static | **+31.0** | 92 | 61 | Scenario: In oneapi::tbb::parallel_for over blocked_range<size_t>, your body fun... |
| q_016 | 🟡 gen | **+29.0** | 93 | 64 | How does tbb::flow compare to MPI in managing data dependencies and synchronizat... |
| q_027 | 🟡 gen | **+16.0** | 94 | 78 | What performance improvements can I expect when using tbb::parallel_do_each for ... |
| onetbb-Q005 | 🔵 static | **+16.0** | 67 | 51 | Scenario: You have a shared read-mostly data structure with frequent readers and... |
| onetbb-Q021 | 🔵 static | **+15.0** | 88 | 73 | Performance tuning scenario (NUMA/hybrid CPUs): You want to improve locality by ... |
| q_036 | 🟡 gen | **+14.0** | 87 | 73 | How can I resolve a deadlock when implementing the parallel_do pattern in oneTBB... |
| onetbb-Q022 | 🔵 static | **+13.0** | 99 | 86 | Scenario: In a fine-grained recursive task algorithm, you observe heavy deque tr... |
| q_011 | 🟡 gen | **+12.0** | 94 | 82 | What is the purpose of info::default_concurrency in oneTBB, and how does it affe... |
| q_026 | 🟡 gen | **+12.0** | 54 | 42 | What happens if a tbb::task_group is used without proper workload balancing betw... |

## Full Q&A Table
| QID | Source | Difficulty | WITH | WITHOUT | Delta | Question |
|---|---|---|---:|---:|---:|---|
| onetbb-Q001 | **static** | easy | 92 | 61 | +31.0 | Scenario: In oneapi::tbb::parallel_for over blocked_range<size_t>, you... |
| onetbb-Q002 | **static** | easy | 86 | 78 | +8.0 | Scenario: You have a simple loop that runs about 100 microseconds on a... |
| onetbb-Q003 | **static** | easy | 99 | 97 | +2.0 | Scenario: You are converting a producer/consumer queue from std::queue... |
| onetbb-Q004 | **static** | easy | 96 | 97 | -1.0 | Scenario: A teammate proposes iterating over oneapi::tbb::concurrent_q... |
| onetbb-Q005 | **static** | easy | 67 | 51 | +16.0 | Scenario: You have a shared read-mostly data structure with frequent r... |
| onetbb-Q006 | **static** | easy | 90 | 97 | -7.0 | Migration scenario: Legacy TBB code used tbb::task_scheduler_init both... |
| onetbb-Q007 | **static** | easy | 84 | 93 | -9.0 | Debugging scenario: You suspect misuse of oneTBB API contracts and wan... |
| onetbb-Q008 | **static** | easy | 91 | 96 | -5.0 | Migration scenario: Legacy TBB code relied on tbb::task_scheduler_init... |
| onetbb-Q009 | **static** | medium | 98 | 88 | +10.0 | Scenario: Your loop body allocates a temporary buffer proportional to ... |
| onetbb-Q010 | **static** | medium | 94 | 92 | +2.0 | Scenario: You are diagnosing cache-locality issues and surprising inte... |
| onetbb-Q011 | **static** | medium | 73 | 100 | -27.0 | Scenario: A oneTBB parallel algorithm body throws an exception while o... |
| onetbb-Q012 | **static** | medium | 89 | 86 | +3.0 | Scenario: Your concurrent_hash_map-based cache intermittently stalls u... |
| onetbb-Q013 | **static** | medium | 76 | 67 | +9.0 | Scenario: Multiple threads append records to a shared oneapi::tbb::con... |
| onetbb-Q014 | **static** | medium | 86 | 86 | +0.0 | Scenario: A teammate implements parallel_reduce with a SumFoo-like bod... |
| onetbb-Q015 | **static** | medium | 86 | 91 | -5.0 | Scenario: You want to use oneapi::tbb::parallel_for(first, last, step,... |
| onetbb-Q016 | **static** | medium | 86 | 86 | +0.0 | Scenario: You want to stop a long-running parallel_for early when a co... |
| onetbb-Q017 | **static** | medium | 96 | 88 | +8.0 | Migration scenario: Legacy code uses the removed low-level task API (d... |
| onetbb-Q018 | **static** | hard | 99 | 89 | +10.0 | Scenario: You set blocked_range(begin, end, g=1000) and assume no task... |
| onetbb-Q019 | **static** | hard | 89 | 89 | +0.0 | Scenario: You need reproducible results across runs and thread counts ... |
| onetbb-Q020 | **static** | hard | 88 | 86 | +2.0 | Scenario: A nested parallel_for unexpectedly breaks an invariant store... |
| onetbb-Q021 | **static** | hard | 88 | 73 | +15.0 | Performance tuning scenario (NUMA/hybrid CPUs): You want to improve lo... |
| onetbb-Q022 | **static** | hard | 99 | 86 | +13.0 | Scenario: In a fine-grained recursive task algorithm, you observe heav... |
| onetbb-Q023 | **static** | hard | 95 | 86 | +9.0 | Compatibility/performance scenario: Your app depends on a third-party ... |
| onetbb-Q024 | **static** | hard | 76 | 88 | -12.0 | Scenario: In a complex service, multiple application threads share a s... |
| q_001 | gen | advanced | 92 | 84 | +8.0 | How do I set up oneTBB's tbb::feeder in a NUMA-aware environment to en... |
| q_002 | gen | advanced | 99 | 90 | +9.0 | How can I configure the affinity_partitioner with tbb::feeder to optim... |
| q_003 | gen | advanced | 89 | 83 | +6.0 | What is the difference between 'task_arena' and 'task_scheduler' in on... |
| q_004 | gen | advanced | 91 | 86 | +5.0 | Why does oneTBB perform better on NUMA architectures when using 'affin... |
| q_005 | gen | advanced | 89 | 93 | -4.0 | What is the difference between using tbb::parallel_do and tbb::paralle... |
| q_006 | gen | advanced | 86 | 86 | +0.0 | When comparing oneTBB's tbb::parallel_do with OpenMP's parallel loops,... |
| q_007 | gen | advanced | 86 | 88 | -2.0 | What are the performance implications of using std::pair within oneTBB... |
| q_008 | gen | advanced | 94 | 55 | +39.0 | How does oneTBB's task_scheduler handle std::pair in a NUMA environmen... |
| q_009 | gen | advanced | 96 | 92 | +4.0 | What is the difference in data affinity management between tbb::parall... |
| q_010 | gen | advanced | 86 | 86 | +0.0 | How does tbb::parallel_do_each compare to OpenMP's tasking model in te... |
| q_011 | gen | advanced | 94 | 82 | +12.0 | What is the purpose of info::default_concurrency in oneTBB, and how do... |
| q_012 | gen | advanced | 86 | 86 | +0.0 | Why would a scientific computing researcher choose to utilize info::de... |
| q_013 | gen | advanced | 87 | 76 | +11.0 | What is the difference between tbb::task_group and tbb::parallel_invok... |
| q_014 | gen | advanced | 86 | 86 | +0.0 | When should I use tbb::task_group instead of tbb::parallel_pipeline in... |
| q_015 | gen | advanced | 79 | 81 | -2.0 | What is the difference between the tbb::flow::graph's broadcast_node a... |
| q_016 | gen | advanced | 93 | 64 | +29.0 | How does tbb::flow compare to MPI in managing data dependencies and sy... |
| q_017 | gen | intermediate | 84 | 93 | -9.0 | What happens if exceptions are thrown within a task scheduled by oneTB... |
| q_018 | gen | intermediate | 63 | 56 | +7.0 | Why does using oneTBB's parallel_for with std::vector sometimes lead t... |
| q_019 | gen | intermediate | 38 | 77 | -39.0 | What is the difference between task_arena in oneTBB and std::thread wh... |
| q_020 | gen | intermediate | 55 | 81 | -26.0 | How does oneTBB handle exceptions differently compared to using a simp... |
| q_021 | gen | intermediate | 91 | 92 | -1.0 | What happens if multiple instances of tbb::global_control are created ... |
| q_022 | gen | intermediate | 94 | 89 | +5.0 | Why does oneTBB global control not enforce my thread pool limits prope... |
| q_023 | gen | intermediate | 90 | 92 | -2.0 | What speedup can I expect when using tbb::parallel_do_each for iterati... |
| q_024 | gen | intermediate | 74 | 86 | -12.0 | How does oneTBB manage thread compatibility when using tbb::parallel_d... |
| q_025 | gen | advanced | 87 | 86 | +1.0 | How do I configure tbb::task_group to manage CPU and GPU tasks separat... |
| q_026 | gen | advanced | 54 | 42 | +12.0 | What happens if a tbb::task_group is used without proper workload bala... |
| q_027 | gen | advanced | 94 | 78 | +16.0 | What performance improvements can I expect when using tbb::parallel_do... |
| q_028 | gen | advanced | 88 | 88 | +0.0 | Why does oneTBB handle dynamic workload balancing differently in tbb::... |
| q_029 | gen | advanced | 92 | 80 | +12.0 | What speedup can I expect from using oneTBB tasks over std::this_threa... |
| q_030 | gen | advanced | 92 | 86 | +6.0 | What are the trade-offs of utilizing oneTBB's task-based parallelism c... |
| q_031 | gen | advanced | 89 | 86 | +3.0 | How does oneTBB's task scheduler compare to OpenMP's in terms of minim... |
| q_032 | gen | advanced | 57 | 84 | -27.0 | What are the differences in memory management between oneTBB's concurr... |
| q_033 | gen | beginner | 84 | 89 | -5.0 | What is the difference between using tbb::parallel_do_each and tbb::pa... |
| q_034 | gen | beginner | 91 | 94 | -3.0 | How is tbb::parallel_do_each in oneTBB different from using OpenMP for... |
| q_035 | gen | beginner | 63 | 86 | -23.0 | What should I do if my application crashes when using tbb::parallel_do... |
| q_036 | gen | beginner | 87 | 73 | +14.0 | How can I resolve a deadlock when implementing the parallel_do pattern... |
| q_037 | gen | beginner | 86 | 86 | +0.0 | How do I install oneTBB on my Windows system to start developing paral... |
| q_038 | gen | beginner | 86 | 86 | +0.0 | How do I set up oneTBB to execute a basic parallel_for loop in my C++ ... |
| q_039 | gen | beginner | 86 | 93 | -7.0 | Why does oneTBB sometimes cause unexpected performance degradation whe... |
| q_040 | gen | beginner | 88 | 82 | +6.0 | What should I do if my program crashes when combining oneTBB tasks wit... |
| q_041 | gen | advanced | 93 | 88 | +5.0 | How do I configure tbb::parallel_do_feeder to optimize cross-platform ... |
| q_042 | gen | advanced | 85 | 91 | -6.0 | What happens if an exception occurs within a body executed by tbb::par... |
| q_043 | gen | advanced | 91 | 87 | +4.0 | How do I configure tbb::parallel_do_each in oneTBB to ensure optimal c... |
| q_044 | gen | advanced | 24 | 94 | -70.0 | What happens if a null iterator is passed to tbb::parallel_do_each in ... |
| q_045 | gen | advanced | 86 | 77 | +9.0 | What specific handling does oneTBB provide for concurrent modification... |
| q_046 | gen | advanced | 83 | 88 | -5.0 | How does oneTBB ensure thread safety and what potential issues should ... |
| q_047 | gen | advanced | 86 | 90 | -4.0 | What performance trade-offs should I consider when using oneTBB's task... |
| q_048 | gen | advanced | 90 | 86 | +4.0 | How does oneTBB handle load balancing under high contention scenarios,... |
| q_049 | gen | intermediate | 67 | 87 | -20.0 | What is the difference between using tbb::task_group and a traditional... |
| q_050 | gen | intermediate | 86 | 86 | +0.0 | How does oneTBB's tbb::task_group compare to OpenMP for thread-level p... |
| q_051 | gen | intermediate | 90 | 88 | +2.0 | What is the difference between using task_arena and task_group in oneT... |
| q_052 | gen | intermediate | 63 | 86 | -23.0 | How does the memory footprint of using oneTBB's parallel_for compare t... |
| q_053 | gen | intermediate | 80 | 89 | -9.0 | What performance trade-offs should I consider when using tbb::flow in ... |
| q_054 | gen | intermediate | 84 | 84 | +0.0 | What expected speedup can I achieve with tbb::flow when scheduling mul... |
| q_055 | gen | intermediate | 75 | 85 | -10.0 | What is the difference in memory footprint when using oneTBB's task-ba... |
| q_056 | gen | intermediate | 90 | 93 | -3.0 | How does the task scheduling efficiency of oneTBB compare to OpenMP fo... |

---

## Low Score Analysis

### Score Distribution

| Mode | Min | Avg | Max |
|------|-----|-----|-----|
| Without docs | 42 | 84.4 | 100 |
| With docs | 24 | 84.3 | 100 |

- **docs_helped:** 50 questions (62.5%) — documentation improved the answer
- **knowledge_sufficient:** 30 questions (37.5%) — model answered well without docs

---

### Lowest-Rated Questions — WITHOUT Documentation

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

**Key weaknesses without docs:**

| Issue | Questions |
|-------|-----------|
| Incorrect / broken code (`code_quality` < 50) | q_026, q_008, onetbb-Q001, q_016 |
| Factually wrong (`correctness` < 50) | q_026, onetbb-Q005, q_008, q_018, onetbb-Q013 |
| Not actionable (`actionability` < 30) | onetbb-Q005 |

**Documentation improvements needed:**

1. **CMake custom allocator** — the `TBBmalloc_proxy` / `TBBMALLOC_SCALABLE_PROXY` section lacks working end-to-end examples
2. **`spin_rw_mutex` vs `speculative_spin_rw_mutex`** — missing read-heavy vs write-heavy performance comparison with code
3. **`tbb::feeder` performance** — no benchmark comparison with `parallel_for`
4. **Arena observers** — no combined CMake + observer API example
5. **Data race anti-patterns in `parallel_for`** — needs an explicit anti-pattern section with race-free counter patterns
6. **NUMA `task_arena::constraints`** — examples exist but are scattered; consolidate into a single how-to guide

---

### Lowest-Rated Questions — WITH Documentation

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

**Specific documentation errors (require fixes):**

🔴 **q_044 — `concurrent_vector` iterator invalidation (Δ -70)**
Documentation contains an incorrect claim: element references in `concurrent_vector` may become invalid on expansion. In fact, `concurrent_vector` guarantees reference stability. This must be corrected.

🔴 **q_019 — CMake component install (Δ -39)**
Documentation describes flags that either don't exist or don't work as described. Needs an up-to-date example using `find_package(TBB COMPONENTS tbb)`.

🔴 **q_032 — flow graph node allocation (Δ -27)**
Code sample has a semantic error: nodes are created on the stack, but `graph` takes ownership and expects heap allocation. The code compiles but causes undefined behavior at runtime.

🟡 **q_020 — Thread pinning (Δ -26)**
Documentation recommends low-level OS pinning (`pthread_setaffinity`) without mentioning `task_arena::constraints` — the correct TBB-native approach.

🟡 **onetbb-Q005 — Reader-writer mutex default (Δ -16 with docs)**
Documentation contains an error in the `scoped_lock` default write flag. Needs verification and correction.

---

### Prioritized Fix List

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

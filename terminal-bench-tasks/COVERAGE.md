# Executable task coverage (Intel oneAPI components)

This document tracks which Intel oneAPI APIs and concepts are covered by
terminal-bench-style coding tasks, and the planned gaps per component.

## oneTBB

This matrix tracks which oneTBB APIs and concepts are covered by terminal-bench-style coding tasks.

| API / concept | Task | Status | Verifier strategy |
| --- | --- | --- | --- |
| `parallel_sort` | `onetbb-parallel-sort` | merged | Sort correctness, runtime bound, source marker checks |
| `parallel_for` + `parallel_reduce` | `onetbb-nstream` | merged | Serial checksum comparison, source marker checks |
| `blocked_range2d` stencil update | `onetbb-stencil` | merged | Serial norm comparison, source marker checks |
| `blocked_range2d` transpose | `onetbb-transpose` | merged | Serial probe-signature comparison, source marker checks |
| `parallel_reduce` | `onetbb-parallel-reduce` | implemented | Serial aggregate comparison, source marker checks |
| `parallel_scan` | `onetbb-parallel-scan` | implemented | Serial prefix signature comparison, source marker checks |
| `flow::graph` | `onetbb-flow-graph` | implemented | Deterministic graph output comparison, graph API checks |
| `task_group` | TBD | candidate | Dependency/task execution validation |
| `concurrent_hash_map` | TBD | candidate | Concurrent update correctness and source API checks |
| `task_arena` / `global_control` | TBD | candidate | Thread-limit behavior and source API checks |

## Other oneAPI components

These tasks live in the separate `terminal-bench-verify-oneapi` CI job because
they pull the Intel oneAPI apt repo, header-only oneDPL from GitHub, or pip
wheels at **build** time. The verifier still runs offline (`--network none`).

| Component | API / concept | Task | Status | Verifier strategy |
| --- | --- | --- | --- | --- |
| oneMKL | `cblas_dgemm` (BLAS) | `onemkl-dgemm` | implemented | Signature (sum of `C=A*B`) vs serial triple-loop reference; runtime bound; source markers (`cblas_dgemm`, `mkl.h`) |
| oneMKL | DFTI FFT | `onemkl-fft` | implemented | Dominant-bin + magnitude-sum vs naive DFT reference, forward/backward round-trip error; source markers |
| oneDPL | `transform_reduce` + `par_unseq` | `onedpl-transform-reduce` | implemented | Sum-of-squares signature vs serial reference; runtime bound; source markers (`oneapi/dpl`, `transform_reduce`, `execution::par`) |
| IPP | `ippsDotProd_64f` | `ipp-dotprod` | implemented | Dot-product signature vs serial reference; source markers (`ippsDotProd_64f`, `ipp.h`) |
| oneCCL | `allreduce` over MPI | `oneccl-allreduce` | implemented (CI-pending) | Multi-rank sum vs analytic `N*(N+1)/2`; source markers (`oneapi/ccl.hpp`, `allreduce`) |
| sklearnex | `patch_sklearn()` + KNN | `sklearnex-classification` | implemented | Accuracy within 0.02 of stock scikit-learn reference; source markers (`sklearnex`, `patch_sklearn`) |

### Candidate tasks per component

| Component | Candidate task | Validation idea |
| --- | --- | --- |
| oneMKL | `onemkl-rng` | RNG stream with a fixed seed → exact reproducible sum/mean vs an independently computed reference |
| oneMKL | `onemkl-lapack` | Solve `Ax=b` with `LAPACKE_dgesv`, verify residual `‖Ax-b‖` is tiny |
| oneMKL | `onemkl-sparse` | Sparse mat-vec (`mkl_sparse_d_mv`) vs dense reference signature |
| oneDPL | `onedpl-sort` | `oneapi::dpl::sort` with a parallel policy; verify sortedness + multiset equality |
| oneDPL | `onedpl-scan` | `inclusive_scan` prefix signature vs serial reference |
| oneDNN | `onednn-relu` / `onednn-gemm` | Single primitive output vs a serial reference array, exact within fp tolerance |
| IPP | `ipp-image-resize` | `ippiResize` on a deterministic raster; verify pixel checksum vs a serial bilinear reference |
| IPP-CP | `ippcp-aes` | AES-128 encrypt→decrypt round-trip recovers plaintext; KAT vector match |
| oneCCL | `oneccl-allgather` / `oneccl-reduce` | Per-rank contributions vs analytic gathered/reduced result |
| sklearnex | `sklearnex-kmeans` / `sklearnex-pca` | Cluster inertia / explained-variance within tolerance of stock sklearn |
| OpenMP | `openmp-reduce` | `#pragma omp parallel for reduction` checksum vs serial (offline, stock `-fopenmp`) |
| oneDNN | `onednn-conv` | Small convolution vs a serial reference output tensor signature |

## Notes for new tasks

Prefer deterministic, small workloads that can be verified offline in CI. Each
task should have a serial reference or an independently computed expected result
so verifiers reject keyword-only implementations. Runtime thresholds should be
conservative enough to avoid flaky CI while still detecting obviously
inefficient or non-terminating solutions.

Validation patterns used across components:

1. **Serial reference signature** — ship a small serial program (built in the
   Dockerfile) that computes a deterministic scalar/array signature; the
   verifier runs both and compares within a tolerance. Used by every numeric
   task here.
2. **Analytic expected value** — when a serial reference is awkward (e.g.
   collectives), derive the answer in closed form (`oneccl-allreduce` uses
   `N*(N+1)/2`).
3. **Round-trip invariants** — forward/backward transforms (FFT) or
   encrypt/decrypt (crypto) must recover the input within tolerance.
4. **Drop-in reference** — for accelerator libraries (sklearnex), compare
   against the stock library it accelerates and require the result to match
   closely.
5. **Source API markers** — grep the agent's source for the required API
   symbols/headers so a hard-coded or keyword-only answer is rejected.

For components whose dependencies are large or only available via the Intel
oneAPI apt repo, add the task to the `terminal-bench-verify-oneapi` CI job and
build/verify/cleanup one image at a time to respect the runner disk budget.

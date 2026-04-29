# oneTBB tiled matrix transpose

You are given `/app/transpose.cpp`, a serial C++17 implementation of a matrix transpose inspired by the Parallel Research Kernels transpose workload.

Create a oneTBB implementation that:

1. Initializes an `n x n` matrix deterministically.
2. Repeatedly computes `B[j,i] = A[i,j] + iter`.
3. Validates several probe locations.
4. Writes an executable binary at `/app/transpose_tbb`.

Requirements:

- Use oneTBB parallelism, preferably `tbb::parallel_for` / `oneapi::tbb::parallel_for` with `blocked_range2d` or another tiled approach.
- Accept optional CLI arguments: `<matrix_order> <iterations> [tile_size]`.
- Print a line containing `VALID` when validation passes.

A typical compile command is:

```bash
g++ -O3 -std=c++17 /app/transpose_tbb.cpp -ltbb -o /app/transpose_tbb
```

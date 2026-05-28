# oneCCL allreduce across MPI ranks

Implement a oneCCL program that performs a sum **allreduce** across multiple MPI
ranks on a single node. There is no serial seed file; the expected result is
defined analytically.

Create a oneCCL implementation that:

1. Initializes MPI and oneCCL, and builds a oneCCL communicator using a KVS
   exchanged over MPI (rank 0 creates the main KVS, broadcasts its address).
2. Each rank fills a `float` buffer of length 1024 with the value `rank + 1`.
3. Performs `ccl::allreduce(..., ccl::reduction::sum, ...)`.
4. On rank 0, prints a line containing `VALID` with
   `ranks=<N> value=<v> expected=<e>`, where `value` is the first element of the
   reduced buffer and `expected = N*(N+1)/2` (the sum of `rank+1` over all ranks).
5. Writes an executable binary at `/app/ccl_allreduce` (run with `mpirun -n 4`).

Requirements:

- Use a real `ccl::allreduce` collective, not a manual reduction.
- Include `"oneapi/ccl.hpp"` and use a oneCCL communicator.

oneCCL and Intel MPI are preinstalled. A typical compile command is:

```bash
mpicxx -std=c++17 /app/ccl_allreduce.cpp -lccl -o /app/ccl_allreduce
mpirun -n 4 /app/ccl_allreduce
```

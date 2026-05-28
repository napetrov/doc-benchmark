#!/usr/bin/env bash
set -euo pipefail

cat > /app/ccl_allreduce.cpp <<'CPP'
#include <mpi.h>
#include <vector>
#include <iostream>
#include "oneapi/ccl.hpp"

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int size = 0, rank = 0;
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    ccl::init();

    ccl::shared_ptr_class<ccl::kvs> kvs;
    ccl::kvs::address_type main_addr;
    if (rank == 0) {
        kvs = ccl::create_main_kvs();
        main_addr = kvs->get_address();
        MPI_Bcast((void *)main_addr.data(), main_addr.size(), MPI_BYTE, 0, MPI_COMM_WORLD);
    } else {
        MPI_Bcast((void *)main_addr.data(), main_addr.size(), MPI_BYTE, 0, MPI_COMM_WORLD);
        kvs = ccl::create_kvs(main_addr);
    }

    auto comm = ccl::create_communicator(size, rank, kvs);

    const size_t L = 1024;
    std::vector<float> send(L, (float)(rank + 1));
    std::vector<float> recv(L, 0.0f);

    ccl::allreduce(send.data(), recv.data(), L, ccl::reduction::sum, comm).wait();

    if (rank == 0) {
        float expected = (float)(size * (size + 1) / 2);
        std::cout << "VALID ccl allreduce ranks=" << size
                  << " value=" << recv[0]
                  << " expected=" << expected << "\n";
    }

    MPI_Finalize();
    return 0;
}
CPP

mpicxx -std=c++17 /app/ccl_allreduce.cpp -lccl -o /app/ccl_allreduce

#!/usr/bin/env bash
set -euo pipefail

cat > /app/dot_fast.cpp <<'CPP'
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>

static inline double a_value(std::size_t i) {
    return static_cast<double>((i * 17u + 13u) % 1024u) * 0.001 + 1.0;
}

static inline double b_value(std::size_t i) {
    return static_cast<double>((i * 29u + 7u) % 2048u) * 0.0005 - 0.25;
}

int main(int argc, char** argv) {
    const std::size_t n = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : 24000000ULL;
    if (n == 0) return 2;
    double acc0 = 0.0, acc1 = 0.0, acc2 = 0.0, acc3 = 0.0;
    double acc4 = 0.0, acc5 = 0.0, acc6 = 0.0, acc7 = 0.0;
    std::size_t i = 0;
    for (; i + 7 < n; i += 8) {
        acc0 += a_value(i + 0) * b_value(i + 0);
        acc1 += a_value(i + 1) * b_value(i + 1);
        acc2 += a_value(i + 2) * b_value(i + 2);
        acc3 += a_value(i + 3) * b_value(i + 3);
        acc4 += a_value(i + 4) * b_value(i + 4);
        acc5 += a_value(i + 5) * b_value(i + 5);
        acc6 += a_value(i + 6) * b_value(i + 6);
        acc7 += a_value(i + 7) * b_value(i + 7);
    }
    double sum = acc0 + acc1 + acc2 + acc3 + acc4 + acc5 + acc6 + acc7;
    for (; i < n; ++i) sum += a_value(i) * b_value(i);
    if (!std::isfinite(sum)) return 1;
    std::cout << std::setprecision(17) << "VALID dot=" << sum << "\n";
    return 0;
}
CPP

g++ -O3 -std=c++17 /app/dot_fast.cpp -o /app/dot_fast

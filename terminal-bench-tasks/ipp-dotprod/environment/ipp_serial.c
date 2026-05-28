/* Serial reference: dot product over two deterministic integer-valued vectors. */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    long n = argc > 1 ? atol(argv[1]) : 4000000;
    if (n < 1) {
        fprintf(stderr, "INVALID_ARGUMENTS\n");
        return 2;
    }
    double dot = 0.0;
    for (long i = 0; i < n; ++i) {
        double a = (double)(((i * 7 + 1) % 101) - 50);
        double b = (double)(((i * 13 + 3) % 97) - 48);
        dot += a * b;
    }
    printf("VALID ipp dot=%.10g\n", dot);
    return 0;
}

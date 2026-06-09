#!/usr/bin/env python3
"""A simple matrix multiplication program for Linux measurement lab.

It computes a simple O(n^3) multiplication with a checksum at the end
so the computation has an observable result.

"""

import sys
import time
from typing import List

Matrix = List[List[float]]

#The matrix entries are initialized deterministically so that every run uses
#the same data. The exact constants are not important; they only create 
#non-uniform values that vary by row and column.
def init_matrix(n: int, seed: float) -> Matrix:
    return [
        [seed + ((i * 131 + j * 17) % 100) / 100.0 for j in range(n)]
        for i in range(n)
    ]

#Zero out output entries.
def zero_matrix(n: int) -> Matrix:
    return [[0.0 for _ in range(n)] for _ in range(n)]


# Intentionally simple O(n^3) matrix multiplication.
# This loop order is correct but cache-unfriendly for matrix B.
def matmul_slow(a: Matrix, b: Matrix, c: Matrix, n: int) -> None:
    for i in range(n):
        for j in range(n):
            start_cell = time.perf_counter_ns()
            total = 0.0
            for k in range(n):
                total += a[i][k] * b[k][j]
            c[i][j] = total
            end_cell = time.perf_counter_ns()
            cell_times.append(end_cell - start_cell)
    print(f"Average cell time: {sum(cell_times)/len(cell_times):.2f} ns")


def checksum(m: Matrix, n: int) -> float:
    total = 0.0
    step = (n // 16) + 1
    for i in range(0, n, step):
        for j in range(0, n, step):
            total += m[i][j]
    return total


def usage(prog: str) -> None:
    print(
        f"Usage: {prog} [matrix_size] [repetitions]\n"
        "  matrix_size  : matrix dimension N for an N x N multiply (default: 192)\n"
        "  repetitions  : number of repeated multiplies (default: 1)",
        file=sys.stderr,
    )


def parse_args(argv: list[str]) -> tuple[int, int]:
    #Default values to use when none provided.
    n = 128
    reps = 2

    if len(argv) > 1:
        n = int(argv[1])
    if len(argv) > 2:
        reps = int(argv[2])
    if len(argv) > 3 or n <= 0 or reps <= 0:
        usage(argv[0])
        raise SystemExit(1)

    return n, reps


def main(argv: list[str]) -> int:
    n, reps = parse_args(argv)

    #Initialise around a seed.
    a = init_matrix(n, 1.0)
    b = init_matrix(n, 2.0)

    c = zero_matrix(n)
    start = time.perf_counter()
    for _ in range(reps):
        matmul_slow(a, b, c, n)
    end = time.perf_counter()

    
    print(f"Total matmul_slow time: {(end-start)*1000:.3f} ms")
    print(f"n={n} reps={reps} checksum={checksum(c, n):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

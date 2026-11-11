#!/usr/bin/env python3
# =============================================================================
# Monte Carlo pi benchmark — Python (CPython 3.14). Same per-point work shape
# as mc_pi.c but with an xorshift32: pure-Python 64-bit emulation (BigInt
# masking per step) distorts the measurement more than the width itself, and
# the 32-bit variant's cost is quantified separately against mc_pi32.c.
#
# Single thread only: the GIL prevents CPU-parallel threading. The xorshift is
# inlined and masked in the loop — the honest cost of idiomatic pure Python.
# Run with PYTHON_JIT=1 to measure the experimental copy-and-patch JIT; the
# runner gives that mode a warm-up round so the JIT is engaged before timing.
#
# Usage: python3 mc_pi.py <ignored-threads> <points>
# =============================================================================
import sys
import time

def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20_000_000
    m = 0xFFFFFFFF
    d = 1.0 / 4294967296.0
    st = (0x9E3779B9 ^ 1) & m
    h = 0
    t0 = time.monotonic()
    for _ in range(n):
        st = (st ^ (st << 13)) & m
        st ^= st >> 17
        st = (st ^ (st << 5)) & m
        x = st * d
        st = (st ^ (st << 13)) & m
        st ^= st >> 17
        st = (st ^ (st << 5)) & m
        y = st * d
        if x * x + y * y <= 1.0:
            h += 1
    ms = (time.monotonic() - t0) * 1000.0
    print(f"pi={4.0 * h / n:.5f} threads=1 points={n} ms={ms:.0f} rate={n / (ms / 1000.0):.4e}")

main()

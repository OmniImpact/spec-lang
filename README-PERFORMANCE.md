# Spec Performance vs Major Languages

Measured, reproducible cross-language comparison — not folklore. Three
benchmarks run across ten languages on one machine; the runner, every
language's source, and the measurement harness live under
[`utilities/benchmarks/`](utilities/benchmarks/) and
[`utilities/run_benchmarks.sh`](utilities/run_benchmarks.sh).

**Headline (Spec @ `34b9a3e`, `feature/llvm` direct LLVM IR backend + `SpecOptimizer`):**

- **Tight numeric loop (`mc_pi`):** Spec reaches **162.6M pts/s** (1 thread,
  `0.98× C`) and **995.0M pts/s** (8 threads, `0.98× C`, `0.204s` wall, **2.6 MB**
  RSS) — **at parity with C, C++, Rust, Go, and JVM** (and **2.17× faster**
  than the retired C backend's 75.0M / 461.9M pts/s).
- **Allocation & recursion (`binary_trees`):** Spec reaches **16.7M nodes/s**
  (1 thread, `0.45× C`, `0.64× Rust`) and scales `3.52×` to **58.8M nodes/s**
  (8 threads, `0.65× C`, `0.76× Rust`) — **3.7× faster than Python** and
  **4.6× faster than Ruby**.
- **Strings & hash maps (`word_freq`):** Spec processes **1.17M lines/s**
  (`0.33× C`, `0.34× Rust`) — **2.4× faster than Python and Ruby** — at
  **3.0 MB** peak RSS (matching C's 2.2 MB and Rust's 2.8 MB, vs ~193 MB on the JVM).

---

## The suites

1. **`mc_pi` (Monte Carlo π):** Two random draws per point, hit when
   `x² + y² ≤ 1`, summed across a thread fan-out (200M points compiled/JS; 20M
   Python/Ruby).
   - **RNG:** xorshift64 with the *same constants as Spec's own runtime*
     (`spec_rng_next`), per-thread deterministic seeds, three discarded warm-up
     draws. Java, Kotlin, Go, Rust, C++, C, and Spec all run this exact loop.
   - **JS/Python/Ruby lane:** xorshift32 (validated within **0.3%** of the
     64-bit anchor via `mc_pi32.c`).
2. **`binary_trees`:** Classic allocation/recursion tree-churn benchmark
   (depth 18 compiled/JS; depth 14 Python/Ruby), measuring nodes allocated and
   checked per second across 1 and 8 threads.
3. **`word_freq`:** Single-threaded string splitting and hash-map insertion
   throughput (1M lines compiled/JS; 200K Python/Ruby).

**Measurement:** every run is wrapped by
[`utilities/benchmarks/Measure.spec`](utilities/benchmarks/Measure.spec)
(compiled to a native Spec binary), which records wall time, total CPU time
across all threads, and peak RSS of the isolated child. **3 measured runs per
configuration; medians below.** Failed commands are never recorded as
datapoints.

**Environment:** AMD Ryzen AI 7 350 (8 cores / 16 threads), Linux 7.3.0,
`gcc`/`g++` 15.3.0 (`-O2`), `rustc` 1.97.1 (`-O`), `go` 1.27.1, OpenJDK 25.0.5,
`kotlinc` 1.3-SNAPSHOT (JRE 25.0.5), Node 24.21.0 (V8), CPython 3.14.8, CRuby
3.3.8 (built **without** YJIT), Spec @ `34b9a3e` (`feature/llvm`).

---

## Suite 1: `mc_pi` (median of 3 runs, 200M points; 20M for Python/Ruby)

| Language | Threads | Rate (pts/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|---|
| C (anchor) | 1 | 165,420,000 | 1.00 | 1.02 | 1.210 | 100% | 2.0 MB |
| C++ | 1 | 165,300,000 | 1.00 | 1.02 | 1.212 | 100% | 4.4 MB |
| Rust | 1 | 165,170,000 | 1.00 | 1.02 | 1.212 | 100% | 2.6 MB |
| Kotlin (JVM) | 1 | 165,150,000 | 1.00 | 1.02 | 2.189 | 103% | 48.0 MB |
| Go | 1 | 165,130,000 | 1.00 | 1.02 | 1.213 | 100% | 2.0 MB |
| Java (C2 JIT) | 1 | 164,880,000 | 1.00 | 1.01 | 2.191 | 102% | 47.6 MB |
| **Spec (LLVM + ARC)** | **1** | **162,600,000** | **0.98** | **1.00** | **1.232** | **100%** | **2.6 MB** |
| JavaScript (V8) | 1 | 93,944,000 | 0.57 | 0.58 | 2.382 | 100% | 53.8 MB |
| Ruby 3.3 (no YJIT) | 1 | 2,274,100 | 0.014 | 0.014 | 8.863 | 100% | 19.9 MB |
| Python 3.14 (JIT) | 1 | 1,534,900 | 0.009 | 0.009 | 13.053 | 100% | 11.1 MB |
| Python 3.14 | 1 | 1,447,000 | 0.009 | 0.009 | 13.840 | 100% | 10.8 MB |
| C (anchor) | 8 | 1,013,800,000 | 1.00 | 1.02 | 0.198 | 703% | 2.1 MB |
| C++ | 8 | 1,006,200,000 | 0.99 | 1.01 | 0.201 | 695% | 4.5 MB |
| Java (C2 JIT) | 8 | 1,000,000,000 | 0.99 | 1.00 | 0.480 | 651% | 47.7 MB |
| **Spec (LLVM + ARC)** | **8** | **995,020,000** | **0.98** | **1.00** | **0.204** | **690%** | **2.6 MB** |
| Kotlin (JVM) | 8 | 985,220,000 | 0.97 | 0.99 | 0.471 | 638% | 48.5 MB |
| Go | 8 | 981,180,000 | 0.97 | 0.99 | 0.206 | 687% | 2.1 MB |
| Rust | 8 | 980,870,000 | 0.97 | 0.99 | 0.205 | 688% | 2.6 MB |
| JavaScript (V8 workers) | 8 | 452,030,000 | 0.45 | 0.45 | 0.482 | 652% | 152.9 MB |

---

## Suite 2: `binary_trees` (median of 3 runs, depth 18; depth 14 for Python/Ruby)

| Language | Threads | Rate (nodes/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|---|
| Kotlin (JVM) | 1 | 154,250,000 | 4.19 | 9.23 | 0.552 | 137% | 434.4 MB |
| Java (C2 JIT) | 1 | 151,850,000 | 4.12 | 9.09 | 0.551 | 133% | 423.7 MB |
| JavaScript (V8) | 1 | 75,564,000 | 2.05 | 4.52 | 0.984 | 118% | 223.0 MB |
| Go | 1 | 43,654,000 | 1.18 | 2.61 | 1.570 | 266% | 37.6 MB |
| C (anchor) | 1 | 36,839,000 | 1.00 | 2.20 | 1.858 | 100% | 34.5 MB |
| C++ | 1 | 30,904,000 | 0.84 | 1.85 | 2.227 | 100% | 36.9 MB |
| Rust | 1 | 26,009,000 | 0.71 | 1.56 | 2.641 | 100% | 35.0 MB |
| **Spec (LLVM + ARC)** | **1** | **16,711,000** | **0.45** | **1.00** | **4.161** | **100%** | **207.2 MB** |
| Python 3.14 | 1 | 4,541,600 | 0.12 | 0.27 | 0.730 | 100% | 13.8 MB |
| Ruby 3.3 (no YJIT) | 1 | 3,609,800 | 0.10 | 0.22 | 0.962 | 100% | 23.5 MB |
| Kotlin (JVM) | 8 | 397,280,000 | 4.38 | 6.76 | 0.276 | 553% | 442.2 MB |
| Java (C2 JIT) | 8 | 355,900,000 | 3.92 | 6.06 | 0.302 | 521% | 586.5 MB |
| Go | 8 | 143,730,000 | 1.59 | 2.45 | 0.488 | 933% | 126.1 MB |
| C (anchor) | 8 | 90,681,000 | 1.00 | 1.54 | 0.758 | 632% | 165.3 MB |
| C++ | 8 | 86,701,000 | 0.96 | 1.48 | 0.812 | 631% | 167.7 MB |
| Rust | 8 | 77,561,000 | 0.86 | 1.32 | 0.906 | 623% | 149.2 MB |
| JavaScript (V8 workers) | 8 | 76,048,000 | 0.84 | 1.29 | 1.018 | 682% | 624.2 MB |
| **Spec (LLVM + ARC)** | **8** | **58,755,000** | **0.65** | **1.00** | **1.245** | **610%** | **785.7 MB** |

---

## Suite 3: `word_freq` (median of 3 runs, 1M lines; 200K for Python/Ruby)

| Language | Rate (lines/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|
| C++ | 3,840,200 | 1.09 | 3.29 | 0.263 | 100% | 4.6 MB |
| C (anchor) | 3,532,800 | 1.00 | 3.02 | 0.284 | 100% | 2.2 MB |
| Go | 3,472,700 | 0.98 | 2.97 | 0.291 | 106% | 7.9 MB |
| Rust | 3,408,600 | 0.96 | 2.92 | 0.295 | 100% | 2.8 MB |
| Java (C2 JIT) | 3,205,100 | 0.91 | 2.74 | 0.458 | 210% | 192.8 MB |
| Kotlin (JVM) | 2,816,900 | 0.80 | 2.41 | 0.522 | 196% | 193.9 MB |
| JavaScript (V8) | 1,697,700 | 0.48 | 1.45 | 0.663 | 103% | 58.7 MB |
| **Spec (LLVM + ARC)** | **1,168,200** | **0.33** | **1.00** | **0.858** | **100%** | **3.0 MB** |
| Ruby 3.3 (no YJIT) | 495,030 | 0.14 | 0.42 | 0.473 | 100% | 20.4 MB |
| Python 3.14 | 482,420 | 0.14 | 0.41 | 0.432 | 100% | 11.3 MB |

---

## Compile-time profile (build step per benchmark)

| Language | Build step | `mc_pi` wall / RSS | `binary_trees` wall / RSS | `word_freq` wall / RSS |
|---|---|---|---|---|
| C | `gcc -O2` | 0.094s / 32.5 MB | 0.256s / 39.5 MB | 0.112s / 33.8 MB |
| C++ | `g++ -O2` | 0.444s / 73.2 MB | 0.937s / 106.1 MB | 0.615s / 94.0 MB |
| Go | `go build` | 3.534s / 279.7 MB | 0.163s / 63.6 MB | 0.236s / 65.8 MB |
| Java | `javac` | 0.582s / 110.0 MB | 0.596s / 112.0 MB | 0.616s / 115.9 MB |
| Rust | `rustc -O` | 0.938s / 186.1 MB | 0.800s / 184.9 MB | 0.689s / 188.6 MB |
| Kotlin | `kotlinc` | 2.497s / 387.0 MB | 2.667s / 419.1 MB | 2.561s / 404.8 MB |
| **Spec** | **`bin/spec` → LLVM IR** | **3.627s / 110.2 MB** | **3.065s / 106.2 MB** | **2.984s / 106.6 MB** |
| Node / Python / Ruby | — (interpreted) | — | — | — |

---

## Caveats — read before quoting these numbers

1. **Three distinct shapes.** `mc_pi` stresses tight arithmetic + loop/call
   overhead; `binary_trees` stresses small-object allocation, recursion, and
   ARC vs tracing GC; `word_freq` stresses string slicing and hash-map churn.
2. **Interpreted-lane RNG width.** Python/Ruby/JS run xorshift32 in `mc_pi`
   (validated within ±0.3% against the 64-bit anchor in C).
3. **JVM/Node wall includes warm-up.** The wall column for Java/Kotlin/Node
   covers JVM/V8 start-up and in-process warm-up rounds; the *rate* is the
   measured round only.
4. **Ruby without YJIT.** This CRuby build has no YJIT; a YJIT-enabled Ruby
   would land meaningfully higher (though the GVL still caps it at one core).
5. **Python JIT is experimental** (`PYTHON_JIT=1`, opt-in) and gained ~6% on
   `mc_pi`.
6. **Reproduce on your own box:**

```bash
./bootstrap.sh                                   # build Spec
RUNS=3 PAR=8 utilities/run_benchmarks.sh         # all 3 suites, medians printed
```

Raw per-run data lands in `/tmp/spec-bench/results.csv` (`mc_pi`),
`/tmp/spec-bench/results_bt.csv` (`binary_trees`),
`/tmp/spec-bench/results_wf.csv` (`word_freq`), and
`/tmp/spec-bench/builds.csv` (compiles).

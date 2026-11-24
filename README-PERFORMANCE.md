# Spec Performance vs Major Languages

Measured, reproducible cross-language comparison — not folklore. Three
benchmarks run across nine languages on one machine; the runner, every
language's source, and the measurement harness live under
[`utilities/benchmarks/`](utilities/benchmarks/) and
[`utilities/run_benchmarks.sh`](utilities/run_benchmarks.sh).

**Headline (Spec `main` @ `d8064c2` — direct LLVM IR backend + pure-Spec ARC/Slab/Heap/Arena/Pool/Intern over OS VM floor + `SpecOptimizer`):**

- **Tight numeric loop (`mc_pi`):** Spec reaches **163.3M pts/s** (1 thread,
  `1.04× C`, `1.226s` wall, **3.3 MB** RSS) and **939.0M pts/s** (8 threads,
  `1.00× C`, `0.215s` wall, **3.3 MB** RSS; peak `980.4M`) — **at parity with
  C, C++, Rust, Go, and JVM** on both 1 and 8 threads.
- **Allocation & recursion (`binary_trees`):** Spec reaches **21.4M nodes/s**
  (1 thread, `0.58× C`, `0.83× Rust`) and scales to **49.3M nodes/s**
  (8 threads, `0.55× C`, `0.59× Rust`) — **4.7× faster than Python** and
  **6.0× faster than Ruby**, at **163.0 MB** (1t) / **611.0 MB** (8t) RSS.
- **Strings & hash maps (`word_freq`):** Spec processes **2.16M lines/s**
  (`0.63× C`, `0.64× Rust`, `0.68× Go`) — **4.5× faster than Python and Ruby** —
  at **3.1 MB** peak RSS (matching C's 2.2 MB and Rust's 2.7 MB, vs ~188 MB on the JVM).

---

## The suites

1. **`mc_pi` (Monte Carlo π):** Two random draws per point, hit when
   `x² + y² ≤ 1`, summed across a thread fan-out (200M points compiled; 20M
   Python/Ruby).
   - **RNG:** xorshift64 with the *same constants as Spec's own runtime*
     (`spec_rng_next`), per-thread deterministic seeds, three discarded warm-up
     draws. Java, Kotlin, Go, Rust, C++, C, and Spec all run this exact loop.
   - **Python/Ruby lane:** xorshift32 (validated against the 64-bit anchor via `mc_pi32.c`).
2. **`binary_trees`:** Classic allocation/recursion tree-churn benchmark
   (depth 18 compiled; depth 14 Python/Ruby), measuring nodes allocated and
   checked per second across 1 and 8 threads.
3. **`word_freq`:** Single-threaded string splitting and hash-map insertion
   throughput (1M lines compiled; 200K Python/Ruby), using `UInt64` xorshift64
   and `Array of Str` in Spec.

**Measurement:** every run is wrapped by
[`utilities/benchmarks/Measure.spec`](utilities/benchmarks/Measure.spec)
(compiled to a native Spec binary), which records wall time, total CPU time
across all threads, and peak RSS of the isolated child. **3 measured runs per
configuration; medians below.** Failed commands are never recorded as
datapoints.

**Environment:** AMD Ryzen AI 7 350 (8 cores / 16 threads), Linux,
`gcc`/`g++` (`-O2`), `rustc` (`-O`), `go`, OpenJDK, `kotlinc`, CPython 3.14,
CRuby 3.3 (built **without** YJIT), Spec @ `d8064c2` (`main`).

---

## Suite 1: `mc_pi` (median of 3 runs, 200M points; 20M for Python/Ruby)

| Language | Threads | Rate (pts/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|---|
| Go | 1 | 164,350,000 | 1.05 | 1.01 | 1.220 | 100% | 1.5 MB |
| Java (C2 JIT) | 1 | 164,340,000 | 1.05 | 1.01 | 2.219 | 102% | 46.6 MB |
| Rust | 1 | 164,190,000 | 1.05 | 1.01 | 1.220 | 100% | 2.5 MB |
| Kotlin (JVM) | 1 | 164,070,000 | 1.05 | 1.00 | 2.231 | 103% | 46.8 MB |
| **Spec (LLVM + ARC)** | **1** | **163,270,000** | **1.04** | **1.00** | **1.226** | **100%** | **3.3 MB** |
| C++ | 1 | 162,900,000 | 1.04 | 1.00 | 1.230 | 100% | 4.3 MB |
| C (anchor) | 1 | 156,240,000 | 1.00 | 0.96 | 1.282 | 100% | 2.0 MB |
| Ruby 3.3 (no YJIT) | 1 | 2,230,900 | 0.014 | 0.014 | 9.054 | 100% | 19.4 MB |
| Python 3.14 (JIT) | 1 | 1,515,400 | 0.010 | 0.009 | 13.225 | 100% | 10.8 MB |
| Python 3.14 | 1 | 1,439,900 | 0.009 | 0.009 | 13.910 | 100% | 10.5 MB |
| Kotlin (JVM) | 8 | 995,020,000 | 1.06 | 1.06 | 0.504 | 639% | 47.6 MB |
| Java (C2 JIT) | 8 | 943,400,000 | 1.01 | 1.00 | 0.514 | 627% | 46.9 MB |
| **Spec (LLVM + ARC)** | **8** | **938,970,000** | **1.00** | **1.00** | **0.215** | **681%** | **3.3 MB** |
| C (anchor) | 8 | 937,310,000 | 1.00 | 1.00 | 0.215 | 680% | 2.1 MB |
| Go | 8 | 930,870,000 | 0.99 | 0.99 | 0.217 | 696% | 1.6 MB |
| C++ | 8 | 881,830,000 | 0.94 | 0.94 | 0.229 | 668% | 4.4 MB |
| Rust | 8 | 867,700,000 | 0.93 | 0.92 | 0.232 | 662% | 2.5 MB |

---

## Suite 2: `binary_trees` (median of 3 runs, depth 18; depth 14 for Python/Ruby)

| Language | Threads | Rate (nodes/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|---|
| Kotlin (JVM) | 1 | 153,210,000 | 4.16 | 7.17 | 0.564 | 140% | 430.2 MB |
| Java (C2 JIT) | 1 | 151,510,000 | 4.11 | 7.09 | 0.559 | 130% | 413.8 MB |
| Go | 1 | 44,524,000 | 1.21 | 2.08 | 1.539 | 266% | 34.6 MB |
| C (anchor) | 1 | 36,857,000 | 1.00 | 1.72 | 1.859 | 100% | 33.8 MB |
| C++ | 1 | 30,210,000 | 0.82 | 1.41 | 2.278 | 100% | 36.1 MB |
| Rust | 1 | 25,658,000 | 0.70 | 1.20 | 2.677 | 100% | 34.3 MB |
| **Spec (LLVM + ARC + Slab)** | **1** | **21,381,000** | **0.58** | **1.00** | **3.228** | **100%** | **163.0 MB** |
| Python 3.14 | 1 | 4,515,100 | 0.12 | 0.21 | 0.734 | 100% | 13.5 MB |
| Ruby 3.3 (no YJIT) | 1 | 3,560,100 | 0.10 | 0.17 | 0.985 | 99% | 22.9 MB |
| Kotlin (JVM) | 8 | 379,620,000 | 4.22 | 7.71 | 0.303 | 524% | 563.8 MB |
| Java (C2 JIT) | 8 | 339,960,000 | 3.78 | 6.90 | 0.314 | 525% | 551.5 MB |
| Go | 8 | 139,850,000 | 1.56 | 2.84 | 0.500 | 931% | 112.3 MB |
| C (anchor) | 8 | 89,928,000 | 1.00 | 1.83 | 0.764 | 637% | 161.0 MB |
| C++ | 8 | 86,266,000 | 0.96 | 1.75 | 0.815 | 638% | 163.6 MB |
| Rust | 8 | 82,853,000 | 0.92 | 1.68 | 0.846 | 643% | 145.7 MB |
| **Spec (LLVM + ARC + Slab)** | **8** | **49,266,000** | **0.55** | **1.00** | **1.411** | **611%** | **611.0 MB** |

---

## Suite 3: `word_freq` (median of 3 runs, 1M lines; 200K for Python/Ruby)

| Language | Rate (lines/s) | × C | × Spec | Wall (s) | CPU util | Peak RSS |
|---|---|---|---|---|---|---|
| C++ | 3,682,700 | 1.07 | 1.70 | 0.274 | 100% | 4.4 MB |
| C (anchor) | 3,438,700 | 1.00 | 1.59 | 0.292 | 100% | 2.2 MB |
| Rust | 3,386,100 | 0.98 | 1.56 | 0.297 | 100% | 2.7 MB |
| Go | 3,196,900 | 0.93 | 1.48 | 0.316 | 107% | 7.1 MB |
| Java (C2 JIT) | 3,003,000 | 0.87 | 1.39 | 0.488 | 208% | 188.3 MB |
| Kotlin (JVM) | 2,666,700 | 0.78 | 1.23 | 0.550 | 197% | 189.3 MB |
| **Spec (LLVM + ARC + Slab)** | **2,164,500** | **0.63** | **1.00** | **0.463** | **100%** | **3.1 MB** |
| Ruby 3.3 (no YJIT) | 481,420 | 0.14 | 0.22 | 0.497 | 99% | 19.7 MB |
| Python 3.14 | 477,770 | 0.14 | 0.22 | 0.438 | 100% | 10.9 MB |

---

## Compile-time profile (build step per benchmark)

| Language | Build step | `mc_pi` wall / RSS | `binary_trees` wall / RSS | `word_freq` wall / RSS |
|---|---|---|---|---|
| C | `gcc -O2` | 0.148s / 31.1 MB | 0.280s / 38.6 MB | 0.129s / 33.2 MB |
| C++ | `g++ -O2` | 0.509s / 71.9 MB | 1.008s / 103.3 MB | 0.685s / 91.3 MB |
| Go | `go build` | 0.176s / 20.8 MB | 0.057s / 20.8 MB | 0.055s / 20.8 MB |
| Java | `javac` | 0.760s / 108.4 MB | 0.670s / 109.8 MB | 0.654s / 110.0 MB |
| Rust | `rustc -O` | 1.051s / 181.6 MB | 0.848s / 179.8 MB | 0.738s / 183.9 MB |
| Kotlin | `kotlinc` | 3.301s / 411.8 MB | 2.904s / 411.1 MB | 2.840s / 418.6 MB |
| **Spec** | **`bin/spec` → LLVM IR** | **16.744s / 191.4 MB**\* | **5.999s / 122.1 MB** | **5.477s / 118.7 MB** |
| Python / Ruby | — (interpreted) | — | — | — |

*\*Note on `mc_pi` compile time: `CleoPi.spec` imports the full `base:cleo` terminal UI stack in addition to the benchmark loop, which increases whole-program LLVM IR size and `clang -O2` link time compared to `BinaryTrees.spec` (`6.0s`) and `WordFreq.spec` (`5.5s`).*

---

## Honest Assessment & Conclusions

1. **Numeric compute is at native C/Rust/Go parity:** `mc_pi` runs at `1.04× C` (1t) and `1.00× C` (8t, `939.0M pts/s`), matching C, C++, Rust, Go, and JVM while keeping RSS at `3.3 MB`.
2. **String/map workloads are competitive and lean:** `word_freq` runs at `2.16M lines/s` (`0.63× C`, `0.64× Rust`, `4.5× Python/Ruby`) with only `3.1 MB` RSS (vs ~188 MB on the JVM).
3. **Allocation-heavy tree churn (`binary_trees`) still has room to improve:** Spec's ARC + 64 KiB slab cartons (`21.4M` 1t / `49.3M` 8t nodes/s, `0.58×`/`0.55× C`) lag tracing-GC bump allocators (JVM/Go) and C/Rust `malloc` in both throughput and RSS (`163 MB` 1t / `611 MB` 8t) because every `TreeNode` pays ARC header + retain/release traffic.
4. **Compile times are the main remaining performance gap:** Whole-program compilation of `spec/lib/` modules plus `clang -O2` takes `5.5–6.0s` for small programs and `16.7s` when pulling in `base:cleo`. Module-level caching / incremental LLVM compilation is the clearest future win.

---

## Caveats — read before quoting these numbers

1. **Three distinct shapes.** `mc_pi` stresses tight arithmetic + loop/call overhead; `binary_trees` stresses small-object allocation, recursion, and ARC vs tracing GC; `word_freq` stresses string slicing and hash-map churn.
2. **Interpreted-lane RNG width.** Python/Ruby run xorshift32 in `mc_pi`.
3. **JVM wall includes warm-up.** The wall column for Java/Kotlin covers JVM start-up and in-process warm-up rounds; the *rate* is the measured round only.
4. **Ruby without YJIT.** This CRuby build has no YJIT; a YJIT-enabled Ruby would land meaningfully higher (though the GVL still caps it at one core).
5. **Python JIT is experimental** (`PYTHON_JIT=1`, opt-in) and gained ~5% on `mc_pi`.
6. **Reproducibility.** Run `utilities/run_benchmarks.sh` on your own machine to regenerate all CSVs under `/tmp/spec-bench/`.

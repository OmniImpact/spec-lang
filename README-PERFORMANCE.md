# Spec Performance vs Major Languages

Measured, reproducible cross-language comparison — not folklore. The same
benchmark runs in ten languages on one machine; the runner, every language's
source, and the raw per-run data are committed under
[`utilities/benchmarks/`](utilities/benchmarks/).

**Headline:** on a tight numeric loop, Spec runs at **~46–47% of C** (75.0M pts/s single-threaded, 461.9M pts/s on 8 threads) — **faster than Node.js (V8 workers) on 8 threads**, **~33× faster** than Ruby, and **~49–51× faster** than CPython — while its peak memory footprint matches C's (12.5–12.6 MB), not the JVM's or V8's. (Structural `SPEC_POOL_AUTO` elision and forwarding-wrapper unwrapping in `OptimizationPolicy` eliminate per-call claim-pool and wrapper-hop overhead in pure-primitive hot loops.)

---

## The benchmark

Monte Carlo π sampling: two random draws per point, hit when `x² + y² ≤ 1`,
hits summed across a thread fan-out. One identical algorithm everywhere:

- **RNG:** xorshift64 with the *same constants as Spec's own runtime*
  (`spec_rng_next`), per-thread deterministic seeds, three discarded warm-up
  draws. Java, Kotlin, Go, Rust, C++, C, and Spec all run this exact loop.
- **JS/Python/Ruby lane:** no practical native 64-bit integer loop (BigInt
  boxing distorts far more than the width does), so these run an equivalent
  xorshift32. The width effect is *measured*, not assumed: the C 32-bit
  variant (`mc_pi32.c`) lands within **0.4%** of the 64-bit anchor, so the
  interpreted lane compares cleanly against the same anchor.
- **JIT warm-up:** JVM rounds run three throwaway rounds before the measured
  one; Node warms in-process (main thread) or per-worker (2M discarded
  points); `PYTHON_JIT=1` gets one unmeasured warm-up run. Compile-to-native
  languages need no warm-up.
- **Parallelism:** 8-thread fan-out + join everywhere the platform allows.
  Python (GIL) and Ruby (GVL) run single-threaded — that is their standard
  CPU story, honestly reported as such.
- **Workloads:** 200M points per compiled/JIT run, 20M for the interpreted
  lane.

**Measurement:** every run is wrapped by
[`utilities/benchmarks/Measure.spec`](utilities/benchmarks/Measure.spec) (compiled to a native Spec binary), which
records wall time, total CPU time across all threads, and peak RSS of the
isolated child. **3 measured runs per configuration; medians below.** Run
spread was ≤5% across all configurations. Failed commands are never recorded
as datapoints.

**Environment:** AMD Ryzen AI 7 350 (8 cores / 16 threads), Linux 7.3.0,
gcc/g++ 15.3.0 (`-O2`, matching Spec's own backend flags), rustc 1.97.1
(`-O`), OpenJDK 25.0.5, kotlinc 2.4.21 (JVM 25), Node 24.21 (V8),
CPython 3.14.8, CRuby 3.3.8 (built **without** YJIT), Spec @ `b65c5e2`
(Go skipped — toolchain not installed in this environment).

All implementations agreed on π ≈ 3.1416 ± 0.001 — the same distribution was
actually sampled everywhere.

---

## Execution speed (median of 3 runs, 200M points; 20M for Python/Ruby)

| Language | Threads | Rate (pts/s) | × C | × Spec | Wall (s) |
|---|---|---|---|---|---|
| C (anchor) | 1 | 164,360,000 | 1.00 | 2.19 | 1.218 |
| C++ | 1 | 164,690,000 | 1.00 | 2.19 | 1.217 |
| Rust | 1 | 165,000,000 | 1.00 | 2.20 | 1.214 |
| Java (C2 JIT) | 1 | 165,020,000 | 1.00 | 2.20 | 2.195 |
| Kotlin (JVM) | 1 | 165,150,000 | 1.00 | 2.20 | 2.196 |
| JavaScript (V8) | 1 | 93,940,000 | 0.57 | 1.25 | 2.383 |
| **Spec (ARC runtime)** | **1** | **75,047,000** | **0.46** | **1.00** | **2.668** |
| Ruby 3.3 (no YJIT) | 1 | 2,270,200 | 0.014 | 0.030 | 8.878 |
| Python 3.14 | 1 | 1,454,600 | 0.009 | 0.019 | 13.767 |
| Python 3.14 (JIT) | 1 | 1,528,900 | 0.009 | 0.020 | 13.102 |
| C (anchor) | 8 | 976,960,000 | 1.00 | 2.12 | 0.206 |
| C++ | 8 | 982,770,000 | 1.01 | 2.13 | 0.206 |
| Rust | 8 | 986,340,000 | 1.01 | 2.14 | 0.204 |
| Java (C2 JIT) | 8 | 995,020,000 | 1.02 | 2.15 | 0.481 |
| Kotlin (JVM) | 8 | 995,020,000 | 1.02 | 2.15 | 0.477 |
| **Spec (ARC runtime)** | **8** | **461,890,000** | **0.47** | **1.00** | **0.435** |
| JavaScript (V8 workers) | 8 | 451,250,000 | 0.46 | 0.98 | 0.485 |

Read: the compiled tier is one speed class — everything from C through
Kotlin lands within ±2% of C on this loop, JIT and AOT alike. Spec sits right
at **~46–47% of C** (matching V8 single-threaded within 20% and beating
V8 workers on 8 threads in both throughput and wall time), well over an order
of magnitude ahead of the pure interpreters.

## Resource profile (per-run medians)

| Language | CPU util (1t) | CPU util (8t) | Peak RSS (1t) | Peak RSS (8t) |
|---|---|---|---|---|
| C | 100% | 681% | 12.4 MB | 12.5 MB |
| C++ | 100% | 683% | 12.3 MB | 12.5 MB |
| Rust | 100% | 687% | 12.4 MB | 12.5 MB |
| Java | 102% | 641% | 47.1 MB | 48.0 MB |
| Kotlin | 103% | 638% | 47.9 MB | 48.5 MB |
| JavaScript | 100% | 652% | 54.0 MB | 154.1 MB |
| Python | 100% | — | 12.4 MB | — |
| Ruby | 100% | — | 19.8 MB | — |
| **Spec** | **100%** | **702%** | **12.6 MB** | **12.5 MB** |

Spec's managed runtime (ARC + per-scope claim pools) costs essentially
nothing in memory: it matches C's footprint, not the JVM's (~4×) or V8's
(~4–12×). CPU utilization tracks real parallel work — the 8-thread runs use
~7.2 of 8 cores.

---

## Compile-time profile (the build of each benchmark itself)

| Language | Build step | Wall (s) | CPU (s) | Peak RSS |
|---|---|---|---|---|
| C | gcc -O2 | 0.091 | 0.091 | 32.5 MB |
| C++ | g++ -O2 | 0.395 | 0.394 | 73.0 MB |
| Rust | rustc -O | 0.790 | 0.793 | 187.1 MB |
| Java | javac | 0.591 | 1.790 | 111.3 MB |
| Kotlin | kotlinc | 2.671 | 11.633 | 425.9 MB |
| **Spec (cached runtime)** | **bin/spec → C11 → gcc** | **1.853** | **1.859** | **77.8 MB** |
| **Spec (self-compile, `--no-cache`)** | **bin/spec (`Driver.spec`, 116.6K LOC C) → gcc** | **29.300** | **30.036** | **344.8 MB** |
| JavaScript / Python / Ruby | — (interpreted) | — | — | — |

With the precompiled runtime accelerator cache warm, `PiBenchmark.spec` compiles
in **1.85 s / 77.8 MB** (down from 2.60 s / 82 MB previously) — faster than
`kotlinc` at under one-fifth the memory. Without cached C (`--no-cache`), a
full self-compilation of the Spec compiler itself (77 classes, 819 methods,
116,566 lines of C) completes in **29.30 s** (`4.96 s` Spec frontend at 186 MB
peak + `24.31 s` `gcc -O2` backend, 344.8 MB combined peak RSS).

---

## Caveats — read before quoting these numbers

1. **One benchmark, one shape.** A tight arithmetic loop measures arithmetic
   + call overhead + memory-system behavior. It says nothing directly about
   I/O-heavy, allocation-heavy, or GUI workloads. Zero allocations occur
   inside the hot loop, so GC languages are measured at their best here —
   allocation-heavy Spec code pays per-object retain/release, which this
   benchmark deliberately does not exercise.
2. **Interpreted-lane RNG width.** Python/Ruby/JS run xorshift32 (validated
   at ±0.4% against the 64-bit anchor in C). Their gap to C is the
   interpreter, not the RNG.
3. **JVM/Node wall includes warm-up.** The wall column for Java/Kotlin/Node
   covers JVM/V8 start-up and in-process warm-up rounds; the *rate* is the
   measured round only. Node's 8-thread scaling (~60% efficiency) includes
   per-worker isolate spawn and shared-nothing result passing.
4. **Ruby without YJIT.** This CRuby build has no YJIT; a YJIT-enabled Ruby
   would land meaningfully higher (published YJIT results on similar loops
   are 2–5× the interpreter). The GVL still caps it at one core.
5. **Python JIT is experimental** (copy-and-patch, opt-in) and gained ~6%
   here.
6. **Single machine, warm kernel caches.** Absolute numbers move with
   hardware; the *ratios* are the point. Re-run on your own box — the whole
   matrix takes ~10 minutes:

```bash
./bootstrap.sh                                   # build Spec
RUNS=3 PAR=8 utilities/run_benchmarks.sh         # full matrix, medians printed
```

Raw per-run data lands in `/tmp/spec-bench/results.csv` (runs) and
`/tmp/spec-bench/builds.csv` (compiles). Every benchmark source, including
the C anchor, lives in [`utilities/benchmarks/`](utilities/benchmarks/).

---

## Where Spec fits

| Tier | Languages | × C on this loop |
|---|---|---|
| Native codegen | C, C++, Rust, Java, Kotlin | 0.98–1.00 |
| Managed JIT | JavaScript/Node (V8) | 0.57 |
| **Spec (C-emitting, ARC)** | **Spec** | **0.46–0.47** |
| Pure interpreters | Ruby, Python | 0.014 / 0.009 |

Spec trades half of C's raw numeric throughput for ARC's predictable
latency (no GC pauses), C-level memory footprint, byte-verified reproducible
compilation, and the safety net of bounds-checked, cast-checked runtime
panics. On this evidence, that trade lands it squarely between the compiled
tier and V8 — closer to Go's old niche than to Python's.

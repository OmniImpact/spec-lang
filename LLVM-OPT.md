# LLVM Backend Optimization Plan

Tracking structural compiler and runtime optimizations for `feature/llvm`,
targeting the performance gap against the retired C backend (`b65c5e2`) and
native peers across `mc_pi`, `binary_trees`, and `word_freq`.

**Core constraint:** All compiler optimizations must operate strictly at the
**data-structure / IR / CFG level** (`IrModule`, `IrFunction`, `IrBlock`,
`IrInst`, `IrStruct`). Never match on Spec class or function names.

---

## Baseline (`02973f8`, `feature/llvm`)

| Benchmark | Spec (1t) | Spec (8t) | C (1t / 8t) | Notes |
|---|---|---|---|---|
| `mc_pi` (pts/s) | 17.74M (`0.11× C`) | 2.58M (`0.0025× C`) | 165.4M / 1,013.8M | 8t is 6.9× slower than 1t |
| `binary_trees` (nodes/s) | 11.12M (`0.30× C`) | 40.60M (`0.45× C`) | 36.8M / 90.7M | Scales 3.65×; 207–780 MB RSS |
| `word_freq` (lines/s) | 935.5K (`0.26× C`) | — | 3.53M | 3.2 MB RSS |

---

## Optimization Roadmap

### 1. Lock-free thread-local RNG (`spec_math_random`) — **DONE**
- **Problem:** `spec_math_random` in `spec/base/compiler/gen/RuntimePrelude.spec`
  calls glibc `rand()`, which acquires a global `libc` mutex on every call.
  Across 8 threads × 400M calls in `mc_pi`, all 8 cores contend on that single
  lock (77.5s wall, 526.6s CPU).
- **Fix:** Switched `spec_math_random` in `RuntimePrelude.spec` and
  `bootstrap/spec_runtime.c` to use the existing `__thread unsigned long long
  _spec_rng_state` xorshift64* (`spec_rng_next` / `spec_fast_random_seed`).
- **Result (`mc_pi`, 200M pts, median of 3):**
  - 1 thread: `17.74M` → **`75.96M` pts/s** (`11.276s` → **`2.635s`**, **4.28× faster**)
  - 8 threads: `2.58M` → **`464.04M` pts/s** (`77.482s` → **`0.434s`**, **179.8× faster**)
  - Already exceeds the retired C backend (`75.05M` / `461.89M`) and Node V8 (`452.03M` on 8t).

### 2. Structural Claim-Pool Elision (`SpecOptimizer` pass) — **DONE**
- **Problem:** Every function, `while` condition, `while` body, and `if`
  condition emits `spec_pool_frame()` + `spec_pool_release_to()`, even when no
  heap objects are allocated or claimed. Because external runtime calls are
  opaque to LLVM across TUs, LLVM cannot prove `_spec_pool_top` is untouched
  and keeps ~10 pool-frame/release calls per hot-loop iteration.
- **Fix:** Added [PoolElisionPass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/PoolElisionPass.spec) (`order = 20`) over `IrModule` / `IrFunction` CFG, using a fixed-point `mayClaimToCaller` analysis and CFG reachability to elide `(spec_pool_frame, spec_pool_release_to)` pairs whose regions cannot claim onto the pool.
- **Result:**
  - `spec_pool_frame` calls in `PiBenchmark.spec`: `738` → **`209`** (**-71.7%**)
  - `mc_pi` 1t: `75.96M` → **`76.31M` pts/s** (+0.5%); 8t: `461.89M` (neutral — bottleneck is now the cross-TU `spec_math_random` call)
  - `binary_trees` 1t: `11.12M` → **`11.13M` nodes/s**; 8t: `40.58M` (neutral)
  - `word_freq`: `935.5K` → **`944.3K` lines/s** (+0.9%)

### 3. Forwarding-Wrapper Unwrapping & Small-Function Inlining (`SpecOptimizer` pass) — **DONE**
- **Problem:** Trivial wrapper functions (single basic block with parameter/constant
  setup, a single `IrCall`, and `Ret`) were not unwrapped in Spec IR, and small
  leaf functions lacked `alwaysinline`.
- **Fix:** Added [WrapperUnwrapPass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/WrapperUnwrapPass.spec) (`order = 30`) and structural `alwaysinline` tagging for small (`<= 20` insts) single-block non-recursive functions in [LlvmEmitter.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/llvm/LlvmEmitter.spec).
- **Result (median of 3):**
  - `mc_pi` 1t: `76.31M` → **`75.96M` pts/s** (neutral); 8t: `461.89M` → **`472.81M` pts/s** (+2.4%, peak `573.1M`)
  - `binary_trees` 1t: `11.13M` → **`11.05M` nodes/s** (neutral); 8t: `40.58M` → **`40.17M` nodes/s** (neutral)
  - `word_freq`: `944.3K` → **`951.5K` lines/s** (+0.8%)
  - `specunit`: 104 passed, 0 failed.

### 4. Pure-Spec Stdlib + `SpecOptimizer` Plan (No Cross-TU C Floor for Hot Paths)
- **Architectural decision:** Instead of ThinLTO or hand-writing individual C
  helpers into `LlvmEmitter.spec`, port non-OS hot runtime helpers into **pure
  Spec** over `base:sys:Mem` so they become real `IrFunction`s inside
  `IrModule`, where `SpecOptimizer` and LLVM `-O2` can optimize them directly.
- **Porting targets:**
  1. **Thread-local RNG (`Math:fastRandom`) — DONE:** Added
     `tlsGetI64` / `tlsSetI64` to `Mem` (backed by `internal thread_local`
     storage in `LlvmEmitter.spec`) and implemented xorshift64* in pure Spec in
     `Math.spec`.
     - **Result (`mc_pi`, 200M pts, median of 3):**
       - 1 thread: `75.96M` → **`162.60M` pts/s** (`1.232s` wall, `2.6 MB` RSS, **`0.98× C`**, **2.17× faster than the retired C backend**)
       - 8 threads: `472.81M` → **`995.02M` pts/s** (`0.204s` wall, `2.6 MB` RSS, **`0.98× C`**, matching C/C++/Rust/Go/JVM)
       - `specunit`: 104 passed, 0 failed.
  2. **Hot string & atomic helpers:** Port `spec_string_equals` /
     `spec_string_hash` over `Mem` and wire `Process` atomics to `Mem` inline
     LLVM atomics.
- **Compiler passes (100% structural, no class/function name matching):**
  1. **Multi-block small-function `alwaysinline` / `InlinePass`:** Extend
     inlining beyond single-block functions to small non-recursive multi-block
     `IrFunction`s (e.g. `Math:fastRandom` with its initial-seed branch).
  2. **Known-Type Devirtualization & Dead-Receiver Elision (`DevirtPass`):**
     Devirtualize `AllocObj` → `IndirectCall` when concrete type is known, and
     elide `AllocObj` + `init` + `spec_claim_pool` when `%self` is never read
     and the receiver does not escape.
  3. **Local `Retain` / `Release` Peephole (`ArcPeepholePass`):** Cancel
     redundant block-local `Retain`/`Release` pairs and null operations.
  4. **Second `PoolElisionPass`:** Run after devirtualization/inlining to clean
     up newly exposed pool frames.

---

### 5. Known-Type Devirtualization & Dead-Receiver Elision (`SpecOptimizer` pass)
- **Problem:** Calling methods on stateless helper/namespace types allocates a
  temporary object (`AllocObj` + `init` + `spec_claim_pool`), performs a null
  check, and dispatches via the vtable even when the concrete `structName` is
  known at the allocation site and `self` is never read.
- **Fix:**
  - When an `AllocObj(dst, structName, ...)` flows directly to an
    `IndirectCall` without escaping, devirtualize to a direct `IrCall` using
    `structName` + vtable slot.
  - When the target `IrFunction` never reads `%self` (and `init` is empty/trivial)
    and `dst` has no escaping uses, elide `AllocObj`, `init`, and
    `spec_claim_pool` (passing `null` for `self`).

### 5. Cross-TU Runtime Visibility (LLVM Bitcode / LTO / Attributes)
- **Problem:** `Driver.spec` compiles `spec_runtime.c` to `spec_runtime.o`
  separately from the emitted `.ll` module, preventing LLVM `-O2` from inlining
  small runtime helpers or proving memory/no-unwind properties.
- **Fix:** Either compile `spec_runtime.c` to LLVM bitcode / use ThinLTO when
  linking, or annotate pure/non-allocating runtime `declare`s in
  `LlvmEmitter.spec` with LLVM attributes (`willreturn`, `nofree`, `nosync`,
  `memory(...)`).

### 6. Local `Retain` / `Release` Peephole (`SpecOptimizer` pass)
- **Problem:** Repeated `Retain(x)` / `Release(x)` pairs on non-escaping locals
  within a basic block add atomic/non-atomic refcount traffic in allocation-heavy
  code (`binary_trees`, `word_freq`).
- **Fix:** Add a block-local `SpecOptimizer` peephole pass to cancel redundant
  paired `Retain`/`Release` instructions and elide operations on known-null or
  immortal values.

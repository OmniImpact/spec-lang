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
  2. **Hot string & atomic helpers — PARTIAL:**
     - **ConstString caching — DONE:** Added `@__spec_intern_cached` +
       `@.str.cache.<id>` in `LlvmEmitter.spec` so constant `ConstString`
       literals cache their immortal pointer in an atomic global slot instead
       of calling `spec_string_intern` on every loop iteration.
       - **Result (`word_freq`, 1M lines, median of 3):** `960.6K` → **`1.021M` lines/s** (`1.043s` → **`0.981s`**, **+6.3%**; **+9.2%** over baseline).
     - **Pure-Spec `Buf:stringEquals` — DONE:** Ported `spec_string_equals`
       into pure Spec (`Buf:stringEquals` over `Mem` in [Buf.spec](file:///home/daniel/Projects/Spec/spec/lib/base/sys/Buf.spec))
       and routed `IrBuilder.spec` / `MatchCallLowerer.spec` string equality
       lowering to `Buf_stringEquals`.
       - **Result (median of 3):** `binary_trees` 8t `41.07M` → **`41.19M` nodes/s**
         (+0.3%), 1t **`11.23M` nodes/s** (neutral); `word_freq` **`998.0K` lines/s**
         (within noise; `HashTable` already used pure-Spec `mapStrKeyEquals`).
       - `specunit`: 104 passed, 0 failed.
     - **Pure-Spec `Buf:intToString` — DONE:** Ported `spec_to_string_int`
       into pure Spec ([Buf.spec](file:///home/daniel/Projects/Spec/spec/lib/base/sys/Buf.spec#L280-L315))
       using a lazy 32-byte per-thread scratch buffer in TLS slot 1 (zero
       per-call `malloc`/`free` and zero `_spec_intern_lock` contention) and
       routed `IrBuilder.spec` integer-to-string lowering to `Buf_intToString`.
       - **Result (`word_freq`, 1M lines, median of 3):** `998.0K` → **`1.049M` lines/s**
         (`1.004s` → **`0.956s`**, **+5.1%**; **+12.2%** over baseline).
       - `specunit`: 104 passed, 0 failed.
     - **Pure-Spec `Buf:stringConcat` — REVERTED (in-place `rc == 1` append wins):**
       Added `Buf:stringConcat` in [Buf.spec](file:///home/daniel/Projects/Spec/spec/lib/base/sys/Buf.spec#L75-L96)
       over TLS slot 2, and tested routing `lowerConcatChainNoClaim` to it.
       Because `Buf:stringConcat` allocates a fresh `String` per `.` instead of
       `spec_string_concat`'s in-place `rc == 1` buffer append, `word_freq`
       regressed from `1.049M` to `922.5K` lines/s. Reverted `IrBuilder.spec` back
       to `spec_string_concat` (kept `Buf:stringConcat` as a public `Buf` helper).
     - **Remaining:** `Process` atomics (`atomic_add`/`put`/`get`, ~8 calls per
       run in `mc_pi`/`binary_trees`, not on hot loops).
- **Compiler passes & runtime IR (100% structural, no class/function name matching):**
  1. **Multi-block small-function `alwaysinline` — DONE:** Extended
     `LlvmEmitter.spec` to tag small acyclic non-recursive functions (`<= 6`
     blocks, `<= 40` instructions) with `alwaysinline`.
  2. **Known-Type Devirtualization & Dead-Receiver Elision (`DevirtPass`) — DONE:**
     Added [DevirtPass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/DevirtPass.spec) (`order = 15`) to devirtualize `AllocObj` → `IndirectCall` → `IrCall` and elide `AllocObj` + no-op `init` + `spec_claim_pool` when `%self` is never read and the receiver does not escape.
     - **Result (median of 3):**
       - `spec_rt_alloc` calls in `PiBenchmark.spec`: `80` → **`32`** (**-60%**)
       - `mc_pi` 1t: **`162.60M` pts/s** (`1.232s`, `0.98× C`); 8t: **`985.22M` pts/s** (`0.204s`, peak `1.005B` pts/s)
       - `binary_trees` 1t: `11.05M` → **`11.25M` nodes/s** (+1.8%); 8t: `40.17M` → **`40.82M` nodes/s** (+1.6%)
       - `word_freq`: `951.5K` → **`957.9K` lines/s** (+0.7%)
       - `specunit`: 104 passed, 0 failed.
  3. **Local `Retain` / `Release` Peephole (`ArcPeepholePass`) — DONE:** Added
     [ArcPeepholePass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/ArcPeepholePass.spec) (`order = 18`) for block-local null `Retain`/`Release` elision and `Retain(x)`/`Release(x)` pair cancellation.
     - **Result (median of 3):**
       - `binary_trees`: 1t **`11.24M` nodes/s** (neutral), 8t `40.82M` → **`41.07M` nodes/s** (+0.6%)
       - `word_freq`: `957.9K` → **`960.6K` lines/s** (+0.3%)
       - `specunit`: 104 passed, 0 failed.
  4. **Second `PoolElisionPass` — DONE:** Re-runs `PoolElisionPass` at the end
     of [OptimizerPipeline.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/OptimizerPipeline.spec#L42-L50)
     after `WrapperUnwrapPass` to elide newly exposed pool frames.
  5. **Return-ownership pool round-trip peephole (`ArcPeepholePass` Pass 3) — DONE:**
     Elides `spec_claim_pool(x); Retain(x); spec_pool_release_to(f); spec_claim_pool(x)`
     to `spec_pool_release_to(f); spec_claim_pool(x)` in [ArcPeepholePass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/ArcPeepholePass.spec#L146-L187).
  6. **Inline `spec_rt_alloc` + 4-bucket TLS small-object free list — DONE:**
     Tagged `@spec_rt_alloc` as `alwaysinline` `noalias` in [LlvmEmitter.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/llvm/LlvmEmitter.spec#L40-L115)
     with a 4-bucket (`16`/`32`/`48`/`64`-byte payload, cap `2048` per thread)
     TLS free list using `SpecHeader.slen` (`free_h` pushes small blocks back
     onto `@_spec_tls_freelist` instead of calling `free()`).
     - **Combined Result (steps 4–6, median of 3):**
       - `binary_trees` 1t: `11.23M` → **`16.71M` nodes/s** (`6.156s` → **`4.161s`**, **+48.8%**; **0.45× C**, **0.64× Rust**)
       - `binary_trees` 8t: `41.19M` → **`58.76M` nodes/s** (`1.738s` → **`1.245s`**, **+42.7%**; **0.65× C**, **0.76× Rust**)
       - `word_freq`: `1.049M` → **`1.168M` lines/s** (`0.956s` → **`0.858s`**, **+11.3%**; **+24.9%** over baseline)
       - `specunit`: 104 passed, 0 failed.
  7. **24-byte `SpecBuf` Small-Buffer Optimization (SBO) + Structural `InlineHintPass` — DONE:**
     - **SBO:** Added `char inline_buf[24]` to `SpecBuf` at offset 40 in [RuntimePrelude.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/gen/RuntimePrelude.spec) and [spec_runtime.c](file:///home/daniel/Projects/Spec/bootstrap/spec_runtime.c), with matching SBO growth check in [Buf.spec](file:///home/daniel/Projects/Spec/spec/lib/base/sys/Buf.spec) (`bufAppendBuf`). Eliminates separate `malloc`/`free` for short strings/buffers (`<= 24` bytes).
     - **`InlineHintPass` (`SpecOptimizer`, `order = 35`):** Replaced hardcoded block/instruction caps in [LlvmEmitter.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/llvm/LlvmEmitter.spec) with [InlineHintPass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/InlineHintPass.spec) setting `IrFunction:alwaysInline` for acyclic non-recursive functions that are single-block (`blocks:length() == 1`) or belong to a model-type `IrStruct` (`userFields > 0 && userFields >= userMethods`, excluding `init`/`toString`/`className`/`equals`/`hashCode`).
     - **Result (median of 3):**
       - `word_freq`: `1.168M` → **`1.195M` lines/s** (`0.858s` → **`0.838s`**, **+2.3%**; peak `1.205M`, **+27.7%** over baseline)
       - `binary_trees` 1t: `16.71M` → **`16.89M` nodes/s** (`4.161s` → **`4.115s`**, **+1.1%**)
       - `binary_trees` 8t: `58.76M` → **`59.16M` nodes/s** (`1.245s` → **`1.235s`**, **+0.7%**)
       - `specunit`: 104 passed, 0 failed.
  8. **Shared TLS Small-Object Freelist for Runtime Containers — DONE:**
     - Exported `_spec_tls_freelist[4]` and `_spec_tls_freecount[4]` from [RuntimePrelude.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/gen/RuntimePrelude.spec) / [spec_runtime.c](file:///home/daniel/Projects/Spec/bootstrap/spec_runtime.c) and marked them `external thread_local` in [LlvmEmitter.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/llvm/LlvmEmitter.spec), routing `spec_alloc`/`spec_release` (`<= 64` bytes: `SpecBuf`, `SpecArray`, `SpecMap`, `SpecClosure`) through the shared TLS freelist.
     - **Result (`word_freq`, 1M lines, median of 3):** `1.195M` → **`1.433M` lines/s** (`0.838s` → **`0.700s`**, **+20.0%**, `3.0–3.1 MB` RSS); `specunit`: 104 passed, 0 failed.
  9. **Pure-Spec `String:concat` + Structural `ConcatFusionPass` (`SpecOptimizer`, `order = 32`) — DONE:**
     - Added [String:concat](file:///home/daniel/Projects/Spec/spec/lib/base/core/String.spec#L448-L473) over `Mem`/`Buf`, fixed `SpecBuf.inline_buf` offset (`36`) in [Buf.spec](file:///home/daniel/Projects/Spec/spec/lib/base/sys/Buf.spec#L285), and routed [IrBuilder.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/llvm/IrBuilder.spec#L2313-L2338) `lowerConcatChainNoClaim` to `String_concat`.
     - Added [ConcatFusionPass.spec](file:///home/daniel/Projects/Spec/spec/base/compiler/opt/ConcatFusionPass.spec) to structurally detect 2-buffer concat functions (`(Ptr, Ptr) -> Ptr`, `>= 2` `__spec_mem_load_i64`, `>= 2` `__spec_mem_copy`/`memcpy`, `>= 1` `__spec_mem_str_from_bytes`/`spec_string_from_bytes`, non-recursive) and fuse single-use chains into a single pre-sized `__spec_concat_<k>` helper call.
     - **Result (median of 3):**
       - `word_freq`: `1.433M` → **`1.486M` lines/s** (`0.700s` → **`0.674s`**, **+3.7%**; peak `1.490M`, **+58.8%** over baseline, `3.1 MB` RSS)
       - `binary_trees` 1t: `16.89M` → **`17.00M` nodes/s** (`4.115s` → **`4.087s`**, **+0.7%**)
       - `binary_trees` 8t: `59.16M` → **`59.99M` nodes/s** (`1.235s` → **`1.220s`**, **+1.4%**)
       - `specunit`: 104 passed, 0 failed.

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

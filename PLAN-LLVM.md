# PLAN-LLVM: Remaining Work for the Pure-Spec LLVM Backend

Consolidated roadmap of remaining architectural and runtime work across the LLVM backend (`spec/base/compiler/llvm/`, `spec/base/compiler/ir/`, `spec/base/compiler/opt/`), stdlib, and runtime. Completed stages (C backend retirement, `base:sysinternal:Mem`, pure-Spec `Box`/`String`/`Array`/`List`/`Map`/`Vector`/`Buf`/`HashTable`/`Introspection`/`Math`, structural `SysinternalCallLowerer`, inlined LLVM ARC/Pool/Atomics/PRNG/`spec_buf_destroy`, and `SpecOptimizer` passes) have been removed.

## Core Design Principles

1. **Structural `sysinternal` Binding**: Only `base:sysinternal` classes touch the floor (`ClassBindings:isSysinternal`); `base:sys` and `base:math` wrappers compile normally as Spec code. Never hijack bare user method calls by name.
2. **Structural `SpecOptimizer` Passes**: All compiler optimizations operate strictly over `IrModule` / `IrFunction` / `IrBlock` / `IrInst` / `IrStruct` — never match on Spec class or function names, and never use hardcoded caps.
3. **Scalar / Byte-Slice OS Boundary**: The C OS PAL shim (`spec_runtime.c`) should accept and return only scalar `Int` handles/lengths and raw byte pointers, never allocating or inspecting Spec objects (`SpecHeader`, `String`, `Array`, `SpecClosure`).

---

## 1. Narrow C Runtime to a Pure Scalar/Byte-Slice OS PAL (`~450` Lines)

- Refactor remaining `base:sysinternal` OS floor domains (`File`, `Dir`, `Process`, `Socket`, `Audio`, `Time`, `Terminal`) so C never touches `SpecHeader`, `String`, `Array`, or `SpecClosure`:
  - Expose raw byte-buffer and scalar primitives from the C PAL (e.g. `pal_file_read`, `pal_dir_open`/`next`/`close`, `pal_process_spawn`, `pal_clock_ms`, `pal_socket_*`, `pal_audio_*`).
  - Construct `String`/`Array` results and invoke `onSuccess`/`onError` closures in pure-Spec `base:sys` wrappers (`File.spec`, `Dir.spec`, `Process.spec`, `Socket.spec`, `Audio.spec`).
  - Move `spec_cli_args_map` CLI argument parsing into pure Spec over `Process:rawArgs()`.

---

## 2. Pure-Spec Unmanaged Floor (`Arc`, `Pool`, `Arena`)

- **Unmanaged Floor Rule in `IrBuilder`**:
  - Compile functions inside `base:sysinternal` (such as `Arc`, `Pool`, `Arena`) without automatic `retain`/`release`/`pool_frame` instrumentation so ARC and pool primitives can be written in pure Spec without recursion.
- **Pure-Spec Runtime Primitives over `Mem`**:
  - Implement `allocObj`, `retain`, `release`, `poolFrame`, `poolReleaseTo`, `claimPool`, and `Arena` in `spec/base/sysinternal/` (`Arc.spec`, `Pool.spec`, `Arena.spec`) over `base:sysinternal:Mem` so they live inside `IrModule` for `SpecOptimizer` and LLVM `-O2` inlining.

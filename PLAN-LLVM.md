# PLAN-LLVM: Remaining Work for the Pure-Spec LLVM Backend

Consolidated roadmap of remaining architectural, correctness, and optimization work across the LLVM backend (`spec/base/compiler/llvm/`, `spec/base/compiler/ir/`, `spec/base/compiler/opt/`), stdlib, and runtime. Completed stages (C backend retirement, `base:sysinternal:Mem`, pure-Spec `Box`/`String`/`Array`/`List`/`Map`/`Vector`/`Buf`, and `SpecOptimizer` passes 1–9) have been removed.

## Core Design Principles

1. **Structural `sysinternal` Binding**: Only `base:sysinternal` classes touch the floor (`ClassBindings:isSysinternal`); `base:sys` and `base:math` wrappers compile normally as Spec code. Never hijack bare user method calls by name.
2. **Structural `SpecOptimizer` Passes**: All compiler optimizations operate strictly over `IrModule` / `IrFunction` / `IrBlock` / `IrInst` / `IrStruct` — never match on Spec class or function names, and never use hardcoded caps.
3. **Scalar / Byte-Slice OS Boundary**: The C OS PAL shim (`spec_pal.c`) should accept and return only scalar `Int` handles/lengths and raw byte pointers, never allocating or inspecting Spec objects (`SpecHeader`, `String`, `Array`, `SpecClosure`).

---

## 1. Generic `sysinternal` Floor Binding & Retire `CallLowerer` Shortcuts

- **Generic `bindFloorCall`**:
  - Replace hardcoded class/method interception in `SysinternalCallLowerer` (`ConsoleCallLowerer`, `ProcessCallLowerer`, `FileCallLowerer`, `DirCallLowerer`, `TimeCallLowerer`, `MathCallLowerer`, `IntrospectionCallLowerer`, `ControlFlowCallLowerer`) with a structural `base:sysinternal` floor binding mechanism (`ClassBindings:isSysinternal`).
  - Ensure bare user calls (e.g. `line(x)`, `print(x)`, `sleep(x)`, `exit(x)`, `abs(x)`, `min(a, b)`, `while(...)`) are never hijacked when the receiver is not the stdlib provider.
  - Ensure `spec/base/sysinternal/Arena.spec` (`arenaNew`, `arenaAlloc`, `arenaDrain`, `arenaUsed`, `activateProcessArena`) is bound automatically through the generic floor mechanism.
  - Replace `IrBuilder:isStdlibClass` substring/name checks with `ClassBindings:isTransparent` / `ClassBindings:isSysinternal`.
- **Correctness Audits**:
  - Verify `Math:abs(Int)` and `Math:min`/`max(Array of Int)` pure-Spec overloads compile cleanly without `F64` type-mismatch interception.
  - Verify `ControlFlowCallLowerer` handles multi-statement `AnonFn` conditions and named argument extraction (`check` / `then` / `else`) rather than positional indexing.

---

## 2. Pure-Spec ARC, Claim Pool, Closures, `Arena`, `Introspection`, and `Process` Atomics

- **Unmanaged Floor Rule in `IrBuilder`**:
  - Compile functions inside `base:sysinternal` (such as `Arc`, `Pool`, `Arena`) without automatic `retain`/`release`/`pool_frame` instrumentation so ARC and pool primitives can be written in pure Spec without recursion.
- **Pure-Spec Runtime Primitives over `Mem`**:
  - Implement `allocObj`, `retain`, `release`, `poolFrame`, `poolReleaseTo`, `claimPool`, and `Arena` in `spec/base/sysinternal/` (`Arc.spec`, `Pool.spec`, `Arena.spec`) over `base:sysinternal:Mem` so they live inside `IrModule` for `SpecOptimizer` and LLVM `-O2` inlining.
  - Move `Process` atomics (`atomic_add`/`put`/`get`) to pure Spec over `Mem` atomics.
  - Move `Introspection:functions` and `Introspection:instantiateSubclasses` fully to pure-Spec `Introspection.spec` walking `@spec_class_registry` and `@spec_held_registry` via `Mem` loads, retiring `IntrospectionCallLowerer` hand-rolled IR loops.

---

## 3. Narrow C Runtime to a Pure Scalar/Byte-Slice OS PAL (`~450` Lines)

- Refactor remaining `base:sysinternal` OS floor domains (`File`, `Dir`, `Process`, `Socket`, `Audio`, `Time`, `Terminal`) so C never touches `SpecHeader`, `String`, `Array`, or `SpecClosure`:
  - Expose raw byte-buffer and scalar primitives from the C PAL (e.g. `pal_file_read`, `pal_dir_open`/`next`/`close`, `pal_process_spawn`, `pal_clock_ms`, `pal_socket_*`, `pal_audio_*`).
  - Construct `String`/`Array` results and invoke `onSuccess`/`onError` closures in pure-Spec `base:sys` wrappers (`File.spec`, `Dir.spec`, `Process.spec`, `Socket.spec`, `Audio.spec`).

---

## 4. Cross-TU Runtime Visibility (Bitcode / ThinLTO / LLVM Attributes)

- Either compile the remaining C runtime / OS PAL to LLVM bitcode (or enable ThinLTO) when linking in `Driver.spec`, or annotate external C `declare`s in `LlvmEmitter.spec` with precise LLVM attributes (`willreturn`, `nofree`, `nosync`, `memory(...)`) so LLVM `-O2` can prove memory/no-unwind properties across the boundary.

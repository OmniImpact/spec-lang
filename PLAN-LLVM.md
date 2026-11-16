# PLAN-LLVM: Path to Pure-Spec Runtime & Minimal OS PAL Shim

This plan outlines the 5-stage architectural roadmap for retiring the legacy C11 code generator and migrating the runtime (containers, strings, boxes, closures, ARC, claim pool, arena, and introspection) into pure Spec over LLVM IR intrinsics, leaving only a ~450-line C OS Platform Abstraction Layer (`spec_pal.c`).

## Core Design Principles

1. **No Throwaway Porting**: Never port C runtime structures (`SpecArray`, `SpecMap`, `SpecBuf`) into hand-written LLVM IR inside `LlvmEmitter` if their final destination is pure Spec.
2. **Retire the C Backend First**: Maintaining two backends (`CodeGenerator.spec` for C and `IrBuilder.spec` for LLVM) doubles the work of every runtime migration step. Retiring the C backend first immediately removes ~12,000 lines and ensures every subsequent stage is implemented once.
3. **Minimal `sysinternal` Memory & Atomic Intrinsics**: Expose raw memory and atomic operations (`base:sysinternal:Mem`) that lower 1-to-1 to single LLVM IR instructions (`load`, `store`, `getelementptr`, `atomicrmw`, `@calloc`, `@realloc`, `@free`, `@memcpy`, `@memcmp`) with zero C wrapper code.
4. **Scalar / Byte-Slice OS Boundary**: The C OS PAL shim should never allocate or inspect Spec objects (`SpecHeader`, `String`, `Array`, `SpecClosure`). It should accept and return only scalar `Int` handles/lengths and raw byte pointers, while `base:sys` wrappers construct `String`s, `Array`s, and invoke closures in pure Spec.

---

## Stage 1: Retire the C Backend (~12,000-Line Immediate Reduction)

Currently, the LLVM backend passes all 107 `specunit` test suites (`examples`, `tests`, `testllvm`) and achieves a byte-for-byte self-hosting fixed point (`spec_llvm1 -> spec_llvm2 -> spec_llvm3`) in < 200 MB peak RAM.

1. **Default `Driver.spec` to LLVM**:
   - Make the LLVM backend the sole code generation path in `spec/base/compiler/driver/Driver.spec`.
   - Update `bootstrap.sh` to bootstrap from the LLVM seed (`bootstrap/spec.ll` + `bootstrap/spec_runtime.c`).
2. **Remove Legacy C Code Generator Classes (~11,000 lines)**:
   - Delete `spec/base/compiler/gen/CodeGenerator.spec`
   - Delete `spec/base/compiler/gen/DeclarationGenerator.spec`
   - Delete `spec/base/compiler/gen/BuiltinCallGenerator.spec`
   - Delete `spec/base/compiler/gen/CBackendUtils.spec`
   - Delete `spec/base/compiler/gen/EmissionPolicy.spec`
   - Delete `spec/base/compiler/gen/OptimizationPolicy.spec`
   - Retire C-codegen-specific unit tests (`tests/compiler/TestSpecCodegen.spec`, `tests/compiler/TestSpecDeclGen.spec`).
3. **Collapse `RuntimePrelude.spec` (~1,000 lines removed)**:
   - Merge `emitHeader()` and `emitBody()` into a single self-contained `spec_runtime.c` emitter.
   - Delete duplicate prototype blocks, `SPEC_AUTO` / `SPEC_POOL_AUTO` cleanup attribute macros, `spec_assign*`, `spec_construct_*`, `spec_string_concat_n`, `spec_branch`, `spec_while`, and redundant `spec_rt_*` inline wrapper shims.

---

## Stage 2: Add `base:sysinternal:Mem` (Direct LLVM IR Memory & Atomic Intrinsics)

Introduce `spec/base/sysinternal/Mem.spec` and a `MemCallLowerer` in `spec/base/compiler/llvm/` that lowers low-level memory and atomic operations directly to LLVM IR instructions (zero C code):

- **Heap Management**:
  - `alloc(Int is bytes) -> Int` $\to$ `@calloc(i64 1, i64 %bytes)` + `ptrtoint`
  - `realloc(Int is ptr, Int is bytes) -> Int` $\to$ `@realloc(ptr, i64 %bytes)` + `ptrtoint`
  - `free(Int is ptr)` $\to$ `@free(ptr)`
  - `memcpy(Int is dst, Int is src, Int is bytes)` $\to$ `@memcpy(ptr, ptr, i64)`
  - `memcmp(Int is a, Int is b, Int is bytes) -> Int` $\to$ `@memcmp(ptr, ptr, i64)`
- **Typed Offset Loads & Stores**:
  - `loadI64(Int is ptr, Int is byteOffset) -> Int`, `storeI64(Int is ptr, Int is byteOffset, Int is val)`
  - `loadI32(Int is ptr, Int is byteOffset) -> Int`, `storeI32(Int is ptr, Int is byteOffset, Int is val)`
  - `loadByte(Int is ptr, Int is byteOffset) -> Int`, `storeByte(Int is ptr, Int is byteOffset, Int is val)`
  - `loadPtr(Int is ptr, Int is byteOffset) -> Any`, `storePtr(Int is ptr, Int is byteOffset, Any is val)`
- **Atomic Operations**:
  - `atomicLoadI32(Int is addr) -> Int` $\to$ `load atomic i32, ptr %p monotonic`
  - `atomicStoreI32(Int is addr, Int is val)` $\to$ `store atomic i32 %v, ptr %p release`
  - `atomicAddI32(Int is addr, Int is delta) -> Int` $\to$ `atomicrmw add ptr %p, i32 %d monotonic`
  - `atomicSubI32(Int is addr, Int is delta) -> Int` $\to$ `atomicrmw sub ptr %p, i32 %d acq_rel`
  - `atomicCasI64(Int is addr, Int is expected, Int is desired) -> Boolean` $\to$ `cmpxchg ptr %p, i64 %exp, i64 %des acq_rel monotonic`
- **Indirect Function Calls**:
  - `callDestroy(Int is fnPtr, Int is objPtr)` $\to$ `call void %fn(ptr %obj)`

---

## Stage 3: Move `Box`, `String`, `Array`, `List`, and `Map` to Pure Spec Over `Mem`

With `base:sysinternal:Mem` in place, reimplement the runtime-transparent containers in pure Spec:

1. **`Box of T` (`spec/lib/base/sys/Box.spec`)**:
   - Express `Box of T` as a standard Spec class with a field `T is value`.
   - Remove `spec/base/sysinternal/Box.spec` and delete `spec_rt_box_*` from the C runtime.
2. **`List of T`, `Array of T`, `Map of K to V`, and `String`**:
   - Implement backing buffer growth, indexing, slicing, FNV-1a / splitmix64 hashing, and probing in pure Spec over `base:sysinternal:Mem`.
   - Delete `StringCallLowerer.spec`, `ArrayCallLowerer.spec`, and `MapCallLowerer.spec`.
   - Simplify `ClassBindings:isTransparent` to Rule 1 only (`isSysinternal`: namespace ends with `'sysinternal'`).
   - Remove ~1,600 lines of `SpecBuf`, `SpecByteBuffer`, `SpecVec`, `SpecArray`, and `SpecMap` C code from `RuntimePrelude.spec`.

---

## Stage 4: Move ARC, Claim Pool, Closures, Arena, and Introspection to Pure Spec

1. **Unmanaged Floor Rule in `IrBuilder`**:
   - Functions inside `base:sysinternal` (such as `Arc` and `Pool`) compile without automatic `retain`/`release`/`pool_frame` instrumentation so they can implement the ARC and pool primitives without recursion.
2. **Pure-Spec ARC, Claim Pool, and Arena (`spec/base/sysinternal/Arc.spec`, `Pool.spec`, `Arena.spec`)**:
   - Implement `allocObj`, `retain`, `release`, `poolFrame`, `poolReleaseTo`, `claimPool`, and `Arena` in pure Spec over `base:sysinternal:Mem`.
   - Because these functions emit into the same LLVM IR module as user code, `clang -O2` will inline `retain`, `release`, and `poolFrame` directly at call sites.
3. **Pure-Spec Introspection**:
   - Walk `@spec_class_registry` and `@spec_held_registry` in `Introspection.spec` using `Mem` loads and `String` comparisons.

---

## Stage 5: Narrow the C Runtime to a Pure Scalar/Byte-Slice OS PAL (`~450 Lines`)

Refactor the remaining `base:sysinternal` OS floor domains (`File`, `Dir`, `Process`, `Socket`, `Audio`, `Time`, `Terminal`) so C never touches Spec objects:

- **Before**: `spec_dir_list(String path)` allocates a `SpecArray*` of `SpecBuf*` strings in C; `spec_file_read(String path, ..., SpecClosure* on_success, SpecClosure* on_error)` invokes `SpecClosure*` in C.
- **After**:
  - The C PAL exposes raw byte-buffer / scalar primitives (e.g., `pal_file_read(const char* path, char** out_buf, int64_t* out_len)`, `pal_dir_open`/`pal_dir_next`/`pal_dir_close`, `pal_process_spawn`, `pal_clock_ms`, `pal_socket_*`, `pal_audio_*`).
  - The pure-Spec wrappers in `spec/lib/base/sys/` (`File.spec`, `Dir.spec`, `Process.spec`, `Socket.spec`, `Audio.spec`) construct `String` and `Array` values and invoke `onSuccess`/`onError` closures in Spec.
- **Final Result**: `spec_pal.c` is a ~450-line, dependency-free C OS PAL shim with zero knowledge of Spec headers, ARC, closures, strings, or containers.

# Spec Memory Safety & Management Architecture Plan

This document outlines the architectural plan, technical specifications, and execution phases for introducing strict memory safety, thread-safe data ownership, and automated memory reclamation into the **Spec** programming language and compiler.

---

## 1. Executive Summary & Problem Definition

Spec is a strictly typed, object-oriented, self-hosted language compiling to C11 via GCC. It provides high-level linguistic guarantees: never-null types, definite field assignment, and exhaustive pattern matching.

However, the current C11 compilation backend operates without an automated memory management strategy:
- Every class instance, collection (`SpecArray`, `SpecMap`), closure, and dynamic string is allocated on the heap via `malloc`/`calloc` and virtually never deallocated.
- Closures capture outer scope variables via file-scope `static` C variables, creating re-entrancy and thread-safety bugs under `Parallel:run`.
- Collection bounds violations return C `NULL`, directly breaching Spec's "Never-Null" contract and causing unhandled segfaults.
- Object casts (`as TargetClass`) emit unchecked C pointer coercions, enabling type confusion.

This plan establishes a phased roadmap to transition Spec to **strict memory safety** and **automated deterministic reclamation**.

---

## 2. Compiler Audit: Current Memory Architecture & Vulnerabilities

| Area | Current Implementation | Failure Mode / Vulnerability |
|---|---|---|
| **Class Instances** | `calloc(1, sizeof(Class))` in `Class_new()` | Leaked permanently; no destructors or `free()` calls. |
| **Collections** | `malloc(sizeof(SpecArray))` & `SpecMap` | Dynamic items array resized via `realloc`; internal mutexes and buffers never freed. |
| **Closures** | Emits file-scope `static <type> _cap_<id>_<var>` | Severe data race in multi-threaded `Parallel:run`; broken recursion/re-entrancy. |
| **Strings** | `spec_str_append` uses fixed 512-slot ring buffer | Overwritten slots clobber pointers without freeing; potential dangling pointer aliases. |
| **Collection Bounds** | `spec_array_get` returns `NULL` on out-of-bounds | Emitted C code casts `NULL` to class pointer; dereference crashes with `SIGSEGV`. |
| **Downcasting** | `expr as Target` emits `((Target*)expr)` | Unchecked downcast; type mismatch causes invalid memory access on vtable/fields. |

---

## 3. Design Principles & Target Invariants

1. **Strict Never-Null Preservation**: No runtime execution path may produce a raw, dereferenceable null pointer. Out-of-bounds lookups must fail-fast with structured runtime diagnostics.
2. **Data-Race Freedom (Concurrency-First)**: Closures passed to `Parallel:run` must have isolated, re-entrant state. Captures must be packaged in explicit per-instance environment blocks.
3. **Deterministic Reclamation**: Memory should ideally be freed as soon as it is no longer referenced, avoiding unpredictable GC pauses while keeping binary footprints small.
4. **Self-Hosting Compatibility**: All compiler modifications must compile cleanly through pure Spec (`lib/compiler/`) and converge deterministically across the 3-stage bootstrap fixed point.

---

## 4. Multi-Phase Implementation Plan

```
┌─────────────────────────────────────────────────────────────────────────┐
│               PHASE 1: Immediate Safety & Hardening                     │
│  1. Safe Closure Env Structs   2. Fail-Fast Bounds Panics              │
│  3. Checked RTTI Downcasting   4. Safe Dynamic String Concatenation    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│               PHASE 2: Memory Reclamation Strategy                      │
│  • Near-Term Bridge: Optional Boehm GC (--gc=boehm) for bootstrap      │
│  • Long-Term Core: Automated Reference Counting (ARC) + RAII Scope      │
│    - Object header (atomic ref count + destructor function pointer)    │
│    - Compiler-injected GCC __attribute__((cleanup(...))) handlers      │
│    - Generated Class_destroy() cascade deallocators                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│               PHASE 3: Static Analysis & Concurrency Safety             │
│  1. Escape Analysis (Stack allocate non-escaping instances)             │
│  2. Sendable / Thread-Isolation Checks in TypeChecker                   │
│  3. Cycle Mitigation (Weak references or explicit acyclic contracts)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Immediate Safety & Hardening (Foundations)

#### 1.1 Safe Closure Environment Structures
* **Problem**: `CodeGeneratorExpressions.spec` lines 521–545 assign captured variables to global `static` variables.
* **Solution**:
  - Replace static variables with an explicit capture environment struct:
    ```c
    typedef struct {
        long long factor;
        MyClass* self;
    } _Env_anon_42;
    ```
  - When creating the closure, allocate `_Env_anon_42` and return `spec_closure_new((void*)_anon_fn_42, (void*)env)`.
  - The anonymous function signature receives `void* _env` as its first parameter and unpacks the variables locally.

#### 1.2 Fail-Fast Safe Collection Indexing
* **Problem**: `spec_array_get` returns `NULL` when `idx < 0 || idx >= a->length`.
* **Solution**:
  - Introduce `spec_panic_bounds(const char* collection_type, long long index, size_t length, const char* file, int line)`.
  - When an index is accessed via `arr[i]` without a fallback default, generate a checked accessor that panics with source line provenance rather than returning a null pointer.

#### 1.3 Checked RTTI Downcasting
* **Problem**: `(TargetClass*)ptr` allows arbitrary pointer type confusion.
* **Solution**:
  - Embed class inheritance metadata in the class descriptor or add a bitmask / class ID hierarchy table.
  - Implement `bool spec_is_instance_of(void* obj, const char* target_type)`.
  - Emit checked downcasts:
    ```c
    #define SPEC_CHECKED_CAST(obj, target_type) \
        (spec_is_instance_of((void*)(obj), #target_type) \
            ? ((target_type*)(obj)) \
            : spec_panic_cast(obj ? ((Any*)obj)->_type_name : "null", #target_type))
    ```

#### 1.4 String Buffer Modernization
* **Problem**: 512-slot static ring buffer in `RuntimePrelude.spec` causes silent overwrites and leaks.
* **Solution**:
  - Deprecate `_spec_str_bufs` ring.
  - Implement a dedicated heap-managed string buffer with explicit capacity tracking and copy-on-write semantics.

---

### Phase 2: Memory Reclamation Strategy

#### 2.1 Near-Term / Bootstrap Bridge: Boehm GC Integration (`--gc=boehm`)
To immediately eliminate all memory leaks in the self-hosted compiler and large programs while the pure ARC system is being developed:
- Introduce `--gc=boehm` compiler flag.
- When enabled, `RuntimePrelude.spec` maps:
  - `malloc` / `calloc` → `GC_malloc`
  - Raw leaf data (strings) → `GC_malloc_atomic`
  - `realloc` → `GC_realloc`
  - Links `-lgc` in gcc invocations.
- Allows running compiler workloads and benchmarks with zero leaks and zero syntax changes.

#### 2.2 Strategic Core: Deterministic Automated Reference Counting (ARC)
Implement compiler-managed deterministic reference counting directly in the C11 emission pipeline:

1. **Object Header**:
   Prepend a standard runtime header to all Spec heap objects:
   ```c
   typedef struct {
       _Atomic uint32_t ref_count;
       void (*destroy)(void* self);
   } SpecHeader;
   ```
2. **Retain / Release Primitives**:
   - `spec_retain(void* obj)`: Atomically increments `ref_count`.
   - `spec_release(void* obj)`: Atomically decrements `ref_count`. If zero, invokes `header->destroy(obj)` and frees the memory.
3. **RAII Scope Cleanup via GCC Attributes**:
   - In `CodeGeneratorProgram.spec`, emit local variables using GCC's cleanup attribute:
     ```c
     __attribute__((cleanup(spec_scope_cleanup))) MyClass* obj = MyClass_new();
     ```
   - On scope exit (normal return or block completion), the compiler automatically calls `spec_release` for all active local pointers.
4. **Cascade Destructors**:
   - Generate `void ClassName_destroy(void* self_ptr)` for each class:
     - Calls `spec_release` on every object-typed, array-typed, and map-typed field.
     - Calls `pthread_mutex_destroy` on collections.
     - Calls `free(self_ptr)`.

---

### Phase 3: Static Analysis & Concurrency Safety

1. **Thread-Isolation Checks for `Parallel:run`**:
   - In `TypeChecker.spec`, validate closures passed to `Parallel:run`.
   - Require that captured variables are either immutable, atomics (`Process:atomic*`), or pass-by-value primitives to guarantee thread safety.
2. **Stack Allocation via Escape Analysis**:
   - For temporary instances (e.g. `Loop` instances in `While:run`, iterator tokens), detect when an instance does not escape the current function scope.
   - Emit stack allocation `MyClass _inst_stack;` instead of heap `_new()` to achieve zero-overhead allocation.
3. **Cycle Mitigation**:
   - Add compiler warning or `weak` reference modifier for self-referential graph or parent-pointer patterns to avoid reference cycles.

---

## 5. Execution Checklist & Verification Protocol

### Tasks
- [x] **Task 2: Bounds Protection** — Implement `spec_panic_bounds` in `RuntimePrelude.spec` and hook into array indexing and assignments.
- [x] **Task 3: Safe Downcasting** — Implement RTTI type checking (`spec_is_subclass_of`) and checked cast macro (`spec_cast_check`) in `CodeGeneratorExpressions.spec` and `CodeGeneratorProgram.spec`.
- [x] **Task 5: Reference Counting Engine** — Implement `SpecHeader`, `spec_alloc`, `spec_retain`, `spec_release`, `spec_assign`, `spec_assign_transfer`, class and collection `_destroy()` generation in `CodeGeneratorInference.spec`, `DeclarationGenerator.spec`, and `RuntimePrelude.spec`.
- [x] **Task 7: Thread-Safety Checks** — Enhance `TypeChecker.spec` with signature and argument validation for `Parallel:run` concurrency blocks.
- [ ] **Task 1: Safe Closures** — Update `lib/compiler/CodeGeneratorExpressions.spec` to use heap env structs instead of file-scope static variables.
- [ ] **Task 4: Boehm GC Bridge** — Add `--gc` compiler option to `Driver.spec` and conditionally emit Boehm GC hooks in `RuntimePrelude.spec`.
- [ ] **Task 6: Scope Cleanup Injection** — Emit `__attribute__((cleanup(...)))` in `CodeGeneratorProgram.spec` for local reference management.

### Verification Commands
```bash
# 1. Run all unit and regression tests
bash utilities/run_tests.sh

# 2. Check memory behavior under Valgrind (verifying zero leaks)
valgrind --leak-check=full ./spec -i examples/helloworld.spec -o /tmp/hello

# 3. Verify 3-Stage Bootstrap Convergence (Fixed Point)
./spec -i lib/compiler/Driver.spec -o spec-stage1
./spec-stage1 -i lib/compiler/Driver.spec -o spec-stage2 --emit-c /tmp/stage2.c
./spec-stage2 -i lib/compiler/Driver.spec -o spec-stage3 --emit-c /tmp/stage3.c
diff -s /tmp/stage2.c /tmp/stage3.c
cp spec-stage3 spec && cp /tmp/stage3.c bootstrap/spec.c
./bootstrap.sh
```

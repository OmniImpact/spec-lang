# Safety & Performance Ledger

## Memory & Performance Metrics

### Baseline (Prior to Optimizations)
- **Peak RSS**: 1048 MB (1,073,860 KB)
- **Time**: ~4086 ms (load: 932 ms, check: 1239 ms, gen: 1894 ms)
- **With GCC**: ~24.18 s total (GCC backend time: ~20.1 s)
- **Key Bottlenecks**:
  1. `cCode:lines():length()` in `Driver.spec` allocated 95,675 heap strings and an Array just to count lines.
  2. Monolithic C buffer in `CodeGenerator.spec` buffered all ~96,500 lines simultaneously in memory.
  3. `Loader` held all 108 files, classes, and deduplication maps throughout the entire build.
  4. `TypeChecker` held 8 semantic registry maps throughout code generation.
  5. All 741 method bodies (`Member:body` statement/expression trees) remained resident until process exit.

---

### Current State (After Streaming & AST Body Release)
- **Peak RSS**: 1047 MB (1,072,224 KB)
- **Time**: ~4213 ms (load: 956 ms, check: 1298 ms, gen: 1957 ms)
- **Optimizations Completed**:
  1. **Direct Disk Streaming**:
     - Added `spec_file_append` runtime primitive in `RuntimePrelude.spec`.
     - Bound through `base:sysinternal:File:file_append` and `base:sys:File:fileAppend`.
     - Implemented `CodeGenerator:generateProgramToFile`, streaming prelude, decls, structs, vtables, hierarchies, helpers, ctors, and methods directly to disk and releasing chunk strings immediately.
  2. **Fast Line & Byte Counting**:
     - Added `spec_buf_count_byte` (vectorized `memchr`) in `RuntimePrelude.spec`.
     - Bound through `Buf:bufCountByte`, `String:countByte`, and `String:lineCount`.
     - Eliminated 95,675 heap string allocations during code generation reporting.
  3. **Method Body AST Release**:
     - Added `Member:clearBody()` in `Member.spec`.
     - Invoked `m:clearBody()` immediately after generating C for each method in `CodeGenerator.spec`.
  4. **Phase Cleanup**:
     - Added `Loader:cleanup()` to drop file and class deduplication maps after loading.
     - Added `TypeChecker:cleanup()` to drop registered classes, enum tables, and scope maps after type checking.

---

### Root Cause Analysis of Persistent RSS (1045 - 1047 MB)
1. **Glibc Arena Retention & `ru_maxrss`**:
   - `Process:peakMemoryKb()` and Linux `/usr/bin/time -v` measure `ru_maxrss` (the high-water mark of resident pages).
   - In glibc, small allocations (< 128 KB) from `malloc`/`calloc` are serviced from heap arenas. When freed, glibc does not return those pages to the OS kernel.
2. **Lexer Object Allocation Churn**:
   - In `Lexer.spec` and loop classes (`SkipWhitespaceLoop`, `TokenizeLoop`), every character inspection allocates `Loop` and `LoopControl` objects via `calloc`.
   - Over a 1,000,000-character codebase, millions of tiny objects are churned in Stage 1 alone, expanding glibc heap arenas to ~498 MB during initial loading.
3. **Parallel Codegen Arenas**:
   - `Parallel:run` spawns 4 pthreads, each allocating an 8 MB stack and separate glibc sub-arenas.

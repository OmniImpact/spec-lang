# Spec String Architecture Plan

This document outlines the architectural plan for reconstituting `String` as a pure-Spec,
ARC-managed class over a minimal `Char`/`CharBuf` primitive floor. The goal is a slimmer
compiler that relies on far less underlying C: the string machinery in the runtime is the
largest C surface in the system, and `String` is the most-used type in every Spec program,
including the compiler itself. Completing this plan retires the string-lifetime weakness,
enables the CI leak ratchet, and honors the "No Magic / userland implementation" promise
for the language's most important type.

---

## 1. Executive Summary & Problem Definition

Today `String` is not a type — it is a `const char*` alias with no header, no refcount,
and no destructor. Every ownership guarantee we have built on top of it is a patch:

- Concatenation (`.`) writes into a 512-slot process-global **ring buffer**; slot pointers
  survive only until ~512 further concats recycle them.
- **Store discipline** (`spec_str_clone_if_buffered` at every assignment site) and
  **read materialization** (`spec_str_ring_copy`) are conventions enforced by scattered
  codegen sites, not guarantees.
- Containers emulate string ownership with a dedicated `SPEC_ELEM_STRING` element kind,
  strdup-on-insert, and free-on-destroy.
- The runtime carries ~30 hand-emitted C string functions, the ring, two length caches,
  and an `atexit` shutdown.

Consequences: string-lifetime churn (~0.5 MB unreachable per self-compile) keeps
LeakSanitizer off in CI; the ring leaks its old buffer on every 512th concat; every read
and insert pays extra allocation traffic; and the method surface cannot be subclassed,
inspected, or implemented in Spec.

## 2. Audit: Current String Architecture

| Area | Current Implementation | Failure Mode |
|---|---|---|
| Representation | `const char*` (`cTypeFor`) | No ownership, no O(1) length (cache hacks), no immutability, no interning |
| Concatenation | 512-slot global ring (`spec_str_append`) | Every 512th concat leaks the old slot buffer; UAF window closed only by store discipline |
| Store discipline | `spec_str_clone_if_buffered` at VAR_DECL/ASSIGN sites | Convention, not guarantee; easy to miss a site |
| Container ownership | `SPEC_ELEM_STRING` kind + strdup + ring materialization | Patch layer; extra allocation per read and insert |
| Runtime surface | ~30 C functions + ring + caches + `atexit` shutdown | Largest non-core C dependency of the compiler |
| Method surface | `BuiltinCallGenerator` interception; `lib/base/struct` stubs | Contract drift (the `Array:get` `default:` bug class); not subclassable; contradicts README §1 |

## 3. Design Decisions (Locked)

1. **Immutable `String`, mutable `CharBuf`.** Java's model with the builder promoted to
   a first-class primitive: `CharBuf` is the growable append/truncate surface
   (Spec's StringBuilder); `String` is the immutable, shareable value produced by
   `CharBuf:toString()`. Immutability is what makes interning and sharing safe under ARC.
2. **`Char` is an 8-bit byte.** Spec strings are UTF-8; code points are a String-layer
   concern (Go's model). Java's UTF-16 `char` is the counterexample. Byte values arise
   from String methods and `Int`↔`Char` casts; character-literal syntax is deferred.
3. **Interned literals.** String literals compile to lazily-initialized, immortal,
   process-global `String` objects (statement-expression static caches in emitted C).
   Interning makes literal-heavy code allocation-free, gives `==` a pointer-equality
   fast path (token kind tags, class names), and is safe because strings are immutable.
4. **Uniqueness fast path for `concat`.** Strings are immutable *by convention*; when
   `spec_string_concat` receives a left operand that is uniquely owned (refcount == 1
   and not interned), it grows that buffer in place — preserving today's O(1) append
   chains (`p: p . "..."`) while keeping value semantics for shared strings. Cached
   hashes are invalidated on in-place growth.
5. **The C floor after migration.** The only string C that remains: `CharBuf` buffer
   primitives (new/push/append/get/set/length/clear/slice/flatten), string
   alloc/from-chars, intern, concat, equals (pointer-eq → memcmp), hash (FNV-1a).
   Roughly ten small functions; no global structures, no caches, no ring.
6. **Bootstrap order: representation first, methods second.** The representation flip
   (Phase 2) keeps the method surface builtin-intercepted so the old compiler can build
   the new one; method bodies migrate to pure Spec afterwards (Phase 3). A 3-stage
   fixed point is re-baselined at the end of each phase.
7. **Threading.** `CharBuf` is deliberately not thread-safe (each `Parallel` worker uses
   its own buffer). Immutable `String` is thread-safe for reads; the lazy hash is
   published via an atomic flag.
8. **Literal syntax hierarchy (temporary overall language format change).** String is
   being rebuilt from the basics, and the literal grammar is reset with it:
   - **`'...'` — the basic String (the default; preferred everywhere it suffices).**
     Simple spaces are allowed, and double quotes may appear inside unescaped.
     The only escape is `\'` for an embedded single quote. No tabs, newlines, control
     characters, or backslash escapes: the lexer scans straight to the closing quote
     with a single `\'` check. This is the fast path, and it should cover the vast
     majority of literals in real code — diagnostics, kind tags, keys, paths.
   - **`"..."` — the control-character string.** Used when a literal needs
     `\n` `\r` `\t` `\0`, or a literal backslash. Supported escapes are exactly the
     structural minimum: `\\ \n \r \t \0 \" \'` — nothing more (no unicode escapes,
     no interpolation). This is the forced minimum: `RuntimePrelude.spec` emits C
     source containing backslashes and newlines (`"...\n"`, `"'\\0'"`), and the
     compiler cannot generate C without at least `\\` and a newline escape.
   - **LATER (explicitly out of scope here):** full-featured `""` strings and
     HEREDOC-style ``` ``` ``` strings (templating and other advanced features).
   This is a temporary format inversion: today `'...'` is the raw string and `"..."` is
   escape-processed. The codebase must be swept (Step Zero) before the grammar flips,
   and docs (`KNOWLEDGE-SPEC.md`, language guide, STYLE_GUIDE, Kate XML) flip with it.
   An optional linter rule ("prefer `'...'` unless control characters are needed") can
   enforce the preference mechanically afterwards.

---

## 4. Multi-Phase Implementation Plan

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 0: Baselines          benchmarks, design lock, no code           │
└─────────────────────────────┬───────────────────────────────────────────┘
┌─────────────────────────────▼───────────────────────────────────────────┐
│  STEP ZERO: Format reset     literal sweep (''-preference) + grammar    │
└─────────────────────────────┬───────────────────────────────────────────┘
┌─────────────────────────────▼───────────────────────────────────────────┐
│  PHASE 1: Primitives         Char type + CharBuf builtin (additive)     │
└─────────────────────────────┬───────────────────────────────────────────┘
┌─────────────────────────────▼───────────────────────────────────────────┐
│  PHASE 2: Representation     String → ARC class; intern; concat;        │
│  flip (2a flip, 2b delete)   delete ring / patch layer / shutdown       │
└─────────────────────────────┬───────────────────────────────────────────┘
┌─────────────────────────────▼───────────────────────────────────────────┐
│  PHASE 3: Pure-Spec String   real class bodies; shrink interception     │
└─────────────────────────────┬───────────────────────────────────────────┘
┌─────────────────────────────▼───────────────────────────────────────────┐
│  PHASE 4: Ratchet            detect_leaks=1 in CI; docs; next target    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 0: Baselines & Groundwork
* Capture benchmark baselines before any change: self-compile wall time (3-stage),
  `pi_benchmark`, `mandelbrot`, compiler binary size, emitted-C size for
  `lib/compiler/Driver.spec`.
* Lock the design decisions in §3 (this document).

### Step Zero: Literal Format Reset
Goal: make the whole codebase conform to the **future** literal grammar before the
lexer semantics flip, so the flip itself is a pure grammar change with a mechanically
clean diff.

* **Census (measured 2026-11-04):** ~6,600 double-quoted literals across
  `lib/` (~5,470), `tests/` (~990), `examples/` (~130); ~3,940 contain whitespace
  (irrelevant under the new grammar — `'...'` allows spaces); ~1,840 contain
  backslashes (dominated by `RuntimePrelude.spec` emitting C escape sequences);
  316 existing single-quoted raw strings.
* **0a. Sweep `""` → `''`**: convert every double-quoted literal that needs no
  control characters — i.e. contains no backslash escape — into a single-quoted
  literal, including literals with spaces and embedded double quotes, and literals
  containing single quotes (via `\'`). Only literals that genuinely need
  `\n`/`\r`/`\t`/`\0`/`\\` (mostly `RuntimePrelude.spec`'s emitted-C sequences)
  remain double-quoted. Expected result: the large majority of the ~6,600 literals
  flip to `'...'`; `""` becomes rare and meaningful.
* **0b. Audit legacy `'...'` raw strings**: the 316 existing raw strings stay valid
  (spaces and `"` are now allowed inside `'...'`); check each for trailing
  backslashes or `\'` sequences whose meaning changes under the new escape rule.
* **0c. Grammar flip**: `'...'` becomes the basic string (spaces + `"` + `\'` only);
  `"..."` becomes the control-character string (structural escape minimum). Update
  Lexer, docs, `utilities/spec-kate.xml`; optional linter preference rule
  ("prefer `'...'` unless control characters are needed").
* **Gate**: full suite green under the flipped grammar; zero behavioral change beyond
  literal syntax.

### Phase 1: `Char` + `CharBuf` Primitives (additive, low risk)
* **1.1 `Char` type**: lexer/parser/TypeChecker entries; `cTypeFor` → `unsigned char`;
  `Int`↔`Char` casts via `as`; Char as a valid `Array of Char` / `CharBuf` element.
* **1.2 `CharBuf` builtin**: C struct (`SpecHeader` + `length` + `capacity` + `data`,
  **no mutex, no vtable**); runtime primitives (new, push, append-from-String,
  get/set with bounds panic, length, clear, slice, toString); `isBuiltinClass`
  registration; `BuiltinCallGenerator` interception; interface stub in
  `lib/base/struct/CharBuf.spec`.
* **1.3 Tests**: positive (build/freeze/read cycles) and negative (bounds panics).
* **Gate**: suite green, fixed point re-baselined, benchmarks unchanged (additive only).

### Phase 2: String Representation Flip (the risk core)
* **2.1 Runtime**: `SpecString` = `SpecHeader` + length + atomic lazy hash + inline
  chars; `spec_string_alloc/from_chars`; intern table + immortal flag;
  `spec_string_concat` with uniqueness fast path; `spec_string_equals`;
  `spec_string_hash`.
* **2.2 Codegen**: `cTypeFor("String")` → `String*`; literals → interned statics;
  `.` → `spec_string_concat`; string `==`/`!=` → `spec_string_equals`; `String`
  becomes an ARC type (stores/returns/params go through retain/release; delete the
  clone-if-buffered emission sites); Map keys become `String*` (hash/equals primitives).
* **2.3 Shim layer**: re-point existing intercepted methods (substring, split, indexOf,
  trim, replace, charAt, toBase, parseInt, …) to operate on `String*` so behavior is
  preserved unchanged during the flip.
* **2.4 Deletions (2b)**: ring buffer + lock + `is_buffered` + `clone_if_buffered` +
  `ring_copy` + `_spec_last_str/_len` caches + `atexit` shutdown;
  `SPEC_ELEM_STRING` paths in arrays/maps (String elements ride the existing
  object path); read-materialization emission in combinators/anon-fn params;
  string special-cases in VAR_DECL/ASSIGN/RETURN.
* **2.5 Verify**: 3-stage convergence, full suite, sanitized suite, benchmark deltas
  vs Phase 0.
* **Gate**: green + self-compile within accepted bounds (expect some regression;
  interning + uniqueness concat are the counters).

### Phase 3: Pure-Spec `String` Class
* **3.1** `lib/base/core/String.spec`: a real class with real method bodies written
  over the primitive floor — substring, indexOf, trim, split, lines, join, replace,
  isDigit/isAlpha/isWhitespace, charAt, code-point iteration, parseInt, toBase,
  toString (returns self), typeName. `String` becomes subclassable/inspectable and
  satisfies `Stringable`.
* **3.2** Shrink `BuiltinCallGenerator` interception to the §3.5 primitive floor;
  delete the 2.3 shims. Method-call drift (the `Array:get` bug class) becomes
  structurally impossible for String.
* **3.3** Docs: language guide, packages reference, README §1 ("userland
  implementation" and "No Magic" become true for String).
* **Gate**: green + benchmarks; interception count for String reduced to the floor.

### Phase 4: Ratchet & Cleanup
* **4.1** Flip `detect_leaks=1` in `run_sanitized.sh` and the CI sanitizer job —
  the permanent leak gate. Remove the leak-accounting caveats from the harness.
* **4.2** Re-baseline `bootstrap/spec.c`; record final benchmark deltas in this plan.
* **4.3** Update `MAINTENANCE.md`; choose the next C-surface target
  (candidates: Map internals, per-instance Array mutex removal, File/Process).

## 5. What Gets Deleted (the slimming payoff)

- The 512-slot ring, its lock, `is_buffered`, `clone_if_buffered`, `ring_copy`,
  the length caches, and the `atexit` shutdown (~150 lines of emitted C per program).
- The `SPEC_ELEM_STRING` element kind and all strdup/materialization code paths.
- ~25 of ~30 C string functions (move to pure Spec in Phase 3).
- String special-cases across VAR_DECL / ASSIGN / RETURN / combinator codegen.
- After Phase 3: the string interception block in `BuiltinCallGenerator` shrinks to
  the primitive floor.

## 6. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Self-compile slowdown (retain/release traffic, per-concat allocs) | Interned literals; uniqueness fast path; per-phase benchmark gates; builder pattern for hot loops |
| Bootstrap transition breaks self-hosting | Representation first, methods second; shim layer in 2.3; fixed point re-baselined per phase |
| Hash lazy-compute data race under `Parallel` | Atomic publish flag (§3.7) |
| Boehm mode interplay | `spec_alloc` already routes through `calloc` → `GC_malloc`; intern table is GC-visible; smoke test per phase |
| `'a'` syntax collision (raw string) | Char literals deferred; Char values arise from methods and casts |
| Scope creep toward full Array/Map migration | Explicitly out of scope; Phase 4.3 only *selects* the next target |

## 7. Execution Checklist

- [ ] **Task 0: Baselines** — capture pre-change benchmark numbers into this document.
- [ ] **Task 0a: Literal sweep `""` → `''`** — project-wide conversion per Step Zero.
- [ ] **Task 0b: Legacy raw-string sweep** — whitespace-containing `'...'` → `""`.
- [ ] **Task 0c: Grammar flip** — `'...'` basic / `"..."` whitespace-capable; lexer,
      docs, Kate XML, optional linter rule.
- [ ] **Task 1: `Char` primitive** — type plumbing, casts, tests.
- [ ] **Task 2: `CharBuf` builtin** — runtime, interception, stub docs, tests.
- [ ] **Task 3: String representation flip** — runtime structs, intern, uniqueness
      concat, codegen flip, shim layer (Phase 2a).
- [ ] **Task 4: Patch-layer deletion** — ring, caches, shutdown, `SPEC_ELEM_STRING`,
      materialization sites (Phase 2b).
- [ ] **Task 5: Pure-Spec `String` class** — real bodies over primitives.
- [ ] **Task 6: Interception shrink** — `BuiltinCallGenerator` down to the floor.
- [ ] **Task 7: Leak ratchet** — `detect_leaks=1` default in harness and CI.
- [ ] **Task 8: Docs** — language guide, packages reference, README, MAINTENANCE.md.

## 8. Verification Protocol

```bash
# 1. Full regression suite (must be green at every phase gate)
bash utilities/run_tests.sh

# 2. Sanitized suite (ASan + fatal UBSan); from Phase 4 with leak detection ON
bash utilities/run_sanitized.sh

# 3. 3-stage bootstrap convergence + re-baseline (per MAINTENANCE.md)
./spec -i lib/compiler/Driver.spec -o spec-stage1
./spec-stage1 -i lib/compiler/Driver.spec -o spec-stage2 --emit-c /tmp/stage2.c
./spec-stage2 -i lib/compiler/Driver.spec -o spec-stage3 --emit-c /tmp/stage3.c
diff -s /tmp/stage2.c /tmp/stage3.c
cp spec-stage3 spec && cp /tmp/stage3.c bootstrap/spec.c && ./bootstrap.sh

# 4. Benchmarks vs Phase 0 baseline (self-compile time, pi, mandelbrot)
time ./spec -i lib/compiler/Driver.spec -o /tmp/self-compile

# 5. Boehm mode smoke test (must keep working in every phase)
./spec --gc=boehm -i examples/helloworld.spec -o /tmp/hw_gc && /tmp/hw_gc
```

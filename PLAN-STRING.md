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
2. **`Byte` is the floor primitive: an unsigned 8-bit value.** The ladder is
   `Byte` → `Char` → `String`: raw bytes at the bottom, a real character layer
   (code points over 1–4 UTF-8 bytes) above them, and `String` on top — Spec-native
   versions of everything. Phase 1 delivers only `Byte`; `Char`'s exact shape is
   designed alongside String's API in Phase 2/3. UTF-8 is a String-layer concern
   (Go's model; Java's UTF-16 `char` is the counterexample). `Int`↔`Byte` via `as`;
   out-of-range `Int → Byte` casts **panic** at runtime — at this primitive level,
   fail-fast is correct and no `default:`/`error:` channel applies. Byte literals are
   deferred.
3. **Interned literals.** String literals compile to lazily-initialized, immortal,
   process-global `String` objects (statement-expression static caches in emitted C).
   Interning makes literal-heavy code allocation-free, gives `==` a pointer-equality
   fast path (token kind tags, class names), and is safe because strings are immutable.
4. **Uniqueness fast path for `concat`.** Strings are immutable *by convention*; when
   `spec_string_concat` receives a left operand that is uniquely owned (refcount == 1
   and not interned), it grows that buffer in place — preserving today's O(1) append
   chains (`p: p . "..."`) while keeping value semantics for shared strings. Cached
   hashes are invalidated on in-place growth.
5. **The C floor after migration.** The only string C that remains: the `[T]` buffer
   primitives (byte-buffer shape + pointer-vector shape: new/push/append/get/set/
   length/clear/flatten), string alloc/from-chars, intern, concat, equals
   (pointer-eq → memcmp), hash (FNV-1a). Roughly ten small functions; no global
   structures, no caches, no ring.
9. **Fallible reads take a mandatory `default:` plus an optional `error` callback —
   never panic.** On `[T]`, `pop`/`get`/`removeAt` return the `default` whenever there
   is no successful answer and invoke `error` (a callback receiving a diagnostic
   String) *in addition* when a problem occurs; `set` invokes `error` on out-of-bounds
   with nothing to return. `default:` is mandatory — every call site explicitly
   handles failure by value. `error:` is optional: when omitted, the codegen supplies
   a shared empty-Function singleton (never-null is preserved — omission means "the
   function that does nothing", not null), and the runtime invokes the callback
   unconditionally on failure: one uniform notification path, no branches, no null
   checks. This mirrors the `File:readAsync` `onSuccess`/`onError` convention and
   becomes the template for the later `Array:get` contract fix. Bracket syntax
   (`buf[i]`) remains the asserting (panicking) path, per the established rule:
   **brackets assert, named reads default.**
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

### Phase 1: `Byte` + `[T]` Primitives (additive, low risk)
* **1.1 `Byte` type**: lexer/parser/TypeChecker entries; `cTypeFor` → `unsigned char`;
  `Int`↔`Byte` casts via `as`; `Byte` as a valid `[Byte]` element.
* **1.2 `[T]` syntax**: `parseType()` accepts `[ Type ]` (one shared parser, six call
  sites); `cTypeFor` maps `[Byte]` → byte-buffer struct, other `[T]` → pointer-vector
  struct; container-hint channel extended for `[]` literals.
* **1.3 `[Byte]` buffer shape**: compact contiguous `char*` data (×2 growth, **no
  mutex, no vtable**); runtime primitives: new, push, appendString, get/set/pop with
  mandatory `default:` + `error` callback (no panics), length, clear, toString
  (freeze — Phase 2's builder op).
* **1.4 `[T]` pointer-vector shape**: `void**` slots with the Stage-1 ownership kinds
  (raw primitives untouched, objects retained/released, String elements
  container-owned until Phase 2); same fallible-read signatures; literals
  `['hello','hi']` and `[]`.
* **1.5 Tests**: positive (build/freeze/read cycles, defaults, error callbacks) and
  negative (omitted `default:`, OOB via brackets).
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
- [x] **Task 0a: Literal sweep `""` → `''`** — 4,664 literals converted across 68
      files (73%); 0b audit clean.
- [x] **Task 1: `Byte` primitive** — out-of-range casts panic (primitive fail-fast).
- [x] **Task 2/3/4: `[T]` syntax + `[Byte]` buffer + pointer-vector builtins** —
      mandatory-`default:` + optional-`error:` reads (no-op-closure default);
      ownership via uniform claim/retain.
- [x] **Task 3: String representation flip (Phase 2a)** — String is a refcounted,
      NUL-terminated char* with a length-cached header; literals interned (immortal);
      concat with uniqueness fast path; claims handed to a 32-slot runtime pool in
      read positions; `spec_is_arc_type(String)`; convergence + re-baseline; ASan
      clean on self-compilation.
- [x] **Task 4: Patch-layer deletion (Phase 2b)** — ring buffer, append/concat,
      clone-if-buffered, ring-copy, length caches, atexit shutdown,
      `SPEC_ELEM_STRING` paths, transfer/owned variants, and read-materialization
      sites deleted; `spec_str_equals` retained (content compare).
- [x] **Task 4b: SpecString parallel-type bootstrap (Steps 1–3)** — String's
      representation is now a `SpecBuf` (elem_size 1, NUL-termination invariant,
      zero-copy `spec_buf_to_cstring`); the old char\* API was made SpecBuf-native
      in one converged cycle (commit 5f88f09), with interning restored for 1-char
      results. Map literals store strdup'd keys/values; every codegen emitter
      boundary (ARC casts, enum `_name`/`_value`/`_toString`, printf, argv
      template, getline→onInput, map/forEach plumbing) produces managed strings.
- [x] **Task 4c: Canonical runtime family (Step 4)** — `spec_str_*` and
      `spec_specstring_*` consolidated into one `spec_string_*` family (commit
      945c41a); the old layers are gone from the prelude and the emitters.
- [x] **Task 4d: Type rename (Step 5)** — `SpecString` → `String` end-to-end via
      the two-cycle bootstrap rename (dual typedefs, then alias removal; commit
      a47c7d5). Emitted code contains zero `SpecString` references and compiles
      with plain `gcc -O2` (no tolerance flags).
- [x] **Task 7a: Leak pass 1** — 1-char results interned again; prefix/suffix
      compares are non-allocating. Budget: 1.18 MB / 86k allocs per self-compile
      (was 2.7 MB / 172k). Transfer-based assign ownership and owned
      map-getString defaults were attempted and REVERTED (see Task 7b).
- [ ] **Task 5: Pure-Spec `String` class** — real bodies over primitives.
- [ ] **Task 6: Interception shrink** — `BuiltinCallGenerator` down to the floor.
- [ ] **Task 7: Leak ratchet** — `detect_leaks=1` default in harness and CI.
      Blocked on the ownership audit (Task 7b).
- [ ] **Task 8: Docs** — language guide, packages reference, README, MAINTENANCE.md.

### 7.1 Phase-4 ownership audit map (Task 7b)

The remaining ~86k leaks per self-compile are one systematic class: expressions
that produce a *fresh owned* value consumed by a site that *retains*, orphaning
the fresh ref. Measured classes (self-compile, ASan):

| Class | Objects | Site |
|---|---|---|
| add-of-fresh | ~38k | `tokens:add(Token:init(...))` — `spec_array_add` retains, fresh ref dropped |
| return-of-fresh | ~12k | `return <fresh concat>` — return emitter retains, fresh ref orphaned |
| getString copies | ~9k | hit path returns a fresh copy per lookup |
| concat-in-loops | ~5k | escapeString / cTypeFor / postfix chains |
| working-set residue | ~1k | pre-existing AST/type-graph refs at exit |

**Findings from the attempted fixes (do not re-attempt blindly):**
- `spec_assign_transfer` on all `yieldsClaim`-true assignments introduced a UAF
  (enum_when_test): claims-true values can be *shared* (e.g. a type string both
  assigned to a local and cached on an AST node); transfer lets a later
  re-assignment release a ref another holder still owns.
- `spec_claim_pool` around assignment RHS breaks the pool contract (the pool
  adopts the sole ref, `spec_assign` retains a second one, the slot dangles and
  double-releases on eviction).
- The safe rule observed so far: adopt only where the consumer takes the value's
  *only* remaining ref and never re-assigns over a shared adopt (VAR_DECL with
  `SPEC_AUTO` is safe; ASSIGN is not, without per-value ownership tracking).

**Cycle results (owned-returns, one site per cycle):**
- RETURN site — LANDED (leak-pass 2a): `isFreshConstructorCall` (CALL on a class
  target, method init/new) passes the creator-abandoned ref through raw. Safe
  because it only *removes* an over-retain; nothing new is released. 86k → 81k
  allocs.
- ADD site — ATTEMPTED AND REVERTED, with two decisive findings:
  1. claims-true call results are **pool-claimed at generation time** (the emitted
     args already carry `spec_claim_pool`); the pool owns the ref and the consumer
     must retain. Any adoption (`add_owned`) double-adopts → pool eviction
     releases a ref the array now owns → UAF. Consumers of claims-true values:
     retain, never adopt.
  2. **The leaks are load-bearing.** The dominant class is not fresh-arg orphans
     but containers created with `elem_kind = NONE` (empty `[]` literals in field
     defaults and locals whose LHS type inference fails), so `destroy` never
     releases their items. Repairing the kind at the add site makes destroy
     actually free AST nodes — and crashes: registries (ClassInfo maps, type
     tables) hold *borrow-without-retain* pointers into those arrays. The leaks
     keep those borrowers alive.

**Revised order of operations for the leak ratchet:**
1. Container creation must carry its element kind: fix the empty-literal and
   field-default creation sites to consult the declared type (`Array of Token`
   → `spec_array_new_object()`), not the add sites.
2. Audit every cross-structure reference that borrows from a container local and
   give it an explicit retain (or restructure ownership).
3. Only then does destroy-freeing become safe and the gate can flip. Until step
   2 completes, leaks are correctness-preserving and the budget is a tracked
   metric, not a failure.

**Cycle results, continued (leak-pass 3/4):**
- `spec_map_get` now returns OWNED object-kind values (retains before return),
  honoring the claims=true contract. This was the over-release behind the
  enum_when UAF *and* the kind-repair crash: with it fixed, the
  `spec_array_add_object` kind-repair lands cleanly.
- `return <owned local>;` now transfers via null-out
  (`({ T* _t = x; x = NULL; _t; })`): the caller receives the local's own ref
  and the SPEC_AUTO cleanup no-ops. Plain transfer without the null-out freed
  the returned array in the returner's cleanup while the caller adopted it
  (ASancaught on stage2). Landed with the freshness predicate from 2a.
- Budget after both: 1.10 MB / 81k allocs - the big classes did not move, so
  the token-text stuck ref lives beyond the tokenize return chain (suspect:
  claim-pool adoption interplay at scale). Next session: mirror-ledger
  tracing of one stuck substring ref.

**Ledger rebuilt as a mirror tool (leak-pass 5):** the shadow-count design was
fundamentally broken — `spec_retain` never recorded (shadow stayed at the alloc
count while real refcounts climbed), and release-to-zero slot clearing let
colliding pointers steal slots, splitting op histories. Rewritten: the ledger is
now a pure per-address op-history ring, every check reads the atomic ref_count
directly, and an atexit dump inventories live objects with histories.
`spec_string_substring` samples its first 16 results; under ASan the dump
reports which samples are still alive at exit (poison-checked) with the op
rings. This tool is what exposed the next real class:

**map:get orphans (measured, not theorized):** sampled substrings show
`ref_count = 87,121` at exit — a hot `map:get` whose owned result is consumed by
plain `spec_assign` (+1 orphan per iteration on the SAME shared value).
Re-applying the claims-true ASSIGN transfer crashed the canary twice more, and
the crashes pinned the last blockers precisely:
- the val_kind guard in `spec_map_get` is load-bearing: NONE-kind maps store
  ints as `(void*)(intptr_t)` — an unconditional retain dereferences fake
  pointers;
- NONE-kind maps holding OBJECT values (class field defaults / empty literals
  where the container hint does not fire) store raw borrows — transfer adopts
  those and dangles.
So the transfer is correct **only after** container creation sites carry their
value kinds (the field-default/empty-literal path must consult the declared
type the way VAR_DECL does). That creation-site fix is the next session's first
move; the ASSIGN transfer and the 87k-orphan class land immediately after.

### 7.2 Runtime introspection plumbing (RTCORE v1)

The runtime already owns the hard part of program introspection: per-address
op-history rings, atomic refcounts, allocation sites, the claim pool. What it
lacks is a **boundary** — the data lives in C structs and escapes as ad-hoc
stderr text. Spec programs (and our own verification loop) need it readable.
This plumbing is also the seed of future Spec debugging/tracing: the C floor
stays a floor, all policy lands in Spec, consistent with the sysinternal
architecture.

Scope (bounded — the part that is cheap now and expensive to retrofit):

1. **RTCORE v1 dump format** — the ledger's atexit output becomes a versioned,
   stable record set (TSV-style: `ptr, ref_count, alloc_site, last_ops...`),
   env-gated as today. Old ad-hoc lines are replaced; the format is frozen so
   dumps stay analyzable and old tools keep working.
2. **`sysinternal:rt` floor** — body-less C-declared functions materializing
   the same data as Spec containers (`[RtRecord]`, site-keyed maps) for
   in-process queries.
3. **`sys:RuntimeReport` wrapper (Spec)** — parses a dump file with Spec's own
   strings / `split` / maps / `parse_base`, and answers the ratchet's questions:
   group live objects by alloc site; flag sites whose objects end on an
   unmatched retain; attribute a live object to its creating container.

Sequencing (agreed): land the **container creation-kind fix** first (it is the
measured blocker: the 87k-orphan class sits behind the ASSIGN transfer, which
is safe only once NONE-kind maps stop holding borrows and fake pointers); then
build (1)-(3); then land the ASSIGN transfer with the RuntimeReport as the
per-cycle verifier; then flip `detect_leaks=1`. The first customer of the
Report is the token-text class — the one stuck ref still unlocated.

**RC-ledger findings (Task 7b tooling):** the `SPEC_RC_DEBUG` ledger's shadow
count diverges from the atomic `ref_count` — at the flagged release the real
header showed `ref_count = 4` (object alive and healthy) while the ledger had
recorded only 2 lifetime ops. Both "freed pointer" symptoms are ledger
artifacts, NOT graph bugs: the ARC graph itself is consistent (62/62 + ASan
clean across the suite). Two ledger fixes landed (slot freed on
release-to-zero; releases cross-check the header refcount and report
divergence), but a trustworthy enforcer needs to *mirror* the atomic refcount
instead of shadow-counting — next tooling task before the ratchet can rely on
it. The leak budget remains the honest metric: 1.10 MB / 81k allocs per
self-compile, dominated by the fresh-arg classes in the table above.

## 8. Verification Protocol

```bash
# 1. Full regression suite (must be green at every phase gate)
bash utilities/run_tests.sh

# 2. Sanitized suite (ASan + fatal UBSan); from Phase 4 with leak detection ON
bash utilities/run_sanitized.sh

# 3. 3-stage bootstrap convergence + re-baseline (per MAINTENANCE.md)
./spec -i lib/compiler/Driver.spec --emit-c /tmp/stage1.c
gcc -O2 /tmp/stage1.c -o spec-stage1 -pthread -lm
./spec-stage1 -i lib/compiler/Driver.spec --emit-c /tmp/stage2.c
gcc -O2 /tmp/stage2.c -o spec-stage2 -pthread -lm
./spec-stage2 -i lib/compiler/Driver.spec --emit-c /tmp/stage3.c
gcc -O2 /tmp/stage3.c -o spec-stage3 -pthread -lm
diff -s /tmp/stage2.c /tmp/stage3.c
cp spec-stage3 spec && cp /tmp/stage3.c bootstrap/spec.c && ./bootstrap.sh

# 4. Benchmarks vs Phase 0 baseline (self-compile time, pi, mandelbrot)
time ./spec -i lib/compiler/Driver.spec -o /tmp/self-compile

# 5. Boehm mode smoke test (must keep working in every phase)
./spec --gc=boehm -i examples/helloworld.spec -o /tmp/hw_gc && /tmp/hw_gc
```

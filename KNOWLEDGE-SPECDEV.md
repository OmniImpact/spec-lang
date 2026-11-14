# KNOWLEDGE-SPECDEV.md — Development Discipline for the Spec Compiler

Practices learned the hard way, kept where the next contributor (human
or agent) will find them. The language's design lives in the docs tree
and KNOWLEDGE-SPEC.md; this file holds how to change the compiler
safely.

---

## 1. The bootstrap ratchet

The compiler compiles itself: each generation's binary must parse,
check, and emit the NEXT generation's sources. Consequences:

- **The fix lives in the working tree, but the old binary does the
  emitting.** Any source change the currently-bootstrapped binary
  cannot parse, check, or emit breaks convergence — even if the change
  is correct.
- A change lands through **prep commits** (bridges): inert
  prerequisites first, each converging alone; the semantic change last,
  once the seed can carry it.
- Every step: converge (`./bootstrap.sh`), gate
  (`bin/specunit -s bin/spec -t examples -t tests` — see §4a for
  building the runner and the sanitized wave), commit.

### The escape patterns (when the old binary blocks the change)

1. **The bridge commit** — teach the old binary both spellings. Dual
   recognition keys in the checker/gen, converged; the flip commit then
   deletes the old key. (Pattern: the if→`Conditional:if` flip, the
   `While`→`Loops` fold.)
2. **The two-part landing** — the runtime prelude is a string the
   binary emits verbatim (it rides BAKED INTO the compiled binary;
   the floor-binding side reads the floor ClassInfo live from source).
   A new runtime function and its first consumer cannot ride one
   convergence: the old binary's baked runtime lacks the symbol while
   its live source parse admits the call — the drifted seed references
   a symbol its own prelude never declares. Land the runtime text
   alone (inert — no consumer), converge, then land the consumers.
   (Pattern: `spec_intern`, the thread-local claim pool, the held
   metadata floor — `spec_held_count` landed a commit ahead of its
   Introspection wrappers.)
3. **The interim-spelling sweep** — land the change at a spelling the
   old binary handles, converge, then sweep to the final spelling.
   (Pattern: the `Loops:loop(` qualified hop between the worker
   plumbing and the bare `while(` flip.)
4. **The stash-split** — when a fix and its first consumer share one
   file: stash, apply the fix alone, converge, commit, pop, converge.
   Verify the split actually split (a same-file fix + consumer stashed
   together pop as one — check `git log` before assuming).

### Seed hygiene

- After ANY failed bootstrap, `git checkout -- bootstrap/spec.c`
  before diagnosing: a failed run's drift-cp can save a partial or
  broken emission, and a stale `bin/spec` makes tests lie.
- **But never destroy a drifted seed you are debugging** — the drifted
  emission is frequently the artifact itself (rebuild the failing
  binary from it with `-g -no-pie` for symbolized traces). Checkpoint
  it: `cp bootstrap/spec.c /tmp/seed_checkpoint.c` before any checkout.
- Never hand-edit `bootstrap/spec.c`; it is generated. Hand patches to
  it evaporate or poison the next convergence.
- A gcc failure ON `bootstrap/spec.c` = a poisoned seed. A panic during
  the VERIFY step = the just-built binary misbehaving on its own
  sources (a real bug in the new code).

---

## 2. Convergence and determinism

- The fixed point is BYTE-exact: the freshly built compiler must
  re-emit its own seed identically. Every emission-affecting change
  must be **deterministic and machine-independent**: no thread-count
  dependence, no map-iteration order, no timing in the output. The
  parallel gen merges per-class slots in class order for exactly this
  reason; verify with N runs + one output hash.
- Runtime *body* changes go live one bootstrap late (see the two-part
  landing). Expect the first run's verify to still show the old
  behavior.
- Convergence failure modes, in sighting order:
  - gcc errors on `bootstrap/spec.c` → poisoned seed (restore).
  - gcc errors on the DRIFTED seed at cycle 2 → the new sources
    reference a symbol the old runtime lacks (two-part landing).
  - LoadErrors/type errors at cycle 1 → the change needs a bridge the
    old binary doesn't have.
  - Runtime panic during the verify → a real bug in the new code; gdb
    the just-built binary, not the seed.

---

## 3. Edit-tool discipline

- **Single-file or targeted edits: the built-in Edit tool, always.**
  Scripts duplicate context badly, no-op on near-miss patterns, and
  duplicate insertions when patterns collide.
- **Scripts are for genuinely multi-file mechanical transforms**:
  renames across many files, sweeping call-site rewrites. Even then:
  - count the matches before applying; print what changed;
  - scope the transform (per function/accumulator, not blanket);
  - review a sample diff after — silent no-ops (a trailing-paren
    mismatch in the search string) and duplicate insertions are the
    two observed failure modes;
  - beware indentation-scoped patterns missing deep-indented sites.
- After any mechanical pass: grep for stragglers
  (`grep -rn <old-spelling> spec/ tests/ examples/`), then converge.

### Formatting

- Spec sources: tab indentation, one statement per line. Match the
  surrounding code exactly.
- Control flow calls (`if`, `while`, `until`) prefer shorthand
  positional arguments (`if({ cond }, { then })`, `while({ cond }, { step })`);
  regular domain method calls use named arguments (`get(index: i, default: '')`).
  Never mix positional and named arguments in the same call (§I.3).
- The emitted C lives inside string literals: verify the generated C
  compiles by emitting (`--emit-c`) and eyeballing the changed region
  before bootstrapping.
- Verify indentation after script edits — a mis-indented block parses
  but reads wrong, and the next contributor pays.

---

## 4a. Running the tests

- **The runner is specunit** — `utilities/specunit/SpecUnit.spec`, a
  standalone Spec program that is part of the language's ecosystem, not
  a compiler mode. The compiler stays lean: it has no test mode and no
  knowledge of the framework; iterating on specunit or the specunit
  package never rebuilds the compiler.
- **Building and invoking the runner.** While developing the test
  runner, build specunit into `bin/` so it stays handy for running the
  project's tests:

  ```
  bin/spec --quiet -i utilities/specunit/SpecUnit.spec -o bin/specunit
  bin/specunit -s bin/spec -t examples -t tests
  ```

  `-s` is the compiler executable the tests are compiled with (default
  `bin/spec`); `-t` is a test directory, repeatable or comma-separated,
  scanned recursively (dot directories skipped). Exit 1 on any failure.
- **The framework lives in `utilities/specunit/`** (moved out of the
  compiler's `spec/lib` tree): `SpecUnitTest` (the base — and the suite
  ENTRY: its argv-Map init constructs the runner, its empty init keeps
  test classes instantiate-able, so a suite compiles with plain `spec`
  and its binary self-runs), `SpecUnitRunner` (discovery by inheritance
  over the reflection registry, per-test fresh instances, the report),
  `SpecUnitState` (the held assertion registry), `Assert`,
  `TestResult`, `CheckRecord`.
- **Classification is self-describing**: each candidate `.spec` file's
  `#!` banner declares `#! specunit: suite|negative|run-fail|helper`;
  `#! expect: <text>` lines carry the expected diagnostics (the
  former hardcoded negative-fixture table moved into the files).
  Unmarked files that mention the specunit package are suites;
  everything else is a helper or a standalone program and is skipped.
  `-t` accepts repeated flags or comma-separated dirs; the walk is
  recursive, dot directories skipped.
- **Parallel**: the wave runs on `Parallel:run` with threads =
  cores − 2 (floor 1) — per-suite work items are pulled stride-wise by
  worker index, and the results are recorded into the held registry
  (mutex-protected arrays), so the wave is safe per worker. (The floor
  behind `Process:threadCount()` must report the MACHINE's cores — an
  earlier version read `/proc/self/status`'s `Threads:` line, which is
  the process's current thread count, 1 at startup: every
  cores-derived worker count collapsed to a serial wave.)
- **Display**: per-item results print in queue order when the wave is
  done, failed items' evidence underneath, then the summary and the CI
  exit (1 on any failure).
- **What it runs**: the specunit suites (`tests/`, including the
  compiler-as-library suites in `tests/compiler/`), and the negative fixtures
  (`tests/negative/` — compile-must-fail with `expect:` diagnostics,
  plus the run-fail form). The bootstrap fixed-point freshness is the
  bootstrap gate's job (`./bootstrap.sh` verifies the fixed point
  byte-for-byte; emit at the DEFAULT thread count — the fixed point is
  thread-count-sensitive in symbol numbering, so never re-baseline
  from a `--threads N` emission).
- **SpecUnit suites**: a suite file named exactly like its class
  (`TestByte.spec` defines `TestByte`), class starts with `Test`,
  methods start with `test`, void with zero parameters, constructed by
  name through the reflection registry. Assertions are typed
  (`Assert:areEqualInt/areEqualString/areClose/isTrue/isFalse/fail`)
  and soft — a failed assert records and the method continues; the
  result passes iff its failure list is empty. Lifecycle:
  `beforeEach`/`afterEach` by convention. The suite binary prints the
  report table and exits 1 on any failure (the CI contract); the
  runner gates on the exit code and the presence of the `== SpecUnit ==`
  report table.
- **The framework and the floor**: the framework lives in
  `utilities/specunit/` (file name = class name): `SpecUnitTest` (the
  base and the suite entry — argv-Map init runs the runner, empty init
  keeps test classes instantiate-able), `SpecUnitRunner` (discovery by
  inheritance over the reflection registry, fresh instance per test,
  the report), `SpecUnitState` (the held assertion registry),
  `Assert`, `TestResult`, `CheckRecord`. Beneath it the reflection
  floor (`spec_class_registry` + the `base:sys:Introspection`
  wrappers) is deliberately domain-neutral — class/method metadata
  only, never test concepts. The meta flag vocabulary: 1 = declared
  Void, 2 = zero parameters, 4 = paramless-Function (the empty
  function, a distinct non-void type); emission details live with the
  registry generator (CodeGenerator, the class-registry emission).
- **Entry semantics and the loudness gate**: the base's argv-Map init
  stamps `SpecUnitTest:entryStamped` (held array — held references are
  immutable, contents are not), fires the `onEntry(args)` hook
  (single-signature, so suites can `replace` it — the overloaded init
  itself cannot be), then calls `runTests()`. Suites pin
  entry-selection semantics by replacing `onEntry`
  (tests/TestEntryPreference.spec); the two-hop inherited-entry chain
  is tests/TestEntryInheritedInit.spec. The runner FAILS any
  suite whose binary exits 0 without a `== SpecUnit ==` report table —
  entry-init machinery failing to start the runner is loud, never silent
  empty-green. Entry-emission properties for non-suite entries (a root
  class with no init anywhere, a zero-arg init called at true arity,
  the non-constructible-overload fallback) are verified via
  `Assert:runSucceeds` in `tests/TestEntrySelection.spec`.
- **Report vocabulary**: a test GROUP is a class, a TEST is one method
  execution — the suite summary reports both (`N test groups, M tests
  passed, F failed`).
- **Compiler memory (measured, the driver's own RSS monitor)**: a
  typical suite compile peaks ~7 MB; the self-compile (the heaviest
  regular path) ~70 MB, ~71 MB under `--debug`. `/usr/bin/time -v`
  readings of a compile-to-binary are dominated by the GCC CHILD
  (~90 MB on suite-sized C, ~330 MB on the 62k-line seed at -O2) — not
  the compiler's own usage; use the driver report's `memory X MB peak`
  line for the compiler process itself.
- **Sanitized gate**: build an ASan+UBSan compiler from the seed, then
  build and run the runner with it — specunit, every suite compile,
  and every produced binary run under the sanitizer; run it after any
  compiler-internal change:

  ```
  gcc -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined \
      -fno-omit-frame-pointer bootstrap/spec.c -o bin/spec-asan -pthread -lm
  ASAN_OPTIONS=detect_leaks=0 bin/spec-asan --quiet \
      -i utilities/specunit/SpecUnit.spec -o bin/specunit-asan
  ASAN_OPTIONS=detect_leaks=0 \
  UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
      bin/specunit-asan -s bin/spec-asan -t examples -t tests
  ```

  Leak detection is OFF by default: strings are refcounted and
  interned, and the direct-leak residue after a self-compile is ~1.18
  MB / ~86k allocs, dominated by fresh-owned values consumed by
  retaining sites. The gate covers the dangerous classes:
  use-after-free, out-of-bounds, double-free, fatal UB.
- **Cross-language benchmarks**: `utilities/run_benchmarks.sh` (see
  README-PERFORMANCE.md).

### speclint — the standalone linter

- **The linter is speclint** — `utilities/speclint/`, the specunit
  treatment applied to the compiler's former `--lint`/`--audit` modes
  (both removed from the Driver). The binary imports the compiler's
  front-end by namespace (`lexer`, `parser`, `ast`) plus the speclint
  package and lints IN-PROCESS — no compiler subprocess, no diagnostic
  scraping. Iterating on lint rules rebuilds only `bin/speclint`; the
  bootstrap seed never reconverges for a lint change.
- **Building and invoking:**

  ```
  bin/spec --quiet -i utilities/speclint/SpecLint.spec -o bin/speclint
  bin/speclint -i path/to/file.spec        # one file (the old `spec --lint`)
  bin/speclint -t examples -t tests        # trees, recursive, repeatable
  bin/speclint -a -i file.spec             # the Phase 0.5 instance-model audit
  ```

  Tree mode skips `#! specunit: negative` fixtures (compile-must-fail
  sources — linting them is permanent noise). Exit contract: 0 clean,
  1 warnings or syntax errors (notices are informational and never
  gate), 2 usage. The indentation rules mask multi-line strings —
  RuntimePrelude.spec's triple-quoted C runtime is DATA, not Spec
  style — and the closing-brace rule validates every closer (column-0
  and tab-indented alike) against the tab indent of the line that
  opened its block, with statement-indent tracking across operator
  continuations. The whole tree lints clean: `bin/speclint -t examples
  -t tests -t spec -t utilities` reports zero warnings.
- **`utilities/speclint/` layout**: `SpecLint.spec` (the entry program
  + `LintTally`), `Linter.spec` (the rules: indentation, AST idioms,
  and the audit), `LintIssue.spec`. `tests/TestSpeclint.spec` is the
  rules' regression net — the first they ever had.
- **Loader constraint the split uncovered**: the loader dedupes
  NON-floor classes by BARE name across namespaces (`seenBareNames` in
  Loader's loadFile) — two same-named classes in different namespaces
  cannot coexist as resolvable imports while both files sit in the
  scan trees, and scan order decides which one loads. The compiler's
  linter had to be deleted in the SAME landing that added
  `utilities/speclint/`; a two-commit move/rename split is not
  possible for same-named classes.
- Known lint reality: `RuntimePrelude.spec` (the C runtime held as
  Spec string data) accounts for ~1,970 of the tree's ~2,030
  indentation warnings — the raw-text rules count the embedded C's
  lines. A multi-line-string mask in `lintIndentation` is the tracked
  follow-up.

## 4b. When stuck

- **If the same class of failure repeats twice, stop theorizing.**
  Instrument and measure; the theories in this project's history were
  wrong more often than right (four optimization levers falsified by
  measurement).
- The tools that worked, in the order to reach for them:
  1. Reproduce minimally (a small .spec file isolating the shape).
  2. Read the generated C at the failing site (`--emit-c` + grep).
  3. `gdb -batch -ex "break spec_panic_bounds" -ex run -ex bt` — the
     panics exit(), so post-mortem bt needs the breakpoint.
  4. ASan the seed (`-fsanitize=address`) for the corruption class;
     gprof (`-pg`) for the timing class.
  5. Temporary instrumentation in the compiler (per-stage prints,
     allocation histograms) — **revert it before committing**; the
     histogram/prelude patches of the memory investigation were
     explicitly temporary.
- A fix that survives the tests but contradicts your mental model is
  still unexplained. Explain it or keep digging — the model pays for
  itself on the next bug.

---

## 5. sysinternal, wrappers, and `as`

### The sysinternal floor

- `base:sysinternal:X` is the FLOOR: C-level implementations bound by
  the naming convention `spec_<snake_case(method)>`. Only the
  `base:sys` wrapper may call it (the checker enforces the wall).
- The gate is structural: the caller's namespace segment array must
  begin `['base', 'sys', ...]` — `base:sys` itself or a base:sys
  sub-package. Segment comparison separates `base:sys` from
  `base:sysinternal` exactly; a prefix test on the joined string would
  conflate them. The control-flow providers (Conditional, Loops) live
  in base:sys and wrap their same-name floors.
- **What C calls things and what WE call things are not necessarily
  the same — that is what this pattern is for.** Expose from C with
  recognizable C names (so the internal provenance is obvious:
  `spec_file_read`, `spec_print_line`, `spec_error_line`), then
  immediately wrap them into a Spec class with the names WE want
  (`fileRead`, `consOut`, `line`). The builtin/floor binding follows
  the C name; the Spec-side name is ours to change. When this is done
  right, renaming a Spec-side function edits ONLY the wrapper — the
  builtin table stops being touched for renames entirely. The console
  and file surfaces are the model: `base:sysinternal:Console` /
  `base:sysinternal:File` carry the C names, `base:sys:Output` /
  `base:sys:File` carry ours.
- User code calls the wrapper; the wrapper's methods delegate to the
  floor. Adding a floor function: the C shim in RuntimePrelude.spec
  (land it ahead of its consumers — the two-part landing), the
  sysinternal declaration, the wrapper delegation.
- Runtime-managed classes (transparent): no struct/vtable emitted; the
  methods are intercepted by the generator. The transparent set lives
  in ClassBindings.isTransparent — and a transparent-listed class
  whose methods gain REAL bodies must leave the list (the bodies must
  emit; the non-empty-body rule carries the bridge).
- Wrapper bodies are SELF-FREE under the elided dispatch (the call
  passes no receiver): state must ride parameters, held functions, or
  reference cells, never `self:`. And the runtime closures capture by
  value with per-closure write-back — two closures cannot share a
  frame local; shared mutable state rides the instance or a reference
  cell. The compiler's literal-closure inlines are the exception: they
  inline into the frame and share its locals.

### Compiler design posture: data structures, not known names

The language's design philosophy — keep the compiler minimal and build
the language in the standard library — has a compiler-internal
counterpart:

- The compiler should dispatch on STRUCTURAL properties — declared
  namespaces, contracts, modifiers, metadata — rather than hardcoded
  class names or keyword lists. Every name-keyed special case
  (the transparency list, the builtin table's class gates, the
  bare-construct parse's name checks) is a debt marker: the structural
  version is a declared annotation the machinery reads. When touching
  one of these sites, prefer moving the decision onto a declaration.
- Existing examples of the structural form: the sysinternal wall
  (namespace segments), the class-model-enum classification (Enum
  root + held members, not a name list), the held-member registries
  (built from declarations, not hardcoded surfaces).
- The control-flow constructs are the model for the whole standard
  library: a minimal floor primitive in base:sysinternal, a real
  same-name wrapper implementation in base:sys composed from it, and
  the compiler's inline lowering as the fast path for the literal
  shapes. Nothing in the language is a compiler special case that
  isn't also inspectable Spec code.

### How `as` works — and what it grants

- `['ns', 'pkg', as X()]` **instance-imports** X. It grants:
  - bare function calls resolved through the provider walk,
  - instance dispatch (elided, or field-ful through the synthesized
    `_import_X` field when X has fields),
  - the qualified NESTED-type references (`X:Inner`).
- It does NOT grant the bare parent-type reference, and never
  construction. `['ns', X]` (the plain form) is the type import: type
  references and construction. The two coexist in one using list.
- Declaration-side defaults (`X is x : X:init()`) are construction the
  DECLARING class bakes in; they gate against the declaring class's
  imports like a body expression.
- Edge cases on record: a duplicate as-import of one class is an error
  (E3); the as-form's `_import_X` field rides the as-grant
  (exempt from the plain-form construction gate); any same-file class's
  using grants the file (the compilation-unit convenience — a sibling's
  plain import admits what yours alone would not).

### Modern control flow & legibility discipline

The codebase uses modern, optimized Spec control structures across the
board to keep compiler, standard library, and application code clean,
legible, and fast:

- **Scope merging via `as`**: Always import control-flow providers with `as`:
  ```spec
  replace Array of Array of String is using: [
      ['base', 'sys', as Conditional()],
      ['base', 'sys', as Loops()]
  ];
  ```
  This brings `if`, `match`, `while`, `repeat`, and `until` directly
  into bare scope. Avoid redundant qualifier prefixes (`Conditional:if`,
  `Loops:repeat`, `Loops:while`).
- **Replace if-else cascades with `match`**:
  - For discrete values, variant enums, or strings: `match(on: val, when: [ ... ])`.
  - For multi-condition ladders: use the predicate table `match(when: [ { c1 }: { a1 }, { c2 }: { a2 }, else: { fallback } ])`.
    This flattens nested-if pyramids into clear, linear decision tables
    that lower directly to zero-allocation C11 else-if chains.
- **Use dedicated loop structures**:
  - Use `while({ cond }, { ... })` or the scoped-variable form
    `while([Int is i: 0], { i < limit }, { ... i++; })` for stateful iteration.
  - Use `repeat(count: n, worker: { ... })` for simple count repetitions
    without an index dependency.
  - Use `until({ cond }, { ... })` when the body must execute at least once.
- **Positional shorthand for conditionals**:
  - Single branch: `if({ cond }, { ... })`.
  - Two branches: `if({ cond }, { ... }, { ... })`.
  - Value-yielding expressions: `local T is res: if({ cond }, { val1 }, { val2 });`.
  - Direct returns: return `match` or `if` expressions directly rather
    than mutating temporary variables and returning after.
- **Argument discipline**: Never mix positional and named forms in one
  call (e.g. `if({ cond }, { then }, else: { ... })` is rejected by §I.3).

### Traps on record

- `Array:add` with an array item CONCATENATES (`spec_array_add_array`)
  — pushing an array into an array-of-arrays silently adds zero
  elements. Use indexed `set` on pre-sized slots.
- The claim pool is thread-local and its eviction is a heuristic window
  the structured per-statement frame design removes the
  tail.
- String literals in generated C leak identifier-shaped text into any
  substring scan of the body — the capture scans strip literals first.
- A new compiler KEYWORD instantly outlaws that spelling as an
  identifier everywhere (locals, members) — the converged binary
  rejects what the seed binary accepted. Grep self-source for the
  spelling BEFORE adding the enum entry (the `held` local in
  generateProgram died to this).
- The held once-guard : CAS 0->2 under acq_rel,
  release-store 1, losers spin on acquire. A held INITIALIZER may not
  reference same-class held members (mutual guards deadlock);
  cross-class chains and held-function bodies are unrestricted —
  checker-enforced, tests n30/n31.
- Keyword retirement (the when removal): the DELETE rides
  one convergence (the old binary parses the keyword-less source
  fine — unused grammar is harmless), but the RENAME that reuses the
  freed identifier rides the NEXT one: the old binary's compiled
  surfaces (lexer maps, arg-name picks) still bind the spelling.
  Patch the seed's compiled picks for the rename convergence; the
  source supersedes on landing.
- The match's last-expression rule covers TERMINATED trailing
  expressions too (the explicit-terminator form): a statement-form
  match arm must not END with a value-yielding call — bind it to a
  local or the arm silently types as the yield.

---

## 6. The limits, concurrency contracts, and the falsification ledger

*(Absorbed from the retired planning docs, 2026-11.)*

### The falsification ledger (measure, don't assume)

| Lever | Result |
|---|---|
| The AST slab (bump-allocated nodes) | FALSIFIED: +112 MB — nodes die incrementally; the slab hoarded them |
| String interning (tokens) | FALSIFIED: +318 MB, 40% slower — it immortalizes the open vocabulary |
| String interning (type stamps) | NEUTRAL — kept: the stamps are canonical now |
| The Expression pointer fusion | ~1% — kept (fewer fields), stages 2–3 cancelled |
| The Buf accumulators | NEUTRAL — kept: better shaped |
| The parallel GENERATION | LANDED: gen 1493→811 ms |
| The parallel LOAD | FALSIFIED: the discovery is inherently serial (the namespace acceptance needs each parse first); the batches lose to spawn overhead |

### The limits table

| Limit | Class | Contract |
|---|---|---|
| the lattice walks | — (no limit) | visited SETS, not counts: marked on entry, terminated on revisit |
| the claim pool | — (no limit) | thread-local STACK, starts at 8, doubles; the SELF-FRAMING claim wrapper releases at the call boundary |
| `SPEC_INTERN_BUCKETS 4096` | PERF | load factor degrades speed only; rehash when outgrown |
| Loader scanTree `depth > 32` | GUARD (documented exception) | the symlink-cycle guard: a dir-symlink loop yields a fresh path per visit — no visited set applies. The eventual BUILD SYSTEM deletes this walk |
| Loader walk-up | BOUNDARY (no count) | climbs while nothing is indexed; terminates at the filesystem root by construction. Also build-system work |
| `threads > 64` clamp | GUARD | pthread_create budget per call |
| argv keys | — (fixed) | `spec_string_from_bytes` (sized) — no fixed buffer |

### The concurrency contracts (every parallel stage holds these)

- The claim pool is THREAD-LOCAL: a borrow's validity counts claims on
  its own thread only.
- The intern table reads lock-free (append-only atomic chains);
  insertion takes the mutex with a re-check. Entries are immortal.
- The AST is READ-ONLY during code generation. No memo writes onto
  shared AST nodes from workers (`namespaceJoined`'s cache was removed
  for exactly this).
- Workers share NOTHING mutable: registries are copied per worker, the
  per-class results land in pre-sized slots by index, and the merge
  walks a fixed order. The emission is thread-count-independent — the
  bootstrap fixed point holds on any machine.

### Deferred and documentation debt

- **The floor pattern's remaining application:** Parallel, LoopControl,
  Math, and the containers (Array/Map/List/String) still bind through
  the builtin table keyed on their Spec-side names — renaming them
  touches the table. The console/file/terminal/process surfaces are
  the converted model (base:sysinternal floors carrying the C names,
  base:sys wrappers carrying ours); the rest follow when their
  packaging lands (Math's wrapper is base:math, the containers' are
  base:struct — the gate question is open).
- **docs/ refresh:** the language guide's runtime-dispatch sections
  should stay in step with the wrapper bodies. Content work, do from
  the code and tests.
- **Deferred by design:** generic as-imports (`as Box of Int()`);
  import aliasing (`as X() is alias`); type-differentiated overloads
  inside generic classes.

**The section-tag legend**: the user-facing diagnostics carry §- and
E-codes (§2.3, E9, E10 — stable shorthand; the semantics live in the
code and its tests). The retired planning docs' progress tags (the
Part/Stage/section numbers) are stripped from the source comments; do
not reintroduce them.

## 7. Values and reuse

- **Correctness, safety, reliability — in that order.** Speed is
  measured, not assumed: the optimization ledger holds four falsified
  levers (the AST slab, string interning, pointer fusion, the Buf
  accumulator conversion) — each implemented, measured, honestly
  recorded. A lever that measures neutral is recorded, not defended.
- **Unify or reuse code paths.** One canonical resolver per concern
  (`memberLookupRoot` for the receiver walks, `containsIdent` for the
  body scans, `copyRegistryMap` for the worker registries). Two copies
  of a rule WILL diverge.
- Call out redundant functionality when found (the old arena's
  immortality vs ARC; the serial loop left beside its parallel
  replacement) — delete it or document why it stays.
- Every debugging session ends with the instrumentation reverted and
  the gates green. The commit message records what was learned, not
  just what changed.

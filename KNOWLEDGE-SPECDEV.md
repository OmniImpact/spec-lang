# KNOWLEDGE-SPECDEV.md — Development Discipline for the Spec Compiler

Practices learned the hard way, kept where the next contributor (human
or agent) will find them. FUNCTIONS.md holds the language's design;
this file holds how to change it safely.

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
  (`utilities/run_tests.sh`, `utilities/run_sanitized.sh`), commit.

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

- Spec sources: tab indentation, one statement per line, named
  arguments everywhere. Match the surrounding code exactly.
- The emitted C lives inside string literals: verify the generated C
  compiles by emitting (`--emit-c`) and eyeballing the changed region
  before bootstrapping.
- Verify indentation after script edits — a mis-indented block parses
  but reads wrong, and the next contributor pays.

---

## 4. When stuck

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
  the naming convention `spec_<snake_case(method)>`. Only the same-name
  `base:sys` wrapper may call it (the checker enforces the wall).
- User code calls `base:sys:X`; the wrapper's methods intercept to the
  floor. Adding a floor function: the C shim in RuntimePrelude.spec
  (land it ahead of its consumers — the two-part landing), the
  sysinternal declaration, the base:sys wrapper.
- Runtime-managed classes (transparent): no struct/vtable emitted; the
  methods are intercepted by the generator. The transparent set lives
  in ClassBindings.isTransparent.

### How `as` works — and what it grants

- `['ns', 'pkg', as X()]` **instance-imports** X. It grants:
  - bare function calls resolved through the provider walk,
  - instance dispatch (elided, or field-ful through the synthesized
    `_import_X` field when X has fields),
  - the qualified NESTED-type references (`X:Inner`) — IV.2c.
- It does NOT grant the bare parent-type reference, and never
  construction. `['ns', X]` (the plain form) is the type import: type
  references and construction. The two coexist in one using list.
- Declaration-side defaults (`X is x : X:init()`) are construction the
  DECLARING class bakes in; they gate against the declaring class's
  imports like a body expression.
- Edge cases on record: a duplicate as-import of one class is an error
  (INSTANCE.md E3); the as-form's `_import_X` field rides the as-grant
  (exempt from the plain-form construction gate); any same-file class's
  using grants the file (the compilation-unit convenience — a sibling's
  plain import admits what yours alone would not).

### Traps on record

- `Array:add` with an array item CONCATENATES (`spec_array_add_array`)
  — pushing an array into an array-of-arrays silently adds zero
  elements. Use indexed `set` on pre-sized slots.
- The claim pool is thread-local and its eviction is a heuristic window
  (see Part VI); the structured per-statement frame design removes the
  tail.
- String literals in generated C leak identifier-shaped text into any
  substring scan of the body — the capture scans strip literals first.
- A new compiler KEYWORD instantly outlaws that spelling as an
  identifier everywhere (locals, members) — the converged binary
  rejects what the seed binary accepted. Grep self-source for the
  spelling BEFORE adding the enum entry (the `held` local in
  generateProgram died to this).
- The held once-guard (PLAN-ENUM Stage 1): CAS 0->2 under acq_rel,
  release-store 1, losers spin on acquire. A held INITIALIZER may not
  reference same-class held members (mutual guards deadlock);
  cross-class chains and held-function bodies are unrestricted —
  checker-enforced, tests n30/n31.
- Keyword retirement (the when removal, Stage 3c): the DELETE rides
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

*(Consolidated from FUNCTIONS.md Parts V–VI when the planning docs
retired, 2026-11.)*

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

- **docs/ refresh (the last FUNCTIONS.md/INSTANCE.md remainder):**
  docs/language/README.md (~866 lines) and docs/packages/README.md
  predate the instance model; STYLE_GUIDE.md/tooling/README.md need the
  as-import spellings. Content work, do from the code and tests.
- **E10** (the loop-hoist lint) is LANDED (Linter.spec) — the old
  checkbox was stale.
- **Deferred by design:** generic as-imports (`as Box of Int()`);
  import aliasing (`as X() is alias`); type-differentiated overloads
  inside generic classes.

**The section-tag legend**: the source comments carry tags like §I.6,
E10, IV.2c, §as — stable identifiers dating from the design docs
(FUNCTIONS.md / INSTANCE.md, consolidated here 2026-11). They persist
as shorthand; the semantics live in the code and its tests.

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

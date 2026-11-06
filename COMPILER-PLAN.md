# Spec Compiler Succession Plan

This document governs the **freeze-and-rewrite** succession: the current compiler finishes
its last two duties (String bodies; a namespace/using bridge plus heredoc/templating
syntax), then freezes forever as the stage-0 bootstrap tool. A new compiler is written
from the ground up in Spec — small namespaced files, multiple inheritance, a minimal C
floor, arena-managed memory — and replaces it wholesale. The string-migration work in
[PLAN-STRING.md](PLAN-STRING.md) feeds this plan: everything it lands (Buf floor, direct
dispatch, String bodies) is base-library inventory for the new compiler, not throwaway.

---

## 1. Executive Summary

The current compiler carries structural sediment: 91 builtin-call interception branches
entangled with codegen, `CodeGenerator` state shared by convention across five mixin
files, load-bearing leaks that cannot be repaired without crashing the registries, and
semantics baked into the seed that make every edit pay the two-cycle generation-lag tax.
The destination state (minimal C, namespaces, tight ownership) is exactly the state the
accreted codegen resists. Patching is the wrong tool.

The succession instead:

1. ~~**Finish String**~~ **DONE** — 16/16 instance methods live over the floor; the
   interception surface reduced to the floor bindings themselves (`26247f3`).
2. ~~**Land heredocs + templating**~~ **DONE** — `'''` raw, double-quote-family fancy
   with `{{expr}}` desugaring; byte-identical backward compatibility (`ca61cf1`).
3. ~~**Bridge & freeze**~~ **DONE** — interface-style declarations, namespace-driven
   sysinternal floor binding (the 14 buf* interception branches replaced by one
   namespace rule), package resolution against scan roots. **The old compiler is
   frozen as of `84b8f6a`**: no further features, ever.
4. **Write the new compiler** on the proven floor (`sysinternal`), in small namespaced
   files, with **arena** memory management for compiler-phase data — per the style
   contract in section 9.5.
5. **Self-host**, gate on the suite (64 tests and growing), retire the old compiler to
   a frozen fossil.

The decisive economics: the floor + base library (Buf, String, Array, Map, io wrappers)
is required by *both* paths, so it is shared work. The only true fork is whether the next
months go into ~170 per-function interceptor migrations inside the old codegen — or into
porting the pipeline onto the new base, after which we live in the clean house.

## 2. Current State (baseline for this plan)

**The bridge era is complete; the old compiler is frozen (commit `84b8f6a`).** What it
carries into the succession:

- **String**: 16/16 instance methods live as compiled Spec bodies over the Buf floor;
  direct dispatch with positional-then-by-name argument binding and declaration-side
  defaults. One static-shaped method (`fromCharCode`) stays intercepted — the rewrite
  handles statics via construct-and-call facades.
- **Heredocs & templating**: `'''` raw byte blocks; the double-quote family
  (`"..."` + ```` ``` ````) with escapes and `{{expr}}` desugaring into ordinary concat
  chains. Suite-locked in `tests/heredoc_test.spec`.
- **The sysinternal mechanism**: interface-style (`;`) declarations, the namespace as
  the binding annotation, one namespace-driven floor-binding branch replacing 14
  hand-written interceptors, the `spec_<snake(method)>` convention, and qualified
  construct-and-call (`base:sysinternal:Buf():bufLength(b)`).
- **Package resolution**: array-form `using:` (`['base', 'widget', Widget]`) resolved
  against the scan roots (executable dir + input dir) via the `Dir` floor primitives —
  `spec_dir_list`/`spec_exe_dir`, the first floor primitives landed with zero
  interception branches.
- **Verification state**: 64/64 + sanitized PASS; suite = the spec for both compilers.
- **Proven discipline**: land source → converge cycles → rebaseline → both suites →
  commit. The new compiler inherits this for its self-hosting loop (section 10).
- Known debt that motivates the rewrite: §7.1 leak classes in PLAN-STRING.md, cTypeFor
  prefix heuristics, mixin state sharing, interceptor/codegen entanglement, the
  load-bearing blanket RETURN retain (§7.1 re-confirmed with an ASan chain in
  `4821bc1` — do not re-attempt ownership tightening on the fossil).

## 3. Phase A — Finish String — **COMPLETE** (`26247f3`)

Per PLAN-STRING.md: land remaining bodies one per cycle (charAt, substring, startsWith,
endsWith, contains, indexOf, replaceAll, split, lines, trim, countLeading, isDigit,
isAlpha, isWhitespace, fromCharCode, parseInt), deleting each method's interception
branch as its body goes live. The Buf floor primitives and direct-dispatch machinery are
done; this is now mechanical. `String.spec` emerges as the first portable base-library file.

## 4. Phase B — Heredocs & String Templating — **COMPLETE** (`ca61cf1`)

Two string families, one job each. Current lexer facts: `'...'` strings process only
`\'` and `\\`; `"..."` strings process `\n \t \r \e \" \\`; backticks are unused in the
language, so triple-backtick introduces no conflict. Triple-quote sequences currently
mis-lex, so triple forms claim precedence over the single/double quote paths.

**The family model**: the single-quote family (`'...'`, `'''`) is for performance —
raw bytes, minimal-to-no processing, no templating. The double-quote family (`"..."`,
```` ``` ````) is for expression — full escapes and `{{expr}}` templating. Pick a
family by what the string is *for*, not per string.

### 4.1 Raw heredoc `'''...'''` — bytes, nothing else

- Multi-line. **No escape processing at all** (even `\'` passes through as two chars).
- **No templating.** Content is bytes exactly as written — the fastest, most
  memory-efficient form: one interned literal, zero runtime work.
- Use for: emitted C blocks (which are full of `"` and `\n` that must stay literal),
  embedded text, any content where backslash means backslash.
- Collision rule (same as shell heredocs): content must not contain the closing
  delimiter; the lexer errors on an unterminated block. Line/col tracking must count
  newlines inside the block.
- Lexer-only change; the AST is unchanged (still a string literal token).

### 4.2 The fancy family: `"..."` and ```` ```...``` ```` — escapes + templates

The fancy property belongs to the **double-quote family**, so it covers both the
existing double-quoted string and the new triple-backtick heredoc. Symmetric mental
model: the single-quote family (`'...'`, `'''`) is for performance — raw bytes, no
processing; the double-quote family (`"..."`, ```` ``` ````) is for expression —
escapes and templates.

- ```` ``` ```` is multi-line; `"..."` stays single-line as today.
- **Escape processing** (fancy family): `"..."` keeps its existing set — `\n \t \r \e
  \" \\` — extended with `\{`; ```` ``` ```` uses the same set plus `\`` (escaped
  backtick, for content containing the delimiter).
- **Template variables**: `{{expr}}` where *expr is any Spec expression* — variables,
  method calls, named args (`{{self:limit(with: 10)}}`), nested everything.
- Semantics: **parse-time desugaring into the existing concat chain**. A template with
  holes becomes exactly the `'a ' . x . ' b ' . f(with: 1)` expression a user would have
  written — so type coercion (`wrapToString`), ownership, and TypeChecker behavior all
  come free. Codegen and runtime are untouched.
- Mechanism: the fancy desugar pass receives the **raw** string content and does
  escapes *and* template splitting in one place — escape processing is deferred out of
  the lexer for fancy strings (if `\{` became `{` at lex time, the escape would be
  indistinguishable from an interpolation start by the time the splitter ran). Literal
  chunks get escape-processed; each `{{...}}` chunk is parsed by a sub-`Lexer`+`Parser`
  (`parseExpression()`), then `}}` is required. The sub-parse reuses the existing
  named-arg heuristics, so spaced `with:arg` style works unchanged. Hole-free fancy
  strings take the same pass and come out as one processed literal — existing `"..."`
  behavior is preserved exactly (a repo audit found **zero** existing `{{` occurrences
  in any `.spec` source, so no migration collisions).
- Cost model (precise): hole-free fancy strings are **zero runtime cost** (escapes
  resolve at compile time; one interned literal). Holes cost a runtime concat chain —
  the "slower" case, and still trivially efficient for compiler-scale emission.
- Edge decisions locked:
  - `\{\{` is the escape for a literal brace-pair (not interpolation).
  - **No nested desugaring**: a string literal inside an interpolation is a plain
    string (matches JS template-literal behavior; avoids confusing recursion).
  - Error positions inside interpolations are approximate (string start + offset);
    lint-quality, acceptable for compiler work.
- Plain `'...'` and `'''` strings are **unchanged** — raw, no templating, no new
  processing. One family per job.
- Load estimate: raw form ~a lexer afternoon; fancy form ~150–250 parser lines covering
  both `"..."` and ```` ``` ```` (one desugar pass, two token sources). Front-end only,
  1–2 convergence cycles total, verified by new suite tests (multi-line literal,
  escapes, interpolation with variables and named-arg calls in both fancy forms, brace
  escapes).

### 4.3 What this buys

The new compiler is a string-emission machine. Today's `RuntimePrelude.spec` — 1,878
lines of `p: p . "#include <stdio.h>\n";` — is the shape of everything it will do. Raw
blocks make C skeletons read as C; fancy templates put holes in them. These features
exist to make Phase G's source clean, and they get used **first in new code only**.

## 5. Phase C — Freeze & Namespace/Using Bridge — **COMPLETE** (`fe35edc`, `8b01b00`, `84b8f6a`); **OLD COMPILER FROZEN**

The old compiler's final work item is the minimum needed to compile the new compiler's
source. The package model (decided in prior sessions) is:

- `namespace: ['base', 'core']` — **array form**; the namespace property is the
  canonical reference; physical file location is a lint concern only.
- `using: [['base', 'core', String], ['base', 'io', File]]` — array of arrays; a bare
  class-name terminator imports that specific class, a string terminator imports the
  whole package; declaration type is `Array of Array of String`; dependency-free
  classes use interface-style `using;`.
- Scan roots: the spec executable's directory and the `.spec` input's directory,
  descending until a directory has no further spec files. **`sysinternal` is the sole
  exception** to dynamic discovery (fixed location, always loaded).
- Uses `Array`/`String` machinery only — no new floors needed; the readdir primitive
  for scanning lands with the sysinternal floor (Phase D) or as a pre-floor stub.

Bridge scope (old compiler): parse the array forms (largely designed — Loader's
`PackageSegLoop`), resolve using entries against the scan roots, admit the classes.
Bridge also needs the sysinternal structural rule's two syntax features: **interface-style
(no-brackets `;`) method declarations** and **namespace-qualified construct-and-call**
(`base:sysinternal:Buf():bufLength(b)`). With those, the floor restructure lands: the
twelve existing `Buf` primitives move to `base:sysinternal:Buf` as interface-style
declarations, `base:core:Buf` becomes the delegating facade, and the Buf interception
branches retarget the sysinternal class.
Explicitly **out of bridge scope**: full package-semantics polish, the layout-mismatch
lint, deleting the old colon-form, and any retrofit of `lib/` to the new syntax. The
new compiler (Phase G) implements the real semantics and dogfoods them on its own source.

After the bridge lands: **the old compiler freezes.** No new features, no interceptor
migrations, no refactors. It exists to be compiled from the fossil seed and to compile
the new compiler. This is what ends the generation-lag churn permanently.

## 6. Phase D — The Floor Contract (`sysinternal`)

**Structural rule (governs both compilers): every C-implemented function is represented
by a `sysinternal` package class, and nothing else may touch C. The namespace is the
annotation** — a class whose namespace ends with the segment `sysinternal` is a floor
class; its interface-style declarations bind to C. The compiler enforces:

- a **body** in a `sysinternal` class is a build error (floor classes are pure bindings);
- a **body-less declaration outside `sysinternal`** is a build error;
- anything but direct construct-and-call on a floor class is rejected (no vtable, no
  subclassing, no overriding; the classes are stateless so `Buf():op(...)` is free).

**C binding convention (no annotations, no tables):** a floor declaration binds to
`spec_` + snake_case of the method name — `bufLength` → `spec_buf_length`,
`bufGetByte` → `spec_buf_get_byte`, `fdOpen` → `spec_fd_open`. Consequences: floor
method names carry their own grouping prefix (`buf*`, `fd*`, `sock*`, `proc*`, `thr*`),
must be lowerCamel with no consecutive capitals (lint-checkable, keeps the case fold
trivial), and must be unique across all of `sysinternal` — a duplicate `spec_*` target
is a build error. The `external` keyword remains the one per-declaration marker, for
bindings to symbols *outside* the runtime floor (`external Function of Float is
sin(Float is x);` → C symbol `sin`, i.e. libm) — everything else binds internally.

- `sysinternal` classes are **interface-style**: body-less, no-brackets declarations —
  `Function of Int is bufLength(String is b);` — bound to C by the convention above.
- Public classes **delegate explicitly**. A facade method reads:
  ```
  Function of Int is bufLength(String is b){
      return base:sysinternal:Buf():bufLength(b);
  }
  ```
  Every C dependency is therefore a visible Spec call chain; there is no hidden
  interception surface and the "No Magic / userland implementation" promise is enforced
  structurally — the compiler can *check* it (see the three rules above).
- The current `base:core:Buf` body-less-with-brackets form is **transitional** (the old
  compiler cannot yet parse interface-style declarations). When the bridge lands,
  `Buf` becomes the delegation facade over `base:sysinternal:Buf`, and String's bodies
  keep calling `Buf:bufX(...)` unchanged — the delegation is a mechanical rewrite of one
  file, not of the call sites.

The floor's function inventory (target: **~40–60 tiny C functions** vs ~230 today,
each 2–15 lines):

1. **Memory + ARC (4)**: `spec_alloc`, `spec_retain`, `spec_release`, `spec_assign`.
   Generated code calls these everywhere; they stay in C.
2. **ByteBuf (~8)**: new/resize/length/get/set/append-bytes/append-buf/`to_cstring`.
   The one true container in C; NUL-termination invariant stays here.
3. **Raw op set**: pointer-as-`Raw` type with load/store/offset and pointer-as-int, for
   container and Arena implementors. Visible **only** to importers of `sysinternal`.
4. **OS, fd-level**: open/read/write/close/lseek, exit, env/args, mono + wall clock,
   sleep, terminal-size ioctl.
5. **Sockets, fd-level**: socket/bind/listen/accept/connect/send/recv/close. Sockets are
   ints; `Socket` becomes a pure-Spec class in `base:io` like `File`.
6. **Processes**: fork/exec/wait (or posix_spawn) + pipe.
7. **Threads/sync**: spawn-with-trampoline, join, mutex lock/unlock, atomic
   fetch-add/CAS.
8. **Panic/abort.**

**`external` declaration form** (decide now, define in the bridge): a body-less
declaration the backend emits as a C extern — `external Function of Float is
sin(Float is x);`. This deletes the entire Math wrapper layer (18 hand-written C
functions become declarations) and makes all future floor extensions declarations
instead of C. Highest-leverage single mechanism for keeping the floor minimal.

What does *not* count as floor: the generated C for structs, vtables, dispatch, and ARC
call sites. That is the compilation target, never hand-maintained, and it converges
through the normal cycle pattern.

## 7. Phase E — Base Library over the Floor

Pure Spec, in dependency order, each layer suite-tested before the next:

- `String` over ByteBuf (Phase A's `String.spec` ports nearly verbatim — the desugar of
  PLAN-STRING.md's method surface).

**String/ByteBuf design decision (settled): String WRAPS the buffer; the builder
paradigm is standard practice.**

- `ByteBuf` = the builder: mutable, append/grow, **exclusively owned during build**.
- `String` = the finalized product: immutable, ARC-shared, holding its buffer in a
  field (`self:bytes`). Every method is pure Spec over that field.
- Finalize is a **zero-copy seal**: the builder transfers its bytes to the String
  (`into`-style move) — the wrap costs one indirection, not a copy at the boundary.
- By-value (String identity == buffer identity) was considered and rejected: it makes
  ARC sharing and building mutually exclusive (any builder mutation breaks string
  aliases, forcing copy-on-write), and it is not cleanly expressible once String is a
  real class. The wrap is a *semantic* choice; physical co-allocation (inline buffer,
  one allocation) remains available later without changing call sites.
- Cost, accepted: one extra allocation and one pointer chase per String, amortized by
  length-proportional method work and partially absorbed by arenas for compiler-phase
  strings.
- The pattern generalizes as the Spec convention: **mutable builder type → immutable
  finalized product** (`ByteBuf` → `String` here; the same shape any future builder
  should follow).
- `Array` / `List` over ByteBuf with element stride: grow-by-doubling, ARC ops on
  elements via exposed `spec_retain`/`spec_release`.
- `Map` as a pure-Spec hash table over Array (FNV-1a over bytes; identity hash via
  pointer-as-int). `Set` over Map.
- `File`, `Socket`, `Process`, `Output`, `Input`, `Ansi` as thin pure-Spec classes over
  the fd/process primitives.
- `Math` as pure `external` declarations over libm — zero hand-written C.
- Int↔string conversions, parseBase, the intern table, the claim pool: pure Spec.

## 8. Phase F — Arena Memory Management (called out explicitly)

Compilers are arena-shaped workloads: AST nodes, tokens, and per-compile interned
strings all die with the compilation. The old architecture cannot take arenas because
its codegen emits per-node ARC everywhere; the new compiler's codegen emits **arena
allocations for compiler-phase data from day one**.

- `Arena` lives in `sysinternal`, built on `Raw`: bump allocation, `drain` (free-all) —
  O(1) per allocation, no per-object header, no fragmentation.
- **Lifecycle rule**: one arena (or a small stack of phase arenas) per compilation;
  everything allocated in it is never individually released. Arena-allocated objects
  must not outlive the arena or be stored in ARC-owned structures — enforced by the
  compiler's own structure (the compiler holds no cross-compile state) and by review.
- **What stays ARC**: `String`/`Buf` values that cross arena boundaries (results
  returned to callers, the immortal intern table, user-visible runtime objects). A
  per-compile string arena absorbs the rest. Exact boundary per type is a Phase G
  design note, settled when each module ports.
- What this kills by construction: the §7.1 leak classes (fresh-arg orphans, borrowed
  from-container locals), most per-node retain/release traffic, and the leak-ratchet
  problem — the new compiler's leak budget is measured in arena drains, not allocations.
- Retire the claim pool in the new compiler: ownership is either arena (bulk) or ARC
  (explicit); the 32-slot ring was scaffolding for the old codegen's ambiguity.

## 9. Phase G — Porting the Pipeline (strangler, suite as oracle)

The macro-architecture is sound and is kept: Lexer → Parser → TypeChecker →
DeclarationGenerator/CodeGenerator → Loader → Driver. The lessons live in the details,
and each is designed in rather than patched in:

- **No interceptor concept at all.** `sysinternal` interface classes are the *only*
  body-less-legal classes; their declarations bind to C by convention and dispatch
  directly (no vtable, no subclassing). Every other class must have real bodies, and
  public facades delegate to `sysinternal` explicitly. A method is either Spec code or
  a floor binding reached through a visible delegation chain — there is no third path.
- **`String` is-a-Buf as ground truth** — no transparent-class special cases, no
  self-param pointer-depth heuristics; the type system knows buffers natively.
- **Container typing without prefix heuristics** — generic types are parsed structures,
  not string patterns; `ArrayItemsLoop`-class collisions are unrepresentable.
- **Namespaces + multiple inheritance for real decomposition** — `CodeGenerator`
  composes `Expressions`/`Program`/`Inference` behaviors explicitly via `using` and MI
  instead of five files sharing `self:fieldTypes` by convention. Small files, one
  responsibility each.
- **Heredocs/templates used from the first file written** — C emission blocks are raw
  `'''` skeletons with ``` holes.

Port order (each module compiles under the old toolchain and runs against the test
corpus as it lands — every module is a delivered artifact, no dark tunnel):

1. Lexer + Token (+ heredoc forms)
2. AST (+ Arena integration)
3. Parser (+ template desugar)
4. TypeChecker
5. DeclarationGenerator
6. CodeGenerator (expressions → program → inference)
7. Loader (full package semantics) + Driver
8. Linter

Gate for each: the full suite compiles and passes with that module's behavior
exercised through the WIP compiler. Gate overall: full suite green with the new
compiler driving compilation end to end.

## 9.5 The Style Contract (how the new compiler is written)

This rewrite is the reference implementation of idiomatic Spec — its source is the
first thing future contributors will read. Every directive below is a requirement, not
a preference:

**Use the language's full expressive surface.** The features exist to be used:

- **Multiple inheritance** for real behavior composition — a class that generates
  expressions *is* an `ExpressionEmitter`; shared concerns (diagnostics, position
  tracking, claim analysis) arrive as base classes, not copy-paste or convention-shared
  fields. If two classes need the same behavior, that behavior gets a base class.
- **Utility classes** for cohesive helper families — static-shaped, stateless,
  construct-and-call (`base:compiler:Strings:isIdentifierStart(...)`), mirroring the
  sysinternal facade pattern. No orphan free-floating logic; everything lives in a
  named class with a stated responsibility.
- **String templates everywhere emission happens** — C skeletons are ```` ``` ````
  blocks with `{{holes}}`, diagnostics are `"..."` templates; per-line concat chains
  are a review flag. The old prelude's 1,878 lines of `p: p . "...\n"` is the
  anti-shape.
- **Enums for every finite set** — token kinds, AST node kinds, member kinds, error
  classes, phases. The old compiler compares raw strings (`'METHOD'`, `'CALL'`) in
  hundreds of places; the new compiler uses enum types with `when` dispatch, so a
  missed variant is a compile error, not a runtime branch silently skipped.
- **`when` over if-chains** wherever a subject has more than two arms; exhaustive
  arms for enums.
- **Named arguments at call sites** (they document intent), **declaration-side
  defaults** where a parameter has an obvious standard value, **array literals** over
  add-loops, **interface-style `using;`** for genuinely dependency-free classes.
- **Loop classes** for iteration bodies with state; `each` for simple folds; the
  sub-parse pattern (fresh Lexer+Parser over a span) wherever a string contains
  structure.

**Clean, maintainable, commented:**

- Every file opens with a `#!` doc block stating the package and the class's single
  responsibility. If the block needs the word "and", the file needs splitting.
- Every method whose purpose is not obvious from its name carries a doc comment
  (`## ... @param/@return`); WHY-comments over WHAT-comments — the code says what,
  the comment says why (invariants, ownership decisions, traps the old compiler fell
  into, e.g. "ordered so ancestor layouts prefix descendants").
- One class per file (plus its private Loop helpers); small methods; no dead code;
  no transitional scaffolding — the rewrite has no generation gap to bridge, so there
  is no excuse for placeholders.
- Ownership is explicit at every boundary: who owns a returned value, what a
  parameter borrows, what an arena absorbs. The §7.1 trap (borrowed-from-container
  locals, shared claims) is documented per module where it applies.
- Error messages are precise and actionable: file, line, what was expected, what was
  found — written as templates with the values in holes.

**The bridge constraint:** the new source must compile under the *frozen* compiler's
feature set — namespaces, array-form using, interface-style declarations, qualified
calls, heredocs/templates, MI, enums, and everything else already landed. Features the
old compiler lacks (new syntax we may want) arrive only *after* self-hosting, when the
new compiler can compile them itself; until then they go on a list, not into the tree.

## 10. Phase H — Self-Host & Retirement

1. Old compiler (frozen) compiles the new compiler's source → `newc-1` (its runtime is
   still the old prelude — the borrowed-floor period; expected, not a defect).
2. `newc-1` compiles the new source → `newc-2`; converge `newc-2`/`newc-3`. The new
   compiler's minimal floor is now the *real* floor; the C surface collapses here, not
   before.
3. Retirement gate: full suite + sanitized PASS **and** the suite's test binaries compiled by
   the self-hosted new compiler.
4. `bootstrap.sh` becomes: build frozen fossil seed → compile new compiler with it →
   self-converge. The old compiler is never edited again; the generation-lag tax on it
   drops to zero by definition.

## 11. Risks & Mitigations

- **Second-system stall** → "done" is defined as parity with the 62-test suite, not
  ambition; macro-architecture kept; heredocs/MI/namespaces serve the port rather than
  inviting redesigns.
- **Borrowed-floor period feels like no progress on the C surface** → expected shape;
  track interceptor count and floor LOC as the honest metrics; the collapse is stepwise
  at self-host.
- **Self-application convergence** → the same discipline already proven; the new
  compiler bakes far less semantics (no interceptors), so lags are smaller and rarer.
- **One-person tunnel** → strangler sequencing; every ported module runs against the
  corpus; String/containers work is shared with the old path, never wasted.
- **Scope creep** → guardrails in §12.

## 12. Guardrails (what we do not do)

1. No further interceptor migrations in the old compiler after the Phase A/B/C freeze.
2. No retrofitting old-compiler source with heredocs/templates/namespace syntax beyond
   the bridge's own needs — it is a fossil-to-be.
3. No new language features in the new compiler until suite parity, except features its
   own source requires (they must work at self-host anyway).
4. `String`/`Buf`/container semantics stay locked by the existing suite throughout —
   the suite is the spec, for both compilers.
5. The floor contract (§6) changes only by explicit decision recorded here — not by
   accretion while porting.
6. **No body-less method declarations outside `sysinternal`** — the
   implementation-environment package: the C floor (bound by naming convention)
   and generator intrinsics like `Reflection` (compile-time constants injected
   at the call site). Checkable by the compiler itself; a violation is a build
   error, not a style nit. Public facades always delegate through a visible
   `base:sysinternal:...():...` call chain.
7. **The new compiler's source uses only the frozen bridge's feature set** — new
   language features are implemented in the new compiler first, self-hosted second,
   and only then used in its own source. No exceptions; this is what makes the
   bootstrap loop converge.
8. **The style contract (section 9.5) is review-blocking** — a module that lands
   without its doc blocks, enum dispatch, templates, or ownership comments does not
   count as ported.

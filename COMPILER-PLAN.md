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

1. **Finish String** in the current compiler (PLAN-STRING.md; mechanism proven, length live).
2. **Land heredocs + templating** — the last language features the old compiler gains.
3. **Freeze the old compiler** after landing only the **namespace/using bridge** it needs
   to compile the new compiler's source. No further interceptor migrations. Ever.
4. **Write the new compiler** on a minimal floor (`sysinternal`), in small namespaced
   files, with **arena** memory management for compiler-phase data.
5. **Self-host**, gate on the 62-test suite, retire the old compiler to a frozen fossil.

The decisive economics: the floor + base library (Buf, String, Array, Map, io wrappers)
is required by *both* paths, so it is shared work. The only true fork is whether the next
months go into ~170 per-function interceptor migrations inside the old codegen — or into
porting the pipeline onto the new base, after which we live in the clean house.

## 2. Current State (baseline for this plan)

- Landed: transparent `String` class, `Buf` floor class, generic direct dispatch
  (body-ful String methods dispatch as `String_<method>(target, ...)`; body-less fall
  through to interception), `String.length` live over the Buf floor. Commit `43778c3`.
- Verification state: converged, rebaselined, 62/62 + sanitized PASS.
- Proven migration pattern: land source → converge cycles → rebaseline → both suites →
  commit. The new compiler inherits this discipline for its own self-hosting loop.
- Known debt that motivates the rewrite: §7.1 leak classes in PLAN-STRING.md, cTypeFor
  prefix heuristics, mixin state sharing, interceptor/codegen entanglement.

## 3. Phase A — Finish String (in flight)

Per PLAN-STRING.md: land remaining bodies one per cycle (charAt, substring, startsWith,
endsWith, contains, indexOf, replaceAll, split, lines, trim, countLeading, isDigit,
isAlpha, isWhitespace, fromCharCode, parseInt), deleting each method's interception
branch as its body goes live. The Buf floor primitives and direct-dispatch machinery are
done; this is now mechanical. `String.spec` emerges as the first portable base-library file.

## 4. Phase B — Heredocs & String Templating (last old-compiler features)

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

## 5. Phase C — Freeze & Namespace/Using Bridge (called out explicitly)

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
Explicitly **out of bridge scope**: full package-semantics polish, the layout-mismatch
lint, deleting the old colon-form, and any retrofit of `lib/` to the new syntax. The
new compiler (Phase G) implements the real semantics and dogfoods them on its own source.

After the bridge lands: **the old compiler freezes.** No new features, no interceptor
migrations, no refactors. It exists to be compiled from the fossil seed and to compile
the new compiler. This is what ends the generation-lag churn permanently.

## 6. Phase D — The Floor Contract (`sysinternal`)

The new compiler is written against a stable floor contract designed once, up front —
not primitives invented per class. Target: **~40–60 tiny C functions** (vs ~230 today),
each 2–15 lines, living in the `sysinternal` package — the sole non-dynamic package.

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

- **No interceptor concept at all.** Body-less floor declarations + direct dispatch is
  the *only* mechanism. A method is either Spec code or a floor binding; there is no
  third path and no per-method C branches.
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

Gate for each: the 62-test suite compiles and passes with that module's behavior
exercised through the WIP compiler. Gate overall: full suite green with the new
compiler driving compilation end to end.

## 10. Phase H — Self-Host & Retirement

1. Old compiler (frozen) compiles the new compiler's source → `newc-1` (its runtime is
   still the old prelude — the borrowed-floor period; expected, not a defect).
2. `newc-1` compiles the new source → `newc-2`; converge `newc-2`/`newc-3`. The new
   compiler's minimal floor is now the *real* floor; the C surface collapses here, not
   before.
3. Retirement gate: 62/62 + sanitized PASS **and** the suite's test binaries compiled by
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

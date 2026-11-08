# FUNCTIONS.md — Overloads, Call Resolution, and the Conditional Plan

**Status:** accepted plan, pre-implementation. Companion to INSTANCE.md,
which remains the governing contract for the instance-based call model — its
enforcement numbering (E1–E10, N1–N11, §2.x) stays authoritative there, and
compiler diagnostics keep referencing it. This file is the contract for the
functions-layer work that builds on that model; nothing in Parts I–II may be
weakened during implementation without updating this file in the same commit.
Part III carries the obligations INSTANCE.md left open.

---

## Part 0 — INSTANCE.md status and verification record

INSTANCE.md is complete on the language side: Phases 0, 0.5, A1–A4 and B
landed; E1–E9, R1–R4, N1–N11 and P1–P6 are implemented and gate-verified
(bootstrap fixed point, suite, sanitized). It remains the reference document
for the call model. Three items carry forward to Part III: **E10**, the
**docs/ tree refresh**, and the **deferred-by-design** §10 remainders
(generic as-imports, import aliasing).

The numbering referenced by compiler diagnostics and comments:

| Ref | Rule | Status |
|-----|------|--------|
| §2.1 | Import forms: `['pkg', X]` type import; `['pkg', as X(args)]` instance import | implemented |
| §2.2 | Call resolution order; class-name receiver admits only `init` unless instance-imported or type-level | implemented |
| §2.3 | Bare scope (own + inherited + direct as-imports, one level, methods only); collisions force qualification; fields unreachable through a prefix | implemented |
| §2.4 | Dispatch: zero-field imports elided; field-ful imports dispatch through the synthetic `_import_X` field | implemented |
| E1–E9 | Enforcement set (literal args, legality, uniqueness, acyclicity, resolution, visibility, construct-only init, static-path deletion, duality removal) | implemented |
| E10 | Loop-body instantiation lint (hoisting hint) | **carried — Part III** |
| X1–X4 | Exempt strata (runtime-managed classes, enums, primitives/containers, sysinternal floor) | implemented |
| R1–R4 | Alias-layer retirement | implemented |
| R5 | Documentation | KNOWLEDGE-SPEC + README done; **docs/ tree carried — Part III** |
| N1–N11 | Negative tests | implemented |
| §10 | Deferred: generic as-imports, import aliasing | **deferred by design** |

---

## Part I — Overloads and call resolution

Spec gains signature overloads. This consciously reverses INSTANCE.md §2.3's
"collision by name only, never by signature": **within one provider,
signatures may vary; across providers (own vs imports), the name rule
stands.**

### I.1 Legality (declaration time)

Two same-named methods may coexist iff their signatures differ. A signature
is (parameter count, parameter names, parameter types). Identical signatures
are the old duplicate-member error, with an upgraded message: *"identical
signature"*.

Overloads are the language's way to provide defaults: a version with a
defaulted argument is an overload without it.

### I.2 Resolution (call time)

Three exact stages; **exactly one survivor** at the end, or a compile error:

1. **Arity** (positional calls): exactly one overload with that parameter
   count. Zero → *"no signature takes N arguments"*. Two or more →
   *"ambiguous — use named arguments"* (the same-arity shorthand ban).
2. **Name-set** (named calls): exactly one overload whose parameter-name set
   equals the given argument-name set, order-insensitive, no extras, no
   missing.
3. **Exact type match**: each argument's inferred type must *equal* the
   parameter's declared type (canonical type strings, generic substitution
   already grounded; an `Any` argument matches nothing exactly).

Because legality requires distinct signatures and selection requires exact
type equality, **at most one candidate can ever survive stage 3** — there is
no ambiguity analysis, no partial ordering, no best match. The only failure
is zero survivors: *"no exact overload for (types); cast the argument"*.

**Conversions never choose.** Int→Float widening applies only *after*
selection, as today. A call whose name has a single overload keeps today's
assignability behavior — zero migration.

Exact static type only: a `Dog`-typed argument selects `f(Dog)`, never
`f(Animal)`; cast to select otherwise.

### I.3 Boundaries (v1)

- **No mixed calls.** A call is all-positional or all-named.
- **No defaults inside overload groups.** Declared parameter defaults
  (`Int is factor: 2`) exist and work on single-method names — the
  merge-forward path depends on them (merge_function_test) — but they are
  invisible to overload resolution: an overloaded name's arity filter
  rejects partial calls, so defaults cannot participate. While's var-decl
  defaults are a separate, contained mechanism.
- **No overriding an overloaded method.** Virtual dispatch is name-keyed
  (`methodSlots`, vtable slots); if a method name is overridden anywhere, it
  has exactly one signature. `replace` on an overloaded name is a compile
  error. Constructor dispatch is direct, so **`init` overloads are allowed**
  — multiple constructors selected by arity/names/types.
- **Generic classes defer.** Inside `Box of T`, type-params do not
  exact-match; generic classes keep arity/name differentiation.
- **Sysinternal floor methods cannot be overloaded** (the `spec_<snake>`
  naming convention binds by name).
- **Builtin-intercepted methods (Math, Output, Stderr):** the builtin table
  keys on method name and must become **type-aware** for overloaded names —
  selecting the emission by the argument's inferred type (an Int `abs`
  variant wants an `llabs`-backed floor function). Contained change to
  `BuiltinCallGenerator`.

### I.4 Implementation map

- [x] **Loader** — replace duplicate-member rejection with the legality
  validation (same name legal iff signatures differ; identical signature →
  the upgraded duplicate error). Group merging validates the same rule
  post-union.
- [x] **Checker** — `selectOverload(className, methodName, args)`:
  the I.2 pipeline, in order, with diagnostics naming the candidates and the
  argument types. Stamp the selected overload on the call expression
  (`overloadIndex`) — the one place the gen must not re-derive.
  `checkCallArguments` type-checks against the selected overload.
- [x] **CodeGenerator** — consume the stamp; emit type-suffixed C symbols
  (`Class_method`, `Class_method_2`, … by declaration order — deterministic
  under the fixed point). `formatCallArguments` binds against the stamped
  overload's parameters.
- [x] **BuiltinCallGenerator** — type-aware interception for overloaded
  runtime-managed methods (Math first: `abs(Int)` via an integer floor, or
  de-intercept Math into real bodies over a floor — decide at
  implementation).
- [x] **Driver** — the heuristic iterates members, so any `init` overload
  with a Map parameter already matches; verified unchanged.
- [x] **Resolution note (implementation finding):** the scoped-region
  desugaring (`as:` / `as (params):`) appends the remainder block as a
  trailing positional argument to a named-argument call — the one sanctioned
  mixed shape. The resolution filter accepts it (named arguments must name
  real parameters; the trailing positional binds to the last parameter).
- [x] **Iteration-closure finding:** an early `return` inside a
  `While:condition` iteration closure compiles to a loop `break` — the
  legality pass nests its body instead of returning early. Codegen
  reference for future passes.
- [ ] **INSTANCE.md's consumers** — E5/E9/bare-scope providers stay
  name-level; overload selection applies within a provider. Composes without
  change.

### I.5 Tests

- [x] Positive: arity-distinct overloads (the Conditional API shape);
  type-distinct same-arity `init` overloads; overloads + bare scope;
  `Math:abs(Int)` via the type-aware interception (`spec_math_abs_int`).
  tests/overloads_test.spec + tests/overloads/Over.spec.
- [x] Negative: illegal identical signature (N12); ambiguous positional
  (N13); no-exact-match for Any arguments (N14); mixed-call rejection
  (N15); `replace` on an overloaded name (N16). Overload-on-floor-method
  is blocked by the sysinternal naming convention (no explicit test).
- [x] Zero migration: the full suite compiled unchanged at every step (the
  only breaks were the new strictness rules catching the scoped-region
  desugaring's shape — now sanctioned).

---

## Part I-d — The scoped region (§as): no invisible argument

**§as The remainder fills the declared-but-unbound scope slot.** The
`as:`/`as (params):` statement collects the remainder of the enclosing
block and binds it to the called callable's **last parameter, declared
`Function`, left unbound** by the explicit arguments. The remainder
never participates in overload selection: resolution runs on the
explicit arguments' arity (exact match first, then the open-slot shape
params == explicit + 1 with a Function-typed last parameter). A callable
whose parameters are all bound has no open slot — a scoped region on it
is a compile error (the Conditional else-collision is unrepresentable,
N19). The scoped region on an open Conditional branch makes the body
the then-branch — conditional scopes compose from the same primitive.

The mixed-call exemption for the old desugared shape is removed: the
desugarer no longer produces mixed calls, and the no-mixed-calls rule
is total.

---

## Part I-c — Import gating (Option A, landed)

**§I.6 Construction and type positions require the import.** The
transitive availability of a dependency's dependency grants nothing:
a type position (`local X is v`, parameters, fields, return types,
`Array of X` elements, casts to `X`) and an `X:init(...)` call require
`X` in the enclosing class's own `using` — or an ancestor's (imports
are inherited), or the same source file, or the X3 stratum. Package
wildcards cover every class whose declared namespace falls inside them;
`group: [X]` declarations grant their target. As-imports grant
everything (they are using entries). When-patterns are ungated: the
subject's declared type already required the import.

The E5 diagnostic no longer says "or construct one" — construction is
gated too. The ancestor-walk budget is raised 8 → 64 (deep hierarchies
no longer fail as misleading undefined-member errors). N18 pins the
gate: a dependency's dependency, loaded but not imported, is rejected
in both type and constructor positions.

---

## Part I-b — Hardening record (landed with Part I)

- **D5 fixed:** relational operators on String compare lexicographically
  through a new `spec_string_compare` floor; the ordering-op emission is
  split from the arithmetic arm; mixed String/non-String relational
  comparisons are compile errors (N17). string_compare_test covers
  ordering, reflexivity, and prefix cases.
- **Iteration-closure return semantics fixed:** the inlined
  `While:condition` loop now gives the iteration body a real return
  variable — `return true` continues (skipping the rest of the body),
  `return false` stops the loop, `return <expr>` decides at runtime. The
  old emission discarded the returned value entirely (early `return false`
  never stopped the loop).
- **Stale claim corrected:** class downcasts are runtime-checked
  (`spec_cast_check` panics on failed narrowing); INSTANCE.md's
  "unchecked casts" note was wrong and is corrected.
- **Composition verified:** a field-ful as-import selects among `init`
  overloads by its literal arguments (StatefulCounter carries both
  `init(String)` and `init()`).

---

## Part II — Conditional (`if` becomes a class)

**Strictly after Part I lands** — the three-overload API is legal only under
the I.1/I.2 rules (arities 2/3/4 are distinct, so positional shorthand is
unambiguous).

### II.1 The API

**Foundation landed** (this commit): the floor (`base:sysinternal:Conditional`,
one primitive bound to `spec_branch` + `spec_call_closure_0`), the wrapper
(`base:sys:Conditional`, three overloads composed — `else` is `!check`),
the statement-form inline (zero-allocation native C if/else; branch bodies
inline into the enclosing function so guard-clause returns work; branch
closures type-check against the enclosing method's return type), and the
conditional_test regression (7 checks: 2-arg primitive, 3-arg composition,
finally, guard clause, nesting, bare calls, scoped open slot). The emitted C contains the
floor's `spec_branch` only in the wrapper's own fallback body — user
conditionals are native C. Param `otherwise` is the temp spelling of
`else` (keyword) until the flip. Branch-as-expression is checker-rejected
(void) until the value-yielding inline lands. The `as:` interaction is
resolved by the scoped-remainder model: the remainder is not an added
argument — it binds to the callable's declared-but-unbound last Function
parameter, never widening the arity. `as:` on an open branch makes the
body the then-branch; `as:` on a fully-bound branch is a compile error
(§as, N19) — the else-collision is unrepresentable.

```spec
Class is Conditional {
	Function is if(Function of Boolean is check, Function is then)
	Function is if(Function of Boolean is check, Function is then, Function is else)
	Function is if(Function of Boolean is check, Function is then, Function is else, Function is finally)
}
```

Call sites pass the check as a Kotlin-style closure — `if(check: { x > 0 },
then: { ... })` — or rely on the parse-desugar to produce it from the
legacy statement form.

`finally` runs always (after whichever branch). `else if` chains become
nested calls — accepted readability cost, and the natural future case for
`as:`-style desugaring.

### II.2 Semantics — the While precedent, not a closure runtime

A closure-runtime `if` (floor function invoking closures) is **rejected**:
non-local `return` dies (guard clauses — ~620 sites), every branch allocates
a closure, and branch typing goes soft. Instead, the proven
`While:condition` arrangement:

- The parser emits an ordinary call with anon-fn arguments — no `IF_ELSE`
  nodes, no `if` keyword.
- The codegen **inlines** the recognized call shape to zero-allocation C:
  `if (check) { <then body> } else { <else body> }` + `finally` after.
  Bodies are inlined into the enclosing function, so `return` inside a
  branch is a real method return.
- The sysinternal floor `if` (`spec_conditional_if` + the runtime's
  `spec_noop_closure` for omitted branches) is the **reference
  implementation and fallback** for any call shape the inliner does not
  recognize.
- The check is a **closure that must return Boolean**
  (`Function of Boolean is check`) — adopted after the expression form
  (below) proved unenforceable: with the param typed `Boolean`, the
  composition `!check` in the wrapper could not be expressed once check
  became a value, and the Boolean-ness of the check body was validated
  only by special case. With the param typed `Function of Boolean` the
  three-stage exact match enforces the shape structurally: a closure
  whose body yields a non-Boolean last expression keeps the plain
  `Function` type and is rejected. The **Kotlin convention** completes
  the typing (FUNCTIONS.md Part II, checker RETURN arm + ANON arm): a
  void-declared closure's `return <expr>` *establishes* the closure's
  return type (the body determines the return), the brace shorthand's
  trailing expression already desugars to that return at parse time, and
  a typed closure's explicit-terminator last expression validates
  against the declared return. Write-backs happen at the return site —
  the checker never re-infers an already-checked expression (re-running
  the call machinery mid-check corrupts the checker's persistent
  scoping state and cascades into every later file). The wrapper's own
  self-calls are recognized as branch calls (the self disjunct), so the
  composed overloads' `check: { return !check(); }` not-closures pre-type
  Boolean and invoke through `spec_branch`'s bool-cast.
- The expression form (`local X is x: if(check: c, then: { a }, else: { b });`)
  inlines as a statement expression; branch typing uses the checker's
  bidirectional flow (the expected type flows into both branches' last
  expressions — the same machinery container callbacks use).

### II.3 The flip

1. Build `Conditional` under a temp name (`branch`) — the parser rejects a
   method named `if` while `if` is a keyword, so the rename and the keyword
   removal are **one atomic commit**.
2. Inline codegen + floor fallback, tested.
3. Scripted migration of ~1,934 `if` sites (1,649 compiler/stdlib statements,
   285 tests/examples, 94 `else if` chains, 26 if-expressions).
   **Migration status:** a textual if→branch sweep was attempted and
   **reverted** — the self-hosted checker's own if-statements are
   state-machine code (local declarations feeding sibling branches,
   validation guards sharing checker state) that closure-conversion
   turns into checker-internal type errors. The correct tool is a
   **parse-time desugar**: the parser's if-statement arm emits the
   branch-call AST directly (the established pattern — the `as:` and
   template desugars work exactly this way), handling every shape
   structurally. Sequencing: desugar if→branch behind the keyword
   (sources keep reading `if` but compile to Conditional calls), verify
   the suite, then the flip.
4. The atomic flip: rename to `if`; delete `Keyword:IF`/`ELSE`,
   `StatementKind:IF`, `ExpressionKind:IF_ELSE`, the statement/expression
   parse arms, the gen's if-emission, and the checker's
   "condition must be Boolean" rule (parameter typing covers it). Every
   exhaustive `when` over the shrunken enums loses arms.
5. `else` ceases to be a keyword in the same commit.

---

## Part III — Carried from INSTANCE.md

- [ ] **E10 — loop-body instantiation lint.** Warn when an `as X(args)`
  import or a manual `X:init(...)` lands inside a loop body of the importer
  (hoisting hint). Warning, not error.
- [ ] **docs/ tree refresh (R5 remainder).** `docs/STYLE_GUIDE.md` and
  `docs/tooling/README.md` still show retired `output:`/`error:` spellings;
  `docs/language/README.md` (852 lines) and `docs/packages/README.md` were
  never updated to the instance model. Update to as-imports, the class-form
  singletons, and the call model; add package-author guidance for type- vs
  instance-imports.
- [ ] **Deferred by design:** generic as-imports (`as Box of Int()`);
  import aliasing (`as Math() is fastMath`); type-differentiated overloads
  inside generic classes.

---

## Verification discipline

Gates at every step: `bash utilities/run_tests.sh`,
`bash utilities/run_sanitized.sh`, `./bootstrap.sh` fixed point.
Commit seed regeneration atomically with each source change. If gcc fails on
the seed itself, the seed was poisoned by a broken intermediate emission:
`git checkout -- bootstrap/spec.c` (the last committed seed compiles any
source set using shipped language features) and reconverge.

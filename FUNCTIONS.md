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
- The expression form (`local X is Conditional:branch(check: { c }, then:
  { a }, otherwise: { b });`) **landed**: a 3-arg branch call in a context
  that expects a value (declaration, assignment, return — detected via the
  bidirectional `expected` flow) is a statement expression
  `({ T _v; if (cond) { ... _v = a; } else { ... _v = b; } _v; })`. Each
  branch closure's LAST return is its yield (the `checkingValueYield`
  marker overrides the method-routing for that one statement; mid-body
  returns still return from the method); the two yields must unify
  (mismatch = compile error, N20). The yield assignment mirrors
  `emitReturn`'s ARC three-way (owned-local swap / fresh-cast / retain) so
  scope releases cannot dangle the result. Statement-form 3-arg calls stay
  void-routed. The whole compiler's 27 legacy `if`-expression sites were
  migrated to this form — the fixed point is byte-identical with control
  flow compiling through Conditional.

### II.3 The flip

1. Build `Conditional` under a temp name (`branch`) — the parser rejects a
   method named `if` while `if` is a keyword, so the rename and the keyword
   removal are **one atomic commit**.
2. Inline codegen + floor fallback, tested.
3. Scripted migration of ~1,934 `if` sites (1,649 compiler/stdlib statements,
   285 tests/examples, 94 `else if` chains, 26 if-expressions).
   **Migration status: the compiler/stdlib half is DONE** — every
   statement-form `if` in `spec/base` and `spec/lib` (≈1,800 sites across
   ~50 files) now compiles as `Conditional:branch(...)`, statement form
   and value form; only the raw-C prelude (RuntimePrelude.spec) still has
   C `if`, and it was never Spec. The first textual sweep was reverted;
   the working tool is a string/comment-aware scanner with
   paren/brace-matched spans, run **incrementally** (a few files per
   batch, emit→gcc→self-load pre-check, bootstrap, commit — the ratchet:
   a too-big single hop breaks the old generation's loader, small hops
   converge). Two latent gen bugs surfaced and were fixed along the way:
   the branch inline must INHERIT the enclosing inline-return context
   (a `return false` inside a branch nested in a loop's iteration is a
   loop-stop, not a method return), and materialized closures must write
   back mutated captures (assignments inside callbacks were silently
   lost). Remaining: tests/examples (~285 sites), then the flip (step 4).
4. **The atomic flip: DONE.** `Conditional`'s user-facing API is
   `if(check:, then:, else:, finally:)`; `Keyword:IF`/`ELSE`,
   `StatementKind:IF`, `ExpressionKind:IF_ELSE`, their parse/checker/gen/
   linter arms, and the AST if-fields are deleted. `else` ceased to be a
   keyword in the same commit; the when-else arm detects it by value.
   The floor keeps its internal `branch` binding (`spec_branch` in C) —
   only the wrapper's Spec-level names matter.
   Bootstrap mechanics (for the record): the flip could not land in one
   bootstrap because each generation's compiler must parse the next
   generation's sources, so the spelling change rode a series of
   converged prep commits — the named-arg and expression-position
   keyword bridges, dual branch/if recognition in the checker and gen,
   the cIdent C-keyword escape, and expected-flow threading into binary
   operands and branch yields — after which the rename + deletions
   converged in one bootstrap. The bridges were removed immediately
   after (the keywords no longer exist to bridge).
5. `spec_checker_test`'s boolean-condition case now exercises the
   Function-of-Boolean enforcement through `While:condition` (the
   if-statement rule it used to check no longer exists).

### II.4 — `While` folds into a control-flow provider (planned)

`While` is a standalone class in `base:iterator` (beside `Loop`,
`LoopControl`, `LoopCallback`); callers import it per-class
(`as While()`) and spell `While:condition(...)` / `While:run(...)`
(~124 call sites; ~103 in the compiler/stdlib). The plan: fold the
control-flow constructors under ONE provider — `Iterator` (matches the
package) or `Loops` (reads better beside `while`/`loop`/`for`;
decision open) — so a single as-import serves the constructs bare,
mirroring `Conditional`'s `if(...)`: `while(evaluate:, iteration:)`.

On record for the move:

- The gen intercepts `While`'s `run`/`condition`/`init` by receiver
  name (`targetC == 'While'` in BuiltinCallGenerator; both bodies are
  runtime-managed — neither is emitted). The interception re-keys onto
  the provider move, or the provider's methods keep the class identity.
- The call-site rewrite is mechanical — `While:condition(` → `while(`
  — the exact shape `utilities/migrate_if.py` handled for the if-flip
  (string/comment-aware, paren/brace-matched, idempotent). **This is
  why the utilities/ folder outlives the if-flip**: it runs once more
  for this rename, then the folder goes.
- The ratchet applies: a few files per batch, emit→gcc→self-load
  pre-check, bootstrap, commit; the bootstrap's older generations must
  parse the new spellings, so the checker/gen carry dual recognition
  bridges until the flip commit deletes them (the II.3 pattern).
- `LoopControl` stays a separately importable TYPE (signature
  positions use it); the provider surfaces only the call forms.

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

## Part IV — Call-scope semantics: `as` imports, inner classes, inherited imports

**Status: planned.** The flip made every call flow through `Conditional:if`;
this part defines WHO can call WHAT bare, and what an import actually grants.
Grounded in the current implementation: `collectBareProviders` already walks
all `baseClasses` transitively (the ancestor lattice), `accessInClass` walks
own using + file grants + ancestors, and nested classes register flat with
NO outer link — they are same-file classes, nothing more.

### IV.1 The semantics (the contract)

1. **`as` import (scoped import).** `['base', 'sys', as Conditional()]`
   adds the imported class's **functions** to the enclosing scope: bare
   `if(check: ..., then: ...)` resolves through the scoped provider. It
   grants **functions only**:
   - fields of the imported class are NOT in scope;
   - private (`local`) members of the imported class are NOT callable
     through the import;
   - the import is **not re-exported**: importing a class that itself
     imports X does not bring X into scope. One level, always.
2. **Inner classes** (classes declared inside a class body):
   - inherit the enclosing class's imports — plain and `as` — **as if they
     were the inner class's direct parent's**;
   - inherit the enclosing class's members under the standard child
     visibility (the same as any parent-child pair; `local` members stay
     sealed to the class that declared them);
   - MAY declare **additional imports** that scope to the inner class and
     everything nested inside it — and to nothing else (not the outer,
     not siblings).
3. **Multiple inheritance merges imports.** A class with several parents
   sees the union of all parents' imports (plain and `as`) in its scope
   and in its §I.6 type-position gating. This already falls out of
   `collectBareProviders`'s lattice walk — the work is verification plus
   the gating walk and the gen side.
4. **An imported class is not a parent.** The as-import grants the
   function surface; it grants no fields, no private access, and no
   transitive scope. Only `of`-inheritance merges scope.

### IV.1b — `group:` retired

The `group: [Target]` partial-class mechanism (fragments merging at load
time) is **removed**. Multi-parent assembly is MI —
`Class of Greeter, Language, English is EnglishGreeter` — and glue between
classes is exactly what the child of an MI declaration provides: normal
access to both parents, both parents independently verifiable. What
partials uniquely offered — cross-fragment shared fields — was unused
outside its own test and is unrepresentable under MI by design. The
loader's fragment machinery, the gating's `group` recognition, and the
docs surface are gone; N21 asserts a `group:` declaration no longer
merges.

### IV.2 The model change: the outer link

- `ClassInfo` gains `outerName: ''` — set by the parser at nesting time
  (the parser knows the nesting; the loader only flattens).
- The registry key for an inner class becomes the qualified
  `Outer:Inner` (chains: `Outer:Mid:Inner`), fixing today's silent
  same-bare-name merge in `seenBareNames` — two same-named inner classes
  under different outers are distinct classes.
- The loader's `synthesizeInto` records the outer link; the diagnostics
  print the qualified name.

### IV.2b — Landed

- **The link**: the parser's `linkNestedClasses` sets the qualified outer
  chain (`outerName`) and appends the enclosing class to the nested
  class's `baseClasses` — the standard lattice walks (the bare scope, the
  §I.6 gating, the visibility, the member lookup) serve inner classes
  with no special cases.
- **The MI field split** (`collectStructFieldsSplit`): the declared-of
  lattice's fields keep their construction expressions; the outer-link
  fields zero-init. An inner instance starts with an **empty
  parent-part** — the inner's methods set what they need. This fixed the
  allocation storm: the hot-path scan loops were allocating the
  enclosing class's containers per instantiation.
- **The construction exemptions**: `init` never enters the ancestor
  signature/return compatibility checks (constructors are per-class);
  the outer-link relation is exempt from the abstract-member enforcement
  (the link is an access scope, not an is-a contract).
- **The inherited-import synthesis**: the loader walks the base lattice
  and synthesizes each ancestor's as-entries onto the inner (deduplicated
  per target) — the outer's as-imports dispatch on the inner's own
  instances.

### IV.2c — The qualified registry keys (landed)

**The refinement**: inner classes, like functions, are available when
imported. Like functions, a bare reference that is ambiguous is an error,
and the user resolves it by prefixing with the imported class
(`LibA:Helper`). The inner classes join the same resolution surface as
the functions — the same providers, the same ambiguity rules, the same
prefix escape.

**The phases** (each converged alone; the suite green at each boundary):

1. **The C symbol qualification** ✅ (90495e3) — `qualifiedName()` on
   ClassInfo; the gen's symbol emissions qualify via cIdent (':' → '_').
   Zero semantic change: findClass still resolves bare, the first
   registration wins. The in-tree nested classes rename mechanically
   (`CBackendUtils_SnakeCaseLoop_init`).
2. **The qualified type references parse** ✅ (dc9cc8b) — parseType
   consumes the glued colon path; findClass (checker + gen) resolves the
   qualified identity; the registries carry the qualified and C-symbol
   keys. The member-lookup funnels route through one canonical resolver
   (`memberLookupRoot` / the gen twin): the qualified receiver resolves
   to the inner class itself — its members, its return types, its
   construction pair (`LibA_Helper_new/_init`) and dispatch symbol
   (`LibA_Helper_value`). The resolved root absorbs the colon chain, so
   the segments are never mistaken for type arguments (container forms
   like `Array:String` keep the bare root).
3. **The import grant + the provider resolution** ✅ (18ee948) — the
   per-scope nested-type map (built once per class: own nested classes,
   the as-imported classes' nested classes, the base lattice; cleared
   and rebuilt on scope change) resolves the bare nested-class reference
   with ONE lookup. Exactly one provider rewrites the type to its
   qualified identity (the parent grant covers it downstream); several
   collide and the error names the providers — the same rule the bare
   function calls run. The N25 blanket collision is retired: same-named
   inners under different outers are legal declarations; the duplicate
   WITHIN one outer stays the declaration error (keyed by qualified
   identity).
4. **The qualified registry keys** ✅ (this commit) — the C identity of
   a nested class is the qualified symbol everywhere: the bare-alias
   typedef exists only when the bare name is unique across the program;
   the synthesized contract symbols (`_toString`), the method
   definitions' symbols and self types, the `self` capture type, the
   ctor/dispatch casts, and the overload owners all derive from
   `qualifiedName()` — the overload-owner accumulator carries the
   qualified identity so two same-named inners emit distinct symbols
   (`LibA_Helper_value` / `LibB_Helper_value`).

**Memory discipline** (8cec4eb): the compiler-phase object arena retired
— every class allocates through ARC; the method-body scope releases
funnel through a cleanup label on every return path (the trailing
release list was dead code past any return and leaked every
early-returning method's locals). The self-compile peak dropped
964 MB → 791 MB.

**What stays out of scope**: importing a nested class WITHOUT importing
its enclosing class (the grant rides the parent's as-import); the
same-named inner classes in the SAME outer (the duplicate declaration —
still an error).

### IV.3 The resolution rules (checker)

- **Bare scope** = own members → own as-imports → the outer chain's
  members and as-imports (inner-of-inner walks all the way out) → the
  base-class lattice's members and as-imports (existing walk). Exactly
  one provider or a compile error (the existing E9/collision rules).
- **Shadowing**: the closer scope wins silently (inner import over outer
  import over parent import); a collision between two providers at the
  SAME level stays the force-qualification error.
- **§I.6 gating** (`accessInClass`): the access walk becomes own using →
  the outer chain's using → the base lattice's using → the file grant.
  The file grant remains as the same-file convenience, but the scoped
  semantics no longer depend on it.
- **The imported wall**: the bare-provider path and the qualified
  `X:member` path both run the visibility check — `local` members of an
  as-imported class are unreachable, and the as-import never exposes
  fields. The elided-dispatch call on a field-ful import keeps the
  synthesized `_import_X` field on the CALLING class (unchanged).
- **The as/using split (strict)**: the PLAIN terminal (`'ns', X`) is the
  type import — it grants the bare type reference and, with it,
  construction. The as-form terminal (`'ns', as X()`) grants functions,
  instance dispatch, and the qualified nested-type references
  (`X:Inner`) — never the bare parent type, never construction. The
  declaration-side defaults (`Math2 is m : Math2:init()`) are the
  dependency-injection surface: the default auto-instantiates on
  omission, binds partially by name, and gates against the DECLARING
  class's imports exactly like a body expression.

### IV.4 The gen side

- The inner class's bare calls to the outer's imports stamp
  `bareProvider` exactly as today — the elided dispatch and the
  synthesized fields must work when the caller is an inner class
  (verify the slot map for the flattened inner classes).
- The qualified `Outer:Inner` registry key renames the emitted C symbols
  (`Outer_Inner_method`) — the cIdent pass handles the colon.

### IV.5 Value-yield polish & hardening (Part II completion)

- **V1 — the Function assignability hole.** `isAssignable` treats all
  Function types as mutually compatible. Tighten: `Function of X` →
  `Function` stays legal (a typed closure feeds an untyped param);
  `Function` (void) → `Function of X` REJECTS (a void closure through a
  bool-cast reads garbage — the spec_branch check cast); `Function of X`
  → `Function of Y` rejects unless X == Y or either is Any. Then audit
  the call sites the tightening breaks (the stdlib's callback params).
- **V2 — the yield-ARC audit.** The yield assignment mirrors emitReturn's
  owned-local NULL-swap — but a yield does not end the enclosing scope:
  if the swapped local is read AFTER the if-expression it is NULL. Decide
  and implement: yield = retain (the ARC-safe copy), keeping the swap
  only for the true-return path; add a use-after-yield regression test.
- **V3 — the negative diagnostics.** The 2-arg form in value context and
  the 4-arg (finally) form in value context get dedicated messages
  (today they surface as `cannot assign 'void'`).
- **V4 — the coverage matrix tests** (`tests/value_yield_test.spec`):
  nested yields in check positions, yields in return position, guard
  clauses inside value branches, yields under `as:` scoped regions, bare
  `if()` yielding, a yield feeding a binary operand, the mismatch
  negative (N20 covers), the statement-form-in-value-context negative.
- **V5 — the diagnostics formatting.** Function types render as
  `Function of Boolean` in error messages (today the colon form leaks:
  `Function:Boolean`).

### IV.6 The test plan (verified)

- `tests/inner_class_test.spec`: the outer's members and imports visible
  inside the inner (the parent method, the parent field, the outer's
  as-import bare); the inner's own additional import scoped to it.
- `tests/import_wall_test.spec`: the grant surface — the MI merge (two
  parents' as-imports both callable bare through the lattice), the
  inherited-import gating (the parent's imported class's nested type
  constructs and dispatches through §I.6 via the lattice).
- The rejection surfaces (the walls hold, each pinned by a regression):
  N24 (the `local` member through an import), N26 (the field wall —
  the grant never exposes fields), N27 (the inner's own import does not
  leak into the enclosing class), the transitive pair (no re-export),
  N3 (the same-level collision forcing qualification), N25 (the bare
  nested reference with two providers naming them).

### IV.7 Sequencing

1. V1 (the Function tightening) alone — converge; fix the fallout.
2. V2 (the yield-ARC) + the regression test — converge.
3. V3 + V5 (the diagnostics) — converge.
4. IV.2 (the outer link + the qualified registry name) — converge; this
   shifts the slot map and the registry keys, so it rides alone.
5. IV.3 (the resolution rules) + the gating walk — converge.
6. IV.4 (the gen verification) + the test files — converge.
7. The negatives — converge.
Every step: the ratchet discipline (small batches, the emit→gcc→self-load
pre-check, bootstrap, commit), the full gates green before the next.

---

## Verification discipline

Gates at every step: `bash utilities/run_tests.sh`,
`bash utilities/run_sanitized.sh`, `./bootstrap.sh` fixed point.
Commit seed regeneration atomically with each source change. If gcc fails on
the seed itself, the seed was poisoned by a broken intermediate emission:
`git checkout -- bootstrap/spec.c` (the last committed seed compiles any
source set using shipped language features) and reconverge.

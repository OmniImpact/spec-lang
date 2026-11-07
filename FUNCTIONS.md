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
- **No declared method-parameter defaults.** Overloads replace the use case;
  `While`'s var-decl defaults are a separate, contained mechanism and stay.
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

- [ ] **Loader** — replace duplicate-member rejection with the legality
  validation (same name legal iff signatures differ; identical signature →
  the upgraded duplicate error). Group merging validates the same rule
  post-union.
- [ ] **Checker** — `selectOverload(className, methodName, args)`:
  the I.2 pipeline, in order, with diagnostics naming the candidates and the
  argument types. Stamp the selected overload on the call expression
  (`overloadIndex`) — the one place the gen must not re-derive.
  `checkCallArguments` type-checks against the selected overload.
- [ ] **CodeGenerator** — consume the stamp; emit type-suffixed C symbols
  (`Class_method`, `Class_method_2`, … by declaration order — deterministic
  under the fixed point). `formatCallArguments` binds against the stamped
  overload's parameters.
- [ ] **BuiltinCallGenerator** — type-aware interception for overloaded
  runtime-managed methods (Math first: `abs(Int)` via an integer floor, or
  de-intercept Math into real bodies over a floor — decide at
  implementation).
- [ ] **Driver** — entry heuristic: *first class with an init accepting a
  Map* (any overload), else first non-enum.
- [ ] **INSTANCE.md's consumers** — E5/E9/bare-scope providers stay
  name-level; overload selection applies within a provider. Composes without
  change.

### I.5 Tests

- [ ] Positive: arity-distinct overloads (the Conditional API shape);
  type-distinct same-arity `init` overloads; overloads + bare scope;
  overloads on a field-ful as-import (synthesized constructor call selects
  by literal types).
- [ ] Negative: illegal identical signature; ambiguous positional (same-arity
  overloads, positional call); no-exact-match (Any argument; wrong type);
  mixed-call rejection; `replace` on an overloaded name; overload on a floor
  method.
- [ ] Zero migration: the full suite compiles unchanged (no overloads exist
  today; every call has exactly one member).

---

## Part II — Conditional (`if` becomes a class)

**Strictly after Part I lands** — the three-overload API is legal only under
the I.1/I.2 rules (arities 2/3/4 are distinct, so positional shorthand is
unambiguous).

### II.1 The API

```spec
Class is Conditional {
	Function is if(Boolean is check, Function is then)
	Function is if(Boolean is check, Function is then, Function is else)
	Function is if(Boolean is check, Function is then, Function is else, Function is finally)
}
```

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
- The check is an **expression** (`Boolean is check`), never a closure.
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

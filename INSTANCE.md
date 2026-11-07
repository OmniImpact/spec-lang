# INSTANCE.md — The Instance-Based Call Model

**Status:** accepted design, pre-implementation. This file is the contract the
implementation must satisfy. Every defect cited below was reproduced against
`bin/spec` (see §1). Work proceeds in the phases of §7; nothing in §2–§5 may be
weakened during implementation without updating this file in the same commit.

---

## 0. Summary

Spec becomes strictly instance-based. A class's members are callable only
through a value of the class's type. The class name itself admits exactly one
call: `init` (construction). To preserve today's ergonomics, the `using` array
gains an instance form — `['pkg', as ClassName(args)]` — which instructs the
compiler to materialize and own an anonymous instance scoped to the importing
class instance; its members are then reachable through the class-name prefix
(`Math:round(...)`) and, where unambiguous, bare (`round(...)`). Name
collisions in scope force qualification. The two accidental dispatch modes in
today's code generator (NULL `self`, throwaway instance) are deleted.

## 1. Motivation — verified defects

All four reproduced against the current compiler; each is fixed structurally by
this model.

| # | Defect | Evidence |
|---|--------|----------|
| D1 | Class-name call to a self-reading method compiles clean (exit 0, lint clean), segfaults at runtime — generator emits `Class_method(NULL, ...)` | `CodeGenerator.spec:1788`; reproduced with `Widget:bump()` reading `self:count` → SIGSEGV |
| D2 | Void method called via class name allocates a fresh instance per call, mutates it, discards it — silent state loss + hidden malloc/ARC per call | `CodeGenerator.spec:1791`; generated C: `({ C* _inst = C_new(); C_bump(_inst); _inst; })` ×N |
| D3 | Bare call of an imported class's function passes type checking, then fails in gcc (`implicit declaration of function 'Main_abs'`) — the implicit-self fallback invents symbols | `TypeChecker.spec:1169` (`targetType == ''` → current class); reproduced with `abs(-5)` while `Math` imported |
| D4 | `using` is a load manifest, not an access list: any loaded class is callable from anywhere; a class's true dependencies are unreadable | `TypeChecker.spec:763` (global `registeredClasses`); reproduced: `Main` used `Helper` with no import of its own |

Related, same family, in scope for this work: the own-class-name trap
(`Widget:bump()` inside `Widget` passes NULL `self` even on a live instance —
verified SIGSEGV), and `instance:init()` re-initializing in place.

Out of scope (recorded, not addressed here): unchecked `as` casts; the loader's
flat bare-name space with readdir-order resolution (first-loaded same-stem
class silently blocks same-named classes in other namespaces — `Loader.spec:102`,
`seenBareNames`).

## 2. The model (normative)

### 2.1 Import forms

```spec
replace Array of Array of String is using: [
	['base', 'struct', Array],          # TYPE import: name usable in type
	                                    # positions and for `X:init` only.
	['base', 'math', as Math()],        # INSTANCE import: compiler materializes
	                                    # and owns an anonymous Math instance.
	['base', 'io', as Output()]         # Args allowed: as Output(mode: "raw")
];
```

- Type import = today's form, minus member calls through the class name
  (except `init`).
- Instance import = a synthetic, hidden field of type `ClassName` on the
  importing class, initialized before the class's own field initializers, in
  `using`-declaration order (parent bindings first). Owned and released with
  the importer instance (existing ARC scope-end rules; no new runtime
  machinery).
- The class name in receiver position (`X:member`) resolves to the owned
  instance. In type position (`local X is v:`) it remains the class. This is
  the *only* dual meaning an identifier carries, and it is decided by
  grammatical position.

### 2.2 Call resolution (checked in this order)

1. **Floor builtins** (§5 remainder, e.g. `output:`/`error:` until migrated):
   lowercase singleton form, prefix-only, unchanged.
2. **Enum variant constructors** (`Result:Ok(...)`): type-level, prefix-only,
   unchanged. Never bare.
3. **Primitive utilities** (`Int:toBase`, `String:parseInt`): type-level,
   prefix-only, unchanged.
4. **Prefixed instance call** `X:member(...)` where `X` is instance-imported:
   dispatch on the owned instance (existing instance path — direct C call
   unless the member is overridden).
5. **Constructor** `X:init(...)` on a type-imported class: allocates and
   initializes. `init` is **not callable on an instance** (`v:init()` is a
   compile error — E7).
6. **Bare call** `member(...)`: resolved against the bare scope (§2.3).
7. **`self:member(...)`**: own dispatch, always legal, always unambiguous.
8. **Own class name in receiver position** (`Widget:member(...)` inside
   `Widget`): **compile error**. There is no instance behind it. Use `self`.
   This permanently removes the D1-adjacent own-name trap.

### 2.3 Bare scope and the collision rule

- A class's **bare scope** = its own methods ∪ inherited methods ∪ the methods
  of every instance-imported class (own bindings and inherited bindings — the
  synthetic field is inherited like any field).
- Collision is **by name only**. Spec has no overloading; signature-sensitive
  collision must not be introduced.
- **One provider** for a name → bare call legal; own provider dispatches via
  `self`, imported provider dispatches on the owned instance.
- **Zero providers** → compile error "undefined function" (fixes D3 at the
  Spec level, with a Spec diagnostic).
- **Two or more providers** → **every bare call of that name is a compile
  error**; the call must be qualified (`self:name` or `X:name`). Collision
  itself is not an error — calling a collided name bare is. The diagnostic
  must name the providers: *"`get` is provided by both Map and Buf — qualify
  as `Map:get` or `Buf:get`."*
- Adding a member or import that creates a collision does not silently rebind
  existing calls — formerly-bare call sites become compile errors (explicit
  breakage, never shadowing).
- **One level deep.** The bare scope includes the instance-imported classes'
  *members*, not their own imports. Reaching further requires the prefix.
- **Methods only.** Imported instances' fields never enter bare scope.
- Determinism: the provider set is order-independent (a property of the set,
  not of declaration or scan order).

### 2.4 Zero-field elision (performance contract)

A zero-field class (e.g. `Math`, `Output`, `Reflection`, `Process`, `While`,
`File` — all verified field-free) imported as an instance requires **no
allocation**: its methods are provably self-free, so prefixed and bare calls
compile to the same direct C calls emitted today, `self` ignored. The instance
is a compile-time fiction. Allocation is real only for field-ful imports.
Corollary: migrating the stateless stratum must not change generated C, and
must not shift the bootstrap seed beyond source-level AST differences.

## 3. Compile-time enforcements

Each item = one checker/loader/parser duty. `E#` referenced by tests (§8).

- [ ] **E1 — Literal args.** A `using` array item is exactly one of: STRING
  literal, IDENT (class name), or `as IDENT '(' literal* ')'` where *literal*
  is a String/Int/Float/Boolean literal. No variables, no `self`, no field or
  parameter references, no enum refs, no expressions. Enforced at parse time.
  Rationale: the `using` array is declaration-level — no `init` params, no
  ordering hazards, trivially checkable.
- [ ] **E2 — Init match + non-abstract.** `as X(args)` requires `X` to be a
  non-abstract class with an accessible `init` accepting `args` by count and
  type. `as X()` on an Enum is an error. Generic classes cannot be
  instance-imported (v1 — see §10).
- [ ] **E3 — Uniqueness.** At most one instance import per class name per
  importing class (post group-merge; fragments' `using` entries union first).
  Duplicate → compile error.
- [ ] **E4 — Acyclicity.** The instance-import graph must be a DAG.
  `A` imports `as B()` and `B` imports `as A()` (directly or transitively,
  self-loops included) = guaranteed unbounded construction recursion at first
  `init` → compile error. Implemented in the loader over the already-loaded
  class graph (DFS on instance-import edges).
- [ ] **E5 — Resolution.** Bare call: 0 providers → undefined; ≥2 →
  must-qualify (diagnostic names providers). Own class name as receiver →
  error (§2.2 item 8). Prefix on a type-imported class with a non-`init`
  member → error.
- [ ] **E6 — Visibility unchanged.** `local`/`contained` rules apply to
  prefixed and bare calls exactly as today (already enforced on prefixed
  calls; extend to bare-scope providers).
- [ ] **E7 — No `init` on instances.** `v:init(...)` where `v` holds an
  instance is a compile error. `init` is construct-only.
- [ ] **E8 — Generator deletion.** Remove the NULL-`self` emission and the
  fresh-instance emission (`CodeGenerator.spec:1773-1791`). Class-name
  emission collapses to: `init` → allocate+construct; everything else is
  instance dispatch. No code path may pass NULL as `self`.
- [ ] **E9 — Checker deletes the duality.** `inferCall`'s class-name branches
  (`TypeChecker.spec:1217-1265`) reduce to: exempt strata (§4), constructor,
  instance-import dispatch, bare-scope resolution. The implicit-self fallback
  that invented `Main_abs` (D3) must be unreachable.
- [ ] **E10 — Loop-body instantiation lint.** Warn when an `as X(args)` import
  or a manual `X:init(...)` lands on a class whose construction occurs inside
  a loop body of the importer (hoisting hint). Warning, not error.

## 4. Exemptions (type-level, prefix-only, unchanged)

- [ ] **X1 — Floor builtins.** `output:` and `error:` remain prefix-only
  singletons *until migrated per §5*. `math:` is removed (§5).
- [ ] **X2 — Enums.** Variant constructors and `name()`/`ordinal()`/`value()`/
  `values()` stay type-level. Destructuring `when` untouched.
- [ ] **X3 — Primitive utilities.** `Int:toBase`, `String:parseInt`, and the
  builtin tables for `Array`/`Map`/`List` literals and methods stay type-level
  (containers are constructed by literal/`X:init` and used through instances —
  no change at call sites).
- [ ] **X4 — Sysinternal floor.** Qualified chains
  (`base:sysinternal:Buf:bufLength(...)`) remain, callable only from `base:sys`
  wrappers (existing checker discipline, `TypeChecker.spec:1176-1195`). This
  is the FFI boundary and is not an instance relation.

## 5. Builtin removal

The lowercase forms are an alias layer over real classes
(`TypeChecker.spec:697-708`, `canonicalClassName`): `output:`→`Output`,
`error:`→`Error`, `math:`→`Math`. Repo-wide usage (verified): `output:line`
×892, `output:print` ×6, `error:line` ×19, `math:*` ×45.

- [ ] **R1 — Remove `math:`.** `Math` is a real, zero-field class with a
  no-arg `init`. Rewrite all 45 `math:*` sites to `as Math()` imports + bare
  or `Math:`-prefixed calls (bare where unique in scope — the checker decides).
  Then delete the `math` alias from `canonicalClassName`, the IDENT fallback
  (`TypeChecker.spec:765`), and the `math:random` linter rule.
- [ ] **R2 — Migrate `output:` → `as Output()`.** The `Output` class already
  exists (`base:io`, runtime-managed, zero fields). Rewrite all ~898 sites —
  prefer the prefixed form `Output:line(...)` to keep the diff visually
  scannable; the checker permits bare `line(...)` where unique. Then delete
  the `output` alias.
- [ ] **R3 — Replace `error:` with a real class.** Verified mechanism:
  `error:line` is a *string-matched routing key* (`BuiltinCallGenerator.spec:133`,
  `targetC == 'error' || targetC == 'Error'`) that inlines the stderr writer —
  the spelling `Error` binds to no struct, method, or C symbol, and merely
  shares a name with the compiler package's real `Error` data type (harmless
  today only because the routing also requires a method named `line`). The
  fiction is deleted, not renamed: add `Stderr` (runtime-managed, zero-field,
  `line`/`print`) to `base:io`, mirror of `Output` — the class-form path is
  already proven (`Output:line` and `output:line` emit identical C). Switch
  routing to class identity (see §6, BuiltinCallGenerator). Rewrite the 19
  sites to `as Stderr()` + `Stderr:line(...)`. Delete the `error`/`Error`
  routing entries and the `error` alias. End state: the name `Error` is bound
  solely to the compiler's error data type. **Decision point:** class name —
  `Stderr` proposed (verified unused repo-wide); confirm before implementing.
- [ ] **R4 — Post-removal invariant.** `canonicalClassName` reduces to
  identity; `TypeChecker.spec:765`'s "callable whether or not imported"
  special case is deleted; no lowercase singleton receiver remains anywhere in
  `spec/`, `tests/`, `examples/` (grep-verified in the gate of §7); and **no
  builtin routing condition matches on a bare class-name string** — every
  callable name resolves through a declared, imported class.
- [ ] **R5 — Documentation.** KNOWLEDGE-SPEC "Builtins (selected)" section
  rewritten to the instance form; README language-features section updated in
  the same commit as the flip (§7 Phase B).

## 6. Implementation map

- [ ] **Parser** — `using`-array item grammar (E1); carry the `as`-form into
  the `using` member's AST.
- [ ] **Loader** — resolve `as` entries (existing resolution, plus E2's
  existence check), record bindings per class, E3 uniqueness (post
  group-merge), E4 acyclicity DFS. Bindings survive into `ProgramNode`.
- [ ] **TypeChecker** — per-class provider map (own+inherited via the existing
  ancestor walk; one entry per instance import from the loaded `ClassInfo`);
  bare-call resolution in `inferCall` (E5); prefix resolution to the synthetic
  field; E2 type-check of literal args; E6 visibility on providers; E7; E9
  branch deletion; `init`-on-instance rejection.
- [ ] **CodeGenerator** — synthetic field emission + construction at importer
  `init` (before user field initializers, `using` order); zero-field elision
  (§2.4); E8 branch deletion; class-name receiver → synthetic-field dispatch.
- [ ] **Linter** — Phase 0.5 worklist mode (§7), then E10; optional
  over-qualification style notice (§10).
- [ ] **BuiltinCallGenerator** — route runtime-managed classes (`Output`,
  `Stderr`, `Math`) by **declared class identity** (namespace-qualified
  `ClassInfo` from the loaded program), never by target-name literals; delete
  the `math:`/`output:`/`error:` alias conditions as R1–R3 land. Under the
  instance model the receiver's class is already known at the call site, so
  identity routing costs nothing.

## 7. Migration plan

Gates at every step: `bash utilities/run_tests.sh` (70 checks),
`bash utilities/run_sanitized.sh` (ASan), `./bootstrap.sh` fixed point.
**Seed atomicity:** `bootstrap.sh:39-40` rewrites `bootstrap/spec.c` on drift —
commit seed regeneration atomically with each source change, or bisect lands
on seed/source disagreement.

- [ ] **Phase 0 — this document.** Rule text frozen; R3 class name decided.
- [ ] **Phase 0.5 — worklist mode.** Linter reports every receiver that is a
  bare class name with a non-`init` method, excluding exempt strata (§4).
  Purely syntactic; no behavior change; count = burn-down metric. Keep green
  in CI until zero.
- [ ] **Phase A — source migration under the permissive compiler.**
  Working-state static calls are provably self-free (a self-touching one
  would have segfaulted per D1; suite+ASan would have caught it), so
  mechanical rewrites are semantics-preserving — except void-static-discard
  sites (D2), which become *more* correct (state persists); the suite
  adjudicates each.
  - [ ] A1: stdlib leaves — `math`, `io` (R1/R2 groundwork), `iterator`
    (`as While()` keeps all `While:run`/`While:condition` sites byte-identical),
    `sys` wrappers.
  - [ ] A2: compiler packages, leaves first (`ast`, `lexer`, `parser`, then
    `checker`, `gen`, `loader`, `linter`, `driver`).
  - [ ] A3: `tests/` + `examples/` sweep.
  - [ ] A4: singletons — R1, R2, R3 (class added, aliases deleted).
  - [ ] A5: bare-scope/collision pass — resolve each forced-qualification
    diagnostic; no call-site churn beyond collisions.
- [ ] **Phase B — the flip.** One commit: E5/E7/E8/E9 enforced as errors;
  negative tests added (§8); worklist mode removed; KNOWLEDGE-SPEC/README
  updated (R5); seed converged. The permissive seed still compiles the
  new-style sources — that is what makes the flip small and safe.

## 8. Test plan

New negative tests in `tests/negative/` (must fail to compile):

- [ ] N1 — prefixed call to self-reading method via class name (D1 class).
- [ ] N2 — bare call, zero providers (D3 class, Spec-level diagnostic).
- [ ] N3 — bare call, two providers (must-qualify diagnostic names both).
- [ ] N4 — prefix on type-imported class, non-`init` member.
- [ ] N5 — duplicate `as X()` bindings (E3).
- [ ] N6 — instance-import cycle A↔B, and self-loop A→A (E4).
- [ ] N7 — non-literal arg in `as X(args)` (E1).
- [ ] N8 — `init` arg mismatch / abstract target / enum target (E2).
- [ ] N9 — own class name as receiver inside the class (§2.2.8).
- [ ] N10 — `v:init()` on an instance (E7).

Positive/regression:

- [ ] P1 — unique bare call resolves to the import (e.g. `round(...)`).
- [ ] P2 — `as While()` keeps `While:run(loop:, control:)` sites unchanged.
- [ ] P3 — zero-field elision: `--emit-c` output for a stateless-stratum
  caller is identical to pre-migration generated C.
- [ ] P4 — inherited instance import: prefix reachable from subclass; bare
  scope follows the same reachability.
- [ ] P5 — stateful `as` import: mutations persist on the owned instance
  across calls (the D2 counter-test).
- [ ] P6 — full suite + ASan + fixed point green after each Phase A step.

## 9. Documentation (Phase B, same commit as the flip)

- [ ] KNOWLEDGE-SPEC.md — Imports & Resolution, Visibility, Builtins, Control
  Flow (`While` idiom) rewritten to the instance model; grammar addition for
  the `as` import form.
- [ ] README.md — language-features and comparison-table rows that reference
  static calls.
- [ ] docs/language, docs/packages — package-author guidance: when to type- vs
  instance-import; stateless-service convention; threading note.

## 10. Explicitly out of scope (future)

- Aliasing for instance imports (`as Math() is fastMath`) — only becomes
  meaningful if cross-package same-name classes are ever supported (loader
  flat name space).
- Generic instance imports (`as Box of Int()`).
- Over-qualification style lint (notice when a prefix was unnecessary).
- `While` API reshape (`loop:run()`) — optional polish; P2 guarantees it is
  not required.
- Transitive bare scope — deliberately excluded (§2.3); revisit only with a
  demonstrated need and a locality argument.
- Thread semantics beyond documentation: `Parallel:run` workers capture the
  importer's instances — stateless services are safe; stateful ones are shared
  mutable state, same as any shared field. Document in docs/language; no v1
  enforcement.

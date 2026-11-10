# PLAN-ENUM.md — Enums Become Classes with Reflective Defaults

**Status:** accepted plan, pre-implementation. Written 2026-11 after the
root-lattice redesign (Any the empty root, Loadable the machinery,
Class the declaration root — see KNOWLEDGE-SPECDEV.md §6). This file is
the working plan for dissolving the compiler's enum special-casing into
general language features.

---

## 0. The vision

An enum stops being a compiler concept and becomes **a class pattern
with reflective defaults**: the variants are static members, the
contract methods are reflective implementations on the `Enum` root
class, and the compact `Enum of <type> is Name` syntax survives as
*sugar that desugars to the class form*. The compiler keeps the
convenience and drops the semantics.

The payoff beyond enums: static member access, a missing-member
resolution hook, runtime class metadata, and generalized `when` — each
is a language feature users ask for independently. The enum is the
first user of all four.

---

## 1. What the compiler does for enums today (the inventory)

Six pieces of special recognition, spread across the pipeline:

1. **The parse** — `atEnumHeader`: `Enum of <type> is Name` produces a
   ClassInfo with baseClass `Enum` and the variants parsed as members
   with value tags.
2. **The resolution** — `Color:Red` resolves through the
   `allEnumVariants` registry. Notably: fields through a class-name
   prefix are otherwise REJECTED ("fields are not reachable through the
   class-name prefix") — the enum variant path is a special exception.
3. **The contract methods** — `name/ordinal/value/values/of` with
   fixed signatures, synthesized per enum by the generator.
4. **The tagged-union emission** — the tagged enums emit a struct with
   the tag + payload fields and the variant constructors; the plain
   enums emit the int constants and the name/value/ordinal tables.
5. **The `when` machinery** — exhaustiveness over the variant set, and
   the payload bindings in the arms (`is Red(r, g, b):`).
6. **The registries** — `allEnumNames` / `allEnumVariants` /
   `allStringBackedEnums` feeding the checker and the gen.

---

## 2. The target model

```
Enum of String is Color { Red; Green; Blue }

desugars to (conceptually — the sugar may keep the compact form):

Class of Enum is Color {                    # of Enum: the enum root parent
    String is Red: 'Red';                   # the variants: static members
    String is Green: 'Green';
    String is Blue: 'Blue';
}
```

- `Color:Red` = the **static member access** — resolves to the
  variant's cached instance.
- `name()` / `values()` / `of()` — implemented ONCE on the `Enum` root
  class, reflectively, over the class's static member metadata.
- The variant identity: the first access constructs and caches; pointer
  identity holds forever (the singleton semantics).
- `when (c) { is Red: ... }` — exhaustive over the class's declared
  static members (the member list is compile-time knowledge).

---

## 3. The mapping — each piece of machinery → a general feature

| Enum machinery | The general feature that replaces it |
|---|---|
| `Color:Red` variant resolution | **Static member access** — `Class:field`. Today REJECTED through a class-name prefix; generalizing is overdue on its own merits (constants, registries, singletons). |
| The variant identity (two `Color:Red` are the same) | **Lazy static initialization + caching** — the first access constructs, caches on the class, pointer identity forever. Order-free. |
| `name/ordinal/value/values/of` | **The Enum root implements them reflectively**, backed by the Introspection floor: a per-class emitted metadata table (the member names). `values()` = the member list; `name()` = the instance's cached variant name. |
| The tagged-union payloads | **Subclasses as variants** — `Red of Color` carrying the payload as real fields; the payload access becomes ordinary field access. |
| `when` exhaustiveness | **Generalized**: exhaustive over the subject class's *declared static members* (compile-time knowledge — the same check the enum version does, but for any class). |
| `when` payload bindings | **Subtype arms**: `is Red:` binds the instance as its subtype; the payload fields come into scope. Also general. |
| The variant registries | The class's own member list — the mechanism every class already has. |

---

## 4. The prerequisites, in build order

1. **Static member access** — `Class:field` resolves (read-only) at the
   class-name prefix. The checker: the class's OWN static members; the
   gen: the slot/instance resolution. The largest single feature.
2. **The runtime class metadata** — the gen emits a per-class member
   table (the names of the static members + the flags); the
   Introspection floor exposes `membersOf(Class)` /
   `memberExists(Class, name)`. Backs `values()`/`of()`/`name()`.
3. **The lazy static initialization** — the static members with
   initializers construct on first access, cache, and are order-free.
   The pointer identity is the equality semantic.
4. **The resolution hook** — when `Class:member` matches no declared
   member and the class implements the resolver contract, the checker
   admits the reference and the runtime resolves it (construct, cache,
   return). The userspace extension point. Without the hook: an error,
   as today.
5. **The `when` generalization** — exhaustive over the declared static
   members of the subject's class; subtype arms with the payload
   bindings. Lowers to the ordinal jump table (the checker knows the
   ordinals statically).

---

## 5. The design details to nail per feature

### 5.1 Static member access

- Read-only first (the mutable statics are a separate, dangerous
  feature — decide later, possibly never).
- The resolution: the class's OWN static members (the fields declared
  without an instance scope). The inherited statics: through the
  lattice, with the nearest declaration winning (the same rule as
  methods).
- The gen: the static field = the class-level storage (emitted once),
  the access = the direct load. The initialization: see 5.3.

### 5.2 The runtime metadata

- The gen emits, per class, a static table: `{ "Red", "Green", "Blue" }`
  + the count — ONLY for the classes that need it? Or for every class
  (the uniformity vs the size)? Decide: every class, compact (the
  names only), the Introspection floor exposes the count + the lookup.
- `values()` returns the instances IN DECLARATION ORDER — the metadata
  must preserve the order (the ordinal = the index).

### 5.3 The lazy statics

- The first access: construct, cache on the class, return. The cache:
  the class-level slot per static member.
- The construction ORDER between members: only matters if a member's
  initializer references another member of the SAME enum — the lazy
  resolution handles it (the reference triggers the other's
  construction first) ✓ order-free by construction.
- The thread safety: the statics are per-process singletons — the
  initialization needs the atomic guard (the once-semantics: the double-
  checked store, or the mutex — the same pattern as the intern table).

### 5.4 The resolution hook

- The checker: when `Class:member` matches no declared member AND the
  class (or its lattice) implements the resolver contract, admit the
  reference with the resolver's declared return type.
- The runtime: the resolver constructs, caches, returns — the same lazy
  path as the declared statics.
- The contract: the resolver lives on the root (`Enum` implements it;
  the users can too). The signature to nail: `resolve(name) → Variant?`
  — the null result = the error (as today).

### 5.5 The `when` generalization

- Exhaustive over the declared static members of the subject's class —
  the checker enumerates exactly as the enum version does today.
- The lowering: the ordinal jump table (the reflective index), not the
  identity-comparison chain — the big enums (the state machines) stay
  O(1).
- The subtype arms (the payload enums): `is Red:` — the instance-of
  check + the field bindings. The ordering/duplication rules: the same
  as the enum arms today.
- The dynamic (hook-resolved) subjects: NOT exhaustive — `else`
  required. The rule, stated.

---

## 6. The risks and the mitigations

1. **The `when` dispatch performance** — today: the tag switch (O(1)).
   The naive class model: the identity chain (O(n)). Mitigation: the
   ordinal jump table (5.5). The benchmark: the state-machine-sized
   enums.
2. **The identity semantics** — the pointer equality IS the enum
   equality. The cache must be airtight (one instance per variant, per
   process). The thread safety: the same once-pattern as the intern
   table.
3. **Dogfooding is the proof and the risk** — the compiler uses its own
   enums everywhere (`Keyword`, `ExpressionKind`, `StatementKind`,
   `TokenKind`, `ContractMethod`, `MetadataField`). `Keyword.of(text)`
   runs per-token. The migration of the compiler's own enums is the
   honest validation; the hot paths must hold the floor-conversion
   speed. The static member accesses resolve at compile time, so the
   steady state should hold — benchmark before declaring victory.
4. **The error-message drift** — the diagnostics reference the enum
   concepts ("the enum variants", the exhaustive-when messages). The
   generalized messages must stay as pointed.
5. **The behavioral changes for the Any-typed receivers** — with the
   enum special-casing gone, the Any-typed `x:toString()` etc. already
   changed under the root-lattice work; the enum-typed `when` subjects
   keep their exhaustiveness only under the static-member model. Audit
   the test expectations per stage.

---

## 7. The migration staging

1. **Stage 1 — the foundations. DONE.** The held members (fields +
   functions, read-only, lazy once-guards) + the runtime class
   metadata + the Introspection exposure — landed 2026-11; see §7b.
   No enum changes; the features landed as general language features
   with their own tests (tests/held_members_test.spec,
   tests/held_methods_test.spec, tests/held_metadata_test.spec,
   negative n30/n31).
2. **Stage 2 — the lazy statics + the resolution hook.** The
   initialization semantics + the userspace extension point. Still
   enum-free.
3. **Stage 3 — the `when` generalization.** The static-member
   exhaustiveness + the subtype arms. Still enum-free.
4. **Stage 4 — the value enums migrate.** The `Enum of String is X`
   sugar desugars to the class + the static members. The compiler's own
   String-backed enums (`ContractMethod`, `MetadataField` — the small
   ones) migrate first; `Keyword` last (the hottest).
5. **Stage 5 — the tagged enums migrate.** The subtype-variant pattern
   (`Red of Color` with the payload fields) + the subtype `when` arms.
   The compiler's tagged enums (`ExpressionKind`? — audit which carry
   payloads) migrate.
6. **Stage 6 — the special-casing dies.** The parser's enum parse
   becomes pure sugar-desugaring; the registries, the enum emission,
   and the enum branches in the checker/gen delete. The compiler's enum
   concept is gone.

Every stage: converge, gates, commit. The compiler compiles itself
throughout (the dogfooding is continuous).

---

## 7b. The `held` modifier — DECIDED and LANDED (Stage 1)

The declaration syntax for this plan: the member modifier **`held`** —
the class holds the member (one copy, class-scoped lifetime), in
contrast to the instance members each object carries. LANDED 2026-11
(commits: held fields, held functions, the metadata floor).

The specifics, as decided:

1. **Visibility composition**: `held` composes with `local`/`contained`
   (the access check reuses checkMemberVisibility; `held local` is
   class-private, `held contained` admits subclasses). `held` alone is
   public. `held`+`replace`/`merge` is a checker error (single-copy,
   cannot be overridden); held loader directives are rejected.
2. **Held functions**: landed WITH fields (not deferred) —
   `held Function of T is name(params)` is a receiver-free class-scoped
   function dispatched by the class-name prefix. Not root-contract
   members (no vtable slot), no overloads, parameter defaults work;
   bodies have no instance (no self, no instance fields), but sibling
   held members resolve through the class name on demand.
3. **Lazy initialization**: full-expression initializers from day one —
   the CAS once-guard (acquire load, compare-exchange 0->2, release
   store 1, loser spins on acquire). Pointer identity forever. A held
   INITIALIZER may not reference held members of its own class (the
   mutual guards would deadlock — checker-enforced); cross-class chains
   resolve (independent guards), and held FUNCTION bodies are
   unrestricted (the call triggers construction on demand).
4. **Storage shape**: file-scope slot + atomic once-flag + `__ensure()`
   accessor per held field; `_held_`-infixed receiver-free C functions
   per held function. Held members never enter the instance struct.
5. **Inheritance**: the held lookup walks the lattice, nearest
   declaration wins (same rule as methods); a subclass name reaches
   ancestors' held members. The metadata tables report each DECLARING
   class's own held surface.
6. **Read-only**: assignment through the class-name prefix is rejected;
   an instance reference reaches exactly the instance members (the
   strict resolution rule — FieldSearchLoop/MethodSearchLoop go
   held-blind), so `obj:held` and `self:held` are pointed errors.

Stage 1 is complete: static member access + held functions + the
runtime metadata (Introspection: heldCount/heldName/hasHeld over the
emitted per-class name tables). Stage 2 (the resolution hook — when
`Class:member` matches no declared held member) is the next build step.

---

## 8. The open questions

1. **The static-member storage shape**: the class-level slots (the
   fields in the struct? the side table?) — the read-only constants
   could live in the metadata tables; the mutables (if ever) would need
   the real storage. Decide at stage 1.
2. **The resolution hook's checker story**: the Any-typed result? The
   declared return type of the resolver? The type inference through the
   hook — the loosest correct story first.
3. **The ordinal stability**: the reflective `ordinal()` = the
   declaration order — stable per compile ✓ but a re-ordered source
   shifts the ordinals — the persisted-ordinal concerns (serialization)
   are the user's, documented.
4. **`Enum of <type>`**: the value-type parameter's role in the class
   model — the tagged enums carry it as the payload type; the value
   enums (`of String`) use it as the tag type. The sugar keeps it; the
   desugaring maps it to the payload/field type.
5. **The compiler's own `Keyword` migration** — the lexer's hot path:
   the per-token lookups. The static member accesses resolve at compile
   time, but `Keyword.of(text)` (the reverse lookup) is the scan — the
   same scan as today's `Keyword:of` ✓ measure, don't assume.

---

## 9. The relationship to the current state

The root-lattice redesign (landed) already gives enums a real root:
`Enum` (base:core) is a Loadable class, and the `Enum of <type> is Name`
declarations resolve their parent to it. The machinery (using/
namespace/init) is inherited. This plan builds ON that: the enum root
gains the reflective contract methods, the variants become the static
members, and the compiler's recognition machinery retires stage by
stage.

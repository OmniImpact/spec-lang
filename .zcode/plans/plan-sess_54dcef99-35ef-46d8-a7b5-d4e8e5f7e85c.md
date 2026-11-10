# PLAN-ENUM Stage 1 — held members (the static-member foundation)

## Context

PLAN-ENUM.md dissolves the compiler's enum special-casing into general features. Stage 1 is the foundation: **held members** — class-scoped storage/methods accessed through the class-name prefix (`Color:Red`), replacing what is today a special exception ("fields are not reachable through the class-name prefix") reserved for enum variants. No enum behavior changes in this stage; the features land as general language features with their own tests.

The `held` specifics (§7b) are now decided:
- **held fields + held functions** both land (user chose "include now")
- **Full-expression initializers** → lazy once-pattern initialization (CAS guard, first access constructs and caches, pointer identity forever) — plan §5.3 lands now, not stage 2
- **Visibility**: held composes with `local`/`contained` (reuses `checkMemberVisibility`); `held`+`replace`/`merge` is a checker error; `held` alone = public
- **Read-only**: assignment through a class-name prefix is rejected
- **Resolution rule** (§7b): a class-name prefix reaches exactly held members; an instance reference reaches exactly instance members (`obj:heldThing` is an error — strict)
- **Inheritance**: held lookup walks the lattice, nearest declaration wins (same rule as methods); a subclass name reaches ancestors' held members
- **Cycle guard**: a held initializer expression may NOT reference held members of its own class (mutual lazy init would deadlock the once-guards); cross-class references are fine (independent lazy chains). Checker-enforced with a clear message.

Key facts from exploration (all verified):
- Keyword recognition: `spec/base/compiler/lexer/Keyword.spec` (enum entries) → `parser/loops/ModifierLoop.spec:24-27` (evaluate() disjunction) → modifiers flow through `Parser:parseMember` as strings automatically; `Member:hasModifier(Keyword:HELD)` works with no AST changes (`Member.spec:76-78` matches by keyword string)
- Checker admission point: `TypeChecker.spec` PATH arm — enum branch at ~1948, the §2.3 rejection at ~1988-1996 (the error we generalize past); CALL-form enum admission at ~2770; field lookup helpers `findMemberOwnerClass`/`findAncestorMember`/`lookupFieldType`/`checkMemberVisibility` (3481-3559) are the lattice-walk patterns to reuse, filtered on `hasModifier(Keyword:HELD)`
- Gen: `emitPath` enum branch at `CodeGenerator.spec:1890-1897` is where the held load goes; `emitCall` enum branch at ~2296 is the held-method call model; registries built in `registerProgram` (280-309) and copied to workers via `copyRegistryMap`; forward decls in `DeclarationGenerator.generateForwardDeclarations` (:378); per-class definitions emitted in the parallel worker body (methods at 3681-3693)
- `<stdatomic.h>` already in the RuntimePrelude includes (line 55); `spec_type_name` (:1701) is the model for the new Introspection floor C
- `held` collides with no existing identifier (grep verified — only doc comments)
- **Ratchet: clean.** No compiler self-source uses `held` or the new floor functions in this stage, so the old binary needs no bridges; the new Keyword entry parses generically as an enum variant

## Implementation — three commits, each gated

### Commit 1: held fields

1. **Lexer/parser**: `Keyword.spec` add `HELD: 'held'`; `ModifierLoop.spec` evaluate() adds `|| checkKeyword(kw: Keyword:HELD)`; `utilities/spec-kate.xml` add `<item>held</item>` to the keywords list (~line 13)
2. **Checker** (`TypeChecker.spec`):
   - Registry `heldFields: Map of String to String` (key `'Class.member'` → declared type), populated in the per-class pass, skipping namespace-array members (the `initExpr:kind == ExpressionKind:ARRAY` convention, same as enum variants at :4131)
   - Validation (alongside `checkMemberVisibility`/`checkShadowTargets`): `held`+`replace`/`merge` → error; `held` on a nested CLASS member → error; held field without initializer → error
   - Held init-expr checking: run `inferExpressionType` with no instance context (no `self`, no `fieldTypes`); reject references to same-class held members (cycle rule)
   - PATH arm: when the root is a registered class and segment 1 matches a held member (own, then lattice via `findAncestorMember`-style walk filtered on HELD, nearest wins), admit with the field's type + `checkMemberVisibility`; this branch sits before the §2.3 rejection so `Class:held` never hits "fields are not reachable"
   - Assignment: a class-prefix PATH as an assignment target → error "held members are read-only"
3. **Gen** (`CodeGenerator.spec`, `DeclarationGenerator.spec`):
   - `registerProgram`: build `heldFields` registry; add to `copyRegistryMap`
   - `emitPath`: class-name root + held member → emit `Sym__ensure()` (the once-guard accessor); parenthesize so deeper path segments chain naturally
   - `tryGenerateTargetOnly`: does NOT resolve held targets (defense in depth for read-only)
   - Forward decls pass: per held field emit `<ctype> <cSym>_<member>;` + `atomic_int <cSym>_<member>_once;` + `<ctype> <cSym>_<member>__ensure(void);` (non-static — cross-class access)
   - Parallel worker body: per held field emit the definitions — the once-guard accessor with the standard CAS pattern (acquire load → CAS 0→2 → init → release store 1; loser spins on acquire until 1), init expression emitted through the worker's expression generator, ARC handled like a method return (mirror `emitReturn`)
4. **Tests**: `tests/held_members_test.spec` — held constants, full-expression initializers (incl. cross-class reference), inherited held via subclass name, visibility (held local from outside → negative), pointer identity of a lazily-built held value via `Introspection:objectHash`; negatives in `tests/negative/` (assignment to held; held+replace; self in held initializer; same-class held reference in initializer)

### Commit 2: held functions

1. **Checker**: CALL branch — when `methodTarget` is a bare registered class name and the method is a held function (own + lattice, visibility checked): check args against the held signature, result = declared return type; stamp what the gen needs via the registry. Held method bodies checked with no instance context: `self` → error, bare identifiers resolve against the class's held fields + locals/params (not instance `fieldTypes`). Instance-side call `obj:heldMethod()` → error ("reaches exactly instance members"). Held methods may not overload-conflict with instance methods of the same name (distinct namespaces, but a clear error beats ambiguity for now)
2. **Gen**: `heldMethods` registry (key `'Class.method'`, with overload/arity info); `emitCall`: class-name target + held method → direct C call `<cSym>_<method>(args)` — no receiver, no vtable slot; worker body emits held method definitions (like `generateMethod` but no `self` first param, no vtable registration); forward decls extended
3. **Tests**: `tests/held_methods_test.spec` — static helper called via `Util:parse(...)`, held method calling sibling held field via class prefix, held method constructing instances (import rules apply), negative: instance call of held method, `self` in held body

### Commit 3: metadata + Introspection floor

1. **Gen**: whole-program pass (single-threaded, pre-pool, deterministic fixed order like `generateVTables`): per class with ≥1 held member emit `const char* <cSym>_held_names[]` + count (fields + methods, declaration order — the ordinal index §5.2 requires) and one program-wide registry array `{ type_name, names, count }` entries
2. **RuntimePrelude**: `spec_held_count(const void* obj)` / `spec_held_name(const void* obj, long long idx)` — resolve the object's type via the `_type_name` header (the `spec_type_name` pattern), scan the emitted registry
3. **Introspection**: floor decls in `spec/base/sysinternal/Introspection.spec` (no bodies), wrappers in `spec/lib/base/sys/Introspection.spec` delegating per the sysinternal discipline — `heldCount(Any)`, `heldName(Any, Int)`, `hasHeld(Any, String)`
4. **Tests**: metadata counts/names on a mixed held class; `hasHeld` false for plain instance members

### Bookkeeping

- `PLAN-ENUM.md` §7b: status PROPOSED → decided; record the six nailed specifics (the decisions above)
- `KNOWLEDGE-SPECDEV.md`: one-line addition to the concurrency contracts (the held once-guard pattern) and the stage-1 landing note

## Verification

Per commit: `./bootstrap.sh` (fixed point holds — no self-source consumes the features), `utilities/run_tests.sh` (new tests + full suite green), `utilities/run_sanitized.sh` (ARC correctness of the once-guard and held returns). Determinism: all new emission iterates `flattenedClasses` in fixed order / merges through pre-sized slots. Before starting: re-grep that no self-source identifier is named `held` (verified today).
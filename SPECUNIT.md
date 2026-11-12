# SPECUNIT.md — the SpecUnit unit-test framework and its reflection floor

Design and landing tracker. SpecUnit is the first consumer of the runtime
reflection floor; the floor is deliberately domain-neutral — it describes
classes and methods, never tests — because its payoffs extend past testing
(plugin loading, serialization, dynamic tooling, the future REPL/eval on-ramp).

---

## 1. Goals and non-goals

**Goals (v1):**
- A runtime introspection floor: enumerate classes and methods, construct by
  name, invoke by name — queryable from any running Spec program.
- SpecUnit: assert library + registry singleton + reflection-driven runner +
  report table + exit codes, built entirely on that floor.
- `--test`: compile-and-run sugar for a suite file (entry main calls
  `SpecUnit:runAll(<root dir>)`); no generated test dispatcher.
- Migrate `tests/*.spec` from the `[PASS]`/`[FAIL]` string-marker convention
  to Assert-based test classes.

**Non-goals (v1, tracked below):** test-name filters beyond argv conventions,
parameterized tests, parallel execution, panic isolation (subprocess-per-class),
held-function/field metadata, multi-argument invoke marshaling.

**Precedents:** Go `testing` (convention over annotation, exit codes),
xUnit.net (fresh instance per test), JUnit 5 (lifecycle hooks, aggregated
failure lists), Rust libtest (harness binary shape), Catch2 (report table).
Soft assertions throughout — Spec has no exceptions; a failed assert records
and the test continues, and a test passes iff its failure list is empty.

---

## 2. The reflection floor

### 2.1 The metadata model (emitted per program, class order — deterministic)

```c
typedef struct SpecMethodMeta {
    const char* name;   /* declared name, e.g. "testRoundTrip" */
    void* fn;           /* the C function (Class_method[_N]) */
    int flags;          /* bit 0: void return; bit 1: zero params */
    int line;           /* declaring source line */
} SpecMethodMeta;

typedef struct SpecClassMeta {
    const char* name;
    const char* source_file;      /* BASENAME only — the full path spelling
                                     varies with the invocation directory and
                                     would break byte-identical emission */
    const char** base_names;
    int base_count;
    void* (*construct)(void);     /* NULL when init needs arguments */
    const SpecMethodMeta* methods;/* own declared methods; queries walk bases */
    int method_count;
} SpecClassMeta;

const SpecClassMeta* const spec_class_registry[];   /* class order */
int spec_class_registry_count(void);                /* emitted definition (Land B) */
```

Invariants:
- **Domain-neutral.** No test flags, no annotations. Conventions (`*Test`,
  `test*`, `beforeEach`) live in SpecUnit, never in the floor.
- **Own-methods emission, base-walking queries.** A subclass's inherited
  methods resolve through `base_names` at query time; invocation works on
  derived instances (prefix struct layout).
- **Construct rules** mirror the entry-init rule: no `init` member → the
  void-default `X_init` (the Loadable contract's synthesized init, realized
  at C emission — no AST member is fabricated: no-magic policy); a declared
  zero-arg `init` → that overload's symbol; anything else →
  `construct == NULL`.
- **No member synthesis.** The first cut baked an `init` member into the
  loader; reverted deliberately — it cascaded abstract-member obligations
  (an empty body reads as an abstract contract) and fought declared parent
  signatures. `X:init()` in Spec source types as `X` at call sites via the
  §I.2 construction rule; held bodies construct services as locals.
- Sizing is dynamic with the class list — no caps.
- Enum-model and transparent floor classes register with `construct == NULL`.

### 2.2 The C floor (RuntimePrelude)

Two tiers:

**Index helpers — `static inline`, Land A (inert: unused static inlines are
never emitted, so the not-yet-defined registry externs cannot break a link):**

```c
static inline int spec_class_registry_count(void);
static inline const SpecClassMeta* spec_class_meta(int index);
static inline const SpecClassMeta* spec_class_find(const char* name);
static inline const SpecMethodMeta* spec_class_find_method(
    const SpecClassMeta* cls, const char* name);        /* walks base_names */
static inline void* spec_class_construct_by_meta(const SpecClassMeta* cls);
static inline void spec_invoke_void_by_meta(void* instance,
    const SpecMethodMeta* m);
```

**Name-level queries — real functions, Land B (land with the registry
emission; a defined function referencing the externs cannot precede them):**

```c
SpecArray* spec_class_names(void);                        /* Array of String */
SpecArray* spec_class_method_names(const char* cls);      /* own + inherited */
const char* spec_class_source_file(const char* cls);
int spec_class_has_method(const char* cls, const char* method);
void* spec_class_construct_by_name(const char* cls);      /* loud panic when NULL */
void spec_invoke_void_by_name(void* instance, const char* method);
    /* finds the class via the instance's own _type_name; panics when the
       method is absent or its flags lack void/zero-params */
```

### 2.3 The wrapper API (base:sys:Introspection, same-name discipline)

```spec
Function of Array of String is classNames();
Function of Array of String is methodNames(String is className);   /* own + inherited */
Function of String is classSourceFile(String is className);
Function of Boolean is hasMethod(String is className, String is methodName);
Function of Boolean is canConstruct(String is className);
Function of Any is instantiate(String is className);
Function of void is invokeVoid(Any is instance, String is methodName);
Function of Boolean is isSubclassOf(Any is instance, String is className);
```

sysinternal declarations follow the existing empty-body style; binding is the
camel→snake convention (`classNames` → `spec_class_names`). Loud panics on
missing/incompatible targets — the bounds-check philosophy, not silent zeros.

---

## 3. SpecUnit (pure Spec, `spec/lib/specunit/`)

```spec
Class is TestResult{
    String is name;                    # "MathTest.testDivide"
    Boolean is passed: true;
    Array of String is failures: [];   # aggregated (JUnit assertAll style)
    Int is startedAtMs: 0;
    Int is durationMs: 0;
}

Class is SpecUnit{                        # registry singleton via held state
    held Array of TestResult is results: [];
    held TestResult is current;
    held Function is runAll(String is sourcePrefix);   # report() at the end
    held Function is runClass(String is className);    # fresh instance per test
    held Function is beginTest(String is name);
    held Function is endTest();
    held Function is addFailure(String is msg);
    held Function is report();                         # table + Process:exit
}

Class is Assert{                          # held functions; class-prefixed calls
    held Function is areEqual(Any is expected, Any is actual);
    held Function is areClose(Float is expected, Float is actual, Float is delta);
    held Function is isTrue(Boolean is condition);
    held Function is isFalse(Boolean is condition);
    held Function is fail(String is message);
}
```

- **Discovery:** `classNames()` filtered by the `*Test` suffix and the
  source-file prefix (the compiling root's directory — same scoping philosophy
  as entry selection).
- **Lifecycle:** `beforeEach`/`afterEach` via `hasMethod` — JUnit hooks,
  zero annotations.
- **Isolation:** fresh `instantiate` per test method — xUnit rule.
- **Failure context:** `Reflection:class()`/`method()` at the assert call
  site — failures report `Class.method:line` with zero user bookkeeping.
- **Report:** `[PASS]`/`[FAIL]` per test with durations (markers kept for
  `run_tests.sh` grep parity), failure detail lines beneath the failing test,
  summary box via `Ansi`, exit 1 when failures > 0.

**Conventions (the whole contract):** class name ends `Test`; method name
starts `test`; lifecycle names `beforeEach`/`afterEach`; test methods are void
with zero parameters. Everything else in a test class is plumbing.

---

## 4. `--test` sugar

`bin/spec --test -i tests/byte_test.spec -o bin` compiles exactly as release
but generates a three-line entry main: `SpecUnit:runAll(<root file's
directory>)`. Entry selection is bypassed (test classes need no `init(Map)`);
everything else — load, typecheck, emission — is the standard pipeline, so
suite files are fully statically checked. No `--test` → byte-identical
emission (policy-gated, the `--debug` pattern).

---

## 5. Landing plan (two-part discipline — each step converges alone)

- [ ] **A — inert floor helpers.** Prelude: meta typedefs, registry externs,
      `static inline` index/lookup/invoke helpers. No consumers; unused
      static inlines are never emitted, so the externs cannot break a link.
- [ ] **B — registry emission.** Generator: per-class meta tables, construct
      thunks, `spec_class_registry` + count definitions, and the name-level
      query functions (self-consistent TU: functions and their data land
      together). No consumers yet.
- [ ] **C — wrapper + library.** sysinternal declarations, `Introspection`
      wrapper methods, the `specunit` package, `--test` flag, suite
      diagnostics (bad test-method signature, init-with-args, no-tests-found).
- [ ] **D — pilots.** Convert `byte_test.spec` and `loops_test.spec`;
      `run_tests.sh` compiles them with `--test`.
- [ ] **E — sweep.** Migrate remaining suites in batches; flip the
      test-suite loop to `--test`. Negative tests and demos stay as-is.

Gate every step: `./bootstrap.sh` fixed point, `utilities/run_tests.sh`,
`utilities/run_sanitized.sh`. Commit per step with reasoning.

---

## 5.1 Observed wart (recorded, not fixed here)

Void has two AST spellings: methods declared without a return type carry
lowercase `'void'` (`WellKnown:voidMemberType()`), while `voidName()` is
`'Void'` — `resolveReturnType` normalizes both at emission. The registry
flags and the --test validation accept both; a future normalization pass
should collapse them at the parser.

## 6. Later (tracked, not scheduled)

- Invoke ladder: arity-1 with `Any` marshaling → typed multi-arg (the
  REPL/eval on-ramp). The `flags` bits make each rung runtime-checkable.
- Held-function and field metadata (names + types) — serialization/ORM
  enablers; held functions already have C symbols (`_held_` infix).
- `--test-filter Class.method`; tags/skip.
- Panic isolation: subprocess-per-class re-exec with merged reports (a
  runtime panic still kills the process today — documented limitation).
- Source-position metadata on method entries for richer failure reports
  (`line` is already in the meta; stack-frame walking stays a gdb concern
  until a runner needs it).
- v1 metadata covers methods with real `Class_method` symbols; floor-bound body-less methods on transparent classes (String.fromCharCode, Array.length — intercepted to spec_* at call sites) are not yet registrable.

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
- SpecUnit: assert library + state registry + reflection-driven in-suite
  runner + report table + exit codes, built entirely on that floor.
- **specunit, the standalone runner program** (`utilities/specunit/`): a
  Spec program, not a compiler mode — `specunit -s ./bin/spec -t tests/`
  scans test trees, dispatches cores−2 workers, each compiles the test
  with one compiler thread, runs the binary, collects the result, and
  prints the summary when all tests are done. The compiler stays lean and
  knows nothing about tests.
- The suite ENTRY lives in the framework: `SpecUnitTest`'s argv-Map init
  constructs `SpecUnitRunner` and runs the file's test classes, so a
  suite compiles with plain `spec` and self-runs. No generated test
  dispatcher, no `--test` flag.
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

## 3. SpecUnit (pure Spec, `utilities/specunit/`)

The framework moved out of the compiler's `spec/lib` tree — it is ecosystem
tooling, not compiler plumbing, and iterating on it never rebuilds the
compiler. Files match their class names:

```spec
Class is SpecUnitTest{                    # the base — and the suite ENTRY
    replace Function is init(Map of String to String is args);  # argv-Map init:
        # the entry the generated main prefers; constructs SpecUnitRunner
        # and runAll(sourcePrefix: own source basename) — declared FIRST
        # so it owns overload index 0
    replace Function is init();           # empty: the per-test fresh instance
    Function of String is name();         # own class name (typeIdentity)
    Function of String is description();  # "Unit test: X has N tests"
    Function of Int is methodCount();     # test* methods, own + inherited
}

Class is SpecUnitRunner{                  # instance runner (per suite binary)
    Function is runAll(String is sourcePrefix);   # discovery + run + report
    Function is runClass(String is className);    # fresh instance per test
    Function is beginTest(String is name);
    Function is endTest();                        # interprets the check span
    Function is report();                         # table + Process:exit
}

Class is SpecUnitState{                   # held registry singleton (mutable)
    held Array of TestResult is results: [];
    held Array of CheckRecord is checks: [];
    held Array of TestResult is currentCell: [];
}

Class is Assert{                          # held functions; class-prefixed calls
    held Function is areEqualInt(...); areEqualString(...); areClose(...);
    held Function is isTrue(...); isFalse(...); fail(...);
}
```

- **Discovery by inheritance, not name matching:** `classNames()` filtered
  by `extendsClass(className, 'SpecUnitTest')` plus the source-file
  basename prefix — exactly the root file's classes run. A class extending
  the base with zero `test*` methods is skipped; a suite with none at all
  is diagnosed (`No test classes found in …`) and exits 1 — never a silent
  all-green.
- **Lifecycle:** `beforeEach`/`afterEach` via `hasMethod` — JUnit hooks,
  zero annotations.
- **Isolation:** fresh `instantiate` per test method — xUnit rule.
- **Branch-free assertions:** Assert appends `CheckRecord`s
  unconditionally (held bodies cannot branch); `endTest` interprets the
  span since the test's `checksBefore`.
- **Report:** `[PASS]`/`[FAIL]` per test with durations (markers kept for
  the runner's `[FAIL]` grep parity), failure detail lines beneath the
  failing test, summary box via `Ansi`, exit 1 when failures > 0.

**Conventions (the whole contract):** class name starts `Test`
(`TestMyFeature`); method name starts `test` (`testFunctionOfFeature`);
lifecycle names `beforeEach`/`afterEach`; test methods are void with zero
parameters. Everything else in a test class is plumbing.

---

## 4. The suite entry and the runner program

**In-suite entry:** `SpecUnitTest`'s argv-Map init is the entry the
generated main prefers (the entry resolver's argv-preference over the
empty init, resolved through the inheritance lattice). Compiling
`tests/TestByte.spec` with plain `spec` produces a binary whose main
constructs `TestByte`, lands in the base's init, and runs the file's
tests. The compiler has no test mode, no test validation, no test main —
the framework owns all of it. (What used to be `--test` compile-time
diagnostics now guard elsewhere: a bad test-method signature trips the
reflection floor's invoke panic at run time; an unconstructible test
class trips the member-compatibility check at compile time; an empty
suite is diagnosed by `runAll`.)

**The runner program (`SpecUnit.spec`, same package):**

```
specunit -s ./bin/spec -t tests/ [-t more/]        # also -t a,b or -t a -t b
```

Scans the trees recursively (dot dirs skipped) and classifies every
`.spec` file by its `#!` banner — self-describing tests, no hardcoded
fixture table:

- `#! specunit: suite` — compile, run, exit 0 and no `[FAIL]` required
  (also the default for unmarked files that mention the specunit package)
- `#! specunit: negative` — compilation MUST fail; every
  `#! expect: <text>` must appear in the diagnostics
- `#! specunit: run-fail` — compile must succeed, the run MUST exit
  non-zero, every expect must appear in the run output
- `#! specunit: helper` — skip (multi-file fixture partners)

Dispatch: `Parallel:run` with cores−2 workers striding a held work queue;
each worker invokes the compiler with `--threads 1`, executes the binary
under a 10s timeout, records the verdict, deletes the compiled test, and
adds the result to the held registry (mutex-protected). The summary
prints when all tests are done; exit 1 on any failure.

---

## 5. Landing plan (two-part discipline — each step converges alone)

- [x] **A — inert floor helpers.** Prelude: meta typedefs, registry externs,
      `static inline` index/lookup/invoke helpers. No consumers; unused
      static inlines are never emitted, so the externs cannot break a link.
- [x] **B — registry emission.** Generator: per-class meta tables, construct
      thunks, `spec_class_registry` + count definitions, and the name-level
      query functions (self-consistent TU: functions and their data land
      together). No consumers yet.
- [x] **C — wrapper + library.** sysinternal declarations, `Introspection`
      wrapper methods (functions/typeIdentity/classExtends reshape), the
      `specunit` package, the `--test` flag (since retired — see below).
- [x] **D — pilots + the runner separation.** TestByte and the converted
      suites; the bash runner replaced by **specunit** (the standalone
      Spec runner, `-s`/`-t` CLI); the framework moved to
      `utilities/specunit/`; the suite entry moved into `SpecUnitTest`'s
      argv-Map init (plain-`spec` compiles self-run); the negative
      fixture table moved into the files as `#! specunit:` banners;
      `spec_thread_count` fixed to read the CPU affinity mask (the
      `/proc/self/status` `Threads:` read collapsed every cores-derived
      worker count to 1 — the serial-wave bug).
- [ ] **E — sweep.** Migrate the remaining marker suites in batches;
      then remove the now-unused `--test` mode from the compiler
      (Driver validation + generateTestMain).

Gate every step: `./bootstrap.sh` fixed point, `utilities/run_tests.sh`,
`utilities/run_sanitized.sh`. Commit per step with reasoning.

---

## 5.1 Observed wart (resolved)

Void had two AST spellings; the vocabulary was standardized to one
(`'Void'`) at the AST and one boundary at C — see the void-vocabulary
commit. Paramless `Function` remains a distinct non-void type (the empty
function), never conflated with Void.

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

# Spec — The Full Breakdown

[README.md](README.md) > **Full Breakdown**

The detailed companion to the overview: design philosophies, the complete
feature list, module resolution, editor support, building, and how Spec
compares to the languages it draws on.

---

## Table of Contents
1. [Key Design Philosophies](#key-design-philosophies)
   - [Minimal Core & Maximum Standard Library](#1-minimal-core--maximum-standard-library)
   - [Classes and Functions as First-Class Types](#2-classes-and-functions-as-first-class-types-uniform-declarations)
   - [The "Never Null" Safety Standard](#3-the-never-null-safety-standard)
   - [Unblockable & Concurrency-First Iteration](#4-unblockable--concurrency-first-iteration)
   - [Scoped Region Desugaring (`as`)](#5-scoped-region-desugaring-as)
   - [Tab-Based Indentation Standard](#6-tab-based-indentation-standard)
   - [Multi-File Module Resolution](#7-multi-file-module-resolution)
   - [Language Features](#8-language-features)
2. [The Call Model & Conditional Provider](#the-call-model--conditional-provider)
3. [Editor Support (Kate / KWrite)](#editor-support-kate--kwrite)
4. [Building and Bootstrapping](#building-and-bootstrapping)
5. [How Spec Compares](#how-spec-compares)

---

## Key Design Philosophies

### 1. Minimal Core & Maximum Standard Library
Spec is architected with a strict philosophy: **keep the compiler minimal, and build the language in the standard library**.
- **Ultra-Lean Compiler**: The entire grammar is the ten-keyword table in the overview (`local`, `contained`, `replace`, `merge`, `held`, `is`, `as`, `of`, `to`, `return`), plus the seven primitive types (`Int`, `Byte`, `Float`, `Boolean`, `String`, `Function`, `Any`). Structural conventions such as `using` are Loader-recognized pseudo-fields, not keywords.
- **Userland Implementation**: Rich language features live in the standard library (`spec/lib/`) written in pure Spec — including dynamic collections (`Array`, `Map`, `List`), filesystem operations (`File`), process management (`Process`), the conditional provider (`Conditional` — branching and match tables), and concurrency runners (`Loops`, `Loop`, `Parallel`).
- **No Magic**: Language abstractions are not compiler special cases; they can be inspected, extended, or replaced using ordinary Spec code.

### 2. Classes and Functions as First-Class Types (Uniform Declarations)

In Spec, both `Class` and `Function` are **types**, not keywords. This establishes two vital design characteristics:

- **Capitalization Discipline**: Keywords are lowercase (`local`, `contained`, `replace`, `merge`, `held`, `is`), while declaration types are PascalCase (`Class`, `Enum`, `Int`, `String`, `Function`). Structural conventions such as `using` are Loader-recognized pseudo-fields, not keywords.

- **Symmetrical Declaration Grammar**: Classes, variables, and methods share the exact same structural pattern — `<modifiers> <Type> is <name>`:
  - Class declaration: parents use the pre-name `of` slot (mirroring `Enum of Int is Status`)
    ```spec
    Class of Greeter is EnglishGreeter { ... }
    Class of T is Box { ... }
    ```
  - Variable: `<modifiers> <Type> is <name>: <value>;`
    ```spec
    local Int is score: 100;
    local Function of String to Boolean is validator;
    ```
  - Method: `<modifiers> <Type> is <name>(<parameters>) { <body> }`
    ```spec
    replace Function is init(Map of String to String is args){ ... }
    replace Function of Boolean is evaluate(){ ... }
    ```

- **First-Class Callables**: Because `Function` is a type, functions and closures can be stored in variables, passed to higher-order functions, and typed generically (`Function of Param to Return`).

- **The Root Class `Any`**: Every class without explicit parents implicitly extends the root class `Any` (`Class of Stringable is Any`), which supplies default `toString()`, a no-op `init()`, and the `using` slot. Any-typed references dispatch only root-contract members — cast to a concrete class for the rest.

### 3. The "Never Null" Safety Standard
In Spec, `null` does not exist as a runtime value, pointer, or type:
- **No Null Keywords or Types**: Functions returning nothing are declared simply as `Function is action()` (no `of null` needed).
- **Concrete Values Required**: Variables and fields cannot be null. If something would be null, the program will not compile.
- **Empty Collections**: Collections like `Array` and `Map` can be empty (`[]`, length 0).
- **Deferred Initialization**: Class fields may be declared without inline values provided they are assigned in `init(...)` before use.
- **Default Fallbacks**: Any operation reading from a source that could be empty requires an explicit default fallback argument (e.g., `getString(key, default)`, `pop(default)`, `charAt(index, default)`).

### 4. Unblockable & Concurrency-First Iteration
Spec has no primitive loop keywords (`while`, `for`, `do`). Iteration is decoupled into lifecycle objects or inlined scoped loops through the `Loops` provider (`['base', 'sys', as Loops()]`):
- **`while({ cond }, { step })`**: The bare predicate loop, inlined directly to a native C11 statement expression with zero closures and zero heap allocations.
- **`while([vars], { cond }, { step })`**: The scoped-variable loop. Variables are scoped strictly to the loop construct:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Loops()]
  ];

  while([Int is i: 0, Int is total: 0], { i < 10 }, {
  	total: total + i;
  	i++;
  });
  ```
- **`repeat(count: n, worker: { ... })`**: The fixed counting loop for index-independent repetitions:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Loops()]
  ];

  repeat(count: 4, worker: {
  	deck:add(item: drawCard());
  });
  ```
- **`until({ cond }, { step })`**: Post-test loop (do-while form) ensuring the body executes at least once.
- **Mixed Scope & Operator Ergonomics**: Scoped loops freely read and mutate outer variables and collections, paired with prefix and postfix increment/decrement operators (`++`, `--`).
- **`base:iterator:Loop`**: Implements `evaluate() -> Boolean` and `iteration(LoopControl is control) -> Boolean`. Returning `false` from `iteration` or `evaluate` cleanly terminates the loop.
- **`base:iterator:LoopControl`**: Supports non-blocking halts (`stop()`) and asynchronous completion triggers (`onComplete`).
- **`Loops:run(loop, control)`**: Drives the iterator lifecycle without blocking threads.

### 5. Scoped Region Desugaring (`as`)
Managing lifecycles, locks, transactions, and file handles often creates deeply nested callback pyramids ("rightward drift"). Spec solves this by repurposing the existing keyword `as` at statement position to desugar the remainder of the block into an anonymous callback passed to the trailing positional argument of a function:
```spec
replace Array of Array of String is using: [
	['base', 'sys', as Output()]
];

# Parameterless: acquires lock/transaction, runs remainder, unwinds on exit
as: self:withTransaction(name: "OrderProcessing");

# With parameter bindings: typed or untyped
as (String is path): self:withTempFile(path: "/tmp/data.csv", content: rawData);

# Clean, linear pipeline — path is in scope, zero indentation drift!
line("Processing: " . path);
```
- **Zero New Keywords**: Reuses `as` unambiguously at statement start.
- **Guaranteed LIFO Unwinding**: Nested `as` statements unwind in reverse stack order on exit, matching RAII, Python `with`, and Go `defer` with zero runtime machinery.
- **Top-to-Bottom Flow**: Flattens nested callbacks into clean, sequential code.

### 6. Tab-Based Indentation Standard
Spec establishes a standard indentation convention using **tabs**. The standalone linter (`bin/speclint`, built from `utilities/speclint/`) detects space-based indentation and optional parameter patterns:
```bash
bin/speclint -i path/to/program.spec
```

### 7. Multi-File Module Resolution
Dependencies declared in `using: [...]` are **pure package segments** — the
namespace declared inside a file is what makes it the package; directories are
organization, not identity. The loader scans two trees (the directory of the
`.spec` file being compiled and the compiler executable's directory, walking up
while a location holds no `.spec` content), builds a map of where every class
lives, and resolves each import by loading the candidate and verifying its
declared namespace. The trailing segment names a class; omitting it imports the
whole package:
```spec
replace Array of Array of String is using: [
	['base', 'struct', Array],
	['base', 'struct', Map],
	['base', 'math', Math],
	['base', 'sys', Output],
	['base', 'iterator', Loops]
];
```

### 8. Language Features

- **Instance-Based Call Model**: members are callable only through instances; `['pkg', as ClassName()]` imports materialize an owned instance whose members answer to the class-name prefix, with bare calls for unambiguous names and compile-time collision enforcement. No NULL receivers, no hidden allocations — enforced by the compiler, not by convention.

- **User-Defined Generic Classes**: Express reusable parametric types with automated type parameter substitution and casting:
  ```spec
  Class of T is Box {
  	local T is item;
  	replace Function is init(T is item){ self:item: item; }
  	Function of T is get(){ return self:item; }
  }
  ```

- **First-Class Capturing Closures & Direct Invocation**: Anonymous function expressions capture outer local variables and `self` automatically, and `Function` variables can be invoked directly:
  ```spec
  local Int is factor: 2;
  local Function of Int is multiplier: local Function of Int(Int is x){
  	return x * factor;
  };
  local Int is result: multiplier(x: 4);
  ```

- **Tagged Union Enums (Algebraic Data Types)**: Enums support payload-carrying variants as well as plain enumeration members. Every enum desugars to the class model — value variants become held members holding shared instances; payload variants become nested subclasses with real payload fields:
  ```spec
  Enum is Result {
  	Ok(String is data),
  	Err(Int is code, String is msg),
  	Pending
  }
  ```

- **`match` with Payload Destructuring**: Match any value against held-member keys (array keys match several cases at once); payload arms are closures whose parameters bind the variant's fields:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Output()],
  	['base', 'sys', as Conditional()]
  ];

  match(on: res, when: [
  	Result:Ok: local Function(String is data){ line("Success: " . data); },
  	Result:Err: local Function(Int is code, String is msg){ line("Error " . code . ": " . msg); },
  	Result:Pending: { line("Pending..."); }
  ]);
  ```

- **Held Members (Class-Scoped State)**: One copy per class, reached through the class-name prefix; lazily constructed behind a CAS once-guard with pointer identity forever, and strictly resolved (an instance reference never reaches a held member):
  ```spec
  held String is appName: 'HeldApp';
  held Function of Int is triple(Int is n){ return n * HeldRegistry:scale; }
  ```

- **The Resolution Hook (`resolveHeld`)**: A class declaring `held Function of <T> is resolveHeld(String is name, Function of <T> is missing)` admits any undeclared name through its class-name prefix — the runtime resolves, caches, and hands the mandatory missing-branch as the safe failure path.

- **Scoped Region Desugaring (`as`)**: Linearizes nested callbacks into sequential blocks without rightward drift:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Output()]
  ];

  as: self:withResource(name: "file.txt", log: log);
  log:add(item: "processing data");

  as (String is text): self:readFile(path: "config.json");
  line("Loaded: " . text);
  ```

- **Default Parameter Values & Call-Site Reordering**: Functions declare optional parameters with default values; call sites may omit defaults and pass named arguments in any order:
  ```spec
  Function of Int is connect(String is host, Int is port: 8080, Int is timeout: 30){ ... }
  local Int is sock: connect(timeout: 10, host: "localhost");
  ```

- **Map Literals & Index Assignment**: First-class map literals, bracket indexing, and index assignment:
  ```spec
  local Map of String to Int is scores: ["alice": 95, "bob": 88];
  scores["charlie"]: 100;
  local Int is top: scores["alice"];
  ```

- **Functional Collection Combinators**: Transform and reduce collections fluently using higher-order combinators:
  ```spec
  local Array of Int is doubled: numbers:map(action: local Function of Int(Int is n){ return n * 2; });
  local Int is total: numbers:fold(init: 0, action: local Function of Int(Int is acc, Int is n){ return acc + n; });
  ```

- **Parser Error Recovery & Source Provenance**: Syntax errors report precise source coordinates with recovery, while type errors retain multi-file provenance and abort cleanly:
  ```text
  [SyntaxError] [src/main.spec:42:15] Expected ';' after expression
  ```

- **Type Casts (`as`)**: Unifies class up/downcasts, numeric casts, and base conversions:
  ```spec
  local Animal is a: dog as Animal;
  local String is hexStr: value as Hex;
  local String is binStr: flags as Bin(8);
  ```

- **Visibility Model**: `local` (private), `contained` (protected + final), and public by default — enforced by the compiler:
  ```spec
  local Int is secretId;
  contained Function is internalHook(){ ... }
  Function is publicApi(){ ... }
  ```

- **Root Contract**: `Any`-typed references may only invoke root members (`toString`, `typeName`, `init`); everything else requires a cast:
  ```spec
  local Any is obj: getUnknownObject();
  line(obj:toString());
  local Greeter is g: obj as Greeter;
  g:greet();
  ```

- **Bitwise Operators & Base Literals**: Full bitwise arithmetic with C precedence, prefixed base literals with separators, and conversions:
  ```spec
  local Int is mask: 0xFF_00 & (0b1010_1010 | ~flags);
  local Int is shifted: mask << 4;
  ```

- **Prefix & Postfix Increment/Decrement (`++` / `--`)**: Expressive, zero-overhead mutation for identifiers, fields, and index expressions:
  ```spec
  counter++;
  local Int is next: ++index;
  scores[idx]--;
  ```

- **Parallel Execution**: Fans pure worker closures across pthreads with lock-free per-thread RNG and atomic coordination:
  ```spec
  Parallel:run(
  	threads: 4,
  	iterations: 1000000,
  	worker: local Function(Int is start, Int is end){ ... }
  );
  ```

- **High-Efficiency C11 Runtime & Memory Model**: Amortized $O(1)$ growable string buffers (`spec_str_append`), zero-allocation character table lookups, cached $O(1)$ string length queries, lazy `SpecArray` buffer allocation, and automatic deallocation of transient `Loop` instances.
- **One Uniform Memory Path — ARC with Claim Pools, Compiler Included**: Memory is atomic reference counting; every function's temporaries register on a thread-local claim pool drained at scope exit (the Objective-C autorelease-pool shape). There is no garbage collector and **no separate compiler arena**: the compiler runs on exactly the ARC machinery it generates for user programs. A bump-arena experiment for compiler-phase AST nodes was measured at **+154 MB peak** — nodes die incrementally and ARC returns their blocks to glibc's tcache, while an arena hoards them until drain — and was removed as a falsified dead path; the dormant arena floor remains in the runtime prelude with nothing activating it.

- **Scope-Merged Imports (`as ClassName()`)**: Instance imports materialize an owned singleton instance scoped to the declaring class, merging its methods directly into bare scope with zero global namespace pollution:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Output()],
  	['base', 'sys', as Conditional()],
  	['base', 'sys', as Loops()]
  ];

  # Members are directly available bare:
  line('Hello, Spec!');
  if({ score > 50 }, { line('Pass'); });
  while([Int is i: 0], { i < 3 }, { i++; });
  ```
  Where collisions occur, the qualified class-name prefix (`Output:line(...)`, `Loops:while(...)`) remains fully supported for unambiguous resolution.

- **Multiple Inheritance & Diamond Ambiguity Prevention**: Classes may inherit from multiple parents (`Class of Reader, Writer is ReadWriter`). If multiple parents declare conflicting concrete implementations and the child does not resolve the conflict with an explicit override, the compiler emits a compile-time diamond ambiguity error.

- **Strict Override & Composition Discipline (`replace` & `merge`)**: Overrides are never silent or accidental:
  - `replace`: Mandatory and compiler-verified when overriding any ancestor field or method (including root contracts `toString()`, `typeName()`, and `init()`).
  - `merge`: Enables structured composition. On methods, the body forwards delegation to the parent implementation via `(args...);`. On Array fields, child items automatically concatenate after parent elements.

- **Predicate Table Matching (`match(when: ...)`)**: Dropping `on:` turns match keys into closures, evaluating each condition in sequence. The first matching predicate executes its arm, returning a value or executing statements with zero allocation and lowering directly to an inlined C11 else-if ladder:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Conditional()]
  ];

  local String is rating: match(when: [
  	{ score >= 90 }: { 'Outstanding' },
  	{ score >= 75 }: { 'Good' },
  	{ score >= 50 }: { 'Pass' },
  	else:            { 'Retry' }
  ]);
  ```

- **Structural `sysinternal` Floor Isolation**: Low-level C runtime primitives live in `base:sysinternal:*` floor classes bound via the `spec_<snake_case>` naming convention. The compiler structurally enforces that only classes whose declared namespace begins with `['base', 'sys', ...]` may invoke the floor, ensuring all userland code interacts through clean, type-safe Spec wrappers.

---

## The Call Model & Conditional Provider

Members are callable only through instances; class-name receivers admit only
construction — except the type-level strata: the primitives and containers, the
desugared enums (whose contract methods and variant constructors dispatch
through the class name by design), held functions, and the providers.

The **`Conditional` provider** replaces `if`/`else` keywords the same way
`Loops` replaces loop keywords: conditionals are calls, and the compiler
inlines them into native C branches with zero closure allocation.

- **Statement form**: `if({ ... }, { ... }, { ... })` — served bare through the as-import — the check closure returns `Boolean`; the branch bodies are statements that may read and mutate the enclosing scope. Single-branch form `if({ ... }, { ... })` is also supported.
- **Value form**: a value-yielding call supplies both branches, and the arms' yields unify into the call's type:
  ```spec
  replace Array of Array of String is using: [
  	['base', 'sys', as Conditional()]
  ];

  local String is grade: if({ score >= 90 }, { 'A' }, { 'B' });
  ```
- **Match tables**: `match(on: value, when: [key: { body }, ...])` — the arm-table form with held-member keys, array keys for multiple matching, `else` as a plain identifier key, and payload arms whose closure parameters bind a tagged variant's fields. See the [Language Guide](docs/language/README.md#matching-with-match).
- **Predicate tables**: `match(when: [{ cond }: { body }, ...])` — drops `on:` so each key is a closure predicate; the first matching branch runs, replacing nested else-if pyramids with flat, zero-allocation decision tables.

---

## Editor Support (Kate / KWrite)

Install syntax highlighting definitions for the KDE Kate editor:
```bash
./utilities/install-kate-syntax.sh
```
*Installs `spec.xml` to `~/.local/share/org.kde.syntax-highlighting/syntax/` with priority association for `*.spec`.*

---

## Building and Bootstrapping

Spec is **100% self-hosted**. Building it requires only a C compiler (`gcc` or `clang`) with standard POSIX threads:

```bash
# Bootstrap the official Spec compiler from the canonical seed and verify
# the self-hosting fixed point (the compiler recompiles its own sources
# and the C must match byte-for-byte):
./bootstrap.sh

# Compile any Spec program:
bin/spec -i examples/helloworld.spec -o helloworld
./helloworld --name "Spec Developer"

# Run the strict whitespace and style linter:
bin/speclint -i spec/base/compiler/driver/Driver.spec
```

---

## How Spec Compares

Spec is a statically typed, class-based language that transpiles to C and is fully
self-hosted: the compiler is written in Spec and rebuilds itself from a single
canonical C file. Where it sits relative to the systems languages it draws on:

| Dimension | **Spec** | **C** | **Java** | **Rust** |
|---|---|---|---|---|
| **Typing** | Static, compiler-enforced (narrowing, container elements, call sites, exhaustiveness, root-contract calls) | Static, weak — unchecked casts, implicit conversions | Static, strong, runtime-checked casts | Static, strongest: affine types, full inference |
| **Null safety** | Never-null: no null value; fallible reads require explicit defaults | `NULL` everywhere | `null` everywhere; `Optional` opt-in | `Option<T>`, compiler-enforced |
| **Memory** | Reference counting with per-scope claim pools; the compiler runs on the same ARC as its generated programs — no separate compiler arena; verified crash-free under ASan/UBSan; no general collector yet | Fully manual (`malloc`/`free`) | Tracing GC | Ownership, compile-time frees |
| **OOP model** | Classes, multiple inheritance with **ambiguity errors**; abstract-by-convention interfaces; four-tier visibility (public / `local` / `contained` / `held`) | None — hand-rolled with structs and function pointers | Single inheritance + interfaces; four visibility levels, all overridable | Traits + composition |
| **Dispatch** | Virtual tables (vtables), most-derived wins; root-typed `Any` refs dispatch dynamically; held functions and the held enum contract (`of`/`values`) dispatch through the class name; the enum identity contract (`name`/`ordinal`) lives on the shared Enum root, reflectively over the metadata floor | Whatever you build — switches or hand-made vtables | All methods virtual by default | Static by default; `dyn` trait objects |
| **Override safety** | `replace` mandatory on overrides; `merge` for data/behavior composition; non-public members cannot be shadowed | None — nothing to override | `@Override` optional (advisory) | No override concept (no inheritance) |
| **Enums & matching** | Algebraic enums with payloads (desugared to real classes); `match` with compile-time exhaustiveness | Plain `int` constants, no namespacing or checking | Enums + pattern `switch` (recent) | Enums + `match`, exhaustiveness enforced |
| **Generics** | `Class of T`, erased with cast insertion | None — macro and `_Generic` tricks | Erasure with bounds | Monomorphized, bounds-checked |
| **Error handling** | Required defaults, callback pairs, `Result`-style ADTs | Return codes and `errno`, trivially ignored | Checked / unchecked exceptions | `Result<T, E>` + `?` propagation |
| **Iteration & scopes** | Loop keywords retired; the `Loops` provider's bare `while`, `repeat`, and `until` inline to C11 statement expressions with zero allocation; scoped `as` eliminates callback pyramids | Primitive `while`/`for`/`break`; callbacks drift rightward | Primitive loops; `try-with-resources` | Primitive loops; `Drop` RAII |
| **Conditionals** | `if({ ... }, { ... }, { ... })`, `match(on:, when:)`, and `match(when:)` calls through the `Conditional` as-import, inlined to native branches; match tables as arm literals | Primitive `if`/`else` | Primitive `if`/`else` | Primitive `if`/`else`, expression-form |
| **Concurrency** | pthreads; mutex-protected collections; atomics; parallel fan-out | pthreads; no memory-model guarantees | Memory model + `java.util.concurrent` | Data races are compile errors |
| **Build model** | Transpiles to one C translation unit; `gcc` links; the compiler is written in Spec and bootstraps from a single canonical C file whose fixed point is verified on every build | Native compilers, headers, make | Bytecode + JIT on the JVM | Native, Cargo ecosystem |
| **Runtime footprint** | Single static binary, no VM | Single binary, no VM | JVM required | Single binary, no VM |

Spec's distinguishing ground: the override discipline (`replace`/`merge`), never-null
defaults, enforced exhaustiveness, a strict root contract (`Any`-typed values may
only call root members — cast for the rest), and a compiler written in itself that
reproduces its own C seed byte-for-byte on every build. It is a young language — its
standard library and tooling are minimal next to the others — but its compile-time
guarantees are already stricter than C's in the areas it covers.

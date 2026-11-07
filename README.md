# Spec Programming Language

**Spec** is an elegant, concurrent-first, unblockable programming language that compiles directly to optimized C11.

```spec
Class is HelloWorld{

	replace Array of Array of String is using: [
		['base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'World');
		output:line(text: 'Hello, ' . name . '!');
	}

}
```

---

## Key Language Philosophies

### 1. Minimal Core & Maximum Standard Library
Spec is architected with a strict philosophy: **keep the compiler minimal, and build the language in the standard library**.
- **Ultra-Lean Compiler**: The entire grammar is the table below — 12 keywords and 6 primitive types. Structural conventions such as `using` and `group` are Loader-recognized pseudo-fields, not keywords.

| Keyword | Role |
|---|---|
| `local` | Private: invisible to children — cannot be replaced, merged, or accessed outside the declaring class |
| `contained` | Protected and final: visible to subclasses, but cannot be replaced, merged, or accessed externally |
| `replace` | Override an ancestor member (mandatory and checked; root-contract overrides are always replace) |
| `merge` | Compose with the ancestor member (array fold, or function delegation via `(args...)`) |
| `is` | Bind a name to a declaration or value; also reads as equality in comparisons |
| `as` | Type cast (classes, numerics, and `Hex`/`Bin`/`Oct` base conversions) or scoped region callback desugaring (`as: call;`, `as (params): call;`) |
| `of` | Parent classes (pre-name: `Class of Greeter is EnglishGreeter`) or generic parameters (post-name or type-level: `Class of T is Box`, `Array of Int`) |
| `to` | Second generic parameter (`Map of K to V`, `Function of A to B`) |
| `if` / `else` | Conditionals — statement form and inline expression form |
| `return` | Return from a method |
| `when` | Pattern matching with compile-time exhaustiveness on enums |

Members without a visibility modifier are **public by default**: overridable via
`replace`/`merge` and callable from anywhere.

| Primitive Type | Meaning |
|---|---|
| `Int` | 64-bit signed integer |
| `Byte` | Unsigned 8-bit value (`Int`↔`Byte` via `as`) |
| `Float` | 64-bit IEEE double |
| `Boolean` | `true` / `false` |
| `String` | UTF-8 text |
| `Function` | First-class callable, typed by return (`Function of Int`) |
| `Any` | Arbitrary typed reference |

`Class` and `Enum` are compiler-known declaration types (`Class is Name { ... }`), not keywords; `Hex`, `Bin`, and `Oct` are compiler-known conversion targets of `as`.
- **Userland Implementation**: Rich language features live in the standard library (`spec/lib/`) written in pure Spec—including dynamic collections (`Array`, `Map`, `List`), filesystem operations (`File`), process management (`Process`), and concurrency runners (`While`, `Loop`).
- **No Magic**: Language abstractions are not compiler special cases; they can be inspected, extended, or replaced using ordinary Spec code.

### 2. Classes and Functions as First-Class Types (Uniform Declarations)

In Spec, both `Class` and `Function` are **types**, not keywords. This establishes two vital design characteristics:

- **Capitalization Discipline**: Keywords are lowercase (`local`, `contained`, `replace`, `merge`, `is`), while declaration types are PascalCase (`Class`, `Enum`, `Int`, `String`, `Function`). Structural conventions such as `using` and `group` are Loader-recognized pseudo-fields, not keywords.

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
Spec has eliminated primitive loop keywords (`while`, `break`) entirely from the language grammar. Rather than hardcoding blocking loop locks, iteration in Spec is fully decoupled into lifecycle objects or inlined scoped loops:
- **`While([Type is name: init, ...], evaluate: { ... }, iterate: { ... })`**: Concise, scoped inline loops with local state declarations and function block shorthands (`{ ... }`), inlined directly to native C11 statement expressions with zero closures and zero heap allocations.
- **Mixed Scope & Operator Ergonomics**: Scoped loops freely read and mutate outer variables and collections, paired with prefix and postfix increment/decrement operators (`++`, `--`).
- **`base:iterator:Loop`**: Implements `evaluate() -> Boolean` and `iteration(LoopControl is control) -> Boolean`. Returning `false` from `iteration` or `evaluate` cleanly terminates the loop.
- **`base:iterator:LoopControl`**: Supports non-blocking halts (`stop()`) and asynchronous completion triggers (`onComplete`).
- **`While:run(loop, control)`**: Drives the iterator lifecycle without blocking threads.

### 5. Scoped Region Desugaring (`as`)
Managing lifecycles, locks, transactions, and file handles often creates deeply nested callback pyramids ("rightward drift"). Spec solves this by repurposing the existing keyword `as` at statement position to desugar the remainder of the block into an anonymous callback passed to the trailing positional argument of a function:
```spec
# Parameterless: acquires lock/transaction, runs remainder, unwinds on exit
as: self:withTransaction(name: "OrderProcessing");

# With parameter bindings: typed or untyped
as (String is path): self:withTempFile(path: "/tmp/data.csv", content: rawData);

# Clean, linear pipeline — path is in scope, zero indentation drift!
output:line("Processing: " . path);
```
- **Zero New Keywords**: Reuses `as` unambiguously at statement start.
- **Guaranteed LIFO Unwinding**: Nested `as` statements unwind in reverse stack order on exit, matching RAII, Python `with`, and Go `defer` with zero runtime machinery.
- **Top-to-Bottom Flow**: Flattens nested callbacks into clean, sequential code.

### 6. Tab-Based Indentation Standard
Spec establishes a standard indentation convention using **tabs**. A built-in linter detects space-based indentation and optional parameter patterns:
```bash
bin/spec --lint path/to/program.spec
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
	['base', 'io', Output],
	['base', 'iterator', While]
];
```

### 8. Language Features
Spec includes modern, expressive language capabilities designed for type safety and clarity:

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

- **Tagged Union Enums (Algebraic Data Types)**: Enums support payload-carrying variants as well as plain enumeration members:
  ```spec
  Enum is Result {
  	Ok(String is data),
  	Err(Int is code, String is msg),
  	Pending
  }
  ```

- **Destructuring `when` Branching**: Destructure and extract tagged enum payloads in both `when` statements and `when` expressions:
  ```spec
  when (res) {
  	is Result:Ok(data): { output:line("Success: " . data); }
  	is Result:Err(code, msg): { output:line("Error " . code . ": " . msg); }
  	is Result:Pending: { output:line("Pending..."); }
  }
  ```

- **Scoped Region Desugaring (`as`)**: Linearizes nested callbacks into sequential blocks without rightward drift:
  ```spec
  as: self:withResource(name: "file.txt", log: log);
  log:add(item: "processing data");

  as (String is text): self:readFile(path: "config.json");
  output:line("Loaded: " . text);
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

- **Class Grouping (Partials)**: Split a class across multiple files with `group: [Target]`; fragments merge at load time with duplicate detection:
  ```spec
  Class is NetworkClient {
  	group: [NetworkClientSocket, NetworkClientTls];
  }
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
  output:line(obj:toString());
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

---

## Documentation

- 📚 **[Documentation Portal](docs/README.md)**: Main documentation index.
- 📖 **[Language Guide](docs/language/README.md)**: Syntax, typing system, Never Null standard, operators, and control flow.
- 📦 **[Standard Library Reference](docs/packages/README.md)**: Package summary tables and full API reference for `base:core`, `base:io`, `base:math`, `base:struct`, `base:iterator`, and `base:sys`.
- 📜 **[Code Style & SpecDoc Guide](docs/STYLE_GUIDE.md)**: Official code style conventions, architectural idioms, and the SpecDoc documentation standard.
- 🛠️ **[Tooling & Compiler Guide](docs/tooling/README.md)**: Compiler CLI, module loader, tab linter, and Kate editor integration.

---

## Getting Started

### Prerequisites
- **GCC or Clang** (C11 compiler with standard POSIX threads)

### Bootstrapping the Compiler
```bash
./bootstrap.sh
```

### Compiling and Running a Program
```bash
# Compile and run a basic program
bin/spec -i examples/helloworld.spec -o helloworld
./helloworld --name Daniel

# Run the scoped region and resource management demo
bin/spec -i examples/scope_as_demo.spec -o scope_demo
./scope_demo

# Emit generated C11 source code (optional)
bin/spec -i examples/helloworld.spec --emit-c helloworld.c
```

### Running the Linter
```bash
bin/spec --lint examples/blackjack.spec
```

---

## Standard Library

The standard library lives in `spec/lib/` — six packages covering the root
lattice (`base:core`), terminal and file I/O (`base:io`), math (`base:math`),
collections (`base:struct`), iteration (`base:iterator`), and process control
and parallelism (`base:sys`) — all written in Spec over the `base:sysinternal`
C floor. A summary table of every package and its functions lives in the
**[Standard Library Reference](docs/packages/README.md)**.

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
bin/spec --lint spec/base/compiler/driver/Driver.spec
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
| **Memory** | Reference counting with scope-end releases; binaries verified leak-free under ASan/LSan; no general collector yet | Fully manual (`malloc`/`free`) | Tracing GC | Ownership, compile-time frees |
| **OOP model** | Classes, multiple inheritance with **ambiguity errors**; abstract-by-convention interfaces; three-tier visibility (public / `local` / `contained`) | None — hand-rolled with structs and function pointers | Single inheritance + interfaces; four visibility levels, all overridable | Traits + composition |
| **Dispatch** | Virtual tables (vtables), most-derived wins; root-typed `Any` refs dispatch dynamically | Whatever you build — switches or hand-made vtables | All methods virtual by default | Static by default; `dyn` trait objects |
| **Override safety** | `replace` mandatory on overrides; `merge` for data/behavior composition; non-public members cannot be shadowed | None — nothing to override | `@Override` optional (advisory) | No override concept (no inheritance) |
| **Enums & matching** | Algebraic enums with payloads; `when` with compile-time exhaustiveness | Plain `int` constants, no namespacing or checking | Enums + pattern `switch` (recent) | Enums + `match`, exhaustiveness enforced |
| **Generics** | `Class of T`, erased with cast insertion | None — macro and `_Generic` tricks | Erasure with bounds | Monomorphized, bounds-checked |
| **Error handling** | Required defaults, callback pairs, `Result`-style ADTs | Return codes and `errno`, trivially ignored | Checked / unchecked exceptions | `Result<T, E>` + `?` propagation |
| **Iteration & scopes** | No loop keywords; zero-allocation scoped `While` inlines to C11 statement expressions; scoped `as` eliminates callback pyramids | Primitive `while`/`for`/`break`; callbacks drift rightward | Primitive loops; `try-with-resources` | Primitive loops; `Drop` RAII |
| **Concurrency** | pthreads; mutex-protected collections; atomics; parallel fan-out | pthreads; no memory-model guarantees | Memory model + `java.util.concurrent` | Data races are compile errors |
| **Build model** | Transpiles to one C translation unit; `gcc` links; the compiler is written in Spec and bootstraps from a single canonical C file whose fixed point is verified on every build | Native compilers, headers, make | Bytecode + JIT on the JVM | Native, Cargo ecosystem |
| **Runtime footprint** | Single static binary, no VM | Single binary, no VM | JVM required | Single binary, no VM |

Spec's distinguishing ground: the override discipline (`replace`/`merge`), never-null
defaults, enforced exhaustiveness, a strict root contract (`Any`-typed values may
only call root members — cast for the rest), and a compiler written in itself that
reproduces its own C seed byte-for-byte on every build. It is a young language — its
standard library and tooling are minimal next to the others — but its compile-time
guarantees are already stricter than C's in the areas it covers.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

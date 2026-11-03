# Spec Programming Language

**Spec** is an elegant, concurrent-first, unlockable programming language that compiles directly to optimized C99.

```spec
class HelloWorld{

	replace local Array of String is using: [
		base:struct:Map,
		base:io:*
	];

	replace local Function is init(Map of String to String is args){
		local String is name: args:getString(key: "name", default: "World");
		output:line("Hello, " . name . "!");
	}

}
```

---

## Key Language Philosophies

### 1. Minimal Core & Maximum Standard Library
Spec is architected with a strict philosophy: **keep the compiler minimal, and build the language in the standard library**.
- **Ultra-Lean Compiler**: The compiler core knows only **10 keywords** (`class`, `extends`, `local`, `replace`, `is`, `of`, `to`, `if`, `else`, `return`) and **6 primitive types** (`Int`, `Float`, `Boolean`, `String`, `Function`, `Any`).
- **Userland Implementation**: Rich language features live in the standard library (`lib/`) written in pure Spec—including dynamic collections (`Array`, `Map`), filesystem operations (`File`), process management (`Process`), and concurrency runners (`While`, `Loop`).
- **No Magic**: Language abstractions are not compiler special cases; they can be inspected, extended, or replaced using ordinary Spec code.

### 2. `Function` as a First-Class Type (Uniform Declarations)
In Spec, `Function` is a **type**, not a keyword. This establishes two vital design characteristics:
- **Capitalization Discipline**: Keywords are lowercase (`class`, `local`, `replace`, `is`), while types are PascalCase (`Int`, `String`, `Boolean`, `Function`).
- **Symmetrical Declaration Grammar**: Variable declarations and method definitions share the exact same structural pattern:
  - Variable: `<Modifiers> <Type> is <name>: <value>;`
    ```spec
    local Int is score: 100;
    local Function of String to Boolean is validator;
    ```
  - Method: `<Modifiers> <Type> is <name>(<parameters>) { <body> }`
    ```spec
    replace local Function is init(Map of String to String is args){ ... }
    replace local Function of Boolean is evaluate(){ ... }
    ```
- **First-Class Callables**: Because `Function` is a type, functions and closures can be stored in variables, passed to higher-order functions, and typed generically (`Function of Param to Return`).

### 3. The "Never Null" Safety Standard
In Spec, `null` does not exist as a runtime value, pointer, or type:
- **No Null Keywords or Types**: Functions returning nothing are declared simply as `Function is action()` (no `of null` needed).
- **Concrete Values Required**: Variables and fields cannot be null. If something would be null, the program will not compile.
- **Empty Collections**: Collections like `Array` and `Map` can be empty (`[]`, length 0).
- **Deferred Initialization**: Class fields may be declared without inline values provided they are assigned in `init(...)` before use.
- **Default Fallbacks**: Any operation reading from a source that could be empty requires an explicit default fallback argument (e.g., `getString(key, default)`, `pop(default)`, `charAt(index, default)`).

### 4. Unlockable & Concurrency-First Iteration
Spec has eliminated primitive loop keywords (`while`, `break`) entirely from the language grammar. Rather than hardcoding blocking loop locks, iteration in Spec is fully decoupled into lifecycle objects:
- **`base:iterator:Loop`**: Implements `evaluate() -> Boolean` and `iteration(LoopControl is control) -> Boolean`. Returning `false` from `iteration` or `evaluate` cleanly terminates the loop.
- **`base:iterator:LoopControl`**: Supports non-blocking halts (`stop()`) and asynchronous completion triggers (`onComplete`).
- **`While:run(loop, control)`**: Drives the iterator lifecycle without blocking threads.

### 5. Tab-Based Indentation Standard
Spec establishes a standard indentation convention using **tabs**. A built-in linter detects space-based indentation and optional parameter patterns:
```bash
./spec --lint path/to/program.spec
```

### 6. Multi-File Module Resolution
Dependencies declared in `using: [...]` automatically resolve against the standard library in `lib/` and local project files:
```spec
replace local Array of String is using: [
	base:struct:Array,
	base:struct:Map,
	base:math:*,
	base:io:*,
	base:sys:*,
	base:iterator:*,
	base:reflect:*,
	base:meta:*
];
```

---

## Documentation

- 📚 **[Documentation Portal](docs/README.md)**: Main documentation index.
- 📖 **[Language Guide](docs/language/README.md)**: Syntax, typing system, Never Null standard, operators, and control flow.
- 📦 **[Standard Library Packages](docs/packages/README.md)**: Full API reference for `base:io`, `base:math`, `base:struct`, `base:iterator`, `base:sys`, and string inspection primitives.
- 📜 **[Code Style & SpecDoc Guide](docs/STYLE_GUIDE.md)**: Official code style conventions, architectural idioms, and the SpecDoc documentation standard.
- 🛠️ **[Tooling & Compiler Guide](docs/tooling/README.md)**: Compiler CLI, module loader, tab linter, and Kate editor integration.

---

## Getting Started

### Prerequisites
- **Rust & Cargo** (for building the Stage 0 compiler)
- **GCC** (C99 compiler for linking binaries)

### Building the Compiler
```bash
cargo build --release
ln -sf target/release/spec ./spec
```

### Compiling and Running a Program
```bash
# Compile
./spec -i examples/helloworld.spec -o helloworld

# Run with CLI arguments
./helloworld --name Daniel
```

### Running the Linter
```bash
./spec --lint examples/blackjack_shorthand.spec
```

---

## Standard Library Packages (`lib/`)

| Package | Key Types & Functions | Description |
|---|---|---|
| **`base:io`** | `output:line`, `Input:prompt`, `File:read`, `File:write`, `File:exists` | Terminal and filesystem I/O. |
| **`base:math`** | `round`, `floor`, `ceil`, `random`, `abs`, `min`, `max`, `clamp` | Math primitives and pure Spec algorithms. |
| **`base:struct`** | `Array` (`length`, `get`, `add`, `pop`, `removeAt`, `slice`, `clear`, `indexOf`, `isEmpty`), `Map` (`getString`, `set`, `has`, `remove`, `keys`, `length`) | Dynamic array and dictionary collections. |
| **`base:iterator`** | `Loop`, `LoopControl`, `While:run` | Decoupled loop execution engine. |
| **`base:sys`** | `Process:execute`, `SourceLocation`, `StackFrame` | Subprocess execution, source coordinates, and execution frames. |
| **`base:reflect`** | `Type`, `Parameter`, `Member`, `Class` | Runtime type information, signature inspection, and reflection metadata. |
| **`base:meta`** | `Expression`, `Statement`, `NamedArg`, `ProgramNode` | Syntax trees, AST transformations, and meta-programming representations. |

---

## Editor Support (Kate / KWrite)

Install syntax highlighting definitions for the KDE Kate editor:
```bash
./utilities/install-kate-syntax.sh
```
*Installs `spec.xml` to `~/.local/share/org.kde.syntax-highlighting/syntax/` with priority association for `*.spec`.*

---

## Building and Bootstrapping

Spec is **100% self-hosted**. You do not need Rust or Cargo to build Spec; only a C compiler (`gcc` or `clang`) with standard POSIX threads:

```bash
# Bootstrap the official Spec compiler directly from canonical C source:
./bootstrap.sh

# Compile any Spec program:
./spec -i examples/helloworld.spec -o helloworld
./helloworld --name "Spec Developer"

# Run the strict whitespace and style linter:
./spec --lint lib/compiler/Driver.spec
```

---

## Project Structure

```
spec-lang/
├── bootstrap.sh             # Canonical C bootstrap script (no Rust required)
├── bootstrap/
│   └── spec.c               # Canonical converged C11 source of self-hosted compiler
├── Cargo.toml               # Stage 0 bootstrap compiler manifest (retired)
├── src/                     # Legacy Stage 0 Rust bootstrap compiler
├── lib/                     # Spec Standard Library & Self-Hosted Compiler (written in Spec)
│   ├── base/
│   │   ├── io/              # File, Input, Output
│   │   ├── iterator/        # Loop, LoopControl, While
│   │   ├── math/            # Math
│   │   ├── struct/          # Array, Map
│   │   └── sys/             # Process, SourceLocation, StackFrame
│   └── compiler/            # Pure Spec Self-Hosted Compiler
│       ├── Token.spec       # Token model
│       ├── Lexer.spec       # Pure Spec Lexer & tokenizer
│       ├── Parser.spec      # Pure Spec recursive-descent Parser
│       ├── AST.spec         # AST definitions
│       ├── TypeChecker.spec # Semantic analyzer & interface contract enforcement
│       ├── Loader.spec      # Transitive multi-file package loader
│       ├── CodeGenerator.spec # C11 translation unit coordinator
│       ├── DeclarationGenerator.spec # Enums, forward decls, and struct layouts
│       ├── BuiltinCallGenerator.spec # Standard library runtime builtin dispatcher
│       ├── CBackendUtils.spec # C type mapping and identifier sanitization
│       ├── RuntimePrelude.spec # Thread-safe C runtime with recursive mutexes
│       ├── Linter.spec      # Pure Spec style and optional parameter linter
│       └── Driver.spec      # Compiler CLI coordinator
├── docs/                    # Nested documentation portal
│   ├── README.md            # Documentation portal index
│   ├── language/            # Language guide & syntax reference
│   ├── packages/            # Standard library package reference
│   └── tooling/             # Compiler, linter, and editor guide
├── examples/                # Example programs & test suites
├── utilities/               # Helper scripts & editor syntax configurations
│   ├── install-kate-syntax.sh
│   └── spec-kate.xml
├── MAINTENANCE.md           # Developer feature addition checklist
└── TASKS.md                 # Project roadmap tracking
```

---

## Roadmap to Self-Hosting

- [x] **Stage 0 Compiler (Rust)**: C99 transpilation, tab linter, multi-file module loader.
- [x] **Phase 1**: File I/O (`File:read`, `File:write`), process execution (`Process:execute`), and string inspection primitives (`charAt`, `substring`, `indexOf`, `isDigit`, `isAlpha`, `isWhitespace`).
- [x] **Phase 2**: Rich collections (`Array:pop`, `removeAt`, `slice`, `clear`, `indexOf`; `Map:set`, `has`, `remove`, `keys`, `length`).
- [x] **Phase 3**: Implement lexer in Spec (`compiler:Lexer.spec`, `compiler:Token.spec`).
- [x] **Phase 4**: Implement parser and AST in Spec (`compiler:Parser.spec`, `compiler:AST.spec`).
- [x] **Phase 5**: Implement pure Spec type checker and modular code generator (`TypeChecker.spec`, `CodeGenerator.spec`, `DeclarationGenerator.spec`, `BuiltinCallGenerator.spec`).
- [x] **Phase 6**: Stage 1, Stage 2, and Stage 3 self-hosting bootstrap verification with 100% bit-for-bit fixed-point convergence. Single-file C bootstrap (`bootstrap/spec.c`, `bootstrap.sh`) established and Rust compiler retired.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

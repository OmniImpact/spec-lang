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

### 1. Unlockable & Concurrency-First Iteration
Rather than hardcoding loop locks, iteration in Spec is fully decoupled into lifecycle objects:
- **`base:iterator:Loop`**: Implements `evaluate() -> Boolean` and `iteration(LoopControl is control) -> Boolean`.
- **`base:iterator:LoopControl`**: Supports non-blocking halts (`stop()`) and asynchronous completion triggers (`onComplete`).
- **`While:run(loop, control)`**: Drives the iterator lifecycle without blocking threads.

### 2. The "Never Null" Safety Standard
In Spec, `null` does not exist as a runtime value:
- **Concrete Values Required**: Variables and fields cannot be null.
- **Empty Collections**: Collections like `Array` and `Map` can be empty (`[]`).
- **Deferred Initialization**: Class fields may be declared without inline values provided they are assigned in `init(...)` before use.
- **Default Fallbacks**: Any operation reading from a source that could be empty requires a default argument (e.g., `getString(key, default)`, `pop(default)`, `removeAt(index, default)`).

### 3. Tab-Based Indentation Standard
Spec establishes a standard indentation convention using **tabs**. A built-in linter detects space-based indentation and optional parameter patterns:
```bash
./spec --lint path/to/program.spec
```

### 4. Multi-File Module Resolution
Dependencies declared in `using: [...]` automatically resolve against the standard library in `lib/` and local project files:
```spec
replace local Array of String is using: [
	base:struct:Array,
	base:struct:Map,
	base:math:*,
	base:io:*,
	base:sys:*,
	base:iterator:*
];
```

---

## Documentation

- 📚 **[Documentation Portal](docs/README.md)**: Main documentation index.
- 📖 **[Language Guide](docs/language/README.md)**: Syntax, typing system, Never Null standard, operators, and control flow.
- 📦 **[Standard Library Packages](docs/packages/README.md)**: Full API reference for `base:io`, `base:math`, `base:struct`, `base:iterator`, `base:sys`, and string inspection primitives.
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
| **`base:sys`** | `Process:execute` | Subprocess execution and system command dispatch. |

---

## Editor Support (Kate / KWrite)

Install syntax highlighting definitions for the KDE Kate editor:
```bash
./utilities/install-kate-syntax.sh
```
*Installs `spec.xml` to `~/.local/share/org.kde.syntax-highlighting/syntax/` with priority association for `*.spec`.*

---

## Project Structure

```
spec-lang/
├── Cargo.toml               # Stage 0 compiler manifest
├── src/                     # Compiler source code (Rust)
│   ├── ast.rs               # AST definitions
│   ├── lexer.rs             # Tokenizer
│   ├── parser.rs            # Recursive-descent parser
│   ├── loader.rs            # Multi-file module loader
│   ├── codegen.rs           # C99 code generator and runtime prelude
│   ├── linter.rs            # Code standards and optional parameter linter
│   └── main.rs              # CLI driver
├── lib/                     # Spec Standard Library (written in Spec)
│   └── base/
│       ├── io/              # File, Input, Output
│       ├── iterator/        # Loop, LoopControl, While
│       ├── math/            # Math
│       ├── struct/          # Array, Map
│       └── sys/             # Process
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
- [ ] **Phase 3**: Implement lexer in Spec (`compiler:Lexer.spec`).
- [ ] **Phase 4**: Implement parser and AST in Spec (`compiler:Parser.spec`).
- [ ] **Phase 5**: Implement code generator in Spec (`compiler:CodeGen.spec`).
- [ ] **Phase 6**: Stage 1 & Stage 2 bootstrap verification.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

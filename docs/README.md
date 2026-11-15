# Spec Documentation

Welcome to the **Spec** language documentation portal. Use the links below to explore language features, standard library packages, compiler tooling, and architectural specifications.

---

## Documentation Sections

### 1. [Language Guide](language/README.md)
Comprehensive reference for the Spec language syntax, typing rules, and execution semantics:
- **[Syntax & Structure](language/README.md#language-syntax--structure)**: Classes, entrypoints, variable declarations, generic classes (`class Box of T`), default parameter values, capturing closures, and `using` imports.
- **[Types & Literals](language/README.md#types--literals)**: `Int`, `Float`, `String` (double vs single quote), `Boolean`, `Any`, generic collections (`Array of T`, `Map of K to V`), map literals (`["k": v]`), and algebraic tagged union `Enum`s.
- **[Never Null Philosophy](language/README.md#the-never-null-standard)**: Why `null` values do not exist in Spec, deferred initialization, and default fallbacks.
- **[Control Flow & Iteration](language/README.md#control-flow--branching)**: `if` branching, pattern and predicate `match` with payload destructuring, and the decoupled iterator model (`Loops`).
- **[Unblockable Concurrency Model](language/README.md#unblockable-concurrency--iteration-model)**: Decoupled iterators (`Loop`, `LoopControl`) and event-driven I/O (`InputHandler`).

---

### 2. [Standard Library Packages](packages/README.md)
Reference manual for the standard library implemented in Spec (`spec/lib/`):
- **[`base:math`](packages/README.md#2-basemath)**: Trigonometry, rounding, random generation, and pure Spec helpers (`abs`, `min`, `max`, `clamp`).
- **[`base:struct`](packages/README.md#3-basestruct)**: Dynamic array containers (`Array` with `map`, `fold`, `filter`, `each`) and 64-bucket hash tables (`Map` with `each`, literals, and bracket indexing).
- **[`base:iterator`](packages/README.md#4-baseiterator)**: The decoupled iteration abstractions (`Loop`, `LoopControl`).
- **[`base:data`](packages/README.md)**: Native JSON parser and serializer (`Json`).
- **[`base:net`](packages/README.md)**: TCP client/server stream sockets (`Socket`).
- **[`base:audio`](packages/README.md)**: Raw PCM audio output (`Audio`).
- **[`base:sys`](packages/README.md#5-basesys)**: Control-flow providers (`Conditional`, `Loops`), console and file I/O (`Output`, `Input`, `Stderr`, `File`), high-resolution timing and calendar dates (`Time`, `DateTime`), cross-platform paths (`Uri`), terminal escapes (`Ansi`), and process/thread execution (`Process`, `Parallel`, `Box`).

---

### 3. [Tooling & Compiler Guide](tooling/README.md)
Guide for building, running, linting, and editing Spec code:
- **[Compiler CLI (`spec`)](tooling/README.md#compiler-cli-spec)**: Self-hosted bootstrap (`./bootstrap.sh`), CLI flags (`-i`, `-o`, `--emit-c`), multi-file compilation, and C11 code generation.
- **[Project Scaffolder & Build Orchestrator (`specinit`, `specbuild`)](tooling/README.md)**: Project initialization and `specbuild.json` manifest-driven builds, tests, and linting.
- **[Code Standards & Linter (`speclint`)](tooling/README.md#code-standards--built-in-linter)**: Reflection-based lint rules — tab indentation, brace alignment, AST idioms, and instance-model audits.
- **[Kate Editor Syntax Highlighting](tooling/README.md#kate--kwrite-syntax-highlighting)**: Installation and XML definition rules for Kate and KWrite.

---

### 4. [Code Style & SpecDoc Guide](STYLE_GUIDE.md)
Official code style conventions, architectural idioms, and documentation standard:
- **[Formatting Rules](STYLE_GUIDE.md#2-code-formatting--layout)**: Hard tabs, OTBS braces, whitespace rules, and naming conventions.
- **[SpecDoc Standard](STYLE_GUIDE.md#5-specdoc-documentation-standard)**: Doc comments (`##`, `#!`), standard tags (`@param`, `@return`, `@fallback`, `@example`), and cross-referencing.

---

### 5. [Roadmap to Self-Hosting](language/README.md#roadmap-to-self-hosting)
Tracks the evolution of the Spec compiler to full self-hosting in Spec.

---

## Quick Navigation

| Target | Description | Path |
|---|---|---|
| 🏠 **Repository Root** | Project home & quickstart | [README.md](../README.md) |
| 📖 **Language Guide** | Syntax, types, control flow | [docs/language/README.md](language/README.md) |
| 📦 **Standard Packages** | Standard library API reference | [docs/packages/README.md](packages/README.md) |
| 🛠️ **Tooling Guide** | Compiler, linter, editor plugins | [docs/tooling/README.md](tooling/README.md) |
| 📜 **Code Style & SpecDoc** | Style guide and SpecDoc documentation standard | [docs/STYLE_GUIDE.md](STYLE_GUIDE.md) |
| 📂 **Examples** | Demo programs | [examples/](../examples) |
| 🧪 **Tests** | Positive test suites | [tests/](../tests) |
| 🚫 **Negative tests** | Must-fail suites asserting diagnostics | [tests/negative/](../tests/negative) |
| 🗺️ **Alpha Roadmap** | 0.1 Alpha milestones and status | [ROADMAP-ALPHA.md](../ROADMAP-ALPHA.md) |
| ⚙️ **Compiler Dev Guide** | Bootstrap ratchet and contributor discipline | [KNOWLEDGE-SPECDEV.md](../KNOWLEDGE-SPECDEV.md) |

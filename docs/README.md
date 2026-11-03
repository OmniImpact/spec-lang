# Spec Documentation

Welcome to the **Spec** language documentation portal. Use the links below to explore language features, standard library packages, compiler tooling, and architectural specifications.

---

## Documentation Sections

### 1. [Language Guide](language/README.md)
Comprehensive reference for the Spec language syntax, typing rules, and execution semantics:
- **[Syntax & Structure](language/README.md#language-syntax--structure)**: Classes, entrypoints, variable declarations, and `using` imports.
- **[Types & Literals](language/README.md#types--literals)**: `Int`, `Float`, `String` (double vs single quote), `Boolean`, `Any`, and generic collections (`Array of T`, `Map of K to V`).
- **[Never Null Philosophy](language/README.md#the-never-null-standard)**: Why `null` values do not exist in Spec, deferred initialization, and default fallbacks.
- **[Control Flow & Iteration](language/README.md#control-flow--branching)**: `if`/`else` branching and decoupled iterator model (`While:run`).
- **[Unlockable Concurrency Model](language/README.md#unlockable-concurrency-model)**: Decoupled iterators (`Loop`, `LoopControl`) and event-driven I/O (`InputHandler`).

---

### 2. [Standard Library Packages](packages/README.md)
Reference manual for the standard library implemented in Spec (`lib/`):
- **[`base:io`](packages/README.md#1-baseio)**: Console output (`output:line`), asynchronous input prompt (`Input:prompt`), and filesystem I/O (`File:read`, `File:write`, `File:exists`).
- **[`base:math`](packages/README.md#2-basemath)**: Trigonometry, rounding, random generation, and pure Spec helpers (`abs`, `min`, `max`, `clamp`).
- **[`base:struct`](packages/README.md#3-basestruct)**: Dynamic array containers (`Array`) and hash tables (`Map`).
- **[`base:iterator`](packages/README.md#4-baseiterator)**: Decoupled loop execution engine (`Loop`, `LoopControl`, `While:run`).
- **[`base:sys`](packages/README.md#5-basesys)**: Subprocess execution and operating system dispatch (`Process:execute`).

---

### 3. [Tooling & Compiler Guide](tooling/README.md)
Guide for building, running, linting, and editing Spec code:
- **[Compiler CLI (`spec`)](tooling/README.md#compiler-cli)**: Options, multi-file compilation, and C99 code generation.
- **[Code Standards & Linter](tooling/README.md#linter)**: Enforcing tab-based indentation and inspecting optional parameter usage.
- **[Kate Editor Syntax Highlighting](tooling/README.md#kate-editor-syntax-highlighting)**: Installation and XML definition rules for Kate and KWrite.

---

### 4. [Code Style & SpecDoc Guide](STYLE_GUIDE.md)
Official code style conventions, architectural idioms, and documentation standard:
- **[Formatting Rules](STYLE_GUIDE.md#2-code-formatting--layout)**: Hard tabs, OTBS braces, whitespace rules, and naming conventions.
- **[SpecDoc Standard](STYLE_GUIDE.md#5-specdoc-documentation-standard)**: Doc comments (`##`, `#!`), standard tags (`@param`, `@return`, `@fallback`, `@example`), and cross-referencing.

---

### 5. [Roadmap to Self-Hosting](language/README.md#roadmap-to-self-hosting)
Tracks the evolution of the Spec compiler from the current Stage 0 Rust transpiler to full self-hosting in Spec.

---

## Quick Navigation

| Target | Description | Path |
|---|---|---|
| 🏠 **Repository Root** | Project home & quickstart | [README.md](../README.md) |
| 📖 **Language Guide** | Syntax, types, control flow | [docs/language/README.md](language/README.md) |
| 📦 **Standard Packages** | Standard library API reference | [docs/packages/README.md](packages/README.md) |
| 🛠️ **Tooling Guide** | Compiler, linter, editor plugins | [docs/tooling/README.md](tooling/README.md) |
| 📜 **Code Style & SpecDoc** | Style guide and SpecDoc documentation standard | [docs/STYLE_GUIDE.md](STYLE_GUIDE.md) |
| 📂 **Examples** | Code samples and test programs | [examples/](../examples) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../TASKS.md) |
| 🔧 **Maintenance Guide** | Feature addition checklist | [MAINTENANCE.md](../MAINTENANCE.md) |

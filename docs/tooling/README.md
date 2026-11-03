[Documentation](../README.md) > **Tooling Guide**

# Spec Tooling & Compiler Guide

This guide covers building, running, linting, and configuring editor support for the Spec programming language.

---

## Table of Contents
1. [Compiler CLI (`spec`)](#compiler-cli-spec)
   - [Building the Compiler](#building-the-compiler)
   - [Compiling a Spec Program](#compiling-a-spec-program)
   - [Multi-File Module Resolution](#multi-file-module-resolution)
   - [Compilation Pipeline](#compilation-pipeline)
2. [Code Standards & Built-in Linter](#code-standards--built-in-linter)
   - [Running the Linter](#running-the-linter)
   - [Enforced Rules](#enforced-rules)
3. [Kate & KWrite Syntax Highlighting](#kate--kwrite-syntax-highlighting)
   - [Installation Script](#installation-script)
   - [XML Definition Rules](#xml-definition-rules)
4. [Quick Navigation](#quick-navigation)

---

## Compiler CLI (`spec`)

The Spec compiler (`spec`) compiles Spec source files down to portable C99 and links them into native executable binaries using the system C compiler (`gcc`).

### Building the Compiler
The Stage 0 compiler is implemented in Rust:

```bash
cargo build --release
```

The resulting binary is created at `target/release/spec`. A symbolic link `spec` is maintained at the project root for convenience.

### Compiling a Spec Program
To compile a Spec program with an entrypoint `init` method into a native executable:

```bash
./spec -i <input.spec> -o <output_binary>
```

#### Example
```bash
./spec -i examples/helloworld.spec -o hello
./hello
# Output: Hello User
```

### Multi-File Module Resolution
Spec automatically resolves imports specified in the class's `using` header:

```spec
replace local Array of String is using: [
	base:struct:Array,
	base:io:File
];
```

The module loader searches for matching files in:
1. Relative directory paths from the compiling file.
2. The standard library directory (`lib/base/...`).

All resolved classes are merged into an AST before code generation, allowing seamless multi-file compilation without manual linker flags.

### Compilation Pipeline
1. **Lexical Analysis (`lexer.rs`)**: Tokenizes the input source files and identifies keywords, types, identifiers, and literals.
2. **Multi-File Loader (`loader.rs`)**: Recursively discovers and parses dependent modules specified in `using` blocks.
3. **Syntactic Parsing (`parser.rs`)**: Constructs the abstract syntax tree (`ast.rs`).
4. **C99 Transpilation (`codegen.rs`)**: Emits clean C99 code, linking runtime structures and handling garbage-free memory management.
5. **Native GCC Compilation**: GCC optimizes the generated C code (`-O2`) and links the math runtime (`-lm`), producing a standalone native executable. Intermediate `.c` files are automatically removed upon success.

---

## Code Standards & Built-in Linter

Spec features a built-in code linter that enforces style guidelines across all codebase files.

### Running the Linter
Run the linter using the `--lint` (or `-l`) flag:

```bash
./spec --lint path/to/file.spec
```

To run the linter across all project examples and standard library files:
```bash
for f in examples/*.spec lib/**/*.spec; do
	./spec --lint "$f"
done
```

### Enforced Rules

#### 1. Tab-Based Indentation Standard
- **Rule**: All Spec source code must be indented using tab characters (`\t`).
- **Violation**: Any leading spaces used for indentation trigger a warning and cause the linter to fail (exit code 1).
- **Rationale**: Ensures deterministic, customizable visual alignment across editors while preventing indentation drift.

#### 2. Optional Parameter Consistency
- **Rule**: Optional method parameters must provide explicit default values in declarations.
- **Violation**: Missing defaults in fallible reads trigger linter notices or warnings.

---

## Kate & KWrite Syntax Highlighting

Spec includes official syntax highlighting definition files for KDE Kate and KWrite editors.

### Installation Script
Run the automated installer from the repository root:

```bash
./utilities/install-kate-syntax.sh
```

This copies `utilities/spec-kate.xml` to KDE syntax definition directories:
- `~/.local/share/org.kde.syntax-highlighting/syntax/spec.xml`
- `~/.local/share/katepart5/syntax/spec.xml`

### XML Definition Rules
The syntax definition provides:
- **File Matching**: Automatically activates for all `*.spec` files.
- **Keywords**: Highlights `class`, `extends`, `local`, `replace`, `is`, `of`, `to`, `if`, `else`, `return`.
- **Types**: Highlights primitive and object types (`Int`, `Float`, `String`, `Boolean`, `Function`, `Any`, `Array`, `Map`).
- **Packages**: Context-aware coloring for package paths (`base:io`, `base:math`, `base:struct`, `base:iterator`, `base:sys`).
- **Comments**: Highlights single-line `#` comments.
- **String Literals**: Supports double-quoted escape sequences and single-quoted raw expressions.

---

## Quick Navigation

| Target | Description | Path |
|---|---|---|
| 🏠 **Repository Root** | Project home & overview | [README.md](../../README.md) |
| 📚 **Documentation Portal** | Docs index | [docs/README.md](../README.md) |
| 📖 **Language Guide** | Syntax, types, and control flow | [docs/language/README.md](../language/README.md) |
| 📦 **Standard Packages** | Standard library API reference | [docs/packages/README.md](../packages/README.md) |
| 📂 **Examples** | Code samples and tests | [examples/](../../examples) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../../TASKS.md) |

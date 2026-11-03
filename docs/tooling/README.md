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

The Spec compiler (`spec`) is **100% self-hosted in pure Spec** (`lib/compiler/`). It compiles Spec source files down to portable C11 and links them into native executable binaries using the system C compiler (`gcc`).

### Bootstrapping & Building the Compiler
You do not need Rust or Cargo to build Spec; only `gcc` (or `clang`) with standard POSIX threads is required:

```bash
./bootstrap.sh
```

This compiles the canonical converged C11 source at `bootstrap/spec.c` into the `./spec` executable at the project root.

To perform a full 3-stage self-hosting convergence build after modifying compiler files under `lib/compiler/`:
```bash
./spec -i lib/compiler/Driver.spec -o spec-stage1
./spec-stage1 -i lib/compiler/Driver.spec -o spec-stage2 --emit-c /tmp/stage2.c
./spec-stage2 -i lib/compiler/Driver.spec -o spec-stage3 --emit-c /tmp/stage3.c
diff -s /tmp/stage2.c /tmp/stage3.c
cp spec-stage3 spec && cp /tmp/stage3.c bootstrap/spec.c
```

### Compiler Exit Codes & Diagnostics
- **`0`** — success.
- **`1`** — compile failure: syntax errors, load errors (`[LoadError]`: missing module files, unresolvable imports, invalid class grouping), type errors, or backend `gcc` failure.
- **`2`** — usage error (missing input or output path).

All compiler diagnostics are written to **stderr** (via the `error:line` builtin); programs write normal output to stdout via `output:line`. A program can terminate itself with an explicit status via `Process:exit(status: N)`. This makes the compiler safe to drive from scripts and CI:
```bash
./spec -i app.spec -o app 2>compile.log || exit 1
```

### Compiling a Spec Program
To compile a Spec program into a native executable:

```bash
./spec -i <input.spec> -o <output_binary>
```

To emit the generated C11 source code (either standalone or alongside `-o`):

```bash
./spec -i <input.spec> --emit-c <output.c>
./spec -i <input.spec> -o <output_binary> --emit-c <output.c>
```

#### Example
```bash
./spec -i examples/helloworld.spec -o hello
./hello --name Daniel
# Output: Hello, Daniel!
```

### Multi-File Module Resolution
Spec automatically resolves imports specified in the class's `using` header:

```spec
replace local Array of String is using: [
	base:struct:Array,
	base:io:File
];
```

The module loader (`lib/compiler/Loader.spec`) searches for matching files in:
1. Relative directory paths from the compiling file.
2. The standard library directory (`lib/`).

All resolved classes are merged into an AST with per-file source provenance before type checking and code generation, allowing seamless multi-file compilation without manual linker flags.

### Compilation Pipeline & Memory Model
1. **Lexical Analysis (`lib/compiler/Lexer.spec`)**: Tokenizes input source files (`Token.spec`) using $O(1)$ cached string length lookups and a static 256-entry character table with zero per-character heap allocations.
2. **Multi-File Loader (`lib/compiler/Loader.spec`)**: Recursively discovers and parses dependent modules specified in `using` blocks.
3. **Syntactic Parsing (`lib/compiler/Parser.spec`)**: Constructs the abstract syntax tree (`lib/base/meta/AST.spec`) with statement-boundary error recovery and `[file:line:col]` diagnostics.
4. **Static Type Checking (`lib/compiler/TypeChecker.spec`)**: Validates types, generic class substitutions, definite field assignment, interface contracts, and `replace` override rules.
5. **C11 Code Generation (`lib/compiler/CodeGenerator.spec`, `DeclarationGenerator.spec`, `BuiltinCallGenerator.spec`, `RuntimePrelude.spec`)**: Emits clean C11 code featuring amortized $O(1)$ growable string buffers (`spec_str_append`), lazy `SpecArray` allocation, static small-integer formatting, and automatic deallocation of transient `Loop` objects.
6. **Native GCC Compilation**: GCC optimizes the generated C11 code (`-O2 -pthread -lm`), producing a standalone native executable. Intermediate `.c` files are automatically removed upon success unless `--emit-c` is specified.

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
for f in examples/*.spec tests/*.spec lib/**/*.spec; do
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
| 📂 **Examples** | Demo programs | [examples/](../../examples) |
| 🧪 **Tests** | Positive test suites (`tests/`) and must-fail suites (`tests/negative/`) | [tests/](../../tests) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../../TASKS.md) |

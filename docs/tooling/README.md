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

The Spec compiler (`bin/spec`) is **100% self-hosted in pure Spec** (`spec/base/compiler/`). It compiles Spec source files down to portable C11 and links them into native executable binaries using the system C compiler (`gcc`).

### Bootstrapping & Building the Compiler
Building Spec requires only `gcc` (or `clang` via `CC=clang ./bootstrap.sh`) with standard POSIX threads:

```bash
./bootstrap.sh
```

This compiles the canonical converged C11 source at `bootstrap/spec.c` into the `bin/spec` executable.

The bootstrap verifies the self-hosting fixed point on every run: the freshly
built compiler recompiles its own sources and the emitted C must match the
canonical seed byte-for-byte. After modifying compiler files under
`spec/base/compiler/`, re-baseline the seed and rebuild:

```bash
bin/spec -i spec/base/compiler/driver/Driver.spec --emit-c bootstrap/spec.c
./bootstrap.sh
```

### Continuous Integration & Sanitized Builds
Every push to `main` and every pull request runs the regression suite on GitHub Actions (`.github/workflows/ci.yml`) in three jobs: a `gcc` bootstrap, a `CC=clang` bootstrap, and an ASan/UBSan-instrumented run. The bootstrap script honors a `$CC` override; the suite runner is `specunit` — point it at any compiler binary with `-s` to test that binary against the full suite.

To validate compiler crash-freedom (use-after-free, out-of-bounds, undefined behavior) locally, build an instrumented compiler and run the suite under it:
```bash
gcc -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined \
    -fno-omit-frame-pointer bootstrap/spec.c -o bin/spec-asan -pthread -lm
ASAN_OPTIONS=detect_leaks=0 bin/spec-asan --quiet \
    -i utilities/specunit/SpecUnit.spec -o bin/specunit-asan
ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
    bin/specunit-asan -s bin/spec-asan -t examples -t tests
```
Leak detection is off by default: the ARC engine reclaims the compiler's object graph and an `atexit` shutdown reclaims the string ring, but string-lifetime churn (~0.5 MB per self-compile) remains until string ownership lands; opt in with `ASAN_OPTIONS=detect_leaks=1` on the runner invocation.

### Compiler Exit Codes & Diagnostics
- **`0`** — success.
- **`1`** — compile failure: syntax errors, load errors (`[LoadError]`: missing module files, unresolvable imports, invalid class grouping), type errors, or backend `gcc` failure.
- **`2`** — usage error (missing input or output path).

All compiler diagnostics are written to **stderr** (via `Stderr:line`); programs write normal output to stdout via `Output:line` — both console wrappers in `base:sys`, instance-imported as `['base', 'sys', as Output()]` / `as Stderr()`. A program can terminate itself with an explicit status via `Process:exit(status: N)`. This makes the compiler safe to drive from scripts and CI:
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
replace Array of Array of String is using: [
	['base', 'struct', Array],
	['base', 'sys', as File()]
];
```

The module loader (`spec/base/compiler/loader/Loader.spec`) scans two trees —
the directory of the `.spec` file being compiled and the compiler executable's
directory (plus the working directory) — and indexes every class it finds. An
import's segments name the package; the namespace declared inside a file is
what makes it that package. A class-form import loads the candidate and
verifies its declared namespace; a wildcard form (no trailing class) loads
everything in the package.

All resolved classes are merged into an AST with per-file source provenance before type checking and code generation, allowing seamless multi-file compilation without manual linker flags.

### Compilation Pipeline & Memory Model
1. **Lexical Analysis (`spec/base/compiler/lexer/Lexer.spec`)**: Tokenizes input source files (`Token.spec`) using $O(1)$ cached string length lookups and a static 256-entry character table with zero per-character heap allocations.
2. **Multi-File Loader (`spec/base/compiler/loader/Loader.spec`)**: Recursively discovers and parses dependent modules specified in `using` blocks.
3. **Syntactic Parsing (`spec/base/compiler/parser/Parser.spec`)**: Constructs the abstract syntax tree (`spec/base/compiler/ast/`) with statement-boundary error recovery and `[file:line:col]` diagnostics.
4. **Static Type Checking (`spec/base/compiler/checker/TypeChecker.spec`)**: Validates types, generic class substitutions, definite field assignment, interface contracts, and `replace` override rules.
5. **C11 Code Generation (`spec/base/compiler/gen/`)**: Emits clean C11 code featuring amortized $O(1)$ growable string buffers (`spec_str_append`), lazy `SpecArray` allocation, static small-integer formatting, and automatic deallocation of transient `Loop` objects.
6. **Native GCC Compilation**: GCC optimizes the generated C11 code (`-O2 -pthread -lm`), producing a standalone native executable. Intermediate `.c` files are automatically removed upon success unless `--emit-c` is specified.

---

## Code Standards & Built-in Linter

The code linter is **speclint**, a standalone Spec program in
`utilities/speclint/` — part of the ecosystem alongside the specunit
test runner, not a compiler mode. Its binary imports the compiler's
front-end (lexer, parser, AST) directly, so linting runs in-process,
and iterating on lint rules never rebuilds or reconverges the compiler.

### Running the Linter
Build the linter binary, then lint one file or whole trees:

```bash
bin/spec --quiet -i utilities/speclint/SpecLint.spec -o bin/speclint

bin/speclint -i path/to/file.spec
bin/speclint -t examples -t tests
```

`-t` is a directory, repeatable or comma-separated, scanned recursively
(dot entries skipped; `#! specunit: negative` compile-must-fail
fixtures are skipped too). The Phase 0.5 instance-model audit over the
fully loaded program is informational and always exits 0:

```bash
bin/speclint -a -i path/to/file.spec
```

Exit codes: **0** clean, **1** findings or syntax errors, **2** usage.

### Enforced Rules

#### 1. Tab-Based Indentation Standard
- **Rule**: All Spec source code must be indented using tab characters (`\t`).
- **Violation**: Any leading spaces used for indentation trigger a warning.
- **Violation**: Trailing whitespace at the end of any line.
- **Violation**: A column-0 closing brace whose indentation does not match the current nesting depth (one tab per open brace). String literals and comments are masked before brace counting, so brace characters inside them are ignored.
- **Rationale**: Ensures deterministic, customizable visual alignment across editors while preventing indentation drift.

#### 2. Optional Parameter Consistency
- **Rule**: Optional method parameters must provide explicit default values in declarations.
- **Violation**: Missing defaults in fallible reads trigger linter notices or warnings.

#### 3. Allocation Idioms (E10)
- **Rule**: Construction inside a While/Loop callback body allocates per iteration.
- **Violation**: An `UpperCamel:init(...)` call inside a loop body triggers a hoist-the-instance warning.

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
- **Keywords**: Highlights `local`, `contained`, `replace`, `merge`, `held`, `is`, `as`, `of`, `to`, `if`, `else`, `return`.
- **Types**: Highlights primitive and object types (`Int`, `Float`, `String`, `Boolean`, `Function`, `Any`, `Array`, `Map`).
- **Packages**: Context-aware coloring for package paths (`base:math`, `base:struct`, `base:iterator`, `base:sys`).
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

# Spec 0.1 Alpha Release Roadmap

This roadmap defines the core milestones, architectural cleanup tasks, tooling additions, and platform reliability goals required to take the **Spec Programming Language** to its first official release: **v0.1 Alpha**.

---

## 1. Vision & Release Objectives

The 0.1 Alpha release represents Spec's transition from an experimental self-hosting language to an accessible, reliable, and developer-ready systems language. The objectives for 0.1 Alpha are:

1. **Rock-Solid Self-Hosting Core**: Byte-identical compiler fixed point, deterministic C11 code generation, and 100% test-suite green status.
2. **First-Class Developer Tooling**: A complete toolchain consisting of `spec` (compiler), `specunit` (test runner), `speclint` (linter), `specinit` (project initializer), `specbuild` (build orchestrator), and `speclsp` (Language Server Protocol server for IDE integration).
3. **Turnkey Installation**: Zero-friction setup on Linux with automated dependency checks and environment configuration.
4. **Clean, Extensible Architecture**: Modular rule-based linting, unified error reporting, native JSON serialization, and a clear abstraction layer isolating POSIX/platform-specific runtime code.

---

## 2. Core Compiler & Language Cleanup

### 2.1 Finalize Phase 0.5 Instance-Model Migration
- **Status**: **Completed** (`v0.000.100`).
- **Accomplishments**:
  - Migrated all non-exempt call sites (including `Conditional:dispatchScan` and throughout `spec/base/compiler`) to instance calls or explicit `held` functions.
  - Verified `speclint -a` reports **0 call site(s) must migrate** across the entire codebase.
  - Locked in the instance-model contract with strict typechecker enforcement and dedicated linter rules (`AsConditionalRule`, `AsLoopsRule`).

### 2.2 On-Demand Precompiled C Runtime Accelerator
- **Status**: **Completed**.
- **Accomplishments**:
  - Partitioned `RuntimePrelude.spec` into `emitHeader()` (types, structs, inlines, and runtime API prototypes) and `emitBody()` (runtime implementation), while preserving `emitRuntime()` for monolithic standalone emission (`--emit-c` and canonical `bootstrap/spec.c`).
  - Added named tags to anonymous structs (`SpecArray`, `SpecMap`, `SpecByteBuffer`, `SpecVec`, `SpecAudioStream`) and converted cross-boundary symbols (`spec_is_subclass_of`, `spec_held_registry`) to external linkage.
  - Implemented an on-demand accelerator cache in `Driver.spec` located at `~/.cache/spec/runtime/` (`spec_runtime.h`, `spec_runtime.c`, and compiled `spec_runtime.o`).
  - Cold compile writes header and source, compiling `spec_runtime.o` via `${CC:-gcc} -O2 -w -c`. Warm compiles emit user programs with `#include ".../spec_runtime.h"` and link `spec_runtime.o` directly.
  - **Stale/Corrupt Cache Auto-Purge**: If the backend C compiler exits with a failure status (`gccStatus != 0`), cached artifacts are automatically removed so the subsequent compile regenerates cleanly.
  - Added CLI flags `--no-cache` and `--clean-cache`.
  - Achieved ~2.7x compilation speedup on single-file builds while preserving byte-for-byte fixed-point bootstrap verification.

### 2.3 Compiler Diagnostic & Error Centralization
- **Status**: **Completed**.
- **Accomplishments**:
  - Expanded `spec/base/compiler/ErrorText.spec` into the central template vocabulary for Lexer, Parser, Loader, and TypeChecker errors.
  - Enhanced `spec/lib/base/sys/SourceLocation.spec` with span `length: Int` for structured source ranges.
  - Updated `spec/base/compiler/Error.spec` and `spec/base/compiler/checker/TypeError.spec` to carry structured `SourceLocation` spans (`file`, `line`, `col`, `length`).
  - Migrated hardcoded syntax, loader, and type error strings across `Parser.spec`, `Loader.spec`, and `TypeChecker.spec` to `ErrorText.spec`.
  - Verified byte-for-byte fixed-point bootstrap verification in `bootstrap.sh` and 100% green test suite in `specunit`.

### 2.4 Standard Library Expansion
- **Native JSON Serialization (`base:data:Json`)** [Completed]: Full-featured, pure Spec JSON library (`spec/lib/base/data/Json.spec`, `JsonNull.spec`, `JsonBool.spec`, `JsonNumber.spec`) providing bidirectional recursive descent parsing (`Json:parse`), typed getters (`getInt`, `getString`, `getBool`, `getFloat`, `getObject`, `getArray`), compact encoding (`Json:stringify`), and pretty printing (`Json:format`). Serves as the shared data interchange foundation for `specbuild.json` manifests and `speclsp` JSON-RPC 2.0 communication. Verified with unit test suite `tests/TestJson.spec` (9/9 passing).
- **Time & Clocks**: Provide a high-resolution time module (`base:sys:Time`) with ISO-8601 formatting, duration arithmetic, and nanosecond/microsecond clocks (expanding beyond `Process:clockMs()`).
- **Basic Networking / Sockets**: Abstract stream sockets (`base:sys:Socket`, TCP client/server) over the sysinternal floor.
- **Collections**: Ensure `List`, `Array`, and `Map` have consistent API parity across iterations, slicing, filtering, and mutations.

### 2.5 Modern Unit Testing Framework & Negative Test Suite Port
- **Status**: **Completed**.
- **Accomplishments**:
  - Extended `Assert` with structured assertion primitives: `Assert:compilerRejects(source:, expect:)`, `Assert:compilerRejectsFile(filePath:, expect:)`, and `Assert:runFails(source:, expect:)`.
  - Replaced ad-hoc loose negative test files with 9 structured, predictable `SpecUnitTest` classes: `TestNegativeReceivers`, `TestNegativeOverloads`, `TestNegativeHeld`, `TestNegativeImportsAndCasts`, `TestNegativeControlFlow`, `TestNegativeTypeSafety`, `TestNegativeClassModel`, `TestNegativeRuntime`, and `TestNegativeMultiFile`.
  - Organized multi-file fixture assets under `tests/negative/fixtures/` classified as `helper` files.
  - Achieved 100% green status across all test suites in `specunit`.

---

## 3. Modular, Reflection-Based Linter (`speclint`)

- **Status**: **Completed** (`v0.000.100`).
- **Accomplishments**:
  - Replaced monolithic `Linter.spec` with a pluggable, reflection-driven engine (`LintRuleRegistry.spec`) mirroring the design of `SpecUnitRunner`.
  - Defined standard contract `Class of Loadable is LintRule`.
  - Implemented dynamic rule discovery via reflection without hardcoded class lists.
  - Modularized rules across formatting, naming, AST idioms, and instance-model enforcement (`AsConditionalRule`, `AsLoopsRule`).
  - Added CLI rule filtering (`--rule` and `--disable`).

### 3.1 Architecture & The `LintRule` Contract
Define a standardized contract class in `utilities/speclint/`:
```spec
Class of Loadable is LintRule {
    namespace: ['speclint', 'rules'];

    ## Unique rule identifier (e.g., 'E10-loop-construction', 'W01-brace-alignment')
    Function of String is id();

    ## Human-readable description of what this rule enforces
    Function of String is description();

    ## Default severity ('warning' or 'notice')
    Function of String is defaultSeverity();

    ## AST inspection hook (called per ProgramNode / ClassInfo / Statement / Expression)
    Function is checkNode(Any is node, LintContext is ctx);

    ## Raw source inspection hook (for whitespace, indentation, trailing spaces)
    Function is checkSource(String is source, LintContext is ctx);
}
```

### 3.2 Dynamic Rule Discovery via Reflection
- Leverage Spec's runtime registry and reflection (`base:sys:Reflection` / `base:sys:Introspection`) to discover all classes inheriting from `LintRule`.
- Automatically register and instantiate rule classes at startup without manual wiring.
- Allow users to enable, disable, or adjust severities per rule via CLI flags or a project configuration file (e.g. `speclint --disable W01 -t spec/`).

### 3.3 Rule Categorization
1. **Formatting & Whitespace Rules**:
   - `TabIndentationRule`: Enforces tabs for indentation (no spaces after tabs).
   - `TrailingWhitespaceRule`: Detects and warns on trailing spaces or tabs.
   - `BraceAlignmentRule`: Enforces opening-brace indent matching for closing braces.
2. **Naming & Convention Rules**:
   - `PascalCaseClassRule`: Verifies classes, interfaces, and enums follow PascalCase.
   - `CamelCaseMemberRule`: Verifies method and field identifiers follow camelCase.
   - `ModifierOrderRule`: Enforces canonical order (`replace`, `local`/`contained`, `held`, `merge`).
3. **AST & Semantic Idioms**:
   - `LoopConstructionRule`: Warns on object construction inside loops (hoisting advisory).
   - `GetStringDefaultRule`: Recommends explicit default values for dictionary lookups.
   - `ExhaustiveWhenRule`: Ensures pattern matches cover all variants or provide an `else` arm.

---

## 4. Developer Experience & New Tooling

To provide a complete developer workflow out of the box, four new utilities will accompany `spec` and `specunit`:

```
   +-----------------------------------------------------------------------------------+
   |                                     SPEC CLI                                      |
   +-----------------+-------------------+-------------------+---------------+---------+
   |  specinit       |  specbuild        |  spec             |  speclint /   | speclsp |
   |  (Scaffolding)  |  (Orchestration)  |  (Compiler)       |  specunit (QA)| (LSP)   |
   +-----------------+-------------------+-------------------+---------------+---------+
```

### 4.1 Project Initializer (`specinit`)
A new tool written in Spec (`utilities/specinit/SpecInit.spec`) to bootstrap new projects:
- **Usage**:
  ```bash
  specinit my_project [--lib | --app]
  ```
- **Generated Project Structure**:
  ```
  my_project/
  ├── specbuild.json          # Build manifest
  ├── .gitignore              # Preconfigured for Spec binaries and build caches
  ├── src/
  │   └── Main.spec           # Entrypoint class with init(Map of String to String is args)
  └── tests/
      └── MainTest.spec       # Basic SpecUnit starter test suite
  ```

### 4.2 Build Orchestrator (`specbuild`)
- **Status**: **Completed**.
- **Accomplishments**:
  - Implemented `utilities/specbuild/SpecBuild.spec` compiled to `bin/specbuild`.
  - Added multi-directory source scanning support (`-s`, `--source-dir`, `--source-dirs`) to the compiler driver (`Driver.spec`) and loader (`Loader.spec`).
  - Added positional command-line argument support in `CodeGenerator.spec` generated `main` entry points.
  - Created standalone manifest build configurations for all example programs (`examples/*.json`).
  - Implemented full project lifecycle commands: `specbuild [manifest.json] [build|test|lint|clean|help]`.
  - Validated via unit test suite `tests/TestSpecBuild.spec` (all passing).

A lightweight, fast build coordinator (`utilities/specbuild/SpecBuild.spec`) to eliminate ad-hoc shell compile scripts:
- **Manifest (`specbuild.json`)**:
  ```json
  {
    "name": "my_project",
    "version": "0.1.0",
    "source": "src/Main.spec",
    "source_dirs": ["src", "lib"],
    "output": "bin/my_project",
    "flags": ["--threads", "4"],
    "c_flags": ["-O2"],
    "tests": {
      "dirs": ["tests"],
      "runner": "specunit"
    }
  }
  ```
- **Capabilities**:
  - `specbuild`: Reads `specbuild.json` via `base:data:Json`, invokes `spec -i <entry> -o <output>` with configured source trees and dependencies.
  - `specbuild test`: Automatically delegates to `specunit` with configured test roots.
  - `specbuild lint`: Automatically runs `speclint` across all defined `source_dirs` package paths.
  - `specbuild clean`: Removes build artifacts and intermediate files.

### 4.3 Shared Terminal UI (TUI) Framework
A shared UI library (`spec/lib/base/ui/` or `utilities/common/tui/`) providing consistent, beautiful command-line output across all Spec tools:
- **Features**:
  - **Color & Style Engine**: ANSI 256-color & truecolor formatting with graceful fallback on dumb terminals.
  - **Status Indicators & Spinners**: Unicode spinners and clear status tags (`[PASS]`, `[FAIL]`, `[WARN]`, `[INFO]`, `[STAGE]`).
  - **Progress Bars**: Multi-threaded progress displays for `specunit` and batch compilations.
  - **Diagnostic Renderers**: Formatted error boxes showing file, line, column, source line snippet, and underlined tokens.
- **Integration**:
  - Update `spec` compilation report for clear 4-stage pipeline rendering.
  - Modernize `specunit` summary with formatted execution times, pass/fail bars, and worker utilization.
  - Enhance `speclint` report with formatted file grouping and grouped issue cards.

### 4.4 Language Server Protocol Server (`speclsp`)
A standalone native LSP binary (`utilities/speclsp/SpecLsp.spec` compiled to `bin/speclsp`) implementing JSON-RPC 2.0 over standard input/output to deliver full IDE intelligence across JetBrains products, VS Code, Zed, and Neovim:
- **Architecture**:
  - Imports the compiler frontend (`base:compiler:lexer`, `parser`, `ast`, `loader`, `checker`) in-process.
  - Compiles to native C11 with instant startup (<5ms) and in-memory parsing/typechecking (<10ms).
  - Uses `base:data:Json` for high-throughput JSON-RPC request and response serialization.
- **0.1 Alpha Capabilities**:
  1. **Live Diagnostics (`textDocument/publishDiagnostics`)**: Surfaces syntax and type errors as in-editor squiggles on file open/save (`TextDocumentSyncKind.Full`).
  2. **Hover & Type Inspection (`textDocument/hover`)**: Displays inferred types, method signatures, and class hierarchy metadata.
  3. **Go to Definition (`textDocument/definition`)**: Jumps to declaring classes, methods, or fields across multi-file packages using the `Loader` and `TypeChecker` symbol index.
  4. **Code Completion (`textDocument/completion`)**: Context-aware member completions following `:` accessors, plus package symbols and keyword proposals.
- **IDE Integration**:
  - **JetBrains (PhpStorm, IntelliJ, CLion)**: Connects via IntelliJ Platform LSP API or the LSP4IJ plugin, pairing with the existing TextMate syntax highlighter bundle.
  - **VS Code**: Minimal extension wrapper launching `bin/speclsp`.
  - **Zed / Neovim / Helix**: Native zero-plugin configuration via standard editor LSP config.

---

## 5. Automated Installation & Linux Setup

A turnkey installation script (`install.sh`) to install Spec on Linux distributions:

### 5.1 Installation Script Workflow
1. **Prerequisite Verification**:
   - Detect presence of C compiler toolchain: `gcc` or `clang` (version checking for C11 support).
   - Verify `make`, `pthread`, and standard C development headers (`libc-dev`).
   - If missing, prompt with package manager commands (`apt-get install build-essential`, `dnf groupinstall "Development Tools"`, or `pacman -S base-devel`).
2. **Download & Build / Install**:
   - Fetch release archive or clone repository to `~/.spec/` (or `/usr/local/share/spec`).
   - Execute bootstrap convergence via `bootstrap.sh` to generate native `bin/spec`.
   - Build companion utilities: `bin/specunit`, `bin/speclint`, `bin/specinit`, `bin/specbuild`, `bin/speclsp`.
3. **Environment & PATH Integration**:
   - Place symlinks in `/usr/local/bin` (system-wide) or add `~/.spec/bin` to `~/.bashrc`, `~/.zshrc`, or `~/.profile`.
   - Register executables:
     - `spec`
     - `specunit`
     - `speclint`
     - `specinit`
     - `specbuild`
     - `speclsp`
4. **Verification**:
   - Run `spec --help` and compile a minimal test program to verify end-to-end functionality.

---

## 6. Cross-Platform Reliability & POSIX Abstraction

Spec compiles to C11, but the current runtime (`RuntimePrelude.spec`) and sysinternal floor (`spec/base/sysinternal/`) include direct POSIX and Linux-specific headers (`_GNU_SOURCE`, `sched.h`, `sys/ioctl.h`, `sys/wait.h`, `sys/resource.h`).

### 6.1 Audit & Isolation of Platform-Specific Primitives
- **Isolate System Dependencies**: Group all direct POSIX system calls into `sysinternal` modules with dedicated C shims rather than embedding them in general prelude code.
- **Platform Feature Detection**:
  - Replace hardcoded Linux headers with conditional compilation flags:
    ```c
    #if defined(__linux__)
        #define _GNU_SOURCE
        #include <sched.h>
    #elif defined(__APPLE__) && defined(__MACH__)
        #include <mach/mach_time.h>
        #include <sys/sysctl.h>
    #elif defined(_WIN32)
        #include <windows.h>
        #include <io.h>
    #endif
    ```

### 6.2 macOS / BSD Support
- Adapt process monitoring (`Process:peakMemoryKb()`) to query `getrusage(RUSAGE_SELF, ...)` portable fields or `sysctl` instead of Linux `/proc/self/status`.
- Abstract thread pinning / core count queries (`sched_getaffinity` on Linux vs `sysctl hw.ncpu` on macOS).
- Ensure terminal width/height queries in `Terminal.spec` cleanly handle BSD `TIOCGWINSZ`.

### 6.3 Windows (Win32) Roadmap Path
- Target **MinGW-w64** / **Clang on Windows** as the initial Windows compilation target.
- Map basic I/O and process execution primitives:
  - Memory: Windows `VirtualAlloc` / `HeapAlloc` backing `Arena.spec`.
  - Process: Win32 `CreateProcess` / `WaitForSingleObject` to provide fallback for `fork` / `exec` / `waitpid`.
  - Threading: C11 `<threads.h>` or Win32 threads alongside `pthread-win32`.

---

## 7. Alpha 0.1 Milestones & Execution Plan

| Milestone | Deliverables | Target Status |
|---|---|---|
| **M1: Core Solidification** | - Phase 0.5 instance-model worklist clean (`speclint -a` = 0) [Completed - `v0.000.100`]<br>- Modern unit testing framework extensions & negative test suite porting [Completed]<br>- On-demand precompiled C runtime accelerator (`~/.cache/spec/runtime/` with auto-purge on failure) [Completed]<br>- Compiler diagnostics & structured spans migration to `ErrorText.spec` [Completed] | Completed |
| **M2: Modular Linter** | - Refactor `speclint` with reflection-based `LintRule` discovery [Completed]<br>- Separate formatting, naming, and AST idiom rules into dedicated classes [Completed]<br>- Instance-model migration rules (`AsConditionalRule`, `AsLoopsRule`) [Completed]<br>- CLI rule filtering flags (`--rule` and `--disable`) [Completed] | Completed (`v0.000.100`) |
| **M3: Serialization & Tooling** | - Implement `base:data:Json` (JSON parser & stringifier) [Completed]<br>- Build `specinit` project scaffolder<br>- Build `specbuild` manifest-driven orchestrator (`specbuild.json`) [Completed]<br>- Build `speclsp` Language Server Protocol binary (Diagnostics, Hover, Definition, Completion)<br>- Implement shared TUI color/status module | In Progress |
| **M4: Platform & Packaging** | - Automated multi-platform release deployment (Linux, macOS, Windows bundles + source archive) [Completed]<br>- POSIX/OSX platform guards in runtime prelude<br>- Complete `install.sh` for Linux<br>- Standard library additions (Time, Sockets) | In Progress |
| **M5: 0.1 Alpha Release** | - Full documentation sweep<br>- Fixed-point bootstrap verification across GCC and Clang<br>- Tag `v0.1.0-alpha` and publish release tarballs | Planned |

---

*This document serves as the master planning guide for all work leading directly to the Spec 0.1 Alpha release.*

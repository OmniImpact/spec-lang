# Spec 0.1 Alpha Release Roadmap

This roadmap defines the core milestones, architectural cleanup tasks, tooling additions, and platform reliability goals required to take the **Spec Programming Language** to its first official release: **v0.1 Alpha**.

---

## 1. Vision & Release Objectives

The 0.1 Alpha release represents Spec's transition from an experimental self-hosting language to an accessible, reliable, and developer-ready systems language. The objectives for 0.1 Alpha are:

1. **Rock-Solid Self-Hosting Core**: Byte-identical compiler fixed point, deterministic C11 code generation, and 100% test-suite green status.
2. **First-Class Developer Tooling**: A complete command-line toolchain consisting of `spec` (compiler), `specunit` (test runner), `speclint` (linter), `specinit` (project initializer), and `specbuild` (build orchestrator).
3. **Turnkey Installation**: Zero-friction setup on Linux with automated dependency checks and environment configuration.
4. **Clean, Extensible Architecture**: Modular rule-based linting, unified error reporting, and a clear abstraction layer isolating POSIX/platform-specific runtime code.

---

## 2. Core Compiler & Language Cleanup

### 2.1 Finalize Phase 0.5 Instance-Model Migration
- **Status**: The instance-model audit (`speclint -a`) currently tracks remaining call sites where methods are invoked directly through uninstantiated class names.
- **Action Items**:
  - Migrate all remaining non-exempt call sites (e.g. `Conditional:dispatchScan` in `spec/lib/base/sys/Conditional.spec`) to instance calls or explicit `held` functions.
  - Verify `speclint -a -i spec/base/compiler/driver/Driver.spec` reports **0 call site(s) must migrate**.
  - Lock in the instance-model contract with strict typechecker enforcement preventing un-held class-receiver method dispatch.

### 2.2 Precompiled C Runtime Library (`libspecrt.a`)
- **Problem**: The compiler embeds the full C11 runtime prelude (~2,600 lines in `RuntimePrelude.spec`) into every generated C output file. This makes even a 20-line `helloworld.spec` produce ~8,600 lines of C and incurs a ~2.5s compilation penalty per build.
- **Action Items**:
  - Separate `RuntimePrelude.spec` into:
    1. A minimal runtime header (`spec_runtime.h`) containing type definitions, inline helpers, and function declarations.
    2. A static library (`libspecrt.a` / `libspecrt.so`) compiled once during bootstrap.
  - Update `spec/base/compiler/driver/Driver.spec` and `CodeGenerator.spec` to `#include <spec_runtime.h>` and link `-lspecrt` instead of emitting static C prelude text verbatim.
  - Target: Reduce single-file compile times from ~2,500ms down to **<100ms**.

### 2.3 Compiler Diagnostic & Error Centralization
- **Status**: `ErrorText.spec` exists as the centralized template vocabulary for compiler error messages, but several passes (`TypeChecker.spec`, `Parser.spec`, `Loader.spec`) still contain hardcoded inline string messages.
- **Action Items**:
  - Move all syntax, semantic, and type error strings into `spec/base/compiler/ErrorText.spec`.
  - Enhance `TypeError.spec` and `Error.spec` to carry structured `SourceLocation` spans (file, line, column, length) for source line snippets and caret squiggles.

### 2.4 Standard Library Expansion
- **Time & Clocks**: Provide a high-resolution time module (`base:sys:Time`) with ISO-8601 formatting, duration arithmetic, and nanosecond/microsecond clocks (expanding beyond `Process:clockMs()`).
- **Data Serialization**: Add lightweight, native JSON parsing and serialization (`base:data:Json`) for data interchange.
- **Basic Networking / Sockets**: Abstract stream sockets (`base:sys:Socket`, TCP client/server) over the sysinternal floor.
- **Collections**: Ensure `List`, `Array`, and `Map` have consistent API parity across iterations, slicing, filtering, and mutations.

---

## 3. Modular, Reflection-Based Linter (`speclint`)

Currently, `Linter.spec` operates as a single monolithic visitor enforcing style and AST rules. For 0.1 Alpha, `speclint` will be refactored into a pluggable, reflection-driven engine mirroring the design of `SpecUnitRunner`.

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

To provide a complete developer workflow out of the box, three new utilities will accompany `spec` and `specunit`:

```
   +-----------------------------------------------------------------+
   |                           SPEC CLI                              |
   +-----------------+-------------------+-------------------+-------+
   |  specinit       |  specbuild        |  spec             |  speclint / specunit
   |  (Scaffolding)  |  (Orchestration)  |  (Compiler)       |  (Quality Assurance)
   +-----------------+-------------------+-------------------+-------+
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
A lightweight, fast build coordinator (`utilities/specbuild/SpecBuild.spec`) to eliminate ad-hoc shell compile scripts:
- **Manifest (`specbuild.json`)**:
  ```json
  {
    "name": "my_project",
    "version": "0.1.0",
    "type": "binary",
    "entry": "src/Main.spec",
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
  - `specbuild`: Reads `specbuild.json`, invokes `spec -i <entry> -o <output>` with configured source trees and dependencies.
  - `specbuild test`: Automatically delegates to `specunit` with configured test roots.
  - `specbuild lint`: Automatically runs `speclint` across all defined `source_dirs`.
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
   - Build companion utilities: `bin/specunit`, `bin/speclint`, `bin/specinit`, `bin/specbuild`.
3. **Environment & PATH Integration**:
   - Place symlinks in `/usr/local/bin` (system-wide) or add `~/.spec/bin` to `~/.bashrc`, `~/.zshrc`, or `~/.profile`.
   - Register executables:
     - `spec`
     - `specunit`
     - `speclint`
     - `specinit`
     - `specbuild`
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
| **M1: Core Solidification** | - Phase 0.5 instance-model worklist clean (`speclint -a` = 0)<br>- All compiler errors migrated to `ErrorText.spec`<br>- Runtime prelude split into `spec_runtime.h` + static `libspecrt.a` | Planned |
| **M2: Modular Linter** | - Refactor `speclint` with reflection-based `LintRule` discovery<br>- Separate formatting, naming, and AST idiom rules into dedicated classes<br>- CLI rule filtering flags | Planned |
| **M3: Project Tooling** | - Build `specinit` project scaffolder<br>- Build `specbuild` manifest-driven orchestrator (`specbuild.json`)<br>- Implement shared TUI color/status module | Planned |
| **M4: Platform & Packaging** | - POSIX/OSX platform guards in runtime prelude<br>- Complete `install.sh` for Linux<br>- Standard library additions (Time, basic Json) | Planned |
| **M5: 0.1 Alpha Release** | - Full documentation sweep<br>- Fixed-point bootstrap verification across GCC and Clang<br>- Tag `v0.1.0-alpha` and publish release tarballs | Planned |

---

*This document serves as the master planning guide for all work leading directly to the Spec 0.1 Alpha release.*

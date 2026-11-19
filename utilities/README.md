# Utilities

All Spec developer tooling is written in pure Spec and built into `bin/`:

- **`specunit/`**: Parallel unit & integration test runner with Cleo TUI, decoupled compile/run scheduling, per-test timeouts, and inline negative-case parallelism (`bin/specunit -s bin/spec -t test -t testcompiler`).
- **`speclint/`**: Modular, reflection-driven code standards linter with Cleo summary output (`bin/speclint -i <file>` or `bin/speclint -t <dir>`).
- **`specbuild/`**: Manifest-driven build orchestrator (`specbuild.json`) with Cleo build summaries (`bin/specbuild <manifest.json>`).
- **`specinit/`**: Project scaffolder for new Spec apps and libraries.
- **`speclsp/`**: JSON-RPC 2.0 Language Server Protocol implementation for IDE diagnostics and navigation.
- **`benchmarks/` & `run_benchmarks.sh`**: Reproducible cross-language benchmark suite (`mc_pi`, `binary_trees`, `word_freq`) with pure-Spec measurement wrapper (`Measure.spec`). See [`README-PERFORMANCE.md`](../README-PERFORMANCE.md).
- **`spec-gdb.py`, `spec-dap.py`, `textmate/`, `spec-kate.xml`**: Debugger pretty-printers and editor syntax definitions.

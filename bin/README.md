# Spec Executables (`bin/`)

This directory holds the native binaries built from the canonical bootstrap C seed and Spec utility sources. Binaries are not tracked in git.

## 1. Initial Step: Bootstrap the Spec Compiler

Spec is a self-hosting programming language. The canonical C11 seed is tracked at `bootstrap/spec.c`.

To build the native `spec` compiler binary and verify the self-hosting fixed point:

```bash
./bootstrap.sh
```

Or using an alternate C compiler (such as Clang):

```bash
CC=clang ./bootstrap.sh
```

This compiles `bootstrap/spec.c` into `bin/spec` via GCC/Clang and verifies byte-for-byte convergence.

## 2. Build the SpecBuild Project Orchestrator

Once `bin/spec` is built, compile `specbuild`:

```bash
bin/spec --quiet -i utilities/specbuild/SpecBuild.spec -o bin/specbuild
```

## 3. Build Binaries via SpecBuild

Use `bin/specbuild` with each project manifest to build native binaries:

### Build the Spec Compiler (`spec`)
```bash
bin/specbuild spec/spec.json
```

### Build the SpecUnit Test Runner (`specunit`)
```bash
bin/specbuild utilities/specunit/specunit.json
```

### Build the SpecLint Linter (`speclint`)
```bash
bin/specbuild utilities/speclint/speclint.json
```

### Build the SpecBuild Project Orchestrator (`specbuild`)
```bash
bin/specbuild utilities/specbuild/specbuild.json
```

### Complete Tooling Build Sequence
```bash
bin/spec --quiet -i utilities/specbuild/SpecBuild.spec -o bin/specbuild && \
bin/specbuild spec/spec.json && \
bin/specbuild utilities/specunit/specunit.json && \
bin/specbuild utilities/speclint/speclint.json
```

## 4. Verify

Run the full regression test suite:
```bash
bin/specunit -s bin/spec -t tests
```

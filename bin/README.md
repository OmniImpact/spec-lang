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

## 2. Produce Tooling Binaries

Once `bin/spec` is built, produce the developer utilities directly from their Spec sources:

### Build the SpecUnit Test Runner (`specunit`)
```bash
bin/spec -i utilities/specunit/SpecUnit.spec -o bin/specunit
```

### Build the SpecLint Linter (`speclint`)
```bash
bin/spec -i utilities/speclint/SpecLint.spec -o bin/speclint
```

### Build the SpecBuild Project Orchestrator (`specbuild`)
```bash
bin/spec -i utilities/specbuild/SpecBuild.spec -o bin/specbuild
```

### Build All Tooling in One Step
```bash
bin/spec -i utilities/specunit/SpecUnit.spec -o bin/specunit && \
bin/spec -i utilities/speclint/SpecLint.spec -o bin/speclint && \
bin/spec -i utilities/specbuild/SpecBuild.spec -o bin/specbuild
```

## 3. Verify
Run the full regression test suite:
```bash
bin/specunit -s bin/spec -t tests
```

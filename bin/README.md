# Spec Executables (`bin/`)

This directory holds the native binaries built from the canonical bootstrap C seed and Spec utility sources. Binaries are not tracked in git.

Building the full toolchain starts from zero (no pre-existing binaries):

## 1. Initial Step: Bootstrap the Spec Compiler

Spec is a self-hosting programming language. The canonical C11 seed is tracked at `bootstrap/spec.c`.

To build the native `spec` compiler binary from source and verify the self-hosting fixed point:

```bash
./bootstrap.sh
```

Or using an alternate C compiler (such as Clang):

```bash
CC=clang ./bootstrap.sh
```

This compiles `bootstrap/spec.c` into `bin/spec` via GCC/Clang and verifies byte-for-byte convergence.

## 2. Build the SpecBuild Project Orchestrator

Once `bin/spec` is built, use it to compile `specbuild`:

```bash
bin/spec --quiet -i utilities/specbuild/SpecBuild.spec -o bin/specbuild
```

## 3. Build Tooling Binaries via SpecBuild

Now that `bin/specbuild` is available, use it with each tool's manifest to build `specunit` and `speclint`:

### Build the SpecUnit Test Runner (`specunit`)
```bash
bin/specbuild utilities/specunit/specunit.json
```

### Build the SpecLint Linter (`speclint`)
```bash
bin/specbuild utilities/speclint/speclint.json
```

### Complete Tooling Build Sequence
From zero to complete toolchain:
```bash
./bootstrap.sh && \
bin/spec --quiet -i utilities/specbuild/SpecBuild.spec -o bin/specbuild && \
bin/specbuild utilities/specunit/specunit.json && \
bin/specbuild utilities/speclint/speclint.json
```

*(Note: SpecBuild manifests are also provided for `spec` at [`spec/spec.json`](../spec/spec.json) and `specbuild` at [`utilities/specbuild/specbuild.json`](../utilities/specbuild/specbuild.json) for convenient subsequent rebuilds.)*

## 4. Verify

Run the full regression test suite:
```bash
bin/specunit -s bin/spec -t tests
```

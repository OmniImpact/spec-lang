# Spec for JetBrains IDEs

JetBrains plugin for the **Spec** programming language, compatible with **PhpStorm**, **Android Studio**, **Rider**, **IntelliJ IDEA**, and **CLion** (build `242+`).

## Prerequisites

1. **Install LSP4IJ** in your JetBrains IDE before installing this plugin:
   - Open **Settings / Preferences -> Plugins -> Marketplace**
   - Search for **LSP4IJ** (by Red Hat) and install it, then restart the IDE.
2. **Java 21+** (for building the plugin with Gradle).
3. **GDB 14+** (`gdb -i dap`) for source-level `.spec` debugging.
4. **Clang toolchain** (`clang`, `make`) if `../bin/spec` and the Spec utilities have not been built yet.

## Building the Plugin

From the `jetbrains/` directory:

```bash
./gradlew buildPlugin
```

During the build, Gradle automatically:
1. Checks `../bin/` for `spec`, `speclsp`, `specbuild`, `specunit`, and `speclint`.
2. Runs `../bootstrap.sh` if `../bin/spec` is missing, then compiles any missing utility binaries.
3. Packages the plugin `.zip` in `jetbrains/build/distributions/spec-jetbrains-*.zip`, bundling the `bin/` executables and the `spec/` standard library.

## Installing Manually

1. Open **Settings / Preferences -> Plugins**.
2. Click the gear icon -> **Install Plugin from Disk...**
3. Select `jetbrains/build/distributions/spec-jetbrains-*.zip`.
4. Restart the IDE.

## Current Features

- `.spec` file type, `#` line commenting, and bundled TextMate syntax highlighting
- **LSP4IJ** integration backed by `speclsp` (diagnostics, hover, go-to-definition, completion)
- `specbuild.json` Run/Build/Test/Clean configurations (`SpecBuild`) with context-menu run producer
- **DAP Debugger** via LSP4IJ (`Spec Debugger (GDB DAP)`), compiling `.spec` files with `spec --debug` and launching `gdb -i dap` with `spec-gdb.py`

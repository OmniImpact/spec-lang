# Spec Dependencies

This document lists what is required on each platform to bootstrap the Spec compiler (`./bootstrap.sh`), build the standard tooling (`specbuild`, `specunit`, `speclint`, `specinit`, `speclsp`), and run standard-library features.

---

## 1. Core Bootstrap & Standard Library Build

Spec bootstraps from `bootstrap/spec.ll` and `bootstrap/spec_runtime.c` using `clang` (no external LLVM toolchain installation, CMake, or Python is required).

### Linux (`x86_64`, `arm64`)

- **Compiler & linker**: `clang` (with standard C library headers, `pthreads`, `libm`, `libdl`)
- **Shell & file comparison**: `bash`, `cmp` or `diff` (`diffutils`), `coreutils`
- **Linker flags used by Spec** (`bootstrap.sh` & `bin/spec`): `-pthread -lm -ldl -no-pie`

Example (Debian / Ubuntu):
```bash
sudo apt-get update && sudo apt-get install -y clang diffutils
CLANG=clang ./bootstrap.sh
```

### macOS (`arm64`, `x86_64`)

- **Compiler & linker**: Apple `clang` (via Xcode Command Line Tools: `xcode-select --install`)
- **Shell & file comparison**: `bash`, `cmp` or `diff` (included with macOS)
- **Frameworks & linker flags used by Spec**: `-pthread -lm -framework AudioToolbox`

```bash
CLANG=clang ./bootstrap.sh
```

### Windows (`x86_64` via MSYS2 UCRT64)

- **Environment**: [MSYS2](https://www.msys2.org/) using the **UCRT64** subsystem
- **Packages**:
  - `mingw-w64-ucrt-x86_64-clang`
  - `diffutils`
  - `git` (if cloning from source)
- **Win32 import libraries linked by Spec**: `-pthread -lm -lws2_32 -lwinmm -lpsapi`

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-clang diffutils
CLANG=clang ./bootstrap.sh
```

---

## 2. Building the Standard Tooling & Running Tests

Once `./bootstrap.sh` completes and produces `bin/spec`:

```bash
bin/spec --quiet -i utilities/specbuild/SpecBuild.spec -o bin/specbuild
bin/specbuild utilities/specunit/specunit.json
bin/specbuild utilities/speclint/speclint.json
bin/specbuild utilities/specinit/specinit.json
bin/specbuild utilities/speclsp/speclsp.json
bin/specunit -s bin/spec -t test -t testcompiler
```

*(On Windows, use `bin/spec.exe` and `bin/specbuild.exe` / `bin/specunit.exe`.)*

---

## 3. Optional Runtime Libraries (Loaded Dynamically)

The following standard-library subsystems load platform libraries dynamically at runtime (`dlopen` / OS frameworks). **They are not required at compile time or bootstrap time**, so CI and headless environments can still bootstrap and build everything without installing `-dev` packages.

| Subsystem | Platform | Runtime Requirement |
| :--- | :--- | :--- |
| **Audio** (`base:audio`, `base:sys:AudioDevice`) | Linux | `libasound.so.2` (ALSA runtime, e.g. `libasound2`) |
| | macOS | `AudioToolbox.framework` (built-in) |
| | Windows | `winmm.dll` (built-in) |
| **Windowing** (`base:suit`, `base:sys:Window`) | Linux | `libwayland-client.so.0`, `libdecor-0.so.0`, and an active Wayland compositor (`WAYLAND_DISPLAY`) |
| **Vulkan 3D Surface** (`base:scrap:VulkanSurface`, `base:sys:Vulkan`) | Linux | `libvulkan.so.1` (Vulkan loader) and a Vulkan ICD (GPU driver or Mesa Lavapipe software rasterizer). No `libvulkan-dev` headers or `glslc` compiler required. |
| **Networking** (`base:net`) | All | Standard OS sockets (`libc` on Linux/macOS, `ws2_32` on Windows) |

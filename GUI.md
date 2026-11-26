# Spec GUI Architecture (Draft)

> **Status:** Architectural draft on `feature/gui` — establishing module boundaries before building out the full toolkit.

## Module Overview

Spec's native GUI stack is split into four focused layers, inspired by Rust's modular GUI ecosystem (`winit`, `softbuffer`/`wgpu`, `tiny-skia`/`vello`, `fontdue`, `taffy`, `iced`/`xilem`):

| Module | Package | Responsibility |
|---|---|---|
| **Suit** | `base:suit` | Platform windowing, event loop, input normalization, and OS surface/present abstraction |
| **Fabric** | `base:fabric` | 2D rendering pipeline (vector paths, SDF shapes, text rasterization, glyph atlas) and **Theme** sub-component |
| **Sew** | `base:sew` | First-generation two-pass constraint layout engine |
| **Mold** | `base:mold` | 3D graphics & SPIR-V helper package (matrices, cameras, meshes, SPIR-V bytecode utilities) |
| **Scrap** | `base:scrap` | Collection of surface components (`PixelBuffer`, `VulkanSurface`) and reusable widgets |

---

## Layer Breakdown

### 1. Suit (`base:suit`) — Windowing, Events & Present
- **Window management:** Native window creation, title, size, decorated/borderless modes, cursor shapes, clipboard, and HiDPI scale factor (Linux Wayland + `libdecor` first; Win32 and macOS Cocoa behind the same `base:sys:Window` floor later).
- **Event loop:** Event-driven poll/wait with `requestRedraw()` scheduling and a typed `SuitEvent` stream (`Resized`, `CloseRequested`, `KeyDown`/`KeyUp`, `TextInput`, `PointerMove`, `PointerDown`/`Up`, `Scroll`, `FocusChanged`).
- **Surface / Present abstraction:**
  - `SuitSurface` interface decoupling rendering from presentation.
  - Software CPU present (`wl_shm` double-buffered swap on Wayland; `StretchDIBits` / `CGContext` later).
  - Native handle exposure (`wl_display` + `wl_surface`, `HWND`, `CAMetalLayer`) for Vulkan surface creation.

### 2. Fabric (`base:fabric`) — Rendering Pipeline & Theme
- **2D Vector & Shape Engine:**
  - `DrawContext` / `Painter` interface targeting CPU pixel buffers now and Vulkan later.
  - Clipping stack (`pushClip` / `popClip`, rounded-rect clipping).
  - Analytic SDF primitives (rounded rectangles, borders, soft shadows), gradients, and alpha-blended image blitting.
  - Vector paths (`moveTo`, `lineTo`, `quadTo`, `cubicTo`, `close`) with scanline anti-aliased fill/stroke rasterization.
- **Text Pipeline:**
  - Font loading and glyph rasterization (`base:sys:Font` / `stb_truetype` initially).
  - Glyph atlas caching (keyed by font, pixel size, and glyph ID).
  - `TextLayout` for measurement, line wrapping, cursor positioning, and selection bounds.
- **Theme Engine (`Fabric:Theme`):**
  - Sub-component of `Fabric` owning visual tokens: color palette, typography scale, border widths, corner radii, shadows, and state styles (normal/hover/active/disabled/focused).

### 3. Sew (`base:sew`) — Layout Engine
- **Two-pass constraint layout:**
  1. **Measure pass:** Parent provides `(minW, maxW, minH, maxH)` constraints; child returns desired `Size(w, h)`.
  2. **Arrange pass:** Parent assigns final `Rect(x, y, w, h)` to each child.
- **Core containers:** `Row`, `Col`, `Stack` (z-order overlay), `Padding`, `Spacer`/`Flex`, `Grid`, and `ScrollView`.
- **Headless testability:** Pure geometry and constraints; text measurement is injected via an interface so `Sew` can be tested without a window.

### 4. Mold (`base:mold`) — 3D Graphics & SPIR-V Helpers
- **SPIR-V bytecode utilities:** Constructing, loading (from `Bundle` `.spv` or pure-Spec word arrays), and validating SPIR-V shader modules without requiring an external `glslc` compiler at runtime.
- **3D math & transforms:** `Mat4` (perspective projection, `lookAt`, translation, rotation, scale), `Vec3`/`Vec4`, and push-constant buffer packing.
- **Geometry & meshes:** Vertex/index buffer builders (`CubeMesh`, color/normal attributes) and material/pipeline descriptors for GPU rendering via Vulkan.

### 5. Scrap (`base:scrap`) — Surface Components & Widgets
- **Initial foundation components:**
  - **`PixelBuffer`:** Managed `ARGB8888` pixel-buffer component/viewport for direct CPU rendering (e.g., fractal/canvas demos) that composes inside a `Sew` layout or full-window frame.
  - **`VulkanSurface`:** Native Vulkan surface/swapchain component (`VkSurfaceKHR`) integrated into `Suit`'s window handles and `Sew`'s layout bounds.
- **Core widgets (subsequent iterations):**
  - `Label`, `Button`, `Panel`, `TextInput`, `Checkbox`, `Slider`, `ScrollView`, `ListView` (virtualized).

---

## Dependency Direction

```text
  base:sys (Window, Font, Mem, Simd, Thread, Vulkan)
      ▲
      │
    Suit  (OS window, event loop, SuitSurface)
      ▲
      │
   Fabric (Vector, Text, Theme) ◄──── Sew (Constraint Layout)
      ▲                                ▲
      │         Mold (3D, SPIR-V) ─────┤
      │                ▲               │
      └────────────────┴───────┬───────┘
                               │
                             Scrap (PixelBuffer, VulkanSurface, Widgets)
```

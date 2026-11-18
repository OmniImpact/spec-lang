# CLEO — Command Line Enhanced Output

> **Status:** Design Specification (Ideation)  
> **Target Package:** `base:cleo` (or `base:sys:Cleo` + supporting `base:cleo:*` types)

**Cleo** (*Command Line Enhanced Output*) is a structured terminal output library for Spec that sits between plain line-by-line printing (`Output:line`) and a full-screen alternate-buffer TUI.

Instead of taking over the entire terminal with an alternate screen buffer, Cleo manages an **inline, indexed output buffer** directly in the user's normal terminal scrollback. You append entries (text rows, throbbers, progress areas, dividers, or ASCII/TrueColor image blocks), receive or assign an index/key, and update any entry in place as events occur.

---

## 1. Design Goals

1. **Inline by default**: Output lives naturally in the terminal stream. When a task finishes, its final rendered state remains visible in scrollback rather than vanishing on exit.
2. **Indexed, mutable buffer**: Every item added to a Cleo surface has a stable slot index (or string key). Updating slot `3` rewrites only what changed on screen—no manual `\r` or cursor math in user code.
3. **Composable presentation**: Built-in support for configurable outside borders, inner dividers, semantic/RGB colors, animated throbbers, multi-line ASCII/pixel-block images, and a dedicated **two-stage overlaid progress area**.
4. **Responsive sizing**: Target output width can be expressed as a **percentage of terminal width** (`percent`) or in **pixels** (`px`)—with explicit column (`cols`) support as the underlying terminal unit.
5. **Graceful degradation**: Automatically adapts when stdout is not a TTY (CI logs, file redirection) by disabling cursor rewrites and emitting clean, readable milestone output.

---

## 2. Core Mental Model

```text
┌─ Build Pipeline ───────────────────────────────────────────────┐  <-- Frame Title (titleColor / titleBgColor) + Outside Border
│ ⠸ Compiling IrBuilder.spec                              [1.4s] │  <-- Section 0: Workers (section fg/bg)
│ ✔ Linked runtime prelude                                [0.2s] │
├─ Stage Summary ────────────────────────────────────────────────┤  <-- Section 1 Title + Inside Divider
│ Linking stage: verifying bitcode & emitting object files...    │  <-- Section 1: Progress Area (independent fg/bg)
│ ████████████████████▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░  40% / 66% │
└────────────────────────────────────────────────────────────────┘
```

A `Cleo` instance maintains:

- **Committed History** *(optional)*: Completed lines/blocks flushed permanently above the live region via `commit()`, freeing viewport height so long-running jobs never overflow the terminal screen.
- **Stacked Sections**: One or more vertical content blocks separated by dividers, each with its own optional title (with title foreground/background color) and section-level foreground/background colors.
- **Live Indexed Buffer**: An ordered list of slots (`0..N-1`) across sections, optionally addressable by string key (`'download'`, `'preview'`, etc.).
- **Dirty-Row Tracker + Diff Renderer**: Tracks which lines changed since the last flush, moves the cursor relative to the bottom of the live region, rewrites only dirty lines (wrapped in DEC Synchronized Output `\e[?2026h ... \e[?2026l` when supported), and parks the cursor cleanly below the frame.

---

## 3. Configuration & Styling Model

### 3.1 Border & Divider Styles

Both the **outside border** and **inside dividers** are configured independently using a `BorderStyle` enum (or custom glyph set):

| Style | Outside Frame Preview | Inside Divider Preview |
|---|---|---|
| `None` | *(no border)* | *(blank line or omitted)* |
| `Ascii` | `+---+` / `\|   \|` / `+---+` | `+---+` or `-----` |
| `Thin` | `┌───┐` / `│   │` / `└───┘` | `├───┤` / `─────` |
| `Thick` | `┏━━━┓` / `┃   ┃` / `┗━━━┛` | `┣━━━┫` / `━━━━━` |
| `Double` | `╔═══╗` / `║   ║` / `╚═══╝` | `╠═══╣` / `═════` |
| `Rounded` | `╭───╮` / `│   │` / `╰───╯` | `├───┤` / `─────` |
| `Dashed` | `┌╌╌╌┐` / `┆   ┆` / `└╌╌╌┘` | `├╌╌╌┤` / `╌╌╌╌╌` |

Custom border sets can also be supplied via `BorderGlyphs` (top-left, top, top-right, left, right, bottom-left, bottom, bottom-right, divider-left, divider-mid, divider-right).

### 3.2 Colors

Cleo defines a unified `CleoColor` value type that maps cleanly onto `base:sys:Ansi`:

- `CleoColor:default()` — terminal default foreground/background
- `CleoColor:ansi(Int is code)` — standard 16-color / 256-color palette index (`0..255`)
- `CleoColor:rgb(Int is r, Int is g, Int is b)` — 24-bit TrueColor
- Semantic presets in `CleoStyle`: `info`, `success`, `warn`, `error`, `muted`, `accent`

Colors can be assigned to:
- `borderColor` (outside frame)
- `dividerColor` (inside separators)
- `titleColor` & `titleBgColor` (frame title text foreground & background)
- Per-section defaults (`fgColor`, `bgColor`, `titleColor`, `titleBgColor`) — section background fills the entire inner width of every row in that section
- Per-slot foreground/background and bold/dim attributes (mutable at any time via `setColor` / `update`, overriding the section default)

### 3.3 Target Width (`percent`, `px`, `cols`)

Cleo resolves target width dynamically before rendering:

```text
CleoWidth:percent(Int is pct)   # e.g. 80 -> 80% of Ansi:terminalWidth(), clamped to [minCols, termWidth]
CleoWidth:px(Int is pixels)     # e.g. 720 -> converted to columns using cell pixel width (see §7.2)
CleoWidth:cols(Int is count)    # e.g. 100 -> exact column count, clamped to termWidth
```

- **Minimum / maximum bounds**: `minWidthCols` (e.g., `24`) and `maxWidthCols` prevent frames from collapsing on narrow splits or stretching unreadably across ultrawide terminals.
- **Overflow policy per slot**: `truncateEllipsis` (`...`), `wrap` (multi-line auto-height within the slot), or `clip`.

### 3.4 Titles & Stacked Sections

A Cleo surface can contain a single implicit content block or multiple **stacked sections** (`CleoSection`), separated automatically by the configured `dividerBorder`:

- **Frame & Section Titles**:
  - `title`: Optional title text for the outer frame (top border) or for each individual section.
  - `titleColor` & `titleBgColor`: Independent foreground and background colors for the title badge/banner (e.g., inverted pill `bg: blue, fg: white`).
  - `titleAlign`: `Left`, `Center`, or `Right`.
  - `titlePlacement`: `InlineBorder` (embedded directly into the top border or section divider line, e.g. `├─ Metrics ─┤`) or `HeaderRow` (a dedicated full-width title bar inside the section, padded with `titleBgColor`).
- **Per-Section Colors**:
  - Each section accepts `fgColor` and `bgColor` (inheriting from `Cleo` defaults if unset).
  - Background color is painted across the full interior column width of every row in the section, allowing visually distinct bands (e.g., dark slate for logs, navy for active workers, muted gray for summary).
  - Both section titles and section colors can be mutated live (`section:setTitle(...)`, `section:setColors(fg: ..., bg: ...)`).

---

## 4. Built-In Components & Slot Types

### 4.1 Text & Status Rows
- Single-line or wrapped multi-line text with alignment (`left`, `center`, `right`) and optional right-hand metadata column (e.g., elapsed time or item count).
- Mutable text, color, and attributes by slot index or key.

### 4.2 Throbbers (Spinners, Blinking & Color-Changing Shapes)
Throbbers support both classic multi-frame spinners and single-shape animated indicators:

- **Spinning frame sets (`ThrobberStyle`)**: `Braille` (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`), `Dots`, `Line` (`-\|/`), `Blocks` (`▖▘▝▗`), `Bounce`, or custom `Array of String` frames.
- **Standard shapes (`ThrobberShape`)**: `Dot` (`●` / `•`), `Circle` (`●` / `○` / `◉`), `Diamond` (`◆` / `◇`), `Square` (`■` / `□`), `Star` (`★` / `☆`), `Triangle` (`▲` / `△`), or `AsciiDot` (`*` / `o` / ` `).
- **Animation effects (`ThrobberEffect`)**:
  - `Spin`: cycles through the glyph frames on each tick.
  - `Blink`: alternates a shape between on/filled and off/hollow (or dim/space) at a configurable cadence—implemented via Cleo's timer rather than ANSI `\e[5m`, so it works reliably across all terminal emulators.
  - `ColorCycle`: steps or smoothly interpolates the shape's foreground through an `Array of CleoColor` palette (e.g., cycling hues or pulsing between two RGB colors for a breathing effect).
  - `BlinkAndColor`: combines blinking (or filled/hollow alternation) with color cycling on each beat.
- **Lifecycle**: Driven either manually (`tick()`) or automatically via a background `Time:setInterval` timer when `start()` is active, and transitions cleanly to a static completion badge (`✔`, `✘`, `!`) when resolved.

### 4.3 Two-Stage Overlaid Progress Area
A dedicated composite block containing:
1. **Text block**: Primary status message (1 or more wrapped/truncated lines) plus optional secondary detail/percentage readout.
2. **Two-stage overlaid progress bar**:
   - **Stage 1 (Primary / Foreground)** — represents completed/verified work (e.g., extracted, compiled, flushed). Rendered with solid fill (`█`) in `stage1Color`.
   - **Stage 2 (Secondary / Background)** — represents buffered/in-flight/downloaded work ahead of Stage 1. Rendered where `stage2 > stage1` using a distinct fill (`▓` or `▒`) and `stage2Color`.
   - **Track (Remaining)** — unfilled portion (`░` or `─`) in `trackColor`.

```text
Example: stage1 = 0.42 (Compiled), stage2 = 0.75 (Parsed)

  Compiling project modules (42/100 compiled, 75/100 parsed)
  ████████████████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░  42% (75%)
  ^----- Stage 1 ----^^--- Stage 2 ---^^-- Track --^
```

Invariant: `stage1` is clamped to `[0.0, 1.0]`, `stage2` is clamped to `[stage1, 1.0]` (or rendered independently if `allowIndependentStages` is enabled, though overlaid progress typically enforces `stage2 >= stage1`).

### 4.4 ASCII & Half-Block Image Slots
A multi-line fixed-aspect or dynamically sized grid slot that can be updated in place without tearing:
- **Plain / Colored ASCII art**: `Array of String` lines (e.g., status diagrams, waveforms, sparklines, logos).
- **24-bit Half-Block Pixel Buffer (`CleoImage`)**: Stores an `Rgba`/`Rgb` pixel grid of width `W` × height `2*H`, rendered using Unicode upper/lower half blocks (`▀` / `▄`) with `fgRgb` for the top pixel and `bgRgb` for the bottom pixel—giving **2 vertical pixels per terminal row** in any TrueColor terminal.

---

## 5. Conceptual API & Spec Examples

> **Note:** The examples below illustrate the proposed API in Spec syntax. Exact namespace placement (`base:cleo` vs `base:sys`) is open to refinement before implementation.

### Example 1: Indexed Buffer with Live Status & Color Transitions

```spec
Class is BuildRunner{
	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoStyle],
		['base', 'cleo', CleoColor],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'sys', Time]
	];

	Function is run(){
		local Cleo is out: Cleo:init(
			title: 'Spec Build',
			width: CleoWidth:percent(pct: 80),
			outerBorder: BorderStyle:Rounded,
			dividerBorder: BorderStyle:Thin,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 238)
		);

		out:start();

		# Add indexed rows; Cleo prints them immediately and tracks their positions
		local Int is sLexer:  out:addThrobber(text: 'Lexing sources...', color: CleoColor:ansi(code: 39));
		local Int is sParser: out:addShapeThrobber(
			shape: ThrobberShape:Diamond,
			effect: ThrobberEffect:BlinkAndColor,
			palette: [
				CleoColor:rgb(r: 80, g: 180, b: 255),
				CleoColor:rgb(r: 160, g: 120, b: 255),
				CleoColor:rgb(r: 255, g: 140, b: 100)
			],
			text: 'Parsing AST...'
		);
		local Int is sEmit: out:addShapeThrobber(
			shape: ThrobberShape:Circle,
			effect: ThrobberEffect:Blink,
			color: CleoColor:ansi(code: 245),
			text: 'Waiting to emit LLVM IR...'
		);

		Time:sleepMs(ms: 400);
		out:resolveSlot(index: sLexer, badge: '✔', text: 'Lexed 42 files (0.4s)', color: CleoColor:ansi(code: 42));

		out:updateText(index: sParser, text: 'Parsing AST (18,400 nodes)...');
		out:setColor(index: sParser, color: CleoColor:ansi(code: 39));

		Time:sleepMs(ms: 500);
		out:resolveSlot(index: sParser, badge: '✔', text: 'Parsed AST (0.5s)', color: CleoColor:ansi(code: 42));

		# Change color to warning/yellow, then error/red or green
		out:updateText(index: sEmit, text: 'Emitting LLVM IR with 1 warning');
		out:setColor(index: sEmit, color: CleoColor:ansi(code: 214));

		out:finish();
	}
}
```

### Example 2: Double/Thick Borders + Two-Stage Overlaid Progress Area

```spec
Function is downloadAndVerify(){
	local Cleo is out: Cleo:init(
		title: 'Artifact Sync',
		width: CleoWidth:px(pixels: 760),
		outerBorder: BorderStyle:Double,
		dividerBorder: BorderStyle:Thick,
		borderColor: CleoColor:rgb(r: 90, g: 160, b: 255),
		dividerColor: CleoColor:rgb(r: 60, g: 90, b: 140)
	);

	local Int is header: out:addLine(text: 'Target: spec-v0.9-linux-x86_64.tar.zst');
	out:addDivider();

	# Built-in Progress Area: text block + two-stage overlaid bar
	local Int is prog: out:addProgressArea(
		text: 'Fetching chunks from mirror...',
		stage1Color: CleoColor:rgb(r: 46, g: 204, b: 113),   # Green: verified
		stage2Color: CleoColor:rgb(r: 52, g: 152, b: 219),   # Blue: downloaded
		trackColor:  CleoColor:ansi(code: 237),
		showTwoStagePercent: true
	);

	out:start();

	local Int is step: 0;
	while({ step <= 100 }, {
		local Float is downloaded: step / 100.0;
		local Float is verified: if({ step > 20 }, { (step - 20) / 80.0 }, { 0.0 });

		out:updateProgress(
			index: prog,
			text: "Downloading & verifying SHA-256 chunks ({step}/100)...",
			stage1: verified,
			stage2: downloaded
		);
		Time:sleepMs(ms: 35);
		step: step + 2;
	});

	out:updateProgress(
		index: prog,
		text: 'All chunks verified and unpacked.',
		stage1: 1.0,
		stage2: 1.0
	);
	out:finish();
}
```

### Example 3: Updating an ASCII / Half-Block Image Slot In-Place

```spec
Function is renderLiveHeatmap(){
	local Cleo is out: Cleo:init(
		title: 'Thermal / Load View',
		width: CleoWidth:percent(pct: 60),
		outerBorder: BorderStyle:Thick,
		dividerBorder: BorderStyle:Dashed
	);

	# Create a 32x12 pixel canvas -> renders as 32 cols x 6 terminal rows using ▀/▄
	local CleoImage is canvas: CleoImage:init(pixelWidth: 32, pixelHeight: 12);
	local Int is imgSlot: out:addImage(image: canvas);
	out:addDivider();
	local Int is captionSlot: out:addLine(text: 'Frame 0 | Peak: 0%');

	out:start();

	local Int is frame: 0;
	while({ frame < 30 }, {
		# Mutate pixels in canvas (e.g., setPixel(x, y, r, g, b))
		local Int is x: 0;
		while({ x < 32 }, {
			local Int is y: 0;
			while({ y < 12 }, {
				local Int is v: ((x * 7 + y * 13 + frame * 11) % 255);
				canvas:setPixel(x: x, y: y, r: v, g: 80, b: 255 - v);
				y: y + 1;
			});
			x: x + 1;
		});

		out:updateImage(index: imgSlot, image: canvas);
		out:updateText(index: captionSlot, text: "Frame {frame} | Live half-block canvas");
		Time:sleepMs(ms: 50);
		frame: frame + 1;
	});

	out:finish();
}
```

### Example 4: Stacked Sections with Per-Section Titles & Colors

```spec
Function is showDashboard(){
	local Cleo is out: Cleo:init(
		title: ' Deployment Console ',
		titleColor: CleoColor:rgb(r: 255, g: 255, b: 255),
		titleBgColor: CleoColor:rgb(r: 37, g: 99, b: 235),
		width: CleoWidth:percent(pct: 85),
		outerBorder: BorderStyle:Rounded,
		dividerBorder: BorderStyle:Thin,
		borderColor: CleoColor:ansi(code: 240),
		dividerColor: CleoColor:ansi(code: 238)
	);

	# Section 1: dark slate background with amber pill title
	local CleoSection is svcSec: out:addSection(
		title: ' Services ',
		titleColor: CleoColor:rgb(r: 20, g: 20, b: 20),
		titleBgColor: CleoColor:rgb(r: 245, g: 158, b: 11),
		titlePlacement: TitlePlacement:InlineBorder,
		fgColor: CleoColor:rgb(r: 226, g: 232, b: 240),
		bgColor: CleoColor:rgb(r: 24, g: 28, b: 36)
	);
	local Int is apiSlot: svcSec:addShapeThrobber(
		shape: ThrobberShape:Circle,
		effect: ThrobberEffect:ColorCycle,
		palette: [CleoColor:ansi(code: 39), CleoColor:ansi(code: 81)],
		text: 'api-gateway: rolling restart (2/4 pods)'
	);
	local Int is dbSlot: svcSec:addLine(text: 'postgres-primary: healthy (12ms)');

	# Section 2: full-width header row banner + navy background
	local CleoSection is progSec: out:addSection(
		title: 'Rollout Progress',
		titleColor: CleoColor:rgb(r: 186, g: 230, b: 253),
		titleBgColor: CleoColor:rgb(r: 30, g: 58, b: 138),
		titlePlacement: TitlePlacement:HeaderRow,
		fgColor: CleoColor:rgb(r: 241, g: 245, b: 249),
		bgColor: CleoColor:rgb(r: 15, g: 23, b: 42)
	);
	local Int is barSlot: progSec:addProgressArea(
		text: 'Applying manifests & draining connections...',
		stage1Color: CleoColor:rgb(r: 34, g: 197, b: 94),
		stage2Color: CleoColor:rgb(r: 56, g: 189, b: 248)
	);

	out:start();
	Time:sleepMs(ms: 600);
	svcSec:resolveSlot(index: apiSlot, badge: '✔', text: 'api-gateway: 4/4 pods ready');
	progSec:setColors(fgColor: CleoColor:rgb(r: 220, g: 252, b: 231), bgColor: CleoColor:rgb(r: 20, g: 45, b: 30));
	progSec:updateProgress(index: barSlot, text: 'Rollout complete.', stage1: 1.0, stage2: 1.0);
	out:finish();
}
```

### Example 5: Committing Completed Items Above a Pinned Live Region

```spec
# When a build has 500 targets, keep only active workers in the live box
# and flush finished targets permanently above it:
out:commitLine(text: '✔ [142/500] Built base:sys:Mem (18ms)', color: CleoColor:ansi(code: 42));
```

---

## 6. Architecture & Thread Safety

To integrate cleanly with Spec's existing `base:sys` stack:

- **Synchronization**: Every public mutation (`add*`, `update*`, `setColor`, `commit*`, `render`, `finish`) acquires a dedicated lock via `Parallel:syncWith` (or a dedicated Cleo mutex) so worker threads in `Parallel:run` or background `Time:setInterval` throbber ticks cannot interleave partial ANSI sequences.
- **Single-Write Frame Flushing**: A frame render builds the entire ANSI diff string in a `Buf` / `String` buffer and flushes it in one `Output:consOut(...)` call, minimizing flicker and syscall overhead.
- **Lifecycle Safety**: `start()` hides the cursor (`Ansi:hideCursor()`) and optionally starts the throbber tick timer; `finish()` cancels the timer, performs a final flush, and restores the cursor (`Ansi:showCursor()`).

---

## 7. Technical Limitations & Implementation Considerations

Building Cleo cleanly in Spec is very feasible, but there are several real terminal, OS, and stdlib constraints that must be designed around up front:

### 7.1 Inline Scrollback Ceiling (The Fundamental Terminal Constraint)
- **Constraint**: Unlike a full-screen TUI (`\e[?1049h` alternate screen), ANSI cursor-up (`\e[nA`) **cannot move above row 1 of the visible terminal viewport**. Once lines scroll off the top into scrollback history, they cannot be rewritten in place.
- **Mitigation**: Cleo must track `renderedLineCount` against `Ansi:terminalHeight()`. If the live buffer would exceed `terminalHeight() - 1`, Cleo should either:
  1. Require/encourage `commitLine()` for completed items so the live region stays compact, and/or
  2. Clamp/scroll the live interior window (`maxVisibleRows`) while keeping the outer frame within the viewport.

### 7.2 "Pixels" vs. Character Cells (`px` Width Mode)
- **Constraint**: Standard terminals are character-cell grids, not pixel surfaces. On POSIX, `ioctl(TIOCGWINSZ)` includes `ws_xpixel` and `ws_ypixel`, **but many terminal emulators, multiplexers (`tmux`/`screen`), SSH sessions, and Windows ConPTY leave `ws_xpixel == 0`**.
- **Mitigation**:
  - Support `CleoWidth:px(pixels)` as a best-effort conversion: if `ws_xpixel > 0 && ws_col > 0`, compute `cols = pixels * ws_col / ws_xpixel`; otherwise fall back to a configurable assumed cell width (e.g., `8` or `9` px/col).
  - Document `CleoWidth:cols` and `CleoWidth:percent` as exact/deterministic, and `CleoWidth:px` as best-effort with fallback.

### 7.3 Windows Console VT Processing & UTF-8 Codepage
- **Constraint**: Currently, `PalCore.spec` / `PalConsole.spec` does not explicitly call `SetConsoleMode(..., ENABLE_VIRTUAL_TERMINAL_PROCESSING)` or `SetConsoleOutputCP(CP_UTF8)` on Windows. While Windows Terminal often enables VT sequences by default, legacy `cmd.exe` / conhost sessions will print raw `\e[...` escapes and garbled UTF-8 box-drawing glyphs (`┌─┐│└┘▀▄`) without them.
- **Mitigation**: Add a one-time `enableVirtualTerminal()` helper in `PalConsole.spec` (called by `Cleo:start()` or `Ansi`), with automatic fallback to `BorderStyle:Ascii` if VT mode cannot be enabled.

### 7.4 Display Column Width vs. UTF-8 Byte Length
- **Constraint**: Spec `String` lengths are UTF-8 byte counts. A string like `"\e[32m✔ Done\e[0m"` has 15 bytes, 6 visible codepoints, and 6 display columns—whereas emoji or CJK characters take 2 display columns each, and ANSI CSI sequences take 0. Measuring by byte length breaks border alignment and padding.
- **Mitigation**: Cleo needs an internal **display-width helper** that skips ANSI CSI/OSC escape sequences and computes Unicode East-Asian/combining column widths (`wcwidth`-style) for accurate padding and truncation.

### 7.5 Missing `base:sys:Ansi` and `PalConsole` Primitives
Several small, low-risk additions to `PalConsole.spec` and `Ansi.spec` are needed:
- **True TTY detection (`isTty()`)**: `PalCore.spec` calls `isatty(1)` internally, and `PalConsole.spec` currently returns `78` as a fallback in `spec_term_width` when not a TTY. Cleo needs an explicit `Ansi:isTty()` so it knows when to disable cursor-up rewrites.
- **Relative cursor & line-erase sequences**: `Ansi.spec` currently has `moveTo(row, col)` (absolute) and `clearScreen()`, but lacks `cursorUp(n)`, `cursorDown(n)`, `carriageReturn()`, `eraseLine()`, `eraseToEnd()`, and Synchronized Output (`beginSyncUpdate` `\e[?2026h`, `endSyncUpdate` `\e[?2026l`).
- **Public `bgRgb`**: `Ansi:bgRgb(r, g, b)` currently exists in `Ansi.spec` marked `local`; making it public enables `CleoImage` half-block (`▀`/`▄`) TrueColor rendering without duplicating escape builders.
- **Pixel geometry query (optional)**: Exposing `ws_xpixel` / `ws_ypixel` from `PalConsole.spec` if `px` width estimation should use live terminal metrics.

### 7.6 Terminal Resize (`SIGWINCH`) & Raw Stdout Interleaving
- **Resize**: If the user resizes the terminal while Cleo is active, previously wrapped lines change row height and relative cursor-up counts can misalign. Re-querying `terminalWidth()` before each render (and doing a clean erase-from-origin + full redraw on width change) handles most cases; catching `SIGWINCH` / `WINDOW_BUFFER_SIZE_EVENT` can trigger an immediate re-layout if needed later.
- **Stdout interleaving**: Calling `Output:line()` or `Stderr:line()` directly while Cleo's live region is active will corrupt cursor tracking. User code should log through `cleo:commitLine(...)` during an active Cleo session.

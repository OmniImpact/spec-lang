# THEO — Terminal-Housed Execution and Operation

> *Big brother to [Cleo](spec/lib/base/cleo/Cleo.spec).*

**Theo** (`base:theo`) is Spec's full-screen, declarative, reactive Terminal User Interface (TUI) framework, modeled after **Kotlin / Jetpack Compose**.

---

## 1. Cleo vs. Theo

Cleo and Theo share Spec's terminal aesthetics (box-drawing borders, 256-color / RGB palettes, clean typography) while serving two distinct roles:

| Aspect | **Cleo** (`base:cleo`) | **Theo** (`base:theo`) |
| --- | --- | --- |
| **Screen model** | Inline in normal terminal scrollback (buffer or streaming) | Dedicated alternate screen buffer (`enterAltScreen` / `exitAltScreen`) |
| **Lifecycle** | Runs alongside CLI output and exits cleanly into scrollback | Full-screen event loop until user quits or app exits |
| **Programming model** | Imperative sections & slots (`addSection`, `addLine`, `updateText`) | Declarative, composable functions & reactive `State` recomposition |
| **Input & focus** | Output-only | Full keyboard & mouse input, focus tree, scrolling, text editing |
| **Use cases** | `spec`, `specbuild`, `speclint`, `specunit`, benchmarks | Interactive dashboards, editors, debuggers, file browsers, TUI apps |

---

## 2. Core Philosophy (Compose in Spec)

1. **UI is a function of state.**
   Screens and components are built by returning widget trees (`Grid`, `Panel`, `Col`, `Row`, `TextLine`, `Button`, etc.) from `Frame:ui()`. Reactive signals from `Emitter`s collected via `Collector`s trigger **recomposition** of the `Frame`.

2. **Unidirectional data flow.**
   State flows *down* into child composables via parameters; events (`onClick`, `onKey`, `onChange`, `onSubmit`) flow *up* via callbacks to update state.

3. **Explicit `Modifier` chains.**
   Layout sizing, padding, alignment, borders, backgrounds, scrolling, and input handlers are attached via immutable, chainable `Modifier` values rather than dozens of constructor flags.

4. **Single-pass `Constraints` layout.**
   Parent layouts pass `(minWidth, maxWidth, minHeight, maxHeight)` constraints down; children return exact `(width, height)` measurements; parents place children at `(x, y)`.

5. **Tear-free diffed terminal rendering.**
   Theo renders into a 2D cell back-buffer, diffs it against the front-buffer, and flushes only changed runs inside synchronized-update frames (`beginSyncUpdate` / `endSyncUpdate`).

---

## 3. Conceptual API Sketch (ViewModel + Overloaded Emitters)

In Spec, **methods and `init` constructors can be overloaded** by parameter type. Widgets take advantage of this so any dynamic property accepts **either** a static value (`String`, `Int`, `Boolean`) **or** an `Emitter` (`TextEmitter`, `IntEmitter`, `BoolEmitter`):

- Static: `TextLine(value: 'Theo Counter', bold: true)`
- Dynamic: `TextLine(value: vm:countLabel, bold: true)` — the widget attaches a `Collector` automatically and updates whenever `vm:countLabel` emits.

```spec
Class is CounterViewModel{
	replace Array of Array of String is using: [
		['base', 'signal', IntEmitter],
		['base', 'signal', TextEmitter]
	];

	IntEmitter is count: IntEmitter(initial: 0);
	TextEmitter is title: TextEmitter(initial: 'Theo Counter');
	TextEmitter is countLabel: count:mapText(
		transform: local Function of String(Int is n){
			"Count: {{n}}";
		}
	);

	Function is increment(){
		count:emit(value: count:current() + 1);
	}

	Function is decrement(){
		count:emit(value: count:current() - 1);
	}
}

Class is CounterApp of TheoApp{
	replace Array of Array of String is using: [
		['base', 'theo', TheoApp],
		['base', 'theo', TheoScreen],
		[CounterFrame]
	];

	replace Function is init(){
		local TheoScreen is screen: TheoScreen(root: CounterFrame());
		run(screen: screen);
	}
}

Class is CounterFrame of Frame{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', Grid],
		[CounterViewModel],
		[HeaderBar],
		[CounterControls]
	];

	CounterViewModel is vm: CounterViewModel();

	replace Function of Widget is ui(){
		Grid(
			orientation: 'vertical',
			panes: [
				Grid:fixed(
					size: 3,
					child: HeaderBar(title: vm:title)
				),
				Grid:weight(
					weight: 1.0,
					child: CounterControls(vm: vm)
				)
			]
		);
	}
}

Class is HeaderBar of Frame{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', TextEmitter],
		['base', 'theo', Panel],
		['base', 'theo', TextLine]
	];

	TextEmitter is title;

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padding: 0,
			child: TextLine(
				value: title,
				bold: true
			)
		);
	}
}

Class is CounterControls of Frame{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', Panel],
		['base', 'theo', Col],
		['base', 'theo', Row],
		['base', 'theo', TextLine],
		['base', 'theo', Button],
		[CounterViewModel]
	];

	CounterViewModel is vm;

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padding: 1,
			child: Col(
				gap: 1,
				children: [
					TextLine(
						value: vm:countLabel,
						bold: true
					),
					Row(
						gap: 2,
						children: [
							Button(
								label: ' -1 ',
								onClick: {
									vm:decrement();
								}
							),
							Button(
								label: ' +1 ',
								onClick: {
									vm:increment();
								}
							)
						]
					)
				]
			)
		);
	}
}
```

---

## 4. Architecture

Theo is organized into five layers under `base:theo` (`spec/lib/base/theo/`), backed by minimal terminal-raw-mode extensions in `base:sysinternal` / `base:sys`:

### Layer 1: Terminal Runtime & Raw Input (`base:sysinternal` / `base:sys`)
- **Alternate screen & cursor guard:** Enters alternate screen (`Ansi:enterAltScreen()`), hides the cursor (`Ansi:hideCursor()`), enables raw/cbreak input mode, and guarantees restoration (cooked mode, `showCursor()`, `exitAltScreen()`) on normal exit, Ctrl+C, or `SpecError`.
- **Non-blocking / timed input reader:** Reads raw bytes from stdin with configurable timeout (e.g. `pollKey(timeoutMs)`), decoding ANSI/VT escape sequences into structured `KeyEvent` values:
  - Printable characters (UTF-8)
  - Control keys (`Enter`, `Tab`, `BackTab`, `Esc`, `Backspace`, `Delete`)
  - Navigation (`Up`, `Down`, `Left`, `Right`, `Home`, `End`, `PageUp`, `PageDown`)
  - Function keys (`F1`..`F12`) and modifiers (`ctrl`, `alt`, `shift`)
  - Optional SGR mouse reporting (`MouseEvent`: press, release, drag, scroll wheel, coordinates)
- **Resize detection:** Tracks `terminalWidth()` / `terminalHeight()` changes (SIGWINCH / resize poll) and invalidates layout on dimension change.

### Layer 2: Virtual Cell Buffer & Diff Renderer (`TheoBuffer`, `TheoRenderer`)
- **`TheoCell`:** Stores grapheme/character, foreground color (`TheoColor`: 256-color, 24-bit RGB, or default), background color, and style flags (`bold`, `dim`, `italic`, `underline`, `reverse`).
- **`TheoBuffer`:** Flat `width * height` array of `TheoCell`s with clipping rects (`pushClip` / `popClip`) and drawing primitives (`drawText`, `fillRect`, `drawBox`).
- **`TheoRenderer`:** Compares `back` buffer to `front` buffer cell-by-cell, coalesces contiguous runs with identical SGR attributes, emits `Ansi:moveTo(row, col)` only on cursor jumps, wraps the frame in `Ansi:beginSyncUpdate()` / `Ansi:endSyncUpdate()`, and swaps buffers.

### Layer 3: Layout Engine (`Constraints`, `Grid`, `Panel`, `Row` / `Col`)
- **`Constraints`:** `(minW, maxW, minH, maxH)` passed top-down during `measure(constraints)`.
- **`Grid` (Frame Splitting & Nestable Panes):**
  - Splits a `Frame` into sub-frames (child panes) and can nest arbitrarily (`Grid` inside a sub-frame).
  - Supports **vertical** or **horizontal** orientation.
  - Each pane specifies either a **fixed size** (rows/columns) or a **weight** (proportional share of remaining space after fixed panes are allocated).
- **`Panel` (Styled & Scrollable Container):**
  - Fills any part of a `Grid` (or `Frame`), configuring `foreground`, `background`, `border`, `borderColor`, `borderStyle`, `padding`, and `scrollable` (viewport clipping + scroll offset).
- **Item Flow Containers:**
  - `Row` / `Col`: Displays items one after another horizontally (`Row`) or vertically (`Col`) with `gap` and alignment. Placing a `Row` or `Col` inside a scrollable `Panel` creates a scrollable list.
  - `Box`: Overlays children with `Alignment` (`topStart`, `center`, `bottomEnd`, etc.).
  - `Spacer`: Flexible or fixed empty space.
- **Modifier pipeline:** Each modifier wraps measurement, placement, or painting cleanly (`padding`, `size`, `width`, `height`, `fillMaxWidth`, `fillMaxHeight`, `fillMaxSize`, `weight`, `border`, `background`, `clip`, `focusable`, `onKey`, `onClick`).

### Layer 4: `TheoApp`, `TheoScreen` / `Frame`, `Emitter` / `Collector`, and Event Loop
- **Application & Navigation Hierarchy (`TheoApp` -> `TheoScreen` -> `Frame`):**
  - **`TheoApp`:** Top-level application host. Owns the alternate-screen terminal lifecycle, raw input loop, `TheoRenderer`, `ThreadScope`, and the root `TheoScreen`.
  - **`TheoScreen`:** The navigation stack made up of `Frame`s. Supports `push(frame)`, `pop()`, `replace(frame)`, `replaceAll(frame)`, and `current()`. Preserves inactive frames' instance state and focus state on the stack so navigating back restores state seamlessly.
  - **`Frame`:** Where widgets live. Holds its own `Emitter` / model fields directly as normal class state, returns a widget tree from `ui()` (hosting widgets directly or splitting into nestable sub-frames via `Grid`), provides `collect(...)` helpers to bind `Emitter`s to frame recomposition, and offers lifecycle hooks (`onEnter`, `onPause`, `onResume`, `onExit`) plus access to its parent `TheoScreen` for navigation.
- **Reactive `Emitter` & `Collector` (LiveData / Kotlin `Flow` Model):**
  - **`Emitter of T`:** Reactive signal/value source supporting `emit(value)`, `current()`, and configurable `replay` buffer depth (`replay: N`, e.g. `1` for state/LiveData semantics, `N` for event replay).
  - **`Collector of T`:** Subscribes to an `Emitter`, receives emitted signals (including replaying buffered emissions on attach), and either runs an `onEmit` handler or binds to the `Frame` (`collect(...)`) so new emissions mark the frame dirty and wake the event loop.
  - **Convenience Subclasses:** `TextEmitter` / `TextCollector`, `IntEmitter` / `IntCollector`, `BoolEmitter` / `BoolCollector`, `FloatEmitter` / `FloatCollector` for clean, zero-boilerplate usage in UI and business logic.
  - **Combinators & Replay Operators:**
    - `zip(other, combine)`: pairs emissions from two `Emitter`s into a derived `Emitter`.
    - `combine(other, transform)`: re-emits whenever either upstream `Emitter` emits using the latest values from both.
    - `map(transform)` / `filter(predicate)`: transforms or filters an `Emitter` stream into a downstream `Emitter`.
    - `replay(count)`: replays the last `count` emitted signals to newly attached `Collector`s.
- **Side Effects & Concurrency:**
  - Integrates with `ThreadScope` so background workers can call `emitter:emit(...)` safely from worker threads and wake the UI event loop.
- **Focus & Event Routing:**
  - Maintains a focusable-node list in tree order (`Tab` / `Shift+Tab` traversal, directional focus, modal focus trapping).
  - Routes `KeyEvent` to the focused node first, bubbling up to ancestors if unhandled (Compose `onPreviewKeyEvent` / `onKeyEvent` pattern).
  - Routes `MouseEvent` via hit-testing against laid-out bounding boxes.

### Layer 5: Built-in Widgets & Components
- **Containers:** `Panel` (foreground, background, border, borderColor, borderStyle, padding, scrollable), `Row`, `Col`, `Box`, `Spacer`.
- **Text & Graphics:** `TextLine` (single-line text display / editing), `TextArea` (multi-line text display / editing), `TextGraphic` (preformatted Unicode / ANSI / block-character graphics).
- **Interactive Controls:** `Button`, `Checkbox`, `Switch`, `RadioGroup`, `Tabs`, `Table`, `TreeView`.
- **Status & Overlays:** `Divider`, `ProgressBar`, `Spinner`, `Dialog` / `Modal` (centered overlay with focus trap), `Menu` / `Dropdown`, `StatusBar` / `KeyHints`.

---

## 5. Phased Implementation Plan

1. **Phase 1 — Terminal Runtime & Diff Renderer**
   - Add raw terminal mode + `pollKey` + cooked-mode/alt-screen restore guard in `base:sysinternal` / `base:sys`.
   - Implement `TheoColor`, `TheoCell`, `TheoBuffer`, and `TheoRenderer` with synchronized double-buffered diffing.
   - Verify with unit tests on buffer diffing and a minimal alt-screen demo.

2. **Phase 2 — Layout Engine, `Grid`, `Panel`, & Core Primitives**
   - Implement `Constraints`, `Modifier`, `TheoNode`, `Grid` (vertical/horizontal, fixed-size & weight-based nestable sub-frames), `Panel` (fg/bg, border/color/style, padding, scrolling), `Row`, `Col`, `Box`, `Spacer`, `TextLine`, and `TextGraphic`.
   - Verify layout measurement/placement and border/padding/scroll rendering with `SpecUnit` snapshot tests against `TheoBuffer`.

3. **Phase 3 — `TheoApp` / `TheoScreen` / `Frame` & `Emitter` / `Collector`**
   - Implement `Emitter of T`, `Collector of T`, convenience subclasses (`TextEmitter`, `TextCollector`, `IntEmitter`, `IntCollector`, `BoolEmitter`, `BoolCollector`, `FloatEmitter`, `FloatCollector`), and combinators (`zip`, `combine`, `map`, `filter`, `replay`).
   - Implement `TheoApp`, `TheoScreen` (navigation stack), `Frame`, and dirty-frame recomposition on `collect`.
   - Connect `ThreadScope` for thread-safe `emit(...)` updates and resize handling.

4. **Phase 4 — Focus & Interactive Widgets**
   - Implement focus tree traversal (`Tab` / `Shift+Tab`), key-event bubbling, and mouse hit-testing.
   - Build `Button`, `TextLine` (editable input), `TextArea` (multi-line), `Checkbox`, and scrollable `Panel` + `Row`/`Col` lists.

5. **Phase 5 — Rich Components & Example App**
   - Build `Table`, `Tabs`, `Dialog` / `Modal`, and `StatusBar`.
   - Ship a flagship `examples/` Theo application demonstrating live state, keyboard navigation, and async workers.

---

## 6. Implementation Notes & First-Pass Priorities

### Correctness First (Defer Repaint Optimization)
- On the first pass, **correctness over efficiency**: whenever a `Collector` receives a new value or the terminal resizes, simply re-measure, re-layout, and redraw the full screen cleanly inside `Ansi:beginSyncUpdate()` / `Ansi:endSyncUpdate()`.
- Incremental diffing, dirty-rectangle tracking, and layout memoization are explicitly deferred until the component model, navigation stack, and reactive bindings are solid.

### Design Considerations
1. **Non-blocking raw input & crash-safe restore (`base:sysinternal` / `base:sys`):**
   Add a timed `pollKey(timeoutMs)` (`termios` raw mode + `poll()` on POSIX) paired with an `atexit` / signal restore guard so `SpecError`, `Ctrl+C`, or abnormal exits never leave the terminal stuck in raw or alternate-screen mode.
2. **Collector cleanup on navigation (`onExit` / structural rebuild):**
   Because a `ViewModel` can outlive a `Frame`, every `Collector` attached by a `Frame`'s widgets must unsubscribe when the `Frame` is popped (`onExit`) or rebuilt so popped frames do not leak or react to future emissions.
3. **Thread-safe `Emitter` & UI wakeup:**
   `Emitter:emit(...)` called from `ThreadScope` workers must synchronize its current value and subscriber list (e.g. `Parallel:syncWith`) and wake the UI loop (via a wakeup pipe/event or short poll interval) so background updates render immediately without waiting for a keypress.
4. **Structural list updates:**
   Overloaded widget constructors (`TextLine(value: TextEmitter)`) handle changing *values* directly; for collections whose membership changes (e.g. dynamic rows in a `Panel`), provide a list-bound container (`ArrayEmitter` / dynamic `Col` & `Row`) or trigger a `Frame` rebuild.
5. **`Str` vs `String` overload resolution:**
   Verify during Phase 2/3 whether `init(String)` + `init(TextEmitter)` resolves `'literal'` (`Str`) unambiguously or if an explicit `init(Str)` overload should also be provided on text widgets.

---

## 7. First Milestone Target: Simple Text Editor

Our first end-to-end Theo application is a minimal terminal text editor opened on a file path (`editor <file>`), exercising `TheoApp`, `TheoScreen`, `Frame`, `Grid`, `Panel`, `Row`, `TextLine`, `TextArea`, `Button`, `ViewModel` + `Emitter`s, focus navigation, and raw keyboard input.

### Layout
A vertical `Grid` with three panes:
1. **Top Bar (`Grid:fixed`):** `Panel` + `TextLine` displaying the opened file name (and optional modified indicator).
2. **Editor Space (`Grid:weight(1.0)`):** Scrollable `Panel` + `TextArea` displaying and editing the file's text.
3. **Bottom Action Bar (`Grid:fixed`):** `Panel` + `Row` containing `Save` and `Exit` `Button`s.

### Focus & Keybinding Requirements
- **Startup:** Opens with focus in the `TextArea`.
- **`Ctrl+M`:** Moves focus from the `TextArea` down to the bottom action bar (focusing `Save`).
- **`Left` / `Right` in bottom bar:** Moves focus between `Save` and `Exit` buttons; `Enter` / `Space` triggers the focused button (`Save` writes buffer to disk; `Exit` exits `TheoApp`).
- **`Up` in bottom bar:** Returns focus back up into the `TextArea`.
- **`TextArea` editing & scrolling:**
  - Printable character insertion, `Enter` (newline / split line), `Backspace` / `Delete` (including line join).
  - Cursor movement (`Up`, `Down`, `Left`, `Right`, `Home`, `End`) with automatic scroll-to-cursor inside the `Panel` viewport.
  - Visible cursor positioning when `TextArea` has focus (and hidden/unfocused styling when focus is in the bottom bar).

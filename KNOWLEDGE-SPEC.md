# Spec — AI Agent Bootstrap

Strictly typed, class-based, compiles to native machine code via LLVM IR (`clang`). Written in itself: compiler is Spec source (`spec/base/compiler/`), bootstrapped from `bootstrap/spec.ll` and scalar C OS PAL `bootstrap/spec_runtime.c`, with the self-hosting fixed point verified on every `./bootstrap.sh`. Never-null (no null; fallible reads require `default:`). Tabs for indentation.

## Layout
- `spec/lib/base/` — stdlib in Spec: `core` (`Any`, `Stringable`, `Class`, `Str`, `String`, `Enum`, `SpecError`, `Mergeable`, `Result`), `math` (+ `math:crypto`: `Sha256`, `X25519`, `ChaCha20Poly1305`, `Aes128Gcm`, `X509`, `X509Cert`), `struct` (`Array`, `Map`, `List`, `Stack`), `iterator` (`Loop`, `LoopControl`, `LoopCallback`), `data` (`Json`, `JsonNull`, `JsonBool`, `JsonNumber`, `JsonError`), `signal` (`Emitter`, `Collector`, `TextEmitter`/`TextCollector`, `IntEmitter`/`IntCollector`, `BoolEmitter`/`BoolCollector`, `EnumEmitter`, `ListEmitter`, `SignalBag`), `theo` (retained+reactive TUI framework), `net` (`Socket`, `Url`, `Http`, `HttpRequest`, `HttpResponse`, `net:tls`), `cleo` (terminal UI), `audio`, `sys` (`Conditional`, `Loops`, `Output`/`Input`/`Stderr`, `File`, `Ansi`, `Process`, `Parallel`, `sys:thread`: `ThreadScope`/`Task`, `Introspection`, `Buf`, `Dir`, `Box`, `Uri`, `Vector`, `HashTable`, `Mem`, `CliArgs`, `OsDispatch`, `Time`, `DateTime`, `AudioDevice`). Declared `namespace` IS the package; directories are organization only.
- `spec/base/sysinternal/` — floor: `Loadable`, pure-Spec unmanaged runtime (`Arc`, `Slab`, `Heap`, `Pool`, `Arena`, `Intern`), compiler-lowered intrinsics (`Mem`, `Introspection`, `Conditional`, `Loops`), body-less OS PAL declarations (`Console`, `Dir`, `File`, `Process`, `Socket`, `Audio`, `Time`). Only `base:sys`/stdlib wrappers may call the floor.
- `spec/base/compiler/` — `lexer`, `parser`, `ast`, `checker` (`TypeChecker`, `TypeDomain`, `TypeError`), `ir`, `opt` (`OptimizerPipeline`, `ConstFoldPass`, `DevirtPass`, `ArcPeepholePass`, `PoolElisionPass`, `WrapperUnwrapPass`, `ConcatFusionPass`, `InlineHintPass`), `llvm` (`IrBuilder`, `LlvmEmitter`, `GenericSpecializer`, `CallLowerer`), `pal`, `loader`, `driver`. Linter: `utilities/speclint/`.
- `spec/runtime/` — C OS PAL sources assembled into `bootstrap/spec_runtime.c`.
- `utilities/` — `specunit` (test runner), `speclint` (linter), `specbuild` (`specbuild <dir> build|test|run|clean`), `specinit`, `speclsp`.

## Grammar & Metadata
Keywords: `local` `contained` `replace` `merge` `held` `is` `as` `of` `to` `return`.
Types: `Int` `Byte` `UInt8` `UInt16` `UInt32` `UInt64` `ISize` `USize` `Float` `Float32` `Boolean` `Rune` `RawPtr` `Str` `String` `Function` `Any` `[T]` (`List of T`).
Declaration types (not keywords): `Class` `Enum`. Conversion targets of `as`: `Hex` `Bin` `Oct`.

Declaration grammar: `<modifiers> <Type> is <name>`.
- Class: `Class of Parent1, Parent2 is Name of T { ... }` (pre-name `of` = parents, post-name `of` = generic params).
- Variable: `local Int is count: 10;`
- Method: `replace Function of Ret is name(Type is param){ ... }`; body-less interface form: `Function of T is name(params);` (floor declarations only).
- Automatic returns & optional `;`: single-expression / final expression before `}` returns automatically and may omit `;` (`Function of Int is zero(){ 0 }`). `return` and intermediate statements still require `;`. Parenthesized `||` at block start (e.g. `(a || b)`) needs explicit `return`.
- Field: `local String is title: 'text';` or `local String is title;` (must be initialized in `init`; `[T]` fields auto-initialize to `[]`).
- **Uniform typed loader metadata** (untyped shorthand `namespace: [...]` and `Array of Array of String is using:` are retired):
  - `replace [String] is namespace: ['pkg', 'sub'];`
  - `replace [[String]] is using: [...];` or `merge [[String]] is using: [...];` (subclasses of `Class` inherit `as Conditional()` + `as Loops()` via `merge`)
  - `replace Map of Any to Function is castable: [Target: method];`

Operators: `++ --`; `+ - * / %`; `& | ^ << >> ~` (Int); `.` string concat; `== != < <= > >= is`; `&& || !`; `as` cast.
String literals: `"..."` (escaped + `{{expr}}` interpolation), `'...'` (raw), `'''...'''` (raw multiline), ```` ```...{{expr}}...``` ```` (interpolated multiline).
Base literals: `0xFF` `0b1010` `0o755` `1_000_000`.

## Imports & Resolution
```spec
merge [[String]] is using: [
	['base', 'sys', as Output()],
	['base', 'sys', as File()],
	['base', 'theo', [Widget, Button, Panel]],
	['base', 'theo', '*']
];
```
- `as ClassName()` instance imports **must** be separate entries (never group `[as A(), as B()]`); plain type imports can group `[A, B]` or use `'*'`.
- `['pkg', as ClassName()]` materializes an owned instance scoped to the class; members answer to `ClassName:fn(...)` and bare `fn(...)` when unambiguous.
- Loader scans the entry `.spec` dir, compiler dir ancestors, and cwd recursively, matching filename stem to class name and verifying declared `namespace`. Root/floor classes (`String`, `Buf`, `Dir`, `Stringable`, `Loadable`, `Class`, `Any`, `CliArgs`, `Arc`, `Pool`, `Arena`, `Intern`) preload automatically; parentless non-enum classes inherit `Any`.

## Call Model & Visibility
- Instance-based dispatch; `ClassName(...)` / `ClassName:init(...)` constructs. `held Function` is receiver-free (`ClassName:helper(...)`, no `:` inside body).
- Overloading: distinct arity, param names, or exact param types; positional allowed only on unique arity match, otherwise named args required. Cannot `replace` an overloaded method.
- Visibility: none = public; `local` = private; `contained` = protected + final.
- `replace` mandatory on public overrides; `merge` on Array/List fields concatenates parent + child; `merge` on methods delegates via `(args...)` forward statement.
- `Any` values only expose `toString`, `typeName`, `init`; cast via `val as Concrete`.

## Control Flow & Enums
Served bare via `['base', 'sys', as Conditional()]` and `['base', 'sys', as Loops()]` (inherited via `Class` + `merge [[String]] is using:`):
- `if({ cond }, { then }, { else })` (value-yielding when both arms yield same type).
- `match(on: val, when: [ 'a': { ... }, else: { ... } ])` — enum match is exhaustiveness-checked.
- Predicate table: `match(when: [ { x < 0 }: { ... }, else: { ... } ])`.
- Loops: `while({ cond }, { ... })`, scoped-var `while([Int is i: 0], { i < n }, { ... i++; })`, `times(count: n, worker: local Function(Int is i){ ... })`, `each(list: xs, action: local Function(T is x){ ... })`, `repeat(count:, worker:)`, `until({ cond }, { ... })`, `Parallel:run(threads:, iterations:, worker:)`. `while` / `times` / `if` with literal closures lower to zero-alloc LLVM IR basic blocks.
- Scoped region desugaring: `as: call(...)` / `as (params): call(...)` passes the rest of the block as the trailing callback arg.
- Value enums (`Enum is Status { A, B }`, `Enum of String is Suit { SPADES: '♠' }`): provide `:value()`, `:name()`, `:ordinal()`, `:of(v:)`, `:values()`. Do NOT add methods to a value enum if you need `:value()` (methods trigger Enhanced Enum desugaring without `:value()`).
- Enhanced enums (sum types with fields/methods): `Enum is Expr { Num(Int is v), Nil, Int is line: 0; Function ... }`. Variants before members use `,` separators.

## Collections & Data
- **`[T]` (`List of T`)** — preferred general list: `[]`, `['a', 'b']`, `push(item:)`, `get(index:)`, `set(index:, item:)`, `pop()`, `length()`, `clear()`, `join(separator:)`, `each(action:)`, `map(fn:)`, `filter(pred:)`, `fold(init:, fn:)`. Bidirectional literal typing chooses `List of T` or `Array of T` from target type.
- **`Array of T`**: `Array()`, `Array(['a'])`, `add(item:)`, `get(index:)`, `set(index:, item:)`, `removeAt(index:)`, `slice(start:, end:)`, `pop()`, `length()`, `clear()`, `join(separator:)`, `each`, `map`, `filter`, `fold`, `count`, `any`.
- **`Map of K to V`**: `[:]`, `['k': v]`, `getString(key:, default:)`, `getInt`, `getFloat`, `getBool`, `get(key:, default:)`, `getChecked(key:)`, `set(key:, value:)`, `has(key:)`, `remove(key:)`, `keys()`, `length()`, `each`.
- **`Json`** (`['base', 'data', as Json()]`): `parseObjectText(text:) -> Map of String to Any`, `parseArrayText(text:) -> Array of Any`, `stringify(value:) -> String`, `asString(val:) -> String`.

## Builtins (selected)
- `Output`: `line(text:)`, `print(text:)`, `write(text:)`. `Stderr`: `line(text:)`, `print(text:)`.
- `File` (`as File()`): `fileRead(path:, default:)`, `fileWrite(path:, content:)`, `fileExists(path:)`, `fileRemove(path:)` (check `fileExists` before `fileRemove` to avoid `IO_ERROR`).
- `Process` (`as Process()`): `execute(command:, args:)`, `getPid()`, `exit(status:)`, `sleep(ms:)`, `clockMs()`, `peakMemoryKb()`, `threadCount()`, `atomicAdd/Put/Get(slot:, value:)`.
- `Time` (`as Time()`): `monotonicMs()`, `monotonicUs()`, `monotonicNs()`, `nowMs()`, `sleepMs(ms:)`.
- `Math` (`as Math()`): `round`, `floor`, `ceil`, `toInt(value:)`, `toFloat(value:)`, `sqrt`, `pow`, `random(min:, max:)`, `fastRandom()`, `abs`, `min`, `max`, `clamp`.

## Reactive Signals (`base:signal`)
- `Emitter` / `Collector`: base pub/sub; `notifyCollectors` auto-prunes inactive collectors.
- Typed emitters: `TextEmitter`/`TextCollector` (`mapText`, `combineText`, `zipText`), `IntEmitter`/`IntCollector`, `BoolEmitter`/`BoolCollector`, `EnumEmitter of T`, `ListEmitter of T` (both use `BoolCollector` for 0-arg `collect(onEmit: { ... })`).
- `SignalBag`: keyed `(slot, emitter, collector)` registry with `track(slot:, emitter:, collector:)` (auto-detaches prior slot collector on rebind) and `clear()`.

## Theo TUI Framework (`base:theo`)
- **App/Screen/Frame**: `TheoApp` (`run(screen:)`, `quit()`), `TheoScreen` (`push(frame:)`, `pop()`, `current()`), `Frame` (`ui()`, `onKey(event:)`, `onTick()`, `rebuild()`, `overlays`: `addOverlay`/`showOverlay(overlay:, anchor:)`/`closeOverlay`/`removeOverlay`/`hasOpenOverlay`/`hasBlockingOverlay`).
- **Widget base**: owns `SignalBag` (`trackBinding(slot:, emitter:, collector:)`, `disposeBindings()`, `runMuted(action:)`, `isMuted()`, `dispose()`) and `activeTheme: TheoTheme`.
- **Layout**: `Grid` (`Grid:fixed(size:, child:)`, `Grid:weight(weight:, child:)`), `Row` (`gap`, `align: 'top'|'center'|'bottom'`, `arrowFocus`), `Col` (`gap`, `padX`, `padY`, `scrollable`, `arrowFocus`), `Center`, `Spacer(weight:)`, `Surface` (solid bg from `activeTheme:surfaceBg`), `Panel` (`border`, `padX`, `padY`, `scrollable`, per-side `topTitle`/`bottomTitle`/`leftTitle`/`rightTitle` + `*Align` + `titleFg`/`titleBg` defaulting to `activeTheme:titleBarFg`/`titleBarBg`).
- **Widgets**:
  - `TextLine` (static `String` or `TextEmitter`, `width`, `color`, `bold`)
  - `TextGraphic` (multiline string, defaults `fg` to `activeTheme:foreground`)
  - `TextInput` (static `String` or `TextEmitter`, `width`, `placeholder`, `onChange`, `onSubmit`, `runMuted` echo guard)
  - `TextArea` / `CodeTextArea` (`CodeTextArea:fromEmitters(value:, filePath:, ...)`)
  - `ListView` (`Array of String`, `[String]`, or `ListEmitter of String`, `onActivate`, `onSelectChange`)
  - `Button` (`label`, `width`, `padX`, `padY`, `shortcut: ShortcutKey`, `FocusTarget`, `onClick`, hover+focus styling)
  - `Dropdown` (anchored `ListView` in `Panel`+`Surface` inside `Frame` `Overlay`)
  - `Tooltip` (wraps `child`, non-blocking `Overlay` on `'top'|'bottom'|'left'|'right'` shown on hover)
  - `Overlay` (`content`, `anchor`, `blocking: true|false`, `closeOnEsc`, `closeOnBackdrop`, `onClose`)
  - `FocusTarget` (`initial`, `focused`, `hovered`, `requestFocus()`, `onFocus(handler:)`, `setHovered(next:)`, `onHover(handler:)`)
  - `ShortcutKey` (`ShortcutKey:none()`, `ShortcutKey:ctrl(key:)`, `ShortcutKey:alt(key:)`, `ShortcutKey:plain(key:)`, `matches(event:)`, `matchesChar(ch:)`, `displayText()`)
  - `TheoTheme` (`foreground`, `background`, `borderColor`, `focusBorderColor`, `titleColor`, `titleBarFg`, `titleBarBg`, `surfaceBg`, `accentColor`, `mutedColor`, `button*`, `scroll*`, `syntaxTheme`). Widgets pull from `activeTheme` by default.

## Architecture & Best Practices
- **MVVM separation (`model` → `util` → `vm` → `view`)**:
  - `model/`: pure data/domain state machines; zero I/O, zero `base:theo`.
  - `util/`: stateless helpers, JSON storage, centralized UI string/constant classes, focus/mode enums; zero `base:theo` widgets.
  - `vm/`: owns state, emitters, persistence, `onTick()`, formatted strings, and user intent methods.
  - `view/`: pure `Frame`s & custom `Widget`s; zero business logic or direct I/O; Compose-style private `local Function of Widget is sectionName()` methods keeping `ui()` as a flat layout scaffold; hoist actions to VM (`onClick: { vm:save(); }`).
- **Hard rules**: no hardcoded capacity caps (use `[T]`/`Map`); never use `:` on self-fields unnecessarily when unshadowed (`speclint` flags notices); gate changes with `bin/specbuild <dir> test`, `bin/specbuild <dir> build`, `bin/speclint -t <dir>`, and `./bootstrap.sh` + `bin/specunit -s bin/spec -t test -t testcompiler` for compiler changes.

## Memory & CLI
- Pure-Spec ARC (`base:sysinternal:Arc`) + thread-local claim pools (`Pool`), 4-bucket freelists, 24-byte `SpecBuf` SBO; parameters are borrows.
- `bin/spec -i file.spec -o binary [--emit-llvm out.ll] [--emit-runtime out.c] [--no-opt] [--debug] [--quiet]`.
- `bin/specbuild <app_dir> test|build|run|clean`; `bin/speclint -t <dir>`; `bin/specunit -s bin/spec -t test -t testcompiler`.

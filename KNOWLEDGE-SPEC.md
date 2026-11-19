# Spec — AI Agent Bootstrap

Strictly typed, class-based, compiles to native machine code via LLVM IR (`clang`). Written in itself: the compiler is Spec source (`spec/base/compiler/`), bootstrapped from the canonical LLVM IR seed `bootstrap/spec.ll` and scalar C OS PAL `bootstrap/spec_runtime.c`, with the self-hosting fixed point (the compiler recompiles its own sources to byte-identical LLVM IR and C PAL) verified on every `./bootstrap.sh`. Never-null (no null; fallible reads require `default:`). Tabs for indentation.

## Layout
- `spec/lib/base/` — the standard library, written in Spec: `core` (Any/Stringable/Str/String/Enum/SpecError), `math` (+ `math:crypto`: Sha256, X25519, ChaCha20Poly1305, Aes128Gcm, X509, X509Cert), `struct` (Array/Map/List/Stack), `iterator` (Loop/LoopControl/LoopCallback), `data` (Json), `net` (Socket, Url, Http, HttpRequest, HttpResponse, `net:tls`: TlsClient, TlsVerifier), `cleo` (Cleo terminal UI), `audio` (Audio), `sys` (Conditional, Loops, Output/Input/Stderr, File, Ansi, Process, Parallel, `sys:thread`: ThreadScope/Task, Introspection, Buf, Dir, Box, Uri, Vector, HashTable, Mem + CSPRNG, CliArgs, OsDispatch, Time, DateTime, AudioDevice). The declared namespace IS the package; directories are organization only.
- `spec/base/sysinternal/` — the floor: pure-Spec unmanaged runtime primitives (`Arc`, `Slab`, `Heap`, `Pool`, `Arena`, `Intern`), compiler-lowered memory/metadata intrinsics (`Mem`, `Introspection`, `Conditional`, `Loops`), and body-less scalar/byte-slice OS PAL declarations (`Console`, `Dir`, `File`, `Process`, `Socket`, `Audio`, `Time`) bound to C by the `spec_<method>` naming convention. Only the `base:sys` (and stdlib) wrappers may call the floor; the checker enforces it structurally.
- `spec/base/compiler/` — the compiler: `lexer`, `parser`, `ast`, `checker` (`TypeChecker`, `TypeDomain`, `TypeError`), `ir` (`IrModule`/`IrFunction`/`IrBlock`/`IrInst`/`IrStruct`), `opt` (`OptimizerPipeline`, `ConstFoldPass`, `DevirtPass`, `ArcPeepholePass`, `PoolElisionPass`, `WrapperUnwrapPass`, `ConcatFusionPass`, `InlineHintPass`), `llvm` (`IrBuilder`, `LlvmEmitter`, `LlvmRuntimePrelude`, `GenericSpecializer`, `CallLowerer` plugins), `pal` (`RuntimePrelude` assembling the real C PAL sources from `spec/runtime/`), `loader`, `driver`. The linter is the standalone `utilities/speclint/` utility.
- `spec/runtime/` — the real C OS PAL sources (`pal_headers.h`, `pal_core.c`, `pal_dir.c`, `pal_file.c`, `pal_process.c`, `pal_time.c`, `pal_console.c`, `pal_socket.c`, `pal_audio.c`) assembled into `bootstrap/spec_runtime.c`.
- `bootstrap/spec.ll` and `bootstrap/spec_runtime.c` — the canonical seeds. `bin/spec` — the built compiler.

## Grammar
Keywords: `local` `contained` `replace` `merge` `held` `is` `as` `of` `to` `return`.
Types: `Int` `Byte` `UInt8` `UInt16` `UInt32` `UInt64` `Float` `Boolean` `Str` `String` `Function` `Any`.
Declaration types (not keywords): `Class` `Enum`.
Conversion targets of `as`: `Hex` `Bin` `Oct`.
`using` is a Loader-recognized pseudo-field.

Declaration grammar: `<modifiers> <Type> is <name>`.
- Class: `Class of Parent1, Parent2 is Name of T { ... }` (pre-name `of` = parents, post-name `of` = generic params).
- Variable: `local Int is count: 10;`
- Method: `replace Function of Ret is name(Type is param) { ... }`; body-less interface form: `Function of T is name(params);` (floor declarations only).
- Field: `local String is title: 'text';` or `local String is title;` (deferred, must be set in init).
- `Class is Name` with no parents implicitly extends root `Any`.

Operators: `++ --` prefix/postfix increment/decrement; `+ - * / %` arithmetic; `& | ^ << >> ~` bitwise (Int only); `.` string concat; `== != < <= > >= is` comparison; `&& || !` logical; `as` cast.
`as` targets: `Int` `Float` `String` (numeric/String), `Hex` `Bin` `Oct` (Int↔String base conversion, optional width arg for Int→String padding). Chaining rejected; parse failures yield 0.

String literals: `"..."` (escape-processed), `'...'` (raw), `'''...'''` (raw multiline heredoc), ```` ```...{{expr}}...``` ```` (escape-processed multiline heredoc with `{{expr}}` interpolation).
Base literals: `0xFF` `0b1010` `0o755` `1_000_000` (underscore separators; bare leading zero stays decimal).
Casts: `value as Target`.

## Imports & Resolution
Array-form, pure package segments; the trailing segment names a class, omitting it imports the whole package (wildcard). The instance form `as ClassName()` materializes an owned instance scoped to the importing class — its members answer to the class-name prefix:
```spec
replace Array of Array of String is using: [
	['base', 'sys', as Output()],
	['base', 'struct', Array]
];
```
The loader scans two trees — the directory of the `.spec` file being compiled and the compiler executable's (walking up while a location holds no `.spec` content) — plus the working directory, recursively, pruning locations with no `.spec` content. It keeps a map (class name → candidate files); resolution loads the candidate and verifies its **declared namespace** — the namespace is the package, the map only says where to find candidates. One class per named file (the map key is the file-name stem). The root and floor classes `String` `Buf` `Dir` `Stringable` `Any` `CliArgs` `Arc` `Pool` `Arena` `Intern` are preloaded before user code; implicit `of Any` is appended to parentless non-enum classes.

## Call Model (instance-based)
Members are callable only through a value of the class's type. Methods may be **overloaded**: same name, distinct signatures (arity, parameter names, or types); resolution is arity → named-argument set → exact type match, exactly one survivor, conversions never choose; positional calls with a unique arity match, otherwise named arguments are required. Identical signatures, mixed positional/named calls (except the scoped-region desugaring's trailing callback), and replacing an overloaded method are compile errors.
Members are callable only through a value of the class's type. The class name itself admits exactly one call: `init` (construction). `['pkg', as ClassName()]` imports materialize an owned, anonymous instance scoped to the importing class (and inherited by subclasses); its members answer to the class-name prefix (`Math:round(...)`) and, where the name has exactly one provider in scope, bare (`round(...)`). Name collisions force qualification; the bare scope is own + inherited members plus direct as-imports, one level deep, methods only. Zero-field classes dispatch with no allocation (methods are self-free by construction); `init` is not callable on instances; a class-name receiver that is not instance-imported is a compile error.

## Visibility
- No modifier = public: overridable, callable everywhere.
- `local` = private: declaring class only; cannot be replaced/merged/shadowed.
- `contained` = protected + final: subclasses can call, cannot override.
- Root-contract members (`toString` `typeName` `init`) always require `replace` when overridden.
- Any-typed values only expose root contract (`toString` `typeName` `init`); cast for other members: `value as ConcreteClass`.

## Classes & Inheritance
- `Class of Parent1, Parent2 is Child { ... }`; generics post-name: `Class of T is Box`.
- Every class without parents implicitly extends root `Any` (`Class of Stringable is Any`), which provides `toString()` (renders class name), `init()`, `using` slot.
- Abstract = field without initializer or method with empty body; concrete subclasses must implement all inherited abstract members.
- Diamond ambiguity (two unrelated parents declare concrete impls, child doesn't) = compile error.
- `replace` mandatory on overrides (checked). `merge` on Array fields: concatenates parent items then child items. `merge` on methods: body must contain a forward statement `(args...)` delegating to parent; partial forwards use named args.
- `replace`/`merge` on non-public ancestor members = error.

## Control Flow
Served bare via scope-merged instance imports `['base', 'sys', as Conditional()]` and `['base', 'sys', as Loops()]`. Both inlined to zero-allocation native LLVM IR basic blocks for literal closures.
```spec
replace Array of Array of String is using: [
	['base', 'sys', as Output()],
	['base', 'sys', as Conditional()],
	['base', 'sys', as Loops()]
];

# Positional shorthand (or named check:, then:, else:)
if({ cond }, { ... });
if({ cond }, { ... }, { ... });
local String is s: if({ cond }, { "A" }, { "B" });

# Match tables: held-member/variant keys, string keys, array multi-keys
match(on: value, when: [
	'a': { ... },
	'b': { ... },
	else: { ... }
]);
local Int is x: match(on: e, when: [
	Variant: { v.field },
	else: { 0 }
]);

# Predicate table (no on:): first true condition runs its arm (replaces else-if ladders)
match(when: [
	{ x < 0 }: { line('negative'); },
	{ x > 0 }: { line('positive'); },
	else:      { line('zero'); }
]);
```
`match` on enums: exhaustiveness enforced for value-yielding matches over enum-rooted subjects (`else` closes the table); payload arms are closures whose parameters bind the variant's fields.

Enums:
```spec
Enum is Status { ACTIVE, INACTIVE }
Enum of Int is Code { OK: 200 }
Enum is Result { Ok(String is data), Err(Int is code) }
# Identity contract (name/ordinal) implemented ONCE on the Enum root,
# reflectively over the Introspection metadata floor:
#   .name() .ordinal()
# Per-enum remainder synthesized by the desugarer: .value() .of(v) .values() .toString()
# Payload constructors: Result:Ok(data: "x") — nested-class construction shorthand
# Payload destructuring: match(on: r, when: [Result:Ok: local Function(String is data){ ... }])
# The resolution hook: held Function of T is resolveHeld(String is name, Function of T is missing)
```

Loops: the `Loops` provider serves them bare — `while({ cond }, { ... })` and scoped-var form `while([Int is i: 0], { i < n }, { ... i++; })` (inlined to zero-allocation LLVM IR basic blocks), `repeat(count: n, worker: { ... })`, `until({ cond }, { ... })`, `Loops:run(loop:, control:)` over a `Loop` subclass; `Parallel:run(threads:, iterations:, worker:)` fans pure closures across pthreads (per-thread RNG via `math:fastRandom`; atomics via `Process:atomicAdd/Put/Get`).

Scoped region desugaring: `as: call(...)` and `as (params): call(...)` (or `return as of Type: call(...)`) desugars the remainder of the enclosing block into an anonymous callback passed as the trailing positional argument to the call, linearizing nested callback pyramids without rightward drift.

## Collections
- `Array of T`: `["a","b"]` `[]` `arr[i]` `arr[i]: v` — `length get set add pop removeAt slice clear indexOf join isEmpty each map fold filter count any`
- `Map of K to V`: `["k": v]` `[:]` `m[k]` `m[k]: v` — `getString getInt getFloat getBool get set has remove keys length each`
- `List of T`: `push appendString get set pop length clear toString` (`[Byte]` is the string-builder floor)

## Builtins (selected)
- Runtime-managed classes, instance-imported: `Output:line/print/write` (stdout), `Stderr:line/print` (stderr), `Math:` `round floor ceil toInt toFloat sqrt pow log log2 sin cos tan atan2 random fastRandom abs min max clamp`. The lowercase `output:`/`error:`/`math:` alias spellings are retired.
- `Process:` `execute(command:, args:)` `getPid()` `exit(status:)` `sleep(ms:)` `clockMs()` `peakMemoryKb()` `threadCount()` `atomicAdd/Put/Get(slot:, value:)`
- `File:` `read(path:, default:)` `write(path:, content:)` `readAsync` `writeAsync` `exists(path:)` `remove(path:)`
- `Int:toBase(base:, digits:)` `String:parseInt(base:, default:)`
- `Parallel:run(threads:, iterations:, worker:) -> Int` (sums worker returns)

## Casts
`expr as Target` — `Int` `Float` (numeric), `Hex` `Bin` `Oct` (Int→String format w/ optional width; String→Int parse, failures yield 0), class names (up/downcast, unchecked), `Any` (identity). Chaining rejected. Class instances in concatenation render class name (generated `toString`); enums render variant name.

## Memory
Pure-Spec reference counting (`base:sysinternal:Arc`) with per-scope thread-local claim pools (`base:sysinternal:Pool`), 4-bucket thread-local small-object freelists, and 24-byte `SpecBuf` small-buffer optimization; parameters are borrows.

## Compiler
- Exit: 0=ok, 1=compile/load/type/clang error, 2=usage. Diagnostics on stderr.
- `bin/spec -i file.spec -o binary`; `--emit-llvm out.ll`; `--emit-runtime out.c`; `--no-opt`; `--debug`; `--quiet`. Linting: `bin/speclint -i file.spec` (standalone utility).

- Root and floor classes `String` `Buf` `Dir` `Stringable` `Any` `CliArgs` `Arc` `Pool` `Arena` `Intern` preloaded before user code; implicit `of Any` appended to parentless non-enum classes.
- Suite: `bin/specunit -s bin/spec -t examples -t tests -t testllvm` (build the runner first: `bin/spec --quiet -i utilities/specunit/SpecUnit.spec -o bin/specunit`); sanitized wave: KNOWLEDGE-SPECDEV.md §4a.

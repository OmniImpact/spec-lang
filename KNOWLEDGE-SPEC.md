# Spec — AI Agent Bootstrap

Strictly typed, class-based, compiles to C11 via `gcc`. Written in itself: the compiler is Spec source (`spec/base/compiler/`), bootstrapped from the canonical C seed `bootstrap/spec.c`, with the self-hosting fixed point (the compiler recompiles its own sources to byte-identical C) verified on every `./bootstrap.sh`. Never-null (no null; fallible reads require `default:`). Tabs for indentation.

## Layout
- `spec/lib/base/` — the standard library, written in Spec: `core` (Any/Stringable/String), `io`, `math`, `struct` (Array/Map/List), `iterator`, `sys`. The declared namespace IS the package; directories are organization only.
- `spec/base/sysinternal/` — the C floor (Buf, Dir, Reflection): body-less declarations bound to C by the `spec_<snake(method)>` naming convention. Only same-name wrappers in `base:sys` may call the floor; the checker enforces it.
- `spec/base/compiler/` — the compiler: lexer, parser, checker, gen (CodeGenerator/BuiltinCallGenerator/DeclarationGenerator/RuntimePrelude), loader, linter, driver.
- `bootstrap/spec.c` — the canonical seed. `bin/spec` — the built compiler.

## Grammar
Keywords: `local` `contained` `replace` `merge` `is` `as` `of` `to` `if` `else` `return` `when`.
Types: `Int` `Byte` `Float` `Boolean` `String` `Function` `Any`.
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

String literals: `"..."` (escape-processed), `'...'` (raw).
Base literals: `0xFF` `0b1010` `0o755` `1_000_000` (underscore separators; bare leading zero stays decimal).
Casts: `value as Target`.

## Imports & Resolution
Array-form, pure package segments; the trailing segment names a class, omitting it imports the whole package (wildcard). The instance form `as ClassName()` materializes an owned instance scoped to the importing class — its members answer to the class-name prefix:
```spec
replace Array of Array of String is using: [
	['base', 'io', as Output()],
	['base', 'struct', Array]
];
```
The loader scans two trees — the directory of the `.spec` file being compiled and the compiler executable's (walking up while a location holds no `.spec` content) — plus the working directory, recursively, pruning locations with no `.spec` content. It keeps a map (class name → candidate files); resolution loads the candidate and verifies its **declared namespace** — the namespace is the package, the map only says where to find candidates. One class per named file (the map key is the file-name stem). The root classes `String` `Buf` `Dir` `Stringable` `Any` are preloaded before user code; implicit `of Any` is appended to parentless non-enum classes.

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
```spec
if (cond) { ... } else { ... }
local String is s: if (cond) "A" else "B";
when (value) {
	is "a", "b": { ... }
	is Pattern(Param p): { ... p ... }
	else: { ... }
}
local Int is x: when (e) { is Variant(v): v.field; else: 0; };
```
`when` on enums: exhaustiveness enforced; `else:` required for non-exhaustive coverage.

Enums:
```spec
Enum is Status { ACTIVE, INACTIVE }
Enum of Int is Code { OK: 200 }
Enum is Result { Ok(String is data), Err(Int is code) }
# Methods: .name() .ordinal() .value() .values()
# Payload constructors: Result:Ok(data: "x"); destructuring: is Result:Ok(data): { ... }
```

Loops (no `while`/`for` keywords): scoped inline `While([Int is i: 0], evaluate: { i < max }, iterate: { ... })` with function block shorthand `{ ... }` (inlines to zero-allocation C11 statement expression); `Loop` subclass + `While:run(loop:, control:)`; `Parallel:run(threads:, iterations:, worker:)` fans pure closures across pthreads (per-thread RNG via `math:fastRandom`; atomics via `Process:atomicAdd/Put/Get`).

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
Reference counting with scope-end releases; runtime binaries verified leak-free under ASan/LSan. Claim pool for transient expression results (32-slot ring); parameters are borrows. The compiler process's own AST slack at exit is a known item (arena model, plan §8).

## Compiler
- Exit: 0=ok, 1=compile/load/type/gcc error, 2=usage. Diagnostics on stderr.
- `bin/spec -i file.spec -o binary`; `--lint file.spec`; `--emit-c out.c`; `--gc=boehm`; `--quiet`.

- Root classes `String` `Buf` `Dir` `Stringable` `Any` preloaded before user code; implicit `of Any` appended to parentless non-enum classes.
- Suite: `bash utilities/run_tests.sh` (70 checks); sanitized: `bash utilities/run_sanitized.sh` (the compiler under ASan).

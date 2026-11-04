# Spec — AI Agent Bootstrap

Strictly typed, class-based, compiles to C11 via `gcc`. Self-hosted: the compiler is written in Spec. Never-null (no null; fallible reads require `default:`). Tabs for indentation.

## Grammar
Keywords: `local` `contained` `replace` `merge` `is` `as` `of` `to` `if` `else` `return` `when`.
Types: `Int` `Byte` `Float` `Boolean` `String` `Function` `Any`.
Declaration types (not keywords): `Class` `Enum`.
Conversion targets of `as`: `Hex` `Bin` `Oct`.
`using` and `group` are Loader-recognized pseudo-fields.

Declaration grammar: `<modifiers> <Type> is <name>`.
- Class: `Class of Parent1, Parent2 is Name of T { ... }` (pre-name `of` = parents, post-name `of` = generic params).
- Variable: `local Int is count: 10;`
- Method: `replace Function of Ret is name(Type is param) { ... }`; shorthand (inferred modifiers): `name(Type is p) -> Ret { ... }`
- Field: `local String is title: 'text';` or `local String is title;` (deferred, must be set in init).
- `Class is Name` with no parents implicitly extends root `Any`.

Operators: `+ - * / %` arithmetic; `& | ^ << >> ~` bitwise (Int only); `.` string concat; `== != < <= > >= is` comparison; `&& || !` logical; `as` cast.
`as` targets: `Int` `Float` `String` (numeric/String), `Hex` `Bin` `Oct` (Int↔String base conversion, optional width arg for Int→String padding). Chaining rejected; parse failures yield 0.

String literals: `"..."` (escape-processed), `'...'` (raw).
Base literals: `0xFF` `0b1010` `0o755` `1_000_000` (underscore separators; bare leading zero stays decimal).
Casts: `value as Target`.

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

## Grouping (Partials)
Fragment declares `Array of String is group: [Target];`. Loader merges into target; duplicate members = error; at most one `init`; fragments must not declare parents.

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

Loops (no `while`/`for` keywords): `Loop` subclass + `While:run(loop:, control:)`; `Parallel:run(threads:, iterations:, worker:)` fans pure closures across pthreads (per-thread RNG via `math:fastRandom`; atomics via `Process:atomicAdd/Put/Get`).

## Collections
- `Array of T`: `["a","b"]` `[]` `arr[i]` `arr[i]: v` — `length get set add pop removeAt slice clear indexOf join isEmpty each map fold filter count any`
- `Map of K to V`: `["k": v]` `[:]` `m[k]` `m[k]: v` — `getString getInt getFloat getBool get set has remove keys length each`

## Builtins (selected)
- `output:line(text)` stdout; `error:line(text)` stderr
- `math:` `round floor ceil toInt toFloat sqrt pow log log2 sin cos tan atan2 random fastRandom abs min max clamp`
- `Process:` `execute(command:, args:)` `getPid()` `exit(status:)` `sleep(ms:)` `clockMs()` `peakMemoryKb()` `threadCount()` `atomicAdd/Put/Get(slot:, value:)`
- `File:` `read(path:, default:)` `write(path:, content:)` `readAsync` `writeAsync` `exists(path:)` `remove(path:)`
- `Int:toBase(base:, digits:)` `String:parseInt(base:, default:)`
- `Parallel:run(threads:, iterations:, worker:) -> Int` (sums worker returns)

## Casts
`expr as Target` — `Int` `Float` (numeric), `Hex` `Bin` `Oct` (Int→String format w/ optional width; String→Int parse, failures yield 0), class names (up/downcast, unchecked), `Any` (identity). Chaining rejected. Class instances in concatenation render class name (generated `toString`); enums render variant name.

## Compiler
- Exit: 0=ok, 1=compile/load/type/gcc error, 2=usage. Diagnostics on stderr.
- `./spec -i file.spec -o binary`; `--lint file.spec`; `--emit-c out.c`
- Grouping: fragment declares `group: [Target]`; merges at load; duplicate members error.
- Root files `lib/base/core/Any.spec` and `Stringable.spec` preloaded before user code; implicit `of Any` appended to parentless non-enum classes.

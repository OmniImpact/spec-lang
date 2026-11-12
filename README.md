# Spec Programming Language

**Spec** is an elegant, concurrent-first, unblockable programming language that compiles directly to optimized C11 — and it is fully self-hosted: the compiler is written in Spec and reproduces its own C seed byte-for-byte on every build. Memory is automatic reference counting over per-scope claim pools — no garbage collector, no GC pauses — and the compiler itself runs on the exact same ARC machinery its generated programs use.

```spec
Class is HelloWorld{

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		line(greeting . ' ' . name);   # the as-import merges Output's line() into scope
	}

}
```

> 📖 **[README-FULL.md](README-FULL.md)** has the detailed breakdown — the design
> philosophies, the full feature list with examples, module resolution, the
> language comparison table, and the building/bootstrapping story.

---

## The Language in Brief

The entire grammar fits one small table — these are the only keywords:

| Keyword | Role |
|---|---|
| `local` | Private: invisible to children — cannot be replaced, merged, or accessed outside the declaring class |
| `contained` | Protected and final: visible to subclasses, but cannot be replaced, merged, or accessed externally |
| `replace` | Override an ancestor member (mandatory and checked; root-contract overrides are always replace) |
| `merge` | Compose with the ancestor member (array fold, or function delegation via `(args...)`) |
| `held` | Class-scoped members: one copy, reached through the class-name prefix |
| `is` | Bind a name to a declaration or value; also reads as equality in comparisons |
| `as` | Type cast (classes, numerics, and `Hex`/`Bin`/`Oct` base conversions) or scoped region callback desugaring (`as: call;`, `as (params): call;`) |
| `of` | Parent classes (pre-name: `Class of Greeter is EnglishGreeter`) or generic parameters (post-name or type-level: `Class of T is Box`, `Array of Int`) |
| `to` | Second generic parameter (`Map of K to V`, `Function of A to B`) |
| `return` | Return from a method |

Members without a visibility modifier are **public by default**: overridable via
`replace`/`merge` and callable from anywhere.

| Primitive Type | Meaning |
|---|---|
| `Int` | 64-bit signed integer |
| `Byte` | Unsigned 8-bit value (`Int`↔`Byte` via `as`) |
| `Float` | 64-bit IEEE double |
| `Boolean` | `true` / `false` |
| `String` | UTF-8 text |
| `Function` | First-class callable, typed by return (`Function of Int`) |
| `Any` | Arbitrary typed reference |

`Class` and `Enum` are compiler-known declaration types (`Class is Name { ... }`), not keywords; `Hex`, `Bin`, and `Oct` are compiler-known conversion targets of `as`.

---

## A Taste of Spec

The as-import merges a provider's functions into scope — `as Conditional()` serves `if` and `match` bare, the same way `as Output()` serves `line`:

```spec
# Merge Output and Conditional into bare scope:
replace Array of Array of String is using: [
	['base', 'sys', as Output()],
	['base', 'sys', as Conditional()]
];

# Shorthand positional if and value-yielding expression
if({ score is 21 }, {
	line('Blackjack!');
}, {
	line('Continue play');
});

local String is grade: if({ score >= 90 }, { 'A' }, { 'B' });

# Pattern matching over enums or values
match(on: state, when: [
	idle:   { 'waiting' },
	running: { 'go' },
	[idle, failed]: { 'not-going' },   # array keys match several cases
	else:   { '?' }
]);

# Predicate tables replace nested else-if ladders
match(when: [
	{ score >= 90 }: { line('Excellent'); },
	{ score >= 70 }: { line('Good'); },
	else:            { line('Needs work'); }
]);
```

Enums are first-class — payload variants, a reflective identity contract on the shared root, and exhaustiveness-checked matching:

```spec
replace Array of Array of String is using: [
	['base', 'sys', as Output()]
];

Enum is Result {
	Ok(String is data),
	Err(Int is code, String is msg),
	Pending
}

local Result is res: Result:Ok(data: 'Payload verified');
line(text: res:name());               # 'Ok'
```

Collections, closures, and combinators:

```spec
local Map of String to Int is scores: ['alice': 95, 'bob': 88];
scores['charlie']: 100;

local Int is factor: 2;
local Function of Int is multiplier: local Function of Int(Int is x){
	return x * factor;
};
local Int is doubled: numbers:map(action: local Function of Int(Int is n){ return n * factor; });
```

Loops are providers too — `as Loops()` serves `while`, `repeat`, and `until` bare, inlined directly to C11 constructs with zero allocations:

```spec
replace Array of Array of String is using: [
	['base', 'sys', as Output()],
	['base', 'sys', as Loops()]
];

# Scoped-variable while loop
while([Int is i: 0], { i < 5 }, {
	line('count: ' . (i as String));
	i++;
});

# Fixed repetitions
repeat(count: 3, worker: {
	line('hello!');
});
```

---

## Documentation

- 📖 **[README-FULL.md](README-FULL.md)**: The full breakdown — design philosophies, the complete feature list, module resolution, editor support, and the language comparison table.
- 🗺️ **[ROADMAP-ALPHA.md](ROADMAP-ALPHA.md)**: Alpha release roadmap (v0.1) — tracking the milestones toward public alpha, modular tooling, packaging, build system, and cross-platform reliability.
- 📊 **[README-PERFORMANCE.md](README-PERFORMANCE.md)**: Measured performance — the same benchmark run in C, C++, Rust, Go, Java, Kotlin, JavaScript, Python, Ruby, and Spec, with build and execution profiles. Reproduce with `utilities/run_benchmarks.sh`.
- 📚 **[Documentation Portal](docs/README.md)**: Main documentation index.
- 📖 **[Language Guide](docs/language/README.md)**: Syntax, typing system, Never Null standard, held members, matching, and the iteration model.
- 📦 **[Standard Library Reference](docs/packages/README.md)**: Package summary tables and full API reference for `base:core`, `base:math`, `base:struct`, `base:iterator`, and `base:sys` (the control-flow providers and the console/file/terminal/process surfaces).
- 📜 **[Code Style & SpecDoc Guide](docs/STYLE_GUIDE.md)**: Official code style conventions, architectural idioms, and the SpecDoc documentation standard.
- 🛠️ **[Tooling & Compiler Guide](docs/tooling/README.md)**: Compiler CLI, module loader, tab linter, and Kate editor integration.

---

## Getting Started

### Prerequisites
- **GCC or Clang** (C11 compiler with standard POSIX threads)

### Bootstrapping the Compiler
```bash
./bootstrap.sh
```

### Compiling and Running a Program
```bash
# Compile and run a basic program
bin/spec -i examples/helloworld.spec -o helloworld
./helloworld --name Daniel

# Run the scoped region and resource management demo
bin/spec -i examples/scope_as_demo.spec -o scope_demo
./scope_demo

# Emit generated C11 source code (optional)
bin/spec -i examples/helloworld.spec --emit-c helloworld.c
```

### Running Tests
```bash
# Run the complete test suite (130+ unit and integration test suites)
bin/specunit
```

### Running the Linter
```bash
# Lint a single file or entire directory trees
bin/speclint -i examples/blackjack.spec
bin/speclint -t examples -t tests

# Run the instance-model audit
bin/speclint -a -i spec/base/compiler/driver/Driver.spec
```

### Debugging
`--debug` builds with full optimization *and* debugger-friendly metadata: every
statement carries a `#line` mapping to its Spec source, and locals stay
inspectable under gdb — with all control flow inlined to native branches.

```bash
bin/spec --debug -i examples/helloworld.spec -o helloworld_dbg
gdb ./helloworld_dbg
(gdb) break helloworld.spec:19   # breakpoint on a Spec line
(gdb) run
(gdb) print name                 # "User" — Spec strings render as text
```

Source the printer helpers for Spec-shaped values and a filtered locals view:

```gdb
source utilities/spec-gdb.py
(gdb) print tags        → Array of 2 elements = {"alpha", "beta"}
(gdb) print args        → Map of 2 entries = {["mode"] = "debug", ...}
(gdb) speclocals        → only Spec-named locals; runtime internals hidden
```

Debug builds measure ~87% of release throughput (see
[README-PERFORMANCE.md](README-PERFORMANCE.md)); release builds (the default)
emit no debug metadata and remain byte-identical to the bootstrap seed.

---

## Standard Library

The standard library lives in `spec/lib/` — five packages covering the root
lattice (`base:core`), math (`base:math`), collections (`base:struct`),
iteration (`base:iterator`), and the control-flow, console, file, and process
surfaces (`base:sys`) — all written in Spec over the `base:sysinternal`
C floor. A summary table of every package and its functions lives in the
**[Standard Library Reference](docs/packages/README.md)**.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

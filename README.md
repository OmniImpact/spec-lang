# Spec Programming Language

**Spec** is an elegant, concurrent-first programming language that compiles directly to native machine code via LLVM IR — and it is fully self-hosted: the compiler is written in Spec and reproduces its own LLVM IR (`bootstrap/spec.ll`) and C PAL (`bootstrap/spec_runtime.c`) seeds byte-for-byte on every build. Memory is automatic reference counting over per-scope claim pools implemented in pure Spec — no garbage collector, no GC pauses — and the compiler itself runs on the exact same ARC machinery its generated programs use.

```spec
Class is HelloWorld{

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		line('Hello, ' . name);        # the as-import merges Output's line() into scope
	}

}
```

> 📖 **[README-FULL.md](README-FULL.md)** has the detailed breakdown — the design
> philosophies, the full feature list with examples, module resolution, the
> language comparison table, and the building/bootstrapping story.

---

## Constructs Are Libraries, Not Keywords

The keyword table below is frozen at ten words. Control flow, error
transport, and every future construct enter the language as **facility
classes** — ordinary Spec classes resolved through the `using` table, the
way `as Conditional()` serves `if` and `match` and `as Loops()` serves
`while`. The compiler recognizes their calls and inlines them; the lexer
never learns their names. This is a contract, not a style preference:

1. **No new keywords. Ever.** If a feature cannot be expressed as a
   facility method call, it does not go in the language.
2. **Two tiers or it does not ship.** Every construct MUST ship with
   (a) a compiler-lowered fast path for literal-closure calls — real
   basic blocks, zero allocation — and (b) a complete runtime twin that
   behaves identically when the call receives function values. A construct
   that only works when its arguments are literals is a trap, not a
   feature.
3. **Done means all six gates.** Lowering. Runtime twin. Checker typing
   with pointed diagnostics. Negative tests asserting those diagnostics.
   Lint rules steering correct use. Documented jurisdiction. Four of six
   is not done, and we do not merge four of six.
4. **Nothing is reserved.** `if`, `while`, `match`, and the future `try`
   remain ordinary method names; user code may define its own and shadow
   ours.

The error story holds the same line — the phased rollout lives in
[ERRORS-PLAN.md](ERRORS-PLAN.md):

- **One currency.** Every error in every transport is a `SpecError of E`.
  Nothing ever flattens an error to `String`.
- **Three transports, fixed jurisdictions.** Result-return for sync,
  expected, default-less failures; callbacks for async observation at the
  call site; unwinding as the fallback and the cross-thread carrier.
  No fourth transport.
- **No facility-held error state.** A parser that parks its failure on a
  field for the caller to check afterwards is banned; the
  `Json:hasError()` pattern is being removed, not reformed.
- **Failures cannot be swallowed.** "Never Null" defaults are sugar over
  results; an absent `onError` re-raises — it never no-ops.

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
| `Byte` / `UInt8` | Unsigned 8-bit integer |
| `UInt16` / `UInt32` / `UInt64` | Fixed-width unsigned integers (`as` casts to/from `Int`) |
| `Float` | 64-bit IEEE double |
| `Boolean` | `true` / `false` |
| `Str` | Lightweight UTF-8-safe byte/ASCII string (`Buf -> Str -> String`) |
| `String` | Full Unicode UTF-8 text (subclass of `Str`) |
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

Loops are providers too — `as Loops()` serves `while`, `repeat`, and `until` bare, inlined directly to native LLVM IR basic blocks with zero allocations:

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
- 📦 **[Standard Library Reference](docs/packages/README.md)**: Package summary tables and full API reference for `base:core`, `base:math`, `base:struct`, `base:iterator`, `base:data`, `base:net`, `base:audio`, and `base:sys`.
- 📜 **[Code Style & SpecDoc Guide](docs/STYLE_GUIDE.md)**: Official code style conventions, architectural idioms, and the SpecDoc documentation standard.
- 🛠️ **[Tooling & Compiler Guide](docs/tooling/README.md)**: Compiler CLI (`spec`), project scaffolder (`specinit`), build orchestrator (`specbuild`), test runner (`specunit`), linter (`speclint`), and editor integrations.

---

## Getting Started

### Prerequisites
- **Clang** (LLVM/C11 toolchain with standard POSIX threads)

### Bootstrapping the Compiler
```bash
./bootstrap.sh
```

### Compiling and Running a Program
```bash
# Compile and run a basic program
bin/spec -i examples/helloworld/src/HelloWorld.spec -s examples/helloworld/src -o helloworld
./helloworld --name Daniel

# Run the pure-Spec HTTPS + TLS 1.3 weather forecast example (Cleo + MVVM)
bin/specbuild examples/cleoweather build
./bin/cleoweather

# Emit generated LLVM IR (optional)
bin/spec -i examples/helloworld/src/HelloWorld.spec -s examples/helloworld/src --emit-llvm helloworld.ll
```

### Running Tests
```bash
# Build and run the full compiler + library regression suite (177 suites, 591 tests)
bin/spec --quiet -i utilities/specunit/SpecUnit.spec -o bin/specunit
bin/specunit -s bin/spec -t test -t testcompiler
```

### Running the Linter
```bash
# Lint a single file or entire directory trees
bin/speclint -i examples/theojack/src/TheoJack.spec
bin/speclint -t examples -t test

# Run the instance-model audit
bin/speclint -a -i spec/base/compiler/driver/Driver.spec
```

### Debugging
`--debug` builds with full optimization *and* debugger-friendly metadata: every
statement carries source location metadata mapping to its Spec source, and locals stay
inspectable under gdb — with all control flow inlined to native branches.

```bash
bin/spec --debug -i examples/helloworld/src/HelloWorld.spec -s examples/helloworld/src -o helloworld_dbg
gdb ./helloworld_dbg
(gdb) break HelloWorld.spec:16   # breakpoint on a Spec line
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

The standard library lives in `spec/lib/` — packages covering the root
lattice (`base:core`: `Any`, `Str`, `String`, `Enum`, `SpecError`), math and
cryptography (`base:math`, `base:math:crypto`: SHA-256/HMAC/HKDF, X25519,
ChaCha20-Poly1305, AES-128-GCM, X.509 DER/PEM/CA trust verification),
collections (`base:struct`: `Array`, `Map`, `List`, `Stack`), iteration
(`base:iterator`), JSON serialization (`base:data`), networking (`base:net`:
TCP `Socket`, `Url`, async HTTP/1.1 client, and pure-Spec TLS 1.3 `TlsClient` +
`TlsVerifier`), terminal UI (`base:cleo`), audio (`base:audio`), and the
control-flow, console, file, time, OS dispatch, threading (`ThreadScope`/`Task`),
and process surfaces (`base:sys`) — all written in Spec over the
`base:sysinternal` unmanaged floor (`Arc`, `Slab`, `Heap`, `Pool`, `Arena`,
`Intern`, `Mem`) and the C OS PAL in `spec/runtime/`.
A summary table of every package and its functions lives in the
**[Standard Library Reference](docs/packages/README.md)**.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

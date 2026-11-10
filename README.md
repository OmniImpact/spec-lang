# Spec Programming Language

**Spec** is an elegant, concurrent-first, unblockable programming language that compiles directly to optimized C11 — and it is fully self-hosted: the compiler is written in Spec and reproduces its own C seed byte-for-byte on every build.

```spec
Class is HelloWorld{

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'io'],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		Output:line(greeting . ' ' . name);   # Output:line or bare line() — the as-import merges both into scope
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

Conditionals are calls to the `Conditional` provider — statement form, value-yielding branches, and match tables all share one call shape:

```spec
Conditional:if(check: { score is 21 }, then: {
	Output:line(text: 'Blackjack!');
}, else: {
	Output:line(text: 'Continue play');
});

local String is grade: Conditional:if(check: { score >= 90 }, then: { 'A' }, else: { 'B' });

Cases:match(on: state, when: [
	idle:   { 'waiting' },
	running: { 'go' },
	[idle, failed]: { 'not-going' },   # array keys match several cases
	else:   { '?' }
]);
```

Enums are first-class — payload variants, synthesized reflection methods, and exhaustiveness-checked matching:

```spec
Enum is Result {
	Ok(String is data),
	Err(Int is code, String is msg),
	Pending
}

local Result is res: Result:Ok(data: 'Payload verified');
Output:line(text: res:name());          # 'Ok'
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

Loops are providers too — no primitive `while`, zero-allocation inlining:

```spec
local Int is total: 0;
while(
	evaluate: local Function of Boolean(){ return total < 5; },
	iteration: local Function of Boolean(){
		total: total + 1;
		return true;
	}
);
```

---

## Documentation

- 📖 **[README-FULL.md](README-FULL.md)**: The full breakdown — design philosophies, the complete feature list, module resolution, editor support, and the language comparison table.
- 📚 **[Documentation Portal](docs/README.md)**: Main documentation index.
- 📖 **[Language Guide](docs/language/README.md)**: Syntax, typing system, Never Null standard, held members, matching, and the iteration model.
- 📦 **[Standard Library Reference](docs/packages/README.md)**: Package summary tables and full API reference for `base:core`, `base:io`, `base:math`, `base:struct`, `base:iterator`, and `base:sys`.
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

### Running the Linter
```bash
bin/spec --lint examples/blackjack.spec
```

---

## Standard Library

The standard library lives in `spec/lib/` — six packages covering the root
lattice (`base:core`), terminal and file I/O (`base:io`), math (`base:math`),
collections (`base:struct`), iteration (`base:iterator`), and process control
and parallelism (`base:sys`) — all written in Spec over the `base:sysinternal`
C floor. A summary table of every package and its functions lives in the
**[Standard Library Reference](docs/packages/README.md)**.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

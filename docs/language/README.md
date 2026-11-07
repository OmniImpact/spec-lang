[Documentation](../README.md) > **Language Guide**

# Spec Language Guide

**Spec** is an object-oriented, statically typed programming language designed with an emphasis on readable syntax, concurrency-first unlocked control flow, and strict value safety.

---

## Table of Contents
1. [Language Syntax & Structure](#language-syntax--structure)
   - [Classes & Entry Point](#classes--entry-point)
   - [User-Defined Generic Classes](#user-defined-generic-classes)
   - [Variables & Declarations](#variables--declarations)
   - [Functions & Methods](#functions--methods)
   - [Default Parameter Values & Named-Argument Reordering](#default-parameter-values--named-argument-reordering)
   - [First-Class Capturing Closures & Direct Invocation](#first-class-capturing-closures--direct-invocation)
   - [First-Class Enums (`Enum`, `Enum of Type`, & Tagged Unions)](#first-class-enums)
   - [Imports & `using`](#imports--using)
2. [Types & Literals](#types--literals)
   - [Primitives](#primitives)
   - [String Literals](#string-literals)
   - [Generic Collections & Map Literals](#generic-collections)
   - [The `Function` Type](#the-function-type)
   - [The `Enum` Type](#the-enum-type)
   - [The `Any` Type](#the-any-type)
3. [The "Never Null" Standard](#the-never-null-standard)
4. [Operators & Expressions](#operators--expressions)
   - [Arithmetic Operators](#arithmetic-operators)
   - [String Concatenation](#string-concatenation)
   - [Member Access & Method Calls](#member-access--method-calls)
   - [Bracket Indexing & Assignment (`arr[i]`, `map[k]`)](#bracket-indexing--assignment)
   - [Inline Conditional Expressions (`if` / `else`)](#inline-conditional-expressions)
   - [String Inspection Primitives](#string-inspection-primitives)
5. [Control Flow & Branching](#control-flow--branching)
   - [Conditionals (`if` / `else`)](#conditionals)
   - [Branching with `when` (`when` Statements & Expressions)](#branching-with-when)
   - [Pattern Destructuring with `when`](#pattern-destructuring-with-when)
6. [Compiler Error Recovery & Multi-File Provenance](#compiler-error-recovery--multi-file-provenance)
7. [Unblockable Concurrency & Iteration Model](#unblockable-concurrency--iteration-model)
   - [Pure Loop Decoupling (`Loop`, `While:run`)](#pure-loop-decoupling)
   - [Terminating Iterations (No `break` Keyword)](#terminating-iterations-no-break-keyword)
   - [Event-Driven Non-Blocking Input](#event-driven-non-blocking-input)

---

## Language Syntax & Structure

### Classes & Entry Point
Every program is organized into classes. The runtime instantiates the class containing an `init` function as the application entry point:

```spec
Class is HelloWorld{

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		output:line("Hello, World!");
	}

}
```

### User-Defined Generic Classes
Classes can declare one or more generic type parameters using the `of <Type>` or `of <Type1> to <Type2>` clauses:

```spec
Class is Box of T{
	local T is val;

	replace Function is init(T is val){
		self:val: val;
	}

	replace Function of T is get(){
		return self:val;
	}

	replace Function is set(T is newVal){
		self:val: newVal;
	}
}

Class is Pair of A to B{
	local A is first;
	local B is second;

	replace Function is init(A is first, B is second){
		self:first: first;
		self:second: second;
	}

	replace Function of A is getFirst(){
		return self:first;
	}

	replace Function of B is getSecond(){
		return self:second;
	}
}
```

#### Instantiation & Type Inference
Generic classes are instantiated with explicit type annotations:
```spec
local Box of String is strBox: Box:init(val: "Hello Generics");
local String is msg: strBox:get();

local Box of Int is intBox: Box:init(val: 42);
local Int is num: intBox:get();

local Pair of String to Int is pair: Pair:init(first: "port", second: 8080);
local String is key: pair:getFirst();
local Int is val: pair:getSecond();
```
The compiler automatically substitutes generic type parameters across field storage and method return signatures.

### Inheritance & Ambiguous Implementations
Method dispatch is virtual: the most-derived override runs regardless of the
static type of the reference. When two unrelated parents provide concrete
implementations of the same method and the class does not declare it itself,
this is a compile error — declare the method (`replace` or `merge`) to resolve
the conflict. Abstract declarations never conflict: unimplemented methods and
valueless fields compose into interface contracts. A shared base reached via
multiple paths counts once (diamond sharing is not a conflict).

### The Root Class (`Any`)
Every class without explicit parents implicitly extends the root class `Any`
(`Class of Stringable is Any`), which supplies:
- `toString()` — default rendering via the declaring class name (override with `replace`)
- `init()` — default no-op constructor
- the `using` declaration slot

`typeName()` on any instance reports its runtime class. Any-typed references
dispatch `Any`-declared methods (like `toString`) through the receiver's vtable.

### Member Visibility
Members are **public by default** — overridable and callable from anywhere.

| Modifier | Overridable | Accessible from |
|---|---|---|
| *(none)* — public | yes (`replace`/`merge`) | everywhere |
| `local` | no | the declaring class only |
| `contained` | no | the declaring class and its subclasses |

Declaring a member with the same name as a `local` or `contained` ancestor member
is a compile error: private members cannot be shadowed — rename, or make the
ancestor public and use `replace`/`merge`.

### Declaring Classes (`Class is Name`)
Classes are declared with the same binder grammar as enums and variables — `Type is Name`:

```spec
Class is Greeter{
	...
}
```

Inheritance and generic parameters follow the declaration name:

```spec
of Greeter  is EnglishGreeter{ ... }
Class of T is Box { ... }
```

Because declarations are type-level constructs, the reflection descriptor type was renamed `base:reflect:Class` → `base:reflect:ClassInfo`; the lowercase `class` keyword has been retired and files using it receive a pointed syntax error.

### Variables & Declarations
Variables are declared using `<Modifiers> <Type> is <name>: <initial_value>;`:

```spec
local Int is score: 100;
local Float is ratio: 0.75;
local String is greeting: "Welcome";
```

### Functions & Methods
Methods and functions declare their signatures using the `Function` type:
- **Void / Default return**: `Function is <name>(<Params>)` (e.g. `replace Function is init(...)`).
- **Typed return**: `Function of <ReturnType> is <name>(<Params>)` (e.g. `Function of Int is add(...)`).
- Modifiers include `local` (scoped to class), `replace` (overriding an inherited member), and `merge` (data-structure-aware override for fields).
- **`merge`** is the data-structure-aware counterpart of `replace`: valid on fields whose type supports merging (currently `Array`), it folds the ancestor's constant array literal and the child's into one — parent items first, then child items — satisfying the override requirement without `replace`:

```spec
of MergeBase is MergeChild{
	merge local Array of Array of String is using: [['base', 'struct', Array]];
	merge local Array of String is tags: ["extended"];
}
```

`merge` is folded during type checking (the merge ceases to exist before code generation); it is rejected on non-mergeable types.

#### Function Merge (Delegation)

`merge` on a method composes with the parent's *behavior*: the method must contain a
**forward statement** — a bare argument list — that delegates to the nearest parent
implementation. Arguments may be constants or derived from the method's parameters:

```spec
of LoggerBase is ChildLogger{
	merge local Function of Int is add(Int is a, Int is b){
		local Int is bumped: a + 100;
		(bumped, b);
	}
}
```

- The forward's value is returned implicitly for value-returning parents.
- **Partial forwards** (fewer arguments than the parent's parameters) must name each
  argument; omitted parameters fall back to their declared defaults: `(n: n);`
- The parent must be concrete (an abstract parent method is a compile error).
- Delegation chains compose: each `merge` forwards to the nearest parent implementation.
- `merge` also chains constructors: `merge local Function is init(String is tag){ (tag); }`
- Merge overrides dispatch **virtually**: calling through a base-typed reference
  reaches the forward exactly like a subclass-typed call.

```spec
# Explicit return type
Function of Int is add(Int is a, Int is b){
	return a + b;
}

# Void return type
Function is logMessage(String is msg){
	output:line(msg);
}
```

#### Property Initialization Shorthand (`self:field`)
Constructors can initialize instance fields directly from parameter lists using the `self:field` parameter shorthand:

```spec
Class is Issue{
	Int is line;
	Boolean is isWarning;
	String is message;

	## Constructor auto-assigns fields without manual assignment statements
	replace Function is init(self:line, self:isWarning, self:message){
	}
}
```

#### Anonymous Function Literals
Functions can be passed inline as first-class expressions using keyword-based anonymous function syntax:

```spec
# Anonymous function expression
words:each(action: local Function(word){
	output:line(word);
});

# Anonymous function with explicit return type
local Boolean is hasMatch: words:any(predicate: local Function of Boolean(String is word){
	return word is "target";
});
```

#### Default Parameter Values & Named-Argument Reordering
Method and function parameters can declare default fallback values using `: <default_expr>` syntax:

```spec
replace Function of String is greet(String is name, String is prefix: "Hello", String is suffix: "!"){
	return prefix . ", " . name . suffix;
}

replace Function of Int is calculate(Int is a, Int is b: 10, Int is c: 100){
	return (a * b) + c;
}
```

At call sites:
- **Defaults can be omitted**: Any parameter with a default value is optional.
- **Named arguments can be passed in any order**:
  ```spec
  # All defaults used for prefix and suffix
  local String is g1: self:greet(name: "Spec"); # "Hello, Spec!"

  # Override suffix only, keeping prefix default
  local String is g2: self:greet(name: "World", suffix: "."); # "Hello, World."

  # Arbitrary named argument ordering
  local String is g3: self:greet(suffix: "!!!", prefix: "Welcome", name: "Daniel"); # "Welcome, Daniel!!!"

  # Numeric defaults with arbitrary ordering
  local Int is res1: self:calculate(a: 5); # (5 * 10) + 100 = 150
  local Int is res2: self:calculate(c: 200, a: 3); # (3 * 10) + 200 = 230
  ```

#### First-Class Capturing Closures & Direct Invocation
Standalone `Function` variables can store anonymous functions that capture outer local variables and `self` automatically. Furthermore, any `Function` variable can be invoked directly like a standard function call:

```spec
local Int is factor: 10;
local Int is baseline: 5;

# Closure captures outer variables 'factor' and 'baseline'
local Function of Int is compute: local Function of Int(Int is x){
	return (x * factor) + baseline;
};

# Direct invocation of Function variable
local Int is r1: compute(x: 3); # (3 * 10) + 5 = 35
local Int is r2: compute(x: 7); # (7 * 10) + 5 = 75

local String is tag: "[INFO]";
local Function of String is logMsg: local Function of String(String is text){
	return tag . " " . text;
};
local String is formatted: logMsg(text: "Ready"); # "[INFO] Ready"
```

### First-Class Enums
Enums in Spec are defined using the `Enum` type, modeled directly after `Function`. Enums can be discrete (unbacked) or explicitly backed by a primitive type like `Int` or `String`:

#### Discrete Enum
```spec
Enum is TokenKind {
	KEYWORD,
	IDENTIFIER,
	NUMBER,
	STRING,
	EOF
}
```

#### Backed Enum (`Enum of Type is Name`)
```spec
Enum of Int is HttpStatus {
	OK: 200,
	CREATED: 201,
	NOT_FOUND: 404,
	SERVER_ERROR: 500
}

Enum of String is LogLevel {
	DEBUG: "DBG",
	INFO: "INF",
	WARN: "WRN",
	ERROR: "ERR"
}
```

#### Enum Reflection & Methods
Every enum type provides built-in reflection and inspection methods:
- `Enum:values() -> Array`: Returns an array containing all variants of the enum.
- `instance:name() -> String`: Returns the identifier name of the variant (e.g. `"NOT_FOUND"`).
- `instance:value() -> Value`: Returns the backing value (or ordinal integer if unbacked).
- `instance:ordinal() -> Int`: Returns the 0-indexed discrete ordinal position.
- `instance:toString() -> String`: Formats the enum variant for display.

#### Tagged Union Enums (Algebraic Data Types)
Spec supports algebraic data types where enum variants carry strongly typed payloads:

```spec
Enum is Result {
	Ok(String is data),
	Err(Int is code, String is msg),
	Pending
}

Enum is Option {
	Some(Int is value),
	None
}
```

##### Constructing Variants
Payload variants are constructed like constructors on the enum type:
```spec
local Result is r1: Result:Ok(data: "Payload verified");
local Result is r2: Result:Err(code: 404, msg: "Endpoint not found");
local Result is r3: Result:Pending;

local Option is opt1: Option:Some(value: 42);
local Option is opt2: Option:None;
```

Payload variants are matched and destructured using Spec's `when` syntax (see [Pattern Destructuring with `when`](#pattern-destructuring-with-when)).

### Imports & `using`
Packages are imported via the class `using` property. Each entry names the
package segments plus the class to load; an entry ending at the package
imports the whole package (the wildcard):
```spec
replace Array of Array of String is using: [
	['base', 'struct', Array],
	['base', 'math', Math],
	['base', 'io', Output],
	['base', 'sys', Process],
	['base', 'iterator', While]
];
```
Imports map directly to `.spec` files in the standard library (`lib/`) or project directory.

### Class Grouping (Partial Classes)

A large class can be split across multiple files using the `group` pseudo-field (a
Loader-recognized sibling of `using`). Every fragment declares the class it belongs
to; at load time the Loader merges all fragments into a single class:

```spec
## CodeGeneratorExpressions.spec
Class is CodeGeneratorExpressions{

	replace Array of String is group: [CodeGenerator];

	replace Function of String is generateExpression(Expression is expr){
		...
	}
}
```

Rules enforced by the Loader:
- Fragments never exist as types; the merged class carries the group's name.
- A group with no primary file is created from the union of its fragments.
- Duplicate member names across fragments are a load error naming both source files.
- At most one `init` per merged class; fragments must not declare parent classes.
- `using` arrays are combined (deduplicated, order preserved).
- A class whose name equals its own group target is an opt-in same-name partial:
  duplicate same-named declarations merge instead of being dropped.

---

## Types & Literals

### Primitives
- **`Int` / `int`**: 64-bit signed integer (`42`, `-10`).
- **`Float` / `float`**: 64-bit IEEE double-precision float (`3.14`, `-0.01`).
- **`Boolean` / `bool`**: Boolean value (`true`, `false`).
- **`String`**: UTF-8 string.

### String Literals
- **Double-Quoted (`"..."`)**: Interprets escape sequences:
  - `\n` (Newline), `\t` (Tab), `\r` (Carriage Return), `\\` (Backslash), `\"` (Quote).
- **Single-Quoted (`'...'`)**: Raw literals where backslashes are preserved literally.

```spec
local String is formatted: "Line 1\tTabbed\nLine 2";
local String is rawPath: 'C:\Windows\System32';
```

### Numeric Base Literals
Integer literals accept `0x` (hex), `0b` (binary), and `0o` (octal) prefixes, with
underscore separators in any base. A bare leading zero stays **decimal** (Spec has
no C-style octal footgun); all literals normalize to decimal before code generation.

```spec
local Int is mask: 0xFF00;
local Int is flags: 0b1010_0011;
local Int is perm: 0o755;
local Int is big: 1_000_000;
```

### Base Conversion
- `n:toBase(base: Int, digits: Int) -> String` — formats an Int in base 2..36
  (lowercase digits), zero-padded to `digits` width when provided.
- `s:parseInt(base: Int, default: Int) -> Int` — parses digits in the given base
  (default 10); a `0x`/`0b`/`0o` prefix overrides the base; underscores are
  tolerated; invalid input yields `default:`.

```spec
local String is hex: 65516:toBase(base: 16);
local Int is port: "1F90":parseInt(base: 16, default: 0);
```

### Generic Collections & Map Literals
Spec provides dynamic array collections and hash map collections with first-class literal initializers:
- `Array of <ElementType>`: Initialized via `[elem1, elem2, ...]`. Empty array: `[]`.
- `Map of <KeyType> to <ValueType>`: Initialized via `["key1": val1, "key2": val2, ...]`. Empty map: `[:]`.

```spec
# Array literal
local Array of String is fruits: ["Apple", "Banana", "Cherry"];
local Array of Int is emptyList: [];

# Map literal
local Map of String to Int is scores: ["alice": 95, "bob": 88];
local Map of String to String is config: [
	"host": "localhost",
	"port": "8080"
];

# Empty map literal
local Map of String to Int is emptyMap: [:];
```

### The `Function` Type
`Function` is a first-class type in Spec. It is used both for declaring method signatures and for storing and passing callables, event handlers, and callbacks as parameters or variables:
- `Function`: Represents a void or generic callable.
- `Function of ReturnType`: Callable returning a value of type `ReturnType`.
- `Function of ParamType to ReturnType`: Callable accepting `ParamType` and returning `ReturnType`.

```spec
# Storing a callback or predicate in a variable
local Function of String to Boolean is validator;

# Passing a function as a parameter
replace Function is execute(Function is callback){
	output:line("Executing callback...");
}
```

### The `Any` Type
`Any` represents an arbitrary typed pointer or reference, used in generic containers and event callbacks.

---

## The "Never Null" Standard

Spec eliminates null reference bugs by making `null` nonexistent as a runtime value:
1. **Concrete Values Required**: You cannot assign or pass null. Code attempting to use null values will not compile.
2. **Empty Collections**: Items can have no elements (`[]`, length 0).
3. **Deferred Initialization**: Class fields may be declared without inline values provided they are initialized in `init(...)` before any read access.
4. **Required Defaults for Fallible Reads**: Any read operation from an optionally empty source requires an explicit default argument:
   ```spec
   local String is val: map:getString(key: "username", default: "Guest");
   local String is popped: array:pop(default: "EMPTY");
   local String is char: text:charAt(index: 5, default: " ");
   local String is fileText: File:read(path: "config.cfg", default: "{}");
   ```
5. **No Null Return Keyword or Type**: Void methods are declared simply as `Function is <name>(...)` without any `of null` clause.

---

## Operators & Expressions

### Type Casts (`as`)
The `as` operator treats a value as another type — classes, numerics, and the base
pseudo-types `Hex`, `Bin`, and `Oct` share one syntax. It binds tighter than every
binary operator; chaining (`x as A as B`) is a syntax error.

```spec
local Animal is a: dog as Animal;       # class upcast (virtual dispatch preserved)
local Dog is d: a as Dog;               # downcast (unchecked, C semantics)
local Int is n: 3.9 as Int;             # numeric truncation (== math:toInt)
local Float is f: 7 as Float;           # widening (== math:toFloat)
local String is h: 65516 as Hex;        # format: "ffec" (Bin, Oct too; width: `as Bin(8)`)
local Int is back: "ffec" as Hex;       # parse: 65516 (invalid input yields 0)
```

`as Int` on a String parses base 10 (fallback 0); `parseInt(default:)` remains the
explicit form for fallible parsing. Casting between unrelated classes is a compile
error; casting to an enum is rejected (construct a variant instead).

### String Rendering
Concatenation and `as String` render every value type: primitives via their
canonical text, enum variants by name, and class instances through a generated
`toString()` that returns the class name (a user-defined `toString` method
overrides it and requires `replace`).

### Bitwise Operators
Bitwise operations follow C precedence: `~` (complement), `<<` / `>>` (shifts, looser
than `+`/`-`), `&`, `^`, `|` (tightest to loosest, all between equality and `&&`).
All require `Int` operands and yield `Int`; non-Int operands are compile errors.

```spec
local Int is flags: 0b0000_0100 | 0b0000_0011;
local Int is cleared: flags & ~(0b0000_0011);
local Int is byte: (value >> 8) & 0xFF;
```

Shifts are arithmetic on signed 64-bit integers.

### Arithmetic Operators
`+`, `-`, `*`, `/`, `%` with standard precedence and parentheses grouping:
```spec
local Int is total: (10 + 2) * 3 - (8 / 2);
```

### String Concatenation
The dot operator (`.`) concatenates strings and automatically formats numeric primitives:
```spec
output:line("Total score: " . score . " points");
```

### Member Access & Method Calls
The colon (`:`) invokes methods and traverses namespaces:
```spec
output:line("Log text");
local Float is r: math:round(value: 3.7);
```

### Bracket Indexing & Assignment
Spec provides bracket indexing syntax for both `Array` and `Map` collections:
- **R-Value Indexing (`collection[index]`)**:
  - `array[index]`: Zero-based element access (e.g. `fruits[0]`).
  - `map[key]`: Hash map key lookup (e.g. `scores["alice"]`, `config["host"]`).
- **L-Value Index Assignment (`collection[index]: value;`)**:
  - `array[index]: val;`: Replaces element at position `index`.
  - `map[key]: val;`: Sets or updates the entry for `key`.

```spec
# Map indexing and assignment
local Map of String to Int is scores: ["alice": 95, "bob": 88];
local Int is aScore: scores["alice"]; # 95
scores["charlie"]: 100; # Insert new key
scores["alice"]: 98;   # Update existing key

# Array indexing and assignment
local Array of String is languages: ["C", "Java", "Spec"];
local String is first: languages[0]; # "C"
languages[1]: "Spec C11"; # Replaces "Java"
```

### Inline Conditional Expressions
Spec provides inline `if (...) expr else expr` conditionals without punctuation ambiguity (`?:`). Both branches are required to uphold Spec's "Never Null" standard:

```spec
local String is status: if (isReady) "Ready" else "Pending";
local String is grade: if (score >= 90) "A" else if (score >= 80) "B" else "C";
```

### String Inspection Primitives
- `str:length() -> Int`
- `str:charAt(index: Int, default: String) -> String`
- `str:substring(start: Int, end: Int) -> String`
- `str:indexOf(search: String, default: Int) -> Int`
- `str:isDigit() -> Boolean`
- `str:isAlpha() -> Boolean`
- `str:isWhitespace() -> Boolean`

---

## Control Flow & Branching

### Conditionals
Standard `if`, `else if`, and `else` blocks with boolean comparisons (`==`, `is`, `!=`, `<`, `<=`, `>`, `>=`) and logical operators (`&&`, `||`, `!`):

The `is` keyword can be used interchangeably with `==` for expressive, natural equality checks:

```spec
if (score is 21) {
	output:line("Blackjack!");
} else if (status is "ERROR") {
	output:line("Failed!");
} else if (score > 21) {
	output:line("Bust!");
} else {
	output:line("Continue play");
}
```

### Branching with `when`
The `when` keyword provides isolated branch matching for both statements and expressions without fallthrough (no `break` required). Branches match using the `is` operator, can match multiple candidates via comma separation (`is A, B:`), and conclude with an optional or required `else:` fallback.

#### `when` Statement
```spec
when (status) {
	is OK, CREATED: {
		output:line("Success");
	}
	is NOT_FOUND: {
		output:line("Resource not found");
	}
	else: {
		output:line("Other error");
	}
}
```

#### `when` Expression
When used as an expression, `when` returns a value. For `Enum` subjects, the compiler verifies full exhaustiveness at compile time—if all variants are covered, `else:` may be omitted:

```spec
local String is description: when (tok) {
	is KEYWORD: "Reserved Keyword";
	is IDENTIFIER: "Type or Variable Name";
	is NUMBER: "Numeric Literal";
	is STRING: "String Constant";
	is EOF: "End of Input";
};
```

If an enum variant is missing, the compiler enforces an explicit `else:` fallback or raises a compile-time exhaustiveness error. For open types (such as `Int` or `String`), `else:` is strictly required.

### Pattern Destructuring with `when`
When pattern matching over tagged union enums, `when` arms can destructure variant payloads into newly bound local variables for both statements and expressions:

#### Destructuring in `when` Statements
```spec
local Result is res: Result:Ok(data: "Connection established");

when (res) {
	is Ok(d): {
		output:line("Success: " . d);
	}
	is Err(c, m): {
		output:line("Error code " . c . ": " . m);
	}
	is Pending: {
		output:line("Operation pending...");
	}
}
```

#### Destructuring in `when` Expressions
```spec
local String is statusSummary: when (res) {
	is Ok(d): "Done: " . d;
	is Err(c, m): "Failed (" . c . "): " . m;
	is Pending: "In Progress";
};
```

---

## Compiler Error Recovery & Multi-File Provenance

The Spec compiler coordinates multi-file compilation with precise diagnostics:
- **Syntax Error Coordinates**: Syntax errors report precise file, line, and column coordinates:
  ```text
  [SyntaxError] [examples/program.spec:42:15] Expected ')', found '}'
  ```
- **Clean Synchronization**: The parser records syntax errors, synchronizes at statement boundaries, and cleanly halts without cascading crashes.
- **Semantic Type Provenance**: The semantic type checker annotates diagnostics with source file provenance:
  ```text
  [spec/lib/base/struct/Array.spec] Incompatible assignment type
  ```

---

## Unblockable Concurrency & Iteration Model

Spec does not include primitive `while` or `break` keywords in its grammar. Instead, all looping is decoupled into explicit state-machine lifecycle contracts driven by the standard library (`base:iterator:*`).

### Pure Loop Decoupling
Loops in Spec are non-blocking, decoupled state machines:
```spec
of Loop is CounterLoop{
	local Int is count: 0;

	replace Function of Boolean is evaluate(){
		return count < 5;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		count: count + 1;
		output:line("Step: " . count);
		return true;
	}
}

While:run(loop: CounterLoop:init(), control: LoopControl:init());
```

### Terminating Iterations (No `break` Keyword)
Because loops are evaluated explicitly per iteration:
- **Returning `false`**: Immediately terminates the loop without needing a `break` keyword.
- **`control:stop()`**: Halts iteration from within a callback or helper.

```spec
replace Function of Boolean is iteration(LoopControl is control){
	count: count + 1;
	if (count == 5) {
		return false; # Halts loop execution cleanly
	}
	return true;
}
```

### Event-Driven Non-Blocking Input
Interactive console I/O delegates to event handlers rather than freezing thread execution:
```spec
of InputHandler is ActionHandler{
	replace Function is onInput(String is action){
		output:line("User chose: " . action);
	}
}

Input:prompt(ActionHandler:init());
```

---

## Quick Navigation

| Target | Description | Path |
|---|---|---|
| 🏠 **Repository Root** | Project home & overview | [README.md](../../README.md) |
| 📚 **Documentation Portal** | Docs index | [docs/README.md](../README.md) |
| 📦 **Standard Packages** | Standard library API reference | [docs/packages/README.md](../packages/README.md) |
| 🛠️ **Tooling Guide** | Compiler CLI, linter, editor plugins | [docs/tooling/README.md](../tooling/README.md) |
| 📂 **Examples** | Demo programs | [examples/](../../examples) |
| 🧪 **Tests** | Positive and negative test suites | [tests/](../../tests) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../../TASKS.md) |


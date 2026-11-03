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
7. [Unlockable Concurrency & Iteration Model](#unlockable-concurrency--iteration-model)
   - [Pure Loop Decoupling (`Loop`, `While:run`)](#pure-loop-decoupling)
   - [Terminating Iterations (No `break` Keyword)](#terminating-iterations-no-break-keyword)
   - [Event-Driven Non-Blocking Input](#event-driven-non-blocking-input)

---

## Language Syntax & Structure

### Classes & Entry Point
Every program is organized into classes. The runtime instantiates the class containing an `init` function as the application entry point:

```spec
class HelloWorld{

	replace local Array of String is using: [
		base:struct:Map,
		base:io:*
	];

	replace local Function is init(Map of String to String is args){
		output:line("Hello, World!");
	}

}
```

### User-Defined Generic Classes
Classes can declare one or more generic type parameters using the `of <Type>` or `of <Type1> to <Type2>` clauses:

```spec
class Box of T{
	local T is val;

	replace local Function is init(T is val){
		self:val: val;
	}

	replace local Function of T is get(){
		return self:val;
	}

	replace local Function is set(T is newVal){
		self:val: newVal;
	}
}

class Pair of A to B{
	local A is first;
	local B is second;

	replace local Function is init(A is first, B is second){
		self:first: first;
		self:second: second;
	}

	replace local Function of A is getFirst(){
		return self:first;
	}

	replace local Function of B is getSecond(){
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

### Variables & Declarations
Variables are declared using `<Modifiers> <Type> is <name>: <initial_value>;`:

```spec
local Int is score: 100;
local Float is ratio: 0.75;
local String is greeting: "Welcome";
```

### Functions & Methods
Methods and functions declare their signatures using the `Function` type:
- **Void / Default return**: `Function is <name>(<Params>)` (e.g. `replace local Function is init(...)`).
- **Typed return**: `Function of <ReturnType> is <name>(<Params>)` (e.g. `Function of Int is add(...)`).
- Modifiers include `local` (scoped to class) and `replace` (overriding an inherited member).

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
class Issue{
	Int is line;
	Boolean is isWarning;
	String is message;

	## Constructor auto-assigns fields without manual assignment statements
	replace local Function is init(self:line, self:isWarning, self:message){
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
replace local Function of String is greet(String is name, String is prefix: "Hello", String is suffix: "!"){
	return prefix . ", " . name . suffix;
}

replace local Function of Int is calculate(Int is a, Int is b: 10, Int is c: 100){
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
Packages are imported via the class `using` property:
```spec
replace local Array of String is using: [
	base:struct:Array,
	base:math:*,
	base:io:*,
	base:sys:*,
	base:iterator:*
];
```
Imports map directly to `.spec` files in the standard library (`lib/`) or project directory.

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
replace local Function is execute(Function is callback){
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
local Array of String is languages: ["C", "Rust", "Spec"];
local String is first: languages[0]; # "C"
languages[1]: "Spec C11"; # Replaces "Rust"
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
  [lib/base/struct/Array.spec] Incompatible assignment type
  ```

---

## Unlockable Concurrency & Iteration Model

Spec does not include primitive `while` or `break` keywords in its grammar. Instead, all looping is decoupled into explicit state-machine lifecycle contracts driven by the standard library (`base:iterator:*`).

### Pure Loop Decoupling
Loops in Spec are non-blocking, decoupled state machines:
```spec
class CounterLoop extends Loop{
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
class ActionHandler extends InputHandler{
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
| 📂 **Examples** | Code samples and tests | [examples/](../../examples) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../../TASKS.md) |


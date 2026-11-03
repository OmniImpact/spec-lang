[Documentation](../README.md) > **Language Guide**

# Spec Language Guide

**Spec** is an object-oriented, statically typed programming language designed with an emphasis on readable syntax, concurrency-first unlocked control flow, and strict value safety.

---

## Table of Contents
1. [Language Syntax & Structure](#language-syntax--structure)
   - [Classes & Entry Point](#classes--entry-point)
   - [Variables & Declarations](#variables--declarations)
   - [Functions & Methods](#functions--methods)
   - [Imports & `using`](#imports--using)
2. [Types & Literals](#types--literals)
   - [Primitives](#primitives)
   - [String Literals](#string-literals)
   - [Generic Collections](#generic-collections)
   - [The `Any` Type](#the-any-type)
3. [The "Never Null" Standard](#the-never-null-standard)
4. [Operators & Expressions](#operators--expressions)
   - [Arithmetic Operators](#arithmetic-operators)
   - [String Concatenation](#string-concatenation)
   - [Member Access & Method Calls](#member-access--method-calls)
   - [String Inspection Primitives](#string-inspection-primitives)
5. [Control Flow](#control-flow)
   - [Conditionals (`if` / `else`)](#conditionals)
   - [Primitive While Loops & `break`](#primitive-while-loops--break)
6. [Unlockable Concurrency Model](#unlockable-concurrency-model)
   - [Loop Decoupling](#loop-decoupling)
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

### Variables & Declarations
Variables are declared using `<Modifiers> <Type> is <name>: <initial_value>;`:

```spec
local Int is score: 100;
local Float is ratio: 0.75;
local String is greeting: "Welcome";
```

### Functions & Methods
Functions declare return types with `Function of <ReturnType> is <name>(<Params>)`:
- If return type is omitted, it defaults to `null` (representing void return).
- Modifiers include `local` (scoped to class) and `replace` (overriding an inherited member).

```spec
# Explicit return type
Function of Int is add(Int is a, Int is b){
	return a + b;
}

# Void return type
Function of null is logMessage(String is msg){
	output:line(msg);
}
```

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

### Generic Collections
- `Array of <ElementType>`
- `Map of <KeyType> to <ValueType>`

```spec
local Array of String is fruits: ["Apple", "Banana", "Cherry"];
local Map of String to Int is scores: Map:init();
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

### String Inspection Primitives
- `str:length() -> Int`
- `str:charAt(index: Int, default: String) -> String`
- `str:substring(start: Int, end: Int) -> String`
- `str:indexOf(search: String, default: Int) -> Int`
- `str:isDigit() -> Boolean`
- `str:isAlpha() -> Boolean`
- `str:isWhitespace() -> Boolean`

---

## Control Flow

### Conditionals
Standard `if`, `else if`, and `else` blocks with boolean comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`) and logical operators (`&&`, `||`, `!`):

```spec
if (score > 21) {
	output:line("Bust!");
} else if (score == 21) {
	output:line("Blackjack!");
} else {
	output:line("Continue play");
}
```

### Primitive While Loops & `break`
```spec
while (count < 10) {
	count: count + 1;
	if (count == 5) {
		break;
	}
}
```

---

## Unlockable Concurrency Model

### Loop Decoupling
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

While:run(CounterLoop:init(), LoopControl:init());
```

### Event-Driven Non-Blocking Input
Interactive console I/O delegates to event handlers rather than freezing thread execution:
```spec
class ActionHandler extends InputHandler{
	replace Function of null is onInput(String is action){
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


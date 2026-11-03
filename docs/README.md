# Spec Language Documentation

**Spec** is an object-oriented, statically typed programming language designed with an emphasis on explicit scoping, readable typing syntax, and straightforward self-hosting compilation via C transpilation.

---

## Table of Contents

1. [Quick Start & Compiler CLI](#quick-start--compiler-cli)
2. [Language Syntax & Structure](#language-syntax--structure)
   - [Classes & Entry Point](#classes--entry-point)
   - [Variables & Declarations](#variables--declarations)
   - [Functions & Methods](#functions--methods)
   - [Imports & the `using` Array](#imports--the-using-array)
3. [Types & Literals](#types--literals)
   - [Primitives (`Int`, `Float`, `String`)](#primitives)
   - [Strings (Single-Quote vs Double-Quote)](#string-literals)
   - [Generic Collections (`Array`, `Map`)](#generic-collections)
4. [Operators & Expressions](#operators--expressions)
   - [Arithmetic Operators](#arithmetic-operators)
   - [String Concatenation](#string-concatenation)
   - [Member Access & Method Calls](#member-access--method-calls)
   - [Named Arguments](#named-arguments)
   - [Array Indexing](#array-indexing)
5. [Standard Packages](#standard-packages)
   - [`base:io`](#baseio)
   - [`base:math`](#basemath)
   - [`base:struct`](#basestruct)

---

## Quick Start & Compiler CLI

Compile `.spec` source files to standalone binaries using the Stage 0 `spec` compiler:

```bash
# Compile source to executable binary
spec -i path/to/source.spec -o myprogram

# Run the compiled binary (with optional named arguments)
./myprogram --name Alice
```

---

## Language Syntax & Structure

### Classes & Entry Point

Every Spec program is organized into classes. The runtime instantiates the class containing an `init` function as the application entry point.

```spec
class HelloWorld{
    replace local Function is init(Map of String to String is args){
        output:line("Hello World");
    }
}
```

### Variables & Declarations

Variables follow a uniform syntax:
`<scope> <Type> is <name> [: <initial_value>];`

```spec
local String is greeting: 'Hello';
local Int is count: 42;
local Float is ratio: 3.14159;
```

### Functions & Methods

Methods are declared with `<scope> Function [of <ReturnType>] is <name>(<parameters>)`:

```spec
replace local Function is init(Map of String to String is args){
    # method body
}
```

Parameters follow `<Type> is <name>`:
```spec
Function is calculate(Int is a, Float is b){ ... }
```

### Imports & the `using` Array

The `using` array is a native property of the `Class` type. Imports are declared by overriding `using` with `replace`:

```spec
replace local Array of String is using: [
    base:struct:Array,
    base:struct:Map,
    base:math:*,
    base:io:*
];
```

---

## Types & Literals

### Primitives
- **`Int` / `int`**: 64-bit signed integer.
  - Literals: `0`, `42`, `-10`.
- **`Float` / `float`**: 64-bit IEEE double-precision float.
  - Literals: `3.14`, `0.0`, `-2.718`.
- **`String`**: Null-terminated UTF-8 / ASCII string.

### String Literals
- **Double-Quoted (`"..."`)**: Interprets whitespace and escape characters:
  - `\n`: Newline
  - `\t`: Horizontal Tab
  - `\r`: Carriage Return
  - `\\`: Backslash
  - `\"`: Double quote
- **Single-Quoted (`'...'`)**: Raw/literal strings. Backslash characters are preserved literally, except for escaped quotes (`\'`) and backslashes (`\\`).

```spec
local String is formatted: "Line 1\nLine 2\tTabbed";
local String is raw: 'C:\path\to\file.txt';
```

### Generic Collections
Generics use the natural `of` and `to` keywords:
- `Array of <ElementType>`
- `Map of <KeyType> to <ValueType>`

---

## Operators & Expressions

### Arithmetic Operators
Spec supports standard arithmetic with precedence:
- `+` (Addition)
- `-` (Subtraction / Negation)
- `*` (Multiplication)
- `/` (Division)
- `%` (Modulus)
- `( ... )` (Grouping with parentheses)

```spec
local Int is result: (10 + 5) * 2 - (8 / 2);
```

### String Concatenation
The dot operator (`.`) concatenates strings and automatically converts primitives (`Int`, `Float`):

```spec
local Int is score: 100;
output:line("Your score is: " . score);
```

### Member Access & Method Calls
The colon (`:`) is used for namespace traversal and method invocation:
```spec
output:line("Message");
args:getString(key: "name", default: "User");
```

### Control Flow & Loops
Spec supports conditional branching and primitive iteration:
- **`if (cond) { ... } else if (cond) { ... } else { ... }`**: Standard conditionals.
- **`while (cond) { ... }`**: Primitive while loop.
- **`break;`**: Immediately exits the enclosing loop.

```spec
while (count < 10) {
	count: count + 1;
	if (count == 5) {
		break;
	}
}
```

### Initialization & Never Null Philosophy
In Spec, `null` is not a valid value and does not exist as a literal:
- **Every initialized variable must have a concrete value**: You cannot assign or pass null. If a value would be null, it cannot compile.
- **Empty collections are supported**: Collections like `Array` can be empty (`[]`).
- **Deferred initialization**: Class fields may be declared without an inline value provided they are initialized in `init(...)` before being read.
- **Default values for potentially empty reads**: Any operation reading from a source that could be empty must take a default argument (e.g. `getString(key, default)`).

---

## Multi-File Compilation & Module Resolution
The Spec compiler automatically resolves packages listed in the class `using` property:
```spec
replace local Array of String is using: [
	base:struct:Array,
	base:math:*,
	base:io:*,
	base:iterator:*
];
```
- Module paths map to `.spec` files located in the `lib/` directory or project tree (e.g. `base:iterator:*` loads all files in `lib/base/iterator/`).
- Standard packages are implemented directly in Spec in `lib/`.
- The compiler recursively traverses and compiles all imported dependencies into a unified executable.

### Named Arguments
Methods support explicit named arguments:
```spec
args:getString(key: "name", default: "User");
math:random(min: 1.0, max: 10.0);
```

### Array Indexing
Arrays support bracket indexing `[index]` and method calls `:get(index: i)`:
```spec
local String is first: fruits[0];
local String is second: fruits:get(index: 1);
```

---

## Standard Packages

### `base:io`
Provides terminal and standard I/O operations.
- `output:line(String is text)`: Prints text followed by a newline to standard output.

### `base:math`
Provides mathematical utilities and random number generation.
- `math:round(Float is value)`: Rounds a float to the nearest integer.
- `math:floor(Float is value)`: Rounds down to the nearest integer.
- `math:ceil(Float is value)` / `math:ceiling(...)`: Rounds up to the nearest integer.
- `math:random()`: Generates a pseudo-random float in the range `[0.0, 1.0)`.
- `math:random(Float is min, Float is max)`: Generates a pseudo-random float in the range `[min, max)`.

### `base:struct`
Data structure definitions.
- **`Array`**:
  - `[item1, item2, ...]`: Array literal initialization.
  - `array:length()`: Returns the number of elements in the array.
  - `array:get(Int is index)` or `array[index]`: Retrieves the item at the specified 0-based index.
  - `array:add(item)` / `array:push(item)`: Appends an item to the end of the array.
- **`Map`**:
  - `map:getString(key: "...", default: "...")`: Retrieves a string value by key or falls back to default.

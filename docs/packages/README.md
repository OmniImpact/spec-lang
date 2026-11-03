[Documentation](../README.md) > **Standard Packages**

# Spec Standard Library Packages

This document details the standard library packages available in the Spec runtime.

---

## Package Summary

| Package | Key Types & Functions | Description |
|---|---|---|
| **`base:io`** | `output:line`, `error:line`, `Input:prompt`, `InputHandler`, `File:read/write/readAsync/writeAsync/exists/remove`, `Ansi` (256-color, RGB, cursor, terminal size) | Terminal I/O, stderr diagnostics, filesystem access, ANSI escapes. |
| **`base:math`** | `round`, `floor`, `ceil`, `toInt`, `toFloat`, `sqrt`, `pow`, `log`, `log2`, `sin`, `cos`, `tan`, `atan2`, `random`, `fastRandom`, `abs`, `min`, `max`, `clamp` | Math primitives, conversions, and transcendental functions. |
| **`base:struct`** | `Array` — `length`, `get`, `set`, `add`, `pop`, `removeAt`, `slice`, `clear`, `indexOf`, `join`, `isEmpty`, `each`, `map`, `fold`, `filter`, `count`, `any`, `arr[i]` · `Map` — `get*`, `set`, `has`, `remove`, `keys`, `length`, `each`, literals, `m[k]` | Thread-safe collections with functional combinators. |
| **`base:iterator`** | `Loop`, `LoopControl`, `LoopCallback`, `While:run`, `While:condition` | Decoupled loop engine and inline closure iteration. |
| **`base:sys`** | `Process:execute/getPid/exit/sleep/clockMs/peakMemoryKb/threadCount/atomicAdd/atomicPut/atomicGet`, `Parallel:run`, `SourceLocation`, `StackFrame` | Processes, timing, memory/thread introspection, atomics, parallel fan-out. |
| **`base:reflect`** | `Type`, `Parameter`, `Member`, `ClassInfo` | Runtime type information and reflection metadata. |
| **`base:meta`** | `Expression`, `Statement`, `NamedArg`, `WhenArm`, `ProgramNode` | Syntax trees and meta-programming models. |

Full API reference by package below.

## Table of Contents
1. [`base:io`](#1-baseio)
   - [Console Output (`output:line`)](#outputline)
   - [Interactive Input (`Input:prompt`)](#inputprompt)
   - [File Operations (`File`)](#file-operations)
2. [`base:math`](#2-basemath)
   - [Rounding & Flooring](#rounding--flooring)
   - [Random Number Generation](#random-number-generation)
   - [Pure Spec Math Primitives](#pure-spec-math-primitives)
3. [`base:struct`](#3-basestruct)
   - [`base:struct:Array`](#basestructarray)
   - [`base:struct:Map`](#basestructmap)
4. [`base:iterator`](#4-baseiterator)
   - [`base:iterator:Loop`](#baseiteratorloop)
   - [`base:iterator:LoopControl`](#baseiteratorloopcontrol)
   - [`base:iterator:While`](#baseiteratorwhile)
5. [`base:sys`](#5-basesys)
   - [`base:sys:Process`](#basesysprocess)
   - [`base:sys:SourceLocation`](#basesyssourcelocation-libbasesyssourcelocationspec)
   - [`base:sys:StackFrame`](#basesysstackframe-libbasesysstackframespec)
6. [`base:reflect`](#6-basereflect)
   - [`base:reflect:Type`](#6-basereflect)
   - [`base:reflect:Parameter`](#6-basereflect)
   - [`base:reflect:Member`](#6-basereflect)
   - [`base:reflect:Class`](#6-basereflect)
7. [`base:meta`](#7-basemeta)
   - [AST Models (`Expression`, `Statement`, `NamedArg`, `ProgramNode`)](#7-basemeta)
8. [String Inspection Primitives](#8-string-inspection-primitives)

---

## 1. `base:io`

Importing:
```spec
replace local Array of String is using: [
	base:io:*
];
```

### `output:line`
Writes a string representation of an expression to standard output followed by a newline:

```spec
output:line("Text message");
output:line("Result: " . (10 + 20));
```

### `Input:prompt`
Provides non-blocking, event-driven user input prompts via `InputHandler`:

```spec
Class is InputExample{
	replace local Function is init(Map of String to String is args){
		Input:prompt("Enter your name: ", local Function(String is response){
			output:line("Hello, " . response . "!");
		});
	}
}
```

### File Operations
Available via `base:io:File` (`lib/base/io/File.spec`):

- **`File:read(path: String, default: String) -> String`**:
  Reads the full contents of the file at `path`. If reading fails or the file does not exist, returns `default`.
  ```spec
  local String is content: File:read(path: "main.spec", default: "");
  ```
- **`File:write(path: String, content: String) -> Boolean`**:
  Writes string content to disk at `path`. Returns `true` on success, `false` on failure.
  ```spec
  local Boolean is ok: File:write(path: "out.c", content: generatedCode);
  ```
- **`File:exists(path: String) -> Boolean`**:
  Checks if a file exists on disk.
  ```spec
  local Boolean is exists: File:exists(path: "main.spec");
  ```
- **`File:remove(path: String) -> Boolean`**:
  Deletes the file at `path` from disk. Returns `true` on success, `false` otherwise.
  ```spec
  local Boolean is removed: File:remove(path: "/tmp/temp.c");
  ```

---

### `Ansi:terminalWidth` / `Ansi:terminalHeight`
- `Ansi:terminalWidth() -> Int` — console width in columns; `0` when stdout is not a terminal.
- `Ansi:terminalHeight() -> Int` — console height in rows; `0` when stdout is not a terminal.

Detection order: `ioctl(TIOCGWINSZ)`, then the `COLUMNS`/`LINES` environment variables, then built-in defaults (78/24). The zero-when-piped contract lets programs fall back to explicit defaults under redirection and in CI.

## 2. `base:math`

Importing:
```spec
replace local Array of String is using: [
	base:math:*
];
```

### Rounding & Flooring

- **`math:round(Float is value) -> Float`**:
  Rounds a floating point number to the nearest integer value.
  ```spec
  local Float is r: math:round(value: 3.7); # 4.0
  ```

- **`math:floor(Float is value) -> Float`**:
  Returns the largest integer value less than or equal to `value`.
  ```spec
  local Float is f: math:floor(value: 3.7); # 3.0
  ```

- **`math:ceil(Float is value) -> Float`** / **`math:ceiling(Float is value) -> Float`**:
  Returns the smallest integer value greater than or equal to `value`.
  ```spec
  local Float is c: math:ceil(value: 3.2); # 4.0
  ```

### Random Number Generation

- **`math:random() -> Float`**:
  Generates pseudo-random double precision floating point numbers seeded with high-resolution epoch time in the range `[0.0, 1.0)`.
  ```spec
  local Float is r: math:random();
  ```

- **`math:random(min: Float, max: Float) -> Float`**:
  Generates a pseudo-random floating point number in `[min, max)`.
  ```spec
  local Float is roll: math:random(min: 1.0, max: 6.0);
  ```

### Pure Spec Math Primitives
Implemented in pure Spec (`lib/base/math/Math.spec`):

- **`math:abs(Float is value) -> Float`**: Returns the absolute value of a number.
- **`math:min(Float is a, Float is b) -> Float`**: Returns the minimum of two values.
- **`math:max(Float is a, Float is b) -> Float`**: Returns the maximum of two values.
- **`math:clamp(Float is val, Float is minVal, Float is maxVal) -> Float`**: Clamps `val` to `[minVal, maxVal]`.

---

## 3. `base:struct`

Importing:
```spec
replace local Array of String is using: [
	base:struct:Array,
	base:struct:Map
];
```

### `base:struct:Array`
A dynamic, auto-resizing array container (`lib/base/struct/Array.spec`).

#### Literal Initialization
```spec
local Array of String is fruits: ["Apple", "Banana", "Cherry"];
local Array of Int is primes: [2, 3, 5, 7];
```

#### Methods

- **`length() -> Int`**:
  Returns the count of elements.
  ```spec
  local Int is count: fruits:length();
  ```

- **`get(Int is index) -> Any`**:
  Fetches the item at index `index`. Alternatively, use bracket indexing `fruits[index]`.
  ```spec
  local String is item: fruits:get(index: 0);
  local String is same: fruits[0];
  ```

- **`set(Int is index, Any is item)`**:
  Replaces the element at zero-based `index` with `item`. Alternatively, use bracket assignment `fruits[index]: item;`.
  ```spec
  fruits:set(index: 0, item: "Apple");
  fruits[1]: "Banana";
  ```

- **`add(item: Any)` / `push(item: Any)`**:
  Appends an element to the dynamic array. Supports single items or array batches:
  ```spec
  fruits:add(item: "Mango");
  fruits:add(["Orange", "Grape"]);
  ```

- **`isEmpty() -> Boolean`** *(Pure Spec)*:
  Returns `true` if the array contains 0 elements, `false` otherwise.
  ```spec
  local Boolean is empty: fruits:isEmpty();
  ```

- **`pop(Any is default) -> Any`**:
  Removes and returns the last element from the array, or returns `default` if the array is empty.
  ```spec
  local String is lastItem: fruits:pop(default: "");
  ```

- **`removeAt(Int is index, Any is default) -> Any`**:
  Removes and returns the element at `index`, shifting subsequent elements left. Returns `default` if `index` is out of bounds.
  ```spec
  local String is removed: fruits:removeAt(index: 1, default: "");
  ```

- **`slice(Int is start, Int is end) -> Array`**:
  Returns a new array containing elements from `start` (inclusive) to `end` (exclusive).
  ```spec
  local Array of String is subset: fruits:slice(start: 0, end: 2);
  ```

- **`clear()`**:
  Clears all elements from the array.
  ```spec
  fruits:clear();
  ```

- **`indexOf(String is search, Int is default) -> Int`**:
  Returns the index of the first matching string element, or `default` if not found.
  ```spec
  local Int is idx: fruits:indexOf(search: "Apple", default: -1);
  ```

- **`each(Function is action)`**:
  Iterates through each element in the array, invoking `action` with the item.
  ```spec
  fruits:each(action: local Function(item){
  	output:line(item);
  });
  ```

- **`any(Function is predicate) -> Boolean`**:
  Returns `true` if any element satisfies the `predicate`.
  ```spec
  local Boolean is hasApple: fruits:any(predicate: local Function of Boolean(item){
  	return item is "Apple";
  });
  ```

- **`count(Function is predicate) -> Int`**:
  Counts how many elements satisfy the `predicate`.
  ```spec
  local Int is count: fruits:count(predicate: local Function of Boolean(item){
  	return item:startsWith(prefix: "A");
  });
  ```

- **`filter(Function is predicate) -> Array`**:
  Returns a new array containing all elements that satisfy the `predicate`.
  ```spec
  local Array of String is filtered: fruits:filter(predicate: local Function of Boolean(item){
  	return item:startsWith(prefix: "A");
  });
  ```

- **`map(Function is transform) -> Array`**:
  Transforms each element in the array using `transform`, returning a new mapped array.
  ```spec
  local Array of Int is nums: [1, 2, 3, 4];
  local Array of Int is doubled: nums:map(transform: local Function of Int(Int is x){
  	return x * 2;
  });
  ```

- **`fold(Any is initial, Function is reducer) -> Any`**:
  Reduces all elements of the array to a single accumulated value starting from `initial`.
  ```spec
  local Int is sum: nums:fold(initial: 0, reducer: local Function of Int(Int is acc, Int is x){
  	return acc + x;
  });
  ```

- **`join(String is separator) -> String`**:
  Joins all string elements in the array using `separator`.
  ```spec
  local String is csv: fruits:join(separator: ", ");
  ```

---

### `base:struct:Map`
A thread-safe, 64-bucket FNV-1a key-value hash table container supporting `String`, `Int`, `Float`, `Boolean`, and arbitrary object value types (`lib/base/struct/Map.spec`).

#### Literal Initialization & Bracket Syntax
Maps can be initialized with inline map literals and accessed via bracket notation:

```spec
# Map literal
local Map of String to Int is scores: ["alice": 95, "bob": 88];

# Empty map literal
local Map of String to String is cache: [:];

# Bracket indexing (R-value)
local Int is aScore: scores["alice"];

# Bracket assignment (L-value)
scores["charlie"]: 100; # Inserts new key-value pair
scores["alice"]: 98;   # Updates existing entry
```

#### Methods

- **`getString(String is key, String is default) -> String`**:
  Looks up a key. If found, returns its string value; otherwise returns the provided default.
  ```spec
  local String is username: args:getString(key: "user", default: "Guest");
  ```

- **`getInt(String is key, Int is default) -> Int`**:
  Looks up a key and returns its `Int` value, or `default` if absent.

- **`getFloat(String is key, Float is default) -> Float`**:
  Looks up a key and returns its `Float` value, or `default` if absent.

- **`getBool(String is key, Boolean is default) -> Boolean`**:
  Looks up a key and returns its `Boolean` value, or `default` if absent.

- **`get(String is key, Any is default) -> Any`**:
  Looks up a key and returns its typed object or primitive value, or `default` if absent.

- **`set(String is key, Any is value)`**:
  Sets or updates the value associated with `key`.
  ```spec
  symbolTable:set(key: "count", value: "10");
  classRegistry:set(key: "User", value: userClass);
  ```

- **`has(String is key) -> Boolean`**:
  Returns `true` if the key exists in the map, `false` otherwise.
  ```spec
  local Boolean is exists: symbolTable:has(key: "count");
  ```

- **`remove(String is key) -> Boolean`**:
  Removes the key from the map. Returns `true` if the key was found and removed, `false` otherwise.
  ```spec
  local Boolean is ok: symbolTable:remove(key: "count");
  ```

- **`keys() -> Array of String`**:
  Returns an array of all keys stored in the map.
  ```spec
  local Array of String is allKeys: symbolTable:keys();
  ```

- **`length() -> Int`**:
  Returns the number of key-value pairs stored in the map.
  ```spec
  local Int is count: symbolTable:length();
  ```

- **`each(Function is action)`**:
  Iterates through each entry in the map, invoking `action` with `(key, value)`.
  ```spec
  scores:each(action: local Function(String is name, Int is score){
  	output:line("Student: " . name . " => " . score);
  });
  ```

---

## 4. `base:iterator`

Importing:
```spec
replace local Array of String is using: [
	base:iterator:*
];
```

The iterator package decouples iteration state and termination logic from loop execution bodies.

### `base:iterator:Loop` (`lib/base/iterator/Loop.spec`)
Base class for iterator implementations:
- **`evaluate() -> Boolean`**: Evaluated before each step. Returns `true` to continue, `false` to end.
- **`iteration(LoopControl is control) -> Boolean`**: Executes a single step.

### `base:iterator:LoopControl` (`lib/base/iterator/LoopControl.spec`)
Controls loop continuation and completion triggers:
- **`stop()`**: Halts iteration.

### `base:iterator:While` (`lib/base/iterator/While.spec`)
- **`While:run(Loop is loop, LoopControl is control)`**: Drives the iterator lifecycle and executes completion callbacks.
- **`While:condition(Function of Boolean is evaluate, Function of Boolean is iteration)`**: Executes an inline loop using `evaluate` and `iteration` closures without requiring a separate `Loop` subclass.

---

## 5. `base:sys`

Importing:
```spec
replace local Array of String is using: [
	base:sys:*
];
```

### `base:sys:Process` (`lib/base/sys/Process.spec`)
Provides external process execution and operating system invocation:

- **`Process:execute(command: String, args: Array of String) -> Int`**:
  Executes an external system command with arguments and returns the process exit status code (`0` for success).
  ```spec
  local Int is code: Process:execute(command: "gcc", args: ["--version"]);
  ```
- **`Process:getPid() -> Int`**:
  Returns the operating system process identifier (PID) of the current running process.

### `base:sys:SourceLocation` (`lib/base/sys/SourceLocation.spec`)
Encapsulates source file provenance, line numbers, and column offsets:
- `SourceLocation:init(file: String, line: Int, col: Int)`
- `loc:getFile() -> String`
- `loc:getLine() -> Int`
- `loc:getCol() -> Int`
- `loc:toString() -> String` (e.g. `"Player.spec:42:15"`)

### `base:sys:StackFrame` (`lib/base/sys/StackFrame.spec`)
Represents a call frame in a runtime call stack or debugging trace:
- `StackFrame:init(location: SourceLocation, className: String, methodName: String)`
- `frame:getLocation() -> SourceLocation`
- `frame:getClassName() -> String`
- `frame:getMethodName() -> String`
- `frame:toString() -> String` (e.g. `"Player:takeDamage (Player.spec:42:15)"`)

---

### Process Introspection
- `Process:clockMs() -> Int` — monotonic wall-clock milliseconds (measure elapsed time as a difference of two calls).
- `Process:peakMemoryKb() -> Int` — peak resident set size in kilobytes (`getrusage`), `0` when unavailable.
- `Process:threadCount() -> Int` — live OS thread count for the current process (`/proc/self/status`), `1` when unavailable.

## 6. `base:reflect`

Importing:
```spec
replace local Array of String is using: [
	base:reflect:*
];
```

Provides runtime type descriptors and object model reflection:

- **`base:reflect:Type` (`lib/base/reflect/Type.spec`)**:
  Represents primitive and parameterized types (e.g. `Int`, `Function of String`, `Map of String to Int`).
  - `Type:init(name: String)`
  - `Type:withParams(name: String, params: Array of Type)`
  - `type:getName() -> String`
  - `type:getParams() -> Array of Type`
  - `type:isGeneric() -> Boolean`
  - `type:toString() -> String`
- **`base:reflect:Parameter` (`lib/base/reflect/Parameter.spec`)**:
  Represents method parameter definitions: `name: String`, `paramType: Type`.
- **`base:reflect:Member` (`lib/base/reflect/Member.spec`)**:
  Represents field, method, or nested class members on a type.
- **`base:reflect:Class` (`lib/base/reflect/Class.spec`)**:
  Represents class definitions and metadata: `name: String`, `baseClass: String`, `members: Array of Member`.

---

## 7. `base:meta`

Importing:
```spec
replace local Array of String is using: [
	base:meta:*
];
```

Provides concrete Abstract Syntax Tree models for code generation, desugaring, macros, and tooling:

- **`base:meta:NamedArg`**: Named arguments in method calls.
- **`base:meta:Expression`**: Expressions (`STRING`, `NUMBER`, `FLOAT`, `BOOL`, `IDENT`, `PATH`, `ARRAY`, `CALL`, `BINARY`, `UNARY`).
- **`base:meta:Statement`**: Statements (`VAR_DECL`, `ASSIGN`, `IF`, `RETURN`, `CLASS`, `EXPR`).
- **`base:meta:ProgramNode`**: Program root node containing an array of `Class` definitions.

---

## 8. String Inspection Primitives

Strings in Spec provide built-in methods for lexical scanning, text transformation, and parsing:

- **`str:length() -> Int`**: Returns the character count of the string.
- **`str:charAt(index: Int, default: String) -> String`**: Returns a single-character string at the zero-based index, or `default` if the index is out of bounds.
- **`str:substring(start: Int, end: Int) -> String`**: Returns the substring between `start` (inclusive) and `end` (exclusive).
- **`str:indexOf(search: String, default: Int) -> Int`**: Finds the first occurrence of `search`, or returns `default` if not found.
- **`str:isDigit() -> Boolean`**: Returns `true` if the string is non-empty and contains only numeric digits (`0`-`9`).
- **`str:isAlpha() -> Boolean`**: Returns `true` if the string is non-empty and contains ASCII letters or underscores (`_`).
- **`str:isWhitespace() -> Boolean`**: Returns `true` if the string is non-empty and contains only whitespace characters (` `, `\t`, `\n`, `\r`).
- **`str:lines() -> Array of String`**: Splits the string on newline boundaries (`\n`, `\r\n`), returning an array of lines.
- **`str:startsWith(prefix: String) -> Boolean`**: Returns `true` if the string begins with `prefix`.
- **`str:endsWith(suffix: String) -> Boolean`**: Returns `true` if the string ends with `suffix`.
- **`str:contains(needle: String) -> Boolean`**: Returns `true` if `needle` appears anywhere within the string.
- **`str:replaceAll(search: String, replacement: String) -> String`**: Returns a new string with all occurrences of `search` replaced by `replacement`.
- **`str:split(delimiter: String) -> Array of String`**: Splits the string on `delimiter` into an `Array of String`.
- **`str:countLeading(search: String) -> Int`**: Counts consecutive occurrences of `search` at the start of the string (e.g. leading spaces or tabs).
- **`str:trim() -> String`**: Strips leading and trailing whitespace characters (` `, `\t`, `\n`, `\r`).

---

## Quick Navigation

| Target | Description | Path |
|---|---|---|
| 🏠 **Repository Root** | Project home & overview | [README.md](../../README.md) |
| 📚 **Documentation Portal** | Docs index | [docs/README.md](../README.md) |
| 📖 **Language Guide** | Syntax, types, and control flow | [docs/language/README.md](../language/README.md) |
| 🛠️ **Tooling Guide** | Compiler CLI, linter, editor plugins | [docs/tooling/README.md](../tooling/README.md) |
| 📂 **Examples** | Demo programs | [examples/](../../examples) |
| 🧪 **Tests** | Positive and negative test suites | [tests/](../../tests) |
| 📋 **Task Tracking** | Active development status | [TASKS.md](../../TASKS.md) |


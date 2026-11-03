# Spec Standard Library Packages

This document details the packages available in the standard runtime.

---

## 1. `base:io`

Importing:
```spec
replace local Array of String is using: [
    base:io:*
];
```

### Functions

#### `output:line`
Writes a string representation of an expression to standard output followed by a newline.

```spec
output:line("Text message");
output:line("Result: " . (10 + 20));
```

---

## 2. `base:math`

Importing:
```spec
replace local Array of String is using: [
    base:math:*
];
```

### Functions

#### `math:round`
Rounds a floating point number to the nearest integer value.

**Signature**: `Function of Float is round(Float is value)`
```spec
local Float is r: math:round(value: 3.7); # 4.0
```

#### `math:floor`
Returns the largest integer value less than or equal to `value`.

**Signature**: `Function of Float is floor(Float is value)`
```spec
local Float is f: math:floor(value: 3.7); # 3.0
```

#### `math:ceil` / `math:ceiling`
Returns the smallest integer value greater than or equal to `value`.

**Signature**: `Function of Float is ceil(Float is value)`
```spec
local Float is c: math:ceil(value: 3.2); # 4.0
```

#### `math:random`
Generates pseudo-random double precision floating point numbers seeded with high-resolution epoch time.

- Without arguments: generates `[0.0, 1.0)`.
  ```spec
  local Float is r: math:random();
  ```
- With `min` and `max`: generates `[min, max)`.
  ```spec
  local Float is roll: math:random(min: 1.0, max: 6.0);
  ```

#### Pure Spec Math Functions (`lib/base/math/Math.spec`)
- **`math:abs(Float is value) -> Float`**: Returns the absolute value of a number.
- **`math:min(Float is a, Float is b) -> Float`**: Returns the minimum of two values.
- **`math:max(Float is a, Float is b) -> Float`**: Returns the maximum of two values.
- **`math:clamp(Float is val, Float is minVal, Float is maxVal) -> Float`**: Clamps a value within `[minVal, maxVal]`.

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
A dynamic array container (`lib/base/struct/Array.spec`).

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

- **`get(Int is index)`**:
  Fetches the item at index `index`. Alternatively, use bracket syntax `fruits[index]`.
  ```spec
  local String is item: fruits:get(index: 0);
  local String is same: fruits[0];
  ```

- **`add(item)` / `push(item)`**:
  Appends an element to the dynamic array. Supports single items or array batches:
  ```spec
  fruits:add(item: "Mango");
  fruits:add(["Orange", "Grape"]);
  ```

- **`isEmpty() -> Boolean`** *(Pure Spec)*:
  Returns `true` if the array contains 0 elements.
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

- **`clear() -> null`**:
  Clears all elements from the array.
  ```spec
  fruits:clear();
  ```

- **`indexOf(String is search, Int is default) -> Int`**:
  Returns the index of the first matching string element, or `default` if not found.
  ```spec
  local Int is idx: fruits:indexOf(search: "Apple", default: -1);
  ```

---

### `base:struct:Map`
A key-value hash table container used for CLI arguments and dictionaries (`lib/base/struct/Map.spec`).

#### Methods

- **`getString(String is key, String is default) -> String`**:
  Looks up a key. If found, returns its string value; otherwise returns the provided default.
  ```spec
  local String is username: args:getString(key: "user", default: "Guest");
  ```

- **`set(String is key, String is value) -> null`**:
  Sets or updates the value associated with `key`.
  ```spec
  symbolTable:set(key: "count", value: "10");
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

---

## 4. `base:iterator`

Importing:
```spec
replace local Array of String is using: [
    base:iterator:*
];
```

### `base:iterator:Loop` (`lib/base/iterator/Loop.spec`)
Base class for iterator implementations.
- **`evaluate() -> Boolean`**: Evaluated before each step. Returns `true` to continue, `false` to end.
- **`iteration(LoopControl is control) -> Boolean`**: Executes a single step.

### `base:iterator:LoopControl` (`lib/base/iterator/LoopControl.spec`)
Controls loop continuation and completion triggers.
- **`stop()`**: Halts iteration.

### `base:iterator:While` (`lib/base/iterator/While.spec`)
- **`While:run(Loop is loop, LoopControl is control)`**: Drives the iterator lifecycle and executes completion callbacks.

---

## 5. `base:sys`

Importing:
```spec
replace local Array of String is using: [
    base:sys:*
];
```

### `base:sys:Process` (`lib/base/sys/Process.spec`)
Provides external process execution capabilities.
- **`Process:execute(command: String, args: Array of String) -> Int`**:
  Executes an external system command with arguments and returns the process exit status code.
  ```spec
  local Int is code: Process:execute(command: "gcc", args: ["--version"]);
  ```

---

## 6. `base:io:File` (`lib/base/io/File.spec`)

Filesystem operations:
- **`File:read(path: String, default: String) -> String`**:
  Reads the full contents of the file at `path`. If reading fails or file does not exist, returns `default`.
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

---

## 7. String Inspection Primitives

Strings provide character-level inspection methods for lexical scanning and parsing:
- **`str:length() -> Int`**: Returns the character count.
- **`str:charAt(index: Int, default: String) -> String`**: Returns a 1-character string at the index, or `default` if out of bounds.
- **`str:substring(start: Int, end: Int) -> String`**: Returns the substring between `start` (inclusive) and `end` (exclusive).
- **`str:indexOf(search: String, default: Int) -> Int`**: Finds the first occurrence of `search`, or returns `default`.
- **`str:isDigit() -> Boolean`**: Returns `true` if string is non-empty and contains only digits (`0`-`9`).
- **`str:isAlpha() -> Boolean`**: Returns `true` if string is non-empty and contains letters or `_`.
- **`str:isWhitespace() -> Boolean`**: Returns `true` if string is non-empty and contains only whitespace (` `, `\t`, `\n`, `\r`).


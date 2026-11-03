[Documentation](README.md) > **Code Style & SpecDoc Guide**

# Spec Code Style & SpecDoc Documentation Guide

This document establishes the official code style conventions, architectural idioms, and the **SpecDoc** documentation standard for the Spec programming language.

---

## Table of Contents

1. [Core Design Principles](#1-core-design-principles)
2. [Code Formatting & Layout](#2-code-formatting--layout)
   - [Indentation: Tabs Exclusively](#indentation-tabs-exclusively)
   - [Brace Placement (OTBS)](#brace-placement-otbs)
   - [Whitespace & Blank Lines](#whitespace--blank-lines)
   - [Line Endings](#line-endings)
3. [Naming Conventions](#3-naming-conventions)
4. [Language Idioms & Syntax](#4-language-idioms--syntax)
   - [Method & Field Declarations](#method--field-declarations)
   - [String Concatenation](#string-concatenation)
   - [The "Never Null" Principle](#the-never-null-principle)
   - [Decoupled Iteration](#decoupled-iteration)
   - [Imports & Package Structure](#imports--package-structure)
5. [SpecDoc Documentation Standard](#5-specdoc-documentation-standard)
   - [Comment Delimiters (`##` and `#!`)](#comment-delimiters--and-)
   - [Doc Comment Structure](#doc-comment-structure)
   - [Standard SpecDoc Tags](#standard-specdoc-tags)
   - [Cross-Referencing](#cross-referencing)
   - [SpecDoc Example](#specdoc-example)
6. [Tooling & Linter Enforcement](#6-tooling--linter-enforcement)

---

## 1. Core Design Principles

1. **Minimalist Grammar**: Spec relies on only **10 keywords** (`class`, `extends`, `local`, `replace`, `is`, `of`, `to`, `if`, `else`, `return`) and **6 primitive types** (`Int`, `Float`, `Boolean`, `String`, `Function`, `Any`). All capabilities belong in the standard library.
2. **Never Null**: Null does not exist in Spec grammar or runtime. Every potentially fallible lookup, query, or extraction accepts a caller-provided `default` fallback or returns an empty representation.
3. **Decoupled Iteration**: Spec does not have primitive `while`, `for`, or `break` keywords. Iteration is encapsulated in reusable `Loop` subclasses evaluated by runners such as `While:run`.
4. **Declarative & English-Like**: Code reads as explicit statements of intent: `local String is name: "Hero";`, `Function of Boolean is isAlive()`.

---

## 2. Code Formatting & Layout

### Indentation: Tabs Exclusively
* **Mandatory Rule**: All `.spec` files must use **hard tabs (`\t`)** for indentation.
* Exactly **one tab** per nesting level.
* Space-based indentation is rejected by the compiler linter (`spec --lint`).

```spec
# Correct (Tabs)
class Player{
	local Int is health: 100;

	replace local Function of Boolean is isAlive(){
		return health > 0;
	}
}
```

### Brace Placement (OTBS)
Spec follows the **One True Brace Style (OTBS)**:
* Opening braces `{` sit on the **same line** as the declaration, following the class name, method signature, or control structure:
  ```spec
  class Player{
  replace local Function is takeDamage(Int is amount){
  if (amount > 0) {
  ```
* Closing braces `}` sit on their **own line**, aligned with the indentation of the enclosing construct.

### Whitespace & Blank Lines
* **Between Members**: Separate fields, methods, and nested classes with exactly **one blank line**.
* **Colon Spacing**:
  * In variable and field declarations, place a space after the colon: `local Int is count: 0;`
  * In assignments, place a space after the colon: `self:count: count + 1;`
  * In method calls, place a space after argument colons: `parser:peekAhead(offset: 1);`
* **Parentheses & Brackets**: No space directly inside parentheses or brackets: `add(item: 42)`, `[1, 2, 3]`.

### Line Endings
* All files must use **LF (`\n`)** line endings. (Configured in `.gitattributes`).

---

## 3. Naming Conventions

| Entity | Casing | Examples | Notes |
|---|---|---|---|
| **Classes & Types** | `PascalCase` | `Player`, `SourceLocation`, `While` | Distinct from primitive keywords |
| **Methods** | `camelCase` | `getName()`, `parseClass()`, `isAlive()` | Action-oriented verbs |
| **Fields** | `camelCase` | `health`, `stringValue`, `params` | Direct nouns describing state |
| **Local Variables** | `camelCase` | `playerClass`, `numExpr`, `tokenList` | Clear, expressive names |
| **Parameters** | `camelCase` | `source`, `defaultVal`, `maxCount` | Required or named arguments |
| **Packages / Modules** | `lowercase` | `base:struct:Array`, `base:sys:Process` | Hierarchical namespace segments |
| **AST / Token Kinds** | `UPPERCASE` | `"KEYWORD"`, `"IDENT"`, `"VAR_DECL"` | String-based tag identifiers |

---

## 4. Language Idioms & Syntax

### Method & Field Declarations
* Modifiers precede the type signature:
  ```spec
  # Void method (procedure)
  replace local Function is init(String is name){
  	self:name: name;
  }

  # Typed return method
  replace local Function of String is getName(){
  	return self:name;
  }
  ```

### String Concatenation
* Use the **dot operator (`.`)** for string concatenation:
  ```spec
  output:line("Player " . name . " has " . health . " HP");
  ```

### The "Never Null" Principle
Every API that retrieves an item by index, key, or path must require a fallback `default` argument:
```spec
# Correct: Requires explicit fallback
local String is first: list:get(index: 0, default: "");
local String is host: config:getString(key: "host", default: "localhost");
local String is content: File:read(path: "save.dat", default: "");
```

### Decoupled Iteration
Loop logic is packaged inside dedicated loop classes extending `base:iterator:Loop`:
```spec
class CountLoop extends Loop{
	local Int is count: 0;
	local Int is limit: 10;

	replace local Function of Boolean is evaluate(){
		return count < limit;
	}

	replace local Function of Boolean is iteration(LoopControl is control){
		output:line("Count: " . count);
		self:count: count + 1;
		return true;
	}
}

# Run the loop
While:run(loop: CountLoop:init());
```

### Imports & Package Structure
* Declare `using` at the top of the primary class definition:
  ```spec
  class MyModule{

  	replace local Array of String is using: [
  		base:io:*,
  		base:struct:Array,
  		base:reflect:Type
  	];

  	...
  }
  ```
* **One Primary Class Per File**: The primary class name must match the file name (e.g. `lib/base/sys/SourceLocation.spec` defines `class SourceLocation`).

---

## 5. SpecDoc Documentation Standard

SpecDoc is Spec's standard for embedded API documentation.

### Comment Delimiters (`##` and `#!`)
* **`#!` (Module / File Doc Comment)**: Placed at the very top of a `.spec` file to document the package or module.
* **`##` (Item Doc Comment)**: Attached directly to the item it describes (`class`, field, method).
* **`#` (Internal Comment)**: Standard implementation comments ignored by documentation generators.

### Doc Comment Structure
A SpecDoc comment consists of:
1. A **concise summary sentence** ending with a period.
2. Optional **extended prose** in Markdown.
3. SpecDoc **tags** (`@param`, `@return`, `@fallback`, `@example`, `@see`).

### Standard SpecDoc Tags

```spec
## Short one-line summary.
##
## Detailed explanation of the item's role, constraints, and behavior.
##
## @param <name>: Description of the parameter.
## @return: Description of the return value.
## @fallback: Description of the default value returned when input is missing or out of bounds.
## @example:
## ```spec
## local String is val: obj:getValue(default: "");
## ```
## @see <path>: Related class or method reference.
## @notice: Important edge-case or performance note.
```

### Cross-Referencing
Enclosing an identifier in square brackets automatically generates cross-reference links in HTML / Markdown output:
* `[ClassName]`: Links to a class in scope.
* `[methodName]`: Links to a method on the current class.
* `[package:Class]`: Links to an external package class (e.g. `[base:struct:Array]`).

### SpecDoc Example

```spec
#! Package base:sys
#! Provides system interaction, process execution, and execution frames.

## Encapsulates source file provenance, line numbers, and column offsets.
##
## Used across compiler diagnostics, tokens, and runtime stack frames.
class SourceLocation{

	## File path or module identifier.
	local String is file: "";

	## One-based line number in source.
	local Int is line: 1;

	## One-based column number in source.
	local Int is col: 1;

	## Initializes a source location with file, line, and column coordinates.
	##
	## @param file: The file path or URI of the source.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace local Function is init(String is file, Int is line, Int is col){
		self:file: file;
		self:line: line;
		self:col: col;
	}

	## Formats the location as a standardized coordinate string.
	##
	## @return: Formatted string in "file:line:col" or "line:col" format.
	## @example:
	## ```spec
	## local String is s: loc:toString(); # Returns "Player.spec:42:15"
	## ```
	replace local Function of String is toString(){
		if (self:file:length() > 0) {
			return self:file . ":" . self:line . ":" . self:col;
		}
		return self:line . ":" . self:col;
	}
}
```

---

## 6. Tooling & Linter Enforcement

Run the Spec compiler linter to check compliance:
```bash
spec --lint path/to/file.spec
```

The linter verifies:
* **Indentation**: Rejects spaces; requires hard tabs (`\t`).
* **Line Endings**: Requires Unix LF (`\n`).
* **Optional Arguments**: Emits notices for optional parameter usage and fallback conventions.
* **SpecDoc Integration**: Validates doc comment presence on public library APIs.

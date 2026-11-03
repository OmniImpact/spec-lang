# Spec Language Quick Reference & AI Agent Bootstrap

Spec is an expressive, strictly typed, indentation-sensitive, compiled systems language (transpiling to C11 via `gcc`). Spec adheres to a strict "Never Null" philosophy.

---

## 1. Syntax Rules & Formatting
- **Hard Tabs Only**: Indentation **must** use hard tabs (`\t`). Spaces for indentation trigger linter errors.
- **Colon (`:`) is Assignment & Access**:
  - Variable declaration: `<Type> is <name>: <value>;`
  - Reassignment: `<name>: <value>;`
  - Property/method access: `<target>:<member>`
  - Field assignment: `self:<field>: <value>;`
- **String Delimiters**:
  - `'...'`: Literal string (no escape processing).
  - `"..."`: Interpreted string (`\n`, `\t`, `\r`, `\"`, `\\`).
  - Concatenation operator is dot (`.`): `'Hello' . ' ' . 'World'`.
- **Never Null**: The `null` keyword does not exist. Use default values, fallback parameters (`default:`), or sentinel patterns.

---

## 2. Program Structure

```spec
class AppName{

	# Class fields
	local String is title: 'Spec App';
	local Int is count: 0;

	# Package imports
	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:*
	];

	# Entrypoint init method (called by runtime with CLI arguments)
	replace local Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		output:line(self:title . ': Hello ' . name);
	}

}
```

---

## 3. Types, Variables & Modifiers
- **Primitives**: `Int` (64-bit signed), `Float` (64-bit double), `Boolean` (`true`/`false`), `String`.
- **Containers**: `Array of <Type>`, `Map of <KeyType> to <ValueType>`.
- **Declarations**:
  ```spec
  local Int is count: 10;
  local String is msg: "Loading...";
  local Array of String is items: ["a", "b", "c"];
  ```
- **Modifiers & Strict Overriding**:
  - `local`: Enforces lexical scope / instance scope.
  - `replace`: **Strictly required** when overriding any superclass member, interface contract, or built-in lifecycle method (`init`, `evaluate`, `iteration`, `using`, `toString`). Omitting `replace` on overrides produces a compile error.
- **Multiple Inheritance & Abstraction Contracts**:
  - **Inherently Abstract**: Any field declared without an initial value (`local String is name;`) or method with an empty body (`describe() -> String{}`) is abstract.
  - **Interfaces as Abstract Classes**: A class composed of abstract members acts as an interface.
  - **Multiple Inheritance**: Classes can extend multiple parents: `class Service extends Named, Identifiable { ... }`.
  - **Enforcement on `init`**: Concrete classes defining or calling `init(...)` must implement all abstract fields and methods inherited from all parents.

---

## 4. Methods & Functions
- **Standard Syntax**:
  ```spec
  replace local Function of ReturnType is methodName(ParamType is param1, ParamType is param2){
  	return param1 + param2;
  }
  ```
- **Shorthand Syntax**:
  ```spec
  methodName(ParamType is param1) -> ReturnType{
  	return param1;
  }
  ```
- **Anonymous Lambdas**:
  ```spec
  items:each(action: local Function(String is item){
  	output:line(item);
  });
  ```

---

## 5. Control Flow: `if`, `when`, and Loops

### Conditional Branching
```spec
# Standard statement
if (score >= 90) {
	grade: "A";
} else {
	grade: "B";
}

# Inline ternary expression
local String is status: if (isActive) "Online" else "Offline";
```

### Pattern Matching (`when`)
```spec
# Statement form
when (action) {
	is "hit", "h": { self:dealCard(); }
	is "stand", "s": { self:stand(); }
	else: { output:line("Invalid action"); }
}

# Expression form
local Int is points: when (rank) {
	is "ace": 11;
	is "king", "queen", "jack": 10;
	else: 0;
};
```

### Enums
```spec
Enum is Status { ACTIVE, INACTIVE, PENDING }
Enum of Int is StatusCode { OK: 200, NOT_FOUND: 404 }

# Access & Methods:
local Status is s: Status:ACTIVE;
local String is name: s:name();     # "ACTIVE"
local Int is code: StatusCode:OK:value(); # 200
local Int is idx: s:ordinal();      # 0
```

### Iteration (No `while` or `for` keywords)
Loops use the decoupled iterator runner `While:run` with a subclass of `Loop`:
```spec
class CountLoop extends Loop{
	local Int is current: 0;
	local Int is max: 10;

	init(Int is max){
		self:max: max;
	}

	evaluate(){
		return self:current < self:max;
	}

	iteration(control){
		output:line("Count: " . self:current);
		self:current: self:current + 1;
		return true; # continue loop; return false to break
	}
}

While:run(loop: CountLoop:init(max: 5));
```

---

## 6. Standard Library Primitives
- **Console I/O**:
  - `output:line(text)`
  - `local String is input: Input:prompt("Enter value: ");`
- **File System (Synchronous, Callback-Driven & Asynchronous)**:
  - `File:exists(path: "path/to/file") -> Boolean`
  - `File:read(path: "...", onSuccess: local Function(String is data){ ... }, onError: local Function(String is err){ ... })`
  - `File:write(path: "...", content: "...", onSuccess: local Function(Int is bytes){ ... }, onError: local Function(String is err){ ... })`
  - `File:readAsync(...)` and `File:writeAsync(...)` for non-blocking worker thread execution.
  - Fallback signatures: `File:read(path: "...", default: "")`, `File:write(path: "...", content: "")`
- **Process Execution**:
  - `Process:execute(command: "gcc", args: ["-O2", "file.c"]) -> Int`
- **Arrays**:
  - `arr:length()`, `arr:get(index: 0)`, `arr:append(item: val)`
  - Higher-order: `arr:each(action:)`, `arr:any(predicate:)`, `arr:filter(predicate:)`, `arr:count(predicate:)`
- **Maps**:
  - `map:set(key: "k", value: "v")`, `map:getString(key: "k", default: "")`, `map:has(key: "k")`, `map:length()`

---

## 7. SpecDoc Documentation
- `#! Package <name>`: Top-of-file package annotation.
- `## <SpecDoc>`: Markdown description before class, method, or field.
- `@param <name>: <desc>`: Parameter documentation.
- `@return: <desc>`: Return value documentation.

---

## 8. Compiler Commands
```bash
# Compile Spec source to native binary
./spec -i examples/helloworld.spec -o ./helloworld

# Check code against style and lint rules
./spec --lint examples/helloworld.spec
```

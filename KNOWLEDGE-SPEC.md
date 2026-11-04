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

Classes are declared `Class of Parent is Name { ... }` — pre-binder `of` names parent classes, mirroring `Enum of Int is Status` (post-name `of` declares generic parameters).
Parents precede the name: `Class of A, B is Child`; generic parameters use `Class of T is Box`.
The `merge` modifier overrides a parent Array field by concatenating parent items then child items. On methods, `merge` requires a forward statement `(args...)` that delegates to the nearest parent implementation (partial forwards must name their arguments); merge init chains parent constructors.

```spec
Class is AppName{

	# Class fields
	local String is title: 'Spec App';
	local Int is count: 0;

	# Package imports
	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:*
	];

	# Entrypoint init method (called by runtime with CLI arguments)
	replace Function is init(Map of String to String is args){
		local String is name: args:getString(key: 'name', default: 'User');
		output:line(self:title . ': Hello ' . name);
	}

}
```

---

## 3. Types, Variables, Generics & Modifiers
- **Primitives**: `Int` (64-bit signed), `Float` (64-bit double), `Boolean` (`true`/`false`), `String`, `Function`, `Any`.
- **Containers & Literals**:
  - `Array of <Type>`: `["a", "b"]`, empty `[]`, bracket indexing `arr[0]`, bracket assignment `arr[0]: "x";`.
  - `Map of <KeyType> to <ValueType>`: `["alice": 95, "bob": 88]`, empty `[:]`, bracket indexing `scores["alice"]`, bracket assignment `scores["charlie"]: 100;`.
- **User-Defined Generic Classes**:
  ```spec
  Class is Box of T{
  	local T is val;
  	replace Function is init(T is val){ self:val: val; }
  	replace Function of T is get(){ return self:val; }
  }
  local Box of String is b: Box:init(val: "Hello");
  ```
- **Declarations**:
  ```spec
  local Int is count: 10;
  local String is msg: "Loading...";
  local Array of String is items: ["a", "b", "c"];
  local Map of String to Int is scores: ["alice": 95];
  ```
- **Modifiers & Strict Overriding**:
  - `local`: Enforces lexical scope / instance scope.
  - `replace`: **Strictly required** when overriding any superclass member, interface contract, or built-in lifecycle method (`init`, `evaluate`, `iteration`, `using`, `toString`). Omitting `replace` on overrides produces a compile error.
- **Multiple Inheritance & Abstraction Contracts**:
  - **Inherently Abstract**: Any field declared without an initial value (`local String is name;`) or method with an empty body (`describe() -> String{}`) is abstract.
  - **Interfaces as Abstract Classes**: A class composed of abstract members acts as an interface.
  - **Multiple Inheritance**: Multiple inheritance: `Class of Named, Identifiable is Service { ... }`.
  - **Enforcement on `init`**: Concrete classes defining or calling `init(...)` must implement all abstract fields and methods inherited from all parents.

---

## 4. Methods & Functions
- **Standard Syntax**:
  ```spec
  replace Function of ReturnType is methodName(ParamType is param1, ParamType is param2){
  	return param1 + param2;
  }
  ```
- **Shorthand Syntax**:
  ```spec
  methodName(ParamType is param1) -> ReturnType{
  	return param1;
  }
  ```
- **Default Parameters & Named-Argument Reordering**:
  ```spec
  replace Function of String is greet(String is name, String is prefix: "Hello", String is suffix: "!"){
  	return prefix . ", " . name . suffix;
  }
  local String is s: self:greet(suffix: ".", name: "World"); # "Hello, World."
  ```
- **First-Class Capturing Closures & Direct Invocation**:
  ```spec
  local Int is factor: 10;
  local Function of Int is scale: local Function of Int(Int is x){ return x * factor; };
  local Int is res: scale(x: 4); # 40
  ```
- **Anonymous Lambdas & Collection Combinators**:
  ```spec
  items:each(action: local Function(String is item){
  	output:line(item);
  });
  local Array of Int is doubled: nums:map(transform: local Function of Int(Int is x){ return x * 2; });
  local Int is sum: nums:fold(initial: 0, reducer: local Function of Int(Int is acc, Int is x){ return acc + x; });
  ```

---

### Casts (`as`) & String Rendering
`value as Target` unifies class up/downcasts, numeric casts, and base conversion:
`as Int`/`as Float` for numerics, `as Hex`/`as Bin`/`as Oct` to format (Int -> String,
optional width) or parse (String -> Int). Chaining is rejected; parse failures
yield 0. Class instances render their class name in concatenation via a generated
`toString()` (user `replace` overrides win); enums render their variant name.

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

### Enums & Tagged Unions (Algebraic Data Types)
```spec
Enum is Status { ACTIVE, INACTIVE, PENDING }
Enum of Int is StatusCode { OK: 200, NOT_FOUND: 404 }
Enum is Result { Ok(String is data), Err(Int is code, String is msg), Pending }

# Access & Methods:
local Status is s: Status:ACTIVE;
local String is name: s:name();            # "ACTIVE"
local Int is code: StatusCode:OK:value();  # 200
local Int is idx: s:ordinal();             # 0

# Destructuring Tagged Unions in when:
local Result is r: Result:Ok(data: "Ready");
when (r) {
	is Result:Ok(data): { output:line(data); }
	is Result:Err(code, msg): { output:line(code . ": " . msg); }
	else: {}
}
```

### Iteration (No `while` or `for` keywords)
Loops use the decoupled iterator runner `While:run` with a subclass of `Loop`:
```spec
of Loop is CountLoop{
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

### Exit Codes & Diagnostics
- `0` success, `1` compile failure (syntax, load, or type errors; backend gcc failure), `2` usage error.
- All diagnostics are written to **stderr** via `error:line(...)`; program output uses `output:line(...)`.
- Programs terminate explicitly with `Process:exit(status: N)`.
- Missing module files and unresolvable `using:` imports are hard load errors (`[LoadError]`).

### Class Grouping (Partials)
A fragment class declares `replace Array of String is group: [Target];`. The Loader merges
fragments into the target class (unioning `using` arrays, stripping `group`). Duplicate members
across fragments are load errors; at most one `init` per merged class; fragments must not
declare parent classes. See the [Class Grouping guide](docs/language/README.md#class-grouping-partial-classes).

```bash
# Compile Spec source to native binary
./spec -i examples/helloworld.spec -o ./helloworld

# Check code against style and lint rules
./spec --lint examples/helloworld.spec
```

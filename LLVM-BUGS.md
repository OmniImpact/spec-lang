# LLVM Backend Review: Shortcuts, Violations, and Correctness Bugs

This document records the architectural review of the LLVM backend (`spec/base/compiler/llvm/` and `spec/base/compiler/ir/`), evaluating its correctness, memory safety, self-hosting readiness, and adherence to the `sysinternal` floor discipline.

---

## Part 1: Shortcuts & Violations of the `sysinternal` Discipline

In the C backend (`BuiltinCallGenerator.spec` and `ClassBindings.spec`), `sysinternal` binding is **structural and generic**:
- `ClassBindings:isSysinternal` inspects whether the class's declared `namespace` ends with `'sysinternal'`.
- `BuiltinCallGenerator:bindFloorCall` binds any call on a `sysinternal` class to `spec_<snake_case(method)>` automatically, matching arguments against the floor declaration's parameters.
- Wrapper classes in `base:sys` (`Output`, `Stderr`, `Input`, `File`, `Dir`, `Process`, `Time`, `Ansi`, `Introspection`, `Buf`, `Vector`, `Box`, `Conditional`, `Loops`) are **not** transparent—their Spec method bodies are compiled normally and delegate to `base:sysinternal:*`.

By contrast, the LLVM backend takes **widespread name-matching shortcuts** across 13 hardcoded `CallLowerer` plugins:

### 1. Hardcoded interception of `base:sys` and `base:math` wrapper classes and bare method names
Instead of compiling the Spec bodies of `base:sys` wrappers and only binding `base:sysinternal` at the floor, the `CallLowerer` classes intercept **both** the `base:sys` wrapper methods and the `base:sysinternal` floor methods by hardcoded class and method names—and worse, when the receiver name is empty (`r == ''`, i.e. any bare call), they match by **method name alone**:
- `SysinternalCallLowerer:receiverName` (`spec/base/compiler/llvm/SysinternalCallLowerer.spec:34-62`) strips the namespace and returns `''` for bare calls or only the final class name segment, completely ignoring whether the target is in `base:sysinternal`, `base:sys`, or a **user-defined class**.
- `ConsoleCallLowerer` (`spec/base/compiler/llvm/ConsoleCallLowerer.spec:28-38`) intercepts `r == '' || r == 'Output' || r == 'Console' || r == 'Stderr' || r == 'Terminal'` and method names `'line'`, `'print'`, `'consOut'`, `'term_width'`, etc. **Impact:** Any user class that defines a method `line(String is x)` or `print(String is x)` and calls it bare (`line(x)`) is hijacked by `ConsoleCallLowerer` and compiled as `spec_print_line`!
- `ProcessCallLowerer` (`spec/base/compiler/llvm/ProcessCallLowerer.spec:28-41`) intercepts `r == '' || r == 'Process' || r == 'Parallel'` for `'exit'`, `'sleep'`, `'getEnv'`, `'execute'`, `'measure'`, `'osName'`, `'getPid'`, `'clockMs'`, `'rawArgs'`, `'sync'`, `'syncWith'`, `'run'`. Any bare call to a user method named `execute(a, b)`, `measure(a, b)`, `sleep(x)`, `exit(x)`, or `sync(x)` is hijacked!
- `FileCallLowerer` (`spec/base/compiler/llvm/FileCallLowerer.spec:45-56`) intercepts `r == '' || r == 'File'` for `'fileExists'`, `'fileRemove'`, `'fileRead'`, `'fileWrite'`, bypassing `spec/lib/base/sys/File.spec`.
- `DirCallLowerer` (`spec/base/compiler/llvm/DirCallLowerer.spec:45-56`) intercepts `r == '' || r == 'Dir'` for `'dirList'`, `'exeDir'`, `'fileSize'`, bypassing `spec/lib/base/sys/Dir.spec`.
- `TimeCallLowerer` (`spec/base/compiler/llvm/TimeCallLowerer.spec:28-44`) intercepts `r == '' || r == 'Time'` for `'monotonicNs'`, `'nowMs'`, `'sleepMs'`, `'localOffsetSec'`, bypassing `spec/lib/base/sys/Time.spec`.
- `MathCallLowerer` (`spec/base/compiler/llvm/MathCallLowerer.spec:29-130`) intercepts `r == '' || r == 'Math'` for `'round'`, `'ceil'`, `'floor'`, `'abs'`, `'min'`, `'max'`, `'random'`, `'fastRandomSeed'`, etc., bypassing the pure-Spec implementations in `spec/lib/base/math/Math.spec` and calling C `round`/`fabs`/`fmin`/`fmax` directly.
  - **Correctness bug from this shortcut:** In `Math.spec:269-332`, `Math:abs(Int)`, `Math:min(Array of Int)`, and `Math:max(Array of Int)` are pure-Spec overloads on `Int` and `Array of Int`. Because `MathCallLowerer` intercepts all 1-arg `abs` and 2-arg `min`/`max` calls and casts them to `F64`, calling `Math:abs(value: -5)` returns a `double` in an `i64`-typed SSA register (invalid LLVM IR / type mismatch), and `fastRandomSeed` is hardcoded as a no-op (`res: '0'`).
- `IntrospectionCallLowerer` (`spec/base/compiler/llvm/IntrospectionCallLowerer.spec:104-197`) hand-rolls 90 lines of inline LLVM IR basic-block loops for `Introspection:functions` and `Introspection:instantiateSubclasses`, even though both are already written in pure Spec in `spec/lib/base/sys/Introspection.spec:104-191` over the `sysinternal` floor!
- `ControlFlowCallLowerer` (`spec/base/compiler/llvm/ControlFlowCallLowerer.spec:57-66`) intercepts `'if'`, `'branch'`, and `'while'` on **any** receiver (`if({ nm == 'while' && call:args:length() >= 2 }, { return true; })`), and intercepts `'repeat'`, `'until'`, `'loop'`, `'times'`, `'range'`, `'rangeStep'`, `'forever'` whenever the target is `self` or bare, rather than checking that the provider is `Loops` or letting non-inline calls compile through `spec/lib/base/sys/Loops.spec`.

### 2. Reimplementing `String`, `Array`, and `Map` Spec methods in IR instead of calling their compiled Spec bodies
In `String.spec`, `Array.spec`, and `Map.spec`, most methods (`String:charAt`, `String:startsWith`, `String:endsWith`, `String:contains`, `Array:join`, `Array:isEmpty`, `Map:isEmpty`, `Map:clear`, `Map:values`, `Map:merge`, `Map:filter`, `Map:any`, `Map:count`, `Map:getInt`, `Map:getBool`) have pure-Spec bodies written over `Buf`, `Vector`, etc.
- Instead of calling the compiled `String_*` / `Array_*` / `Map_*` functions, `StringCallLowerer` (`spec/base/compiler/llvm/StringCallLowerer.spec:187-333`) and `MapCallLowerer` (`spec/base/compiler/llvm/MapCallLowerer.spec:168-578`) emit custom inline IR loops for those methods.
- **Correctness & performance bug from this shortcut:** In `StringCallLowerer` (`spec/base/compiler/llvm/StringCallLowerer.spec:288-323`), `startsWith` and `endsWith` unconditionally allocate a substring (`spec_string_substring`) *before* checking if `slen >= plen`, and never claim or release `sub` (leaking a string on every `startsWith`/`endsWith` call!).
- **Missing Floor Class:** `spec/base/sysinternal/Arena.spec` (`arenaNew`, `arenaAlloc`, `arenaDrain`, `arenaUsed`, `activateProcessArena`) is not handled at all because there is no generic `bindFloorCall` mechanism in the LLVM backend.
- **Substring check for `sysinternal`:** `IrBuilder:isStdlibClass` (`spec/base/compiler/llvm/IrBuilder.spec:149-154`) checks `cls:sourceFile:contains(needle: 'sysinternal')` and a hardcoded list of class names instead of using `ClassBindings:isTransparent` / `ClassBindings:isSysinternal`.

---

## Part 2: Critical Self-Hosting Crashers & Correctness Bugs

When compiling the compiler itself with `--llvm` (`bin/spec --llvm -i spec/base/compiler/driver/Driver.spec -o /tmp/spec_llvm`) and then running `/tmp/spec_llvm` to self-host, two immediate bugs surface: **6.1 GB of memory usage during loading** (vs. 113 MB in the C-built compiler) followed by a **SIGSEGV at the start of `IrBuilder:buildProgram`**.

### 1. Immediate Self-Hosting SIGSEGV: `Map:init()` defaults to `SPEC_ELEM_OBJECT` (`vk = 1`) for `Map of String to Int`
- **Location:** `MapCallLowerer.spec` lines 73–97 and `IrBuilder.spec` lines 780–805
- **What happens:**
  1. Field initializers like `Map of String to Int is globalVtableMap: Map:init();` are emitted in `emitFieldDefaults` (`IrBuilder.spec:788`) **without** setting `b:expectedMapKeyType` or `b:expectedMapValType` (which is only set in `Statement:VarDecl` at lines 1572–1579, and not in `Statement:Assign` or `emitFieldDefaults`).
  2. In `Statement:Assign` (`self:globalVtableMap: Map:init();` at `IrBuilder.spec:291`), `expectedMapValType` is also not set, and `expr:resolvedType` on `Map:init()` is bare `'Map'`.
  3. At `MapCallLowerer.spec` line 95 (`if({ resTy == 'Map' || resTy == '' }, { vk: 1; });`), when `resTy` is `'Map'` and `expectedMapValType` is `''`, `MapCallLowerer` sets `vk = 1` (`SPEC_ELEM_OBJECT`) and emits `spec_map_new_object()` (whereas the C backend defaults bare `'Map'` to `valIsArc = false` and emits `spec_map_new()`).
  4. When `IrBuilder.spec:306` executes `self:globalVtableMap:set(key: vk, value: self:globalVtableNames:length())` with integer `1`, `MapCallLowerer` calls `spec_map_set_any(map, key, (void*)1)`. Because the map was created with `val_kind = SPEC_ELEM_OBJECT`, `_spec_map_set_raw` calls `spec_retain((void*)1)` and dereferences address `0x1 - 0x8`, causing an immediate **SIGSEGV**.

### 2. 6.1 GB Memory Blowup & String Mutation Bug: Missing `bufAppendBuf` optimization and mutating interned strings
- **Location:** `IrBuilder.spec` lines 2100–2143
- **What happens:**
  1. In `IrBuilder.spec:2137-2140` for `op == '.'`:
     ```spec
     self:emit(inst: IrInst:Retain(val: ls));
     self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: cTypes, args: cArgs));
     ```
     Because `IrBuilder` **unconditionally emits `spec_rt_retain(ls)`** before calling `spec_string_concat(ls, rs)`, if `ls` is a local variable (which already has `ref_count == 1` from its local slot), retaining `ls` bumps its `ref_count` to `2`.
  2. Consequently, inside `spec_string_concat(a, b)` (`RuntimePrelude.spec:2939`), `h->ref_count == 1` is **NEVER TRUE** for any local variable! Every single `out: out . ...` concatenation in the compiler copies the entire buffer from scratch ($O(N^2)$ allocations), consuming **6.1 GB of RAM** just to load the 109 files of the compiler.
  3. When `a . b . c` is chained, the intermediate `a . b` is claimed in the pool (`ref_count == 1`), then retained by the outer `.` (`ref_count == 2`), then released once inside `spec_string_concat` (`ref_count == 1`), so it stays alive in the function-level pool until the entire function exits.
  4. **Silent Corruption of Interned String Literals:** In `IrBuilder.spec:1590-1595`, `VarDecl` copies a `StringLit` initializer with `spec_string_copy`, **but `Statement:Assign` (`IrBuilder.spec:1653-1658`) does NOT!** If a variable is assigned `out: '';` via `Statement:Assign` and then passed to `Buf:bufAppendBuf(dst: out, src: ...)`, `bufAppendBuf` mutates the **immortal interned `""` literal in-place**, corrupting every empty string `""` in the entire process.

### 3. Function-Wide Claim Pool Frame Instead of Per-Statement / Per-Call Pool Framing
- **Location:** `IrBuilder.spec` lines 484–500, 1453, 1499
- **What happens:**
  - `emitPoolEnter()` is called **only once at function entry**, and `emitPoolExit()` is called **only at function return**.
  - Any loop in a large function (`buildProgram`, `emitModule`, `checkProgram`, `tokenize`) pushes thousands or millions of transient strings/arrays/objects onto `_spec_pool_stack` without ever releasing them until the function returns.

### 4. Uncaptured Local Variables in Closures Pass Stack Slot Pointers Directly into `%env` (Use-After-Return / ABI Corruption)
- **Location:** `IrBuilder.spec` lines 2670–2672 and 2784–2786
- **What happens:**
  - `collectAllAnonCapturesInStmts` (`IrBuilder.spec:1199-1291`) only scans `Statement:VarDecl` declarations. Variables declared in `while([Int is i: 0], ...)` (`lowerWhileCall` / `lowerLoopCall` / `bindWorkerParam`) or `match` payload arms (`MatchCallLowerer.spec:348`) are in `self:localSlots`, **not** in `decls`, so `collectAllAnonCapturesInStmts` never marks them in `capturedNames` / `boxedLocals`.
  - In `lowerAnonFn` (line 2785), for any captured variable not in `boxedLocals`, it stores `oSlot` (the **raw `alloca` stack pointer**) into the heap-allocated `%env` struct.

### 5. `ControlFlowCallLowerer` & `MatchCallLowerer`: `return` Inside `match` & `if` Fails to Return from the Enclosing Method
- **Location:** `ControlFlowCallLowerer.spec` lines 225–267 (`lowerBlockExprVal`) and `MatchCallLowerer.spec` lines 80–118 (`lowerArmBody`)
- **What happens:**
  1. In `MatchCallLowerer:lowerArmBody` (`MatchCallLowerer.spec:80-118`), `b:inlineReturnEndLbl` is set to `endLbl` even when `hasResult` is **false** (a statement `match`). Any `return` statement inside a statement-level `match` arm (including nested inside an `if` inside a `match` arm) emits `br label %match_end`, silently swallowing the `return` statement and continuing execution of the method after the `match`!
  2. In `ControlFlowCallLowerer:lowerBlockExprVal` (`ControlFlowCallLowerer.spec:242-251`), when an `if` statement has two branches that end in `return a;` and `return b;`, the TypeChecker stamps `expr:resolvedType` on the `if`, so `lowerIfCall` sets `yieldVal = true` and `lowerBlockExprVal` turns `return a;` into storing `a` into `%if_res` and branching to `if_end` instead of returning from the method!

### 6. Non-Inline Closures & Multi-Statement Conditions in `ControlFlowCallLowerer`
- **Location:** `ControlFlowCallLowerer.spec:168-178, 269-287`
- **What happens:**
  - In `ControlFlowCallLowerer:lowerCondExpr`, if the condition is an `Expression:AnonFn` with more than 1 statement, lines 168–178 only lower `bd:get(index: 0)` and drop all remaining statements in the condition block.
  - In `ControlFlowCallLowerer:lowerIfCall`, `condNa` and `thenNa` are extracted positionally (`index: 0` and `index: 1`) without checking argument names `check` / `then` / `else`.

### 7. Enum Handling & Payload Destructuring
- **Location:** `IrBuilder.spec:2178-2185` and `MatchCallLowerer.spec:147-190, 340-351`
- **What happens:**
  - In `MatchCallLowerer.spec:340-351`, when destructuring a variant's fields into arm parameters (`%arm_p`), `b:localIsArc` is not updated, inheriting any stale `localIsArc` entry from a previous variable with the same name.

### 8. Function-Scoped `localSlots` Collisions & Variable Shadowing Bugs
- **Location:** `IrBuilder.spec:1552-1647`, `MatchCallLowerer.spec:348`, `ControlFlowCallLowerer.spec:652`
- **What happens:**
  - `localSlots`, `localTypes`, `localIsArc`, `localSpecTypes`, and `boxedLocals` are flat function-wide maps keyed by variable name. Inner blocks, loop variables, and `match` payload parameters overwrite outer variables of the same name and are never restored on scope exit.

### 9. Multiple Inheritance, `merge` Fields, Overloaded `init`, and `held` Functions
- **Location:** `IrBuilder.spec:176-204, 385-420, 557, 759-807, 829-838, 1102`
- **What happens:**
  1. Held field inheritance (`IrBuilder.spec:392-418`) only walks `baseClasses:get(index: 0)`, ignoring secondary base classes in multiple inheritance.
  2. Outer-link fields on nested classes (`IrBuilder:addInheritedFields`) are placed before own fields rather than split like `DeclarationGenerator:collectStructFieldsSplit`.
  3. `merge` on Array fields (`IrBuilder:emitFieldDefaults`) overwrites the parent array instead of concatenating parent items then child items.
  4. `Driver` does not pass `entryInitOverloadIndex` to `IrBuilder`, so `main` always calls `_init` even when the chosen entry `init` is an overload (`_init_2`).
  5. `IrBuilder:buildHeldResolvers` (line 1102) allocates 16 bytes instead of 24 bytes for `SpecClosure` (heap buffer overflow).
  6. `held` functions do not use the `_held_` symbol infix, colliding with same-name instance methods.

### 10. `LlvmEmitter:escapeLlvmBytes` Only Escapes 5 Characters
- **Location:** `LlvmEmitter.spec:424-443`
- **What happens:**
  - `escapeLlvmBytes` only escapes `\`, `"`, `\n`, `\r`, and `\t`. Control characters (such as `\e` = `0x1B` in `Ansi.spec`) and non-ASCII UTF-8 bytes (`>= 0x80`) are emitted raw inside `c"..."`, and it allocates a 1-char `String` per byte via `charAt` instead of using `byteAt`.

### 11. Container & `Never Null` Semantics (`Array:get`, `Vector:vecGetAt`, `Map:get`, `m[k]`)
- **Location:** `ArrayCallLowerer.spec:107, 391`, `MapCallLowerer.spec:261`, `IrBuilder.spec:2408`
- **What happens:**
  - `Array:get` and `Vector:vecGetAt` call `spec_array_get` (which ignores `default:` and panics on out-of-bounds) instead of `spec_vec_get_at`.
  - `Array:pop` and `Array:removeAt` are missing from `ArrayCallLowerer` or broken when `Array.spec` delegates to `Vector:vecPopLast` / `Vector:vecRemoveAt`.
  - `m[k]` and `m:getString(key: k)` without an explicit default pass `null` instead of `""`, violating `Never Null`.

---

## Summary Table

| # | Category | Severity | Location | Status |
|---|---|---|---|---|
| **1** | **`sysinternal` Discipline & Wrapper Reimplementations** | **High** | `spec/base/compiler/llvm/*CallLowerer.spec`, `IrBuilder.spec` | Pending |
| **2** | **Container & `Never Null` Semantics (`Array`, `Map`, `String`, `Vector`)** | **High** | `ArrayCallLowerer.spec`, `MapCallLowerer.spec`, `StringCallLowerer.spec` | Pending |
| **3** | **Self-Hosting SIGSEGV (`Map:init()` default `vk = 1`)** | **Blocker** | `MapCallLowerer.spec:73-97`, `IrBuilder.spec:291, 788` | Pending |
| **4** | **Memory Blowup (6.1 GB) & String Literal Mutation** | **Blocker** | `IrBuilder.spec:1590, 1653, 2137` | Pending |
| **5** | **Early `return` Swallowed in `match` & `if`** | **Blocker** | `MatchCallLowerer.spec:80-118`, `ControlFlowCallLowerer.spec:242-251` | Pending |
| **6** | **Pool Framing Scope (Per-Statement / Loop Framing)** | **High** | `IrBuilder.spec:484-500, 1453` | Pending |
| **7** | **Variable Shadowing & Scope Restoration** | **High** | `IrBuilder.spec:1558`, `MatchCallLowerer.spec:348`, `ControlFlowCallLowerer.spec:652` | Pending |
| **8** | **Closure Captures & `SpecClosure` Allocation Size** | **High** | `IrBuilder.spec:1102, 1199-1291, 2670, 2785` | Pending |
| **9** | **Class Model, Inheritance, `merge` Fields, `held` Infix** | **Medium** | `IrBuilder.spec:176, 392, 557, 780, 829, 965` | Pending |
| **10** | **LLVM String Escaping (`escapeLlvmBytes`)** | **Medium** | `LlvmEmitter.spec:424-443` | Pending |

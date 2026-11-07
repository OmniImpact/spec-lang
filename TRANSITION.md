# TRANSITION — the fossil-to-Spec boundary

A small, direct reference for the one question that matters while the new
compiler is bootstrapped by the old one: **what stays in C, what becomes
Spec, and what is scheduled for deletion.** The authoritative source is
[COMPILER-PLAN.md](COMPILER-PLAN.md) (§6 Floor Contract, §7 Base Library,
§12 Guardrails); this document is the working checklist. When the two
disagree, the plan wins and this file gets updated.

---

## 1. The C floor (permanent — `base:sysinternal`)

Exactly what §6 of the plan allows in C, forever. Everything here is a
tiny binding (2–15 lines), interface-style, bound by the
`spec_<snake(method)>` convention, reachable only through explicit
delegation. Current and planned members:

| Domain | Members | Status |
|---|---|---|
| Memory + ARC | `alloc`, `retain`, `release`, `assign` | in prelude C; sysinternal class pending |
| ByteBuf | new/resize/length/get/set/append/to_cstring | `Buf` class live; prelude C |
| Filesystem meta | `dirList`, `exeDir`, `fileSize` | `Dir` class live |
| Source identity | `Reflection:class()/method()` | live (generator-injected) |
| OS fd-level | open/read/write/close/lseek, exit, env/args, clock, sleep, terminal ioctl | prelude C; sysinternal declarations pending |
| Sockets fd-level | socket/bind/listen/accept/connect/send/recv/close | pending |
| Processes | fork/exec/wait (or posix_spawn), pipe | prelude C; declarations pending |
| Threads/sync | spawn-with-trampoline, join, mutex, atomic fetch-add/CAS | prelude C; declarations pending |
| Panic | abort | prelude C |
| `external` FFI | e.g. libm math, declared per-symbol | mechanism defined; Math lands as externals |

**Rule**: nothing outside `base:sysinternal` may touch C. A body-less
declaration anywhere else is a build error once the new checker enforces it.

## 1.1 Prelude function inventory (the 1,984-line C runtime, classified)

The prelude has ~192 functions. Here is every one, classified by
destination. The prelude emission stays as the big C blob until
self-hosting (Phase H); at that point the Spec implementations replace
the C functions and the prelude shrinks to the §1 floor.

### Stays in C (~46 — the true floor)

| Group | Functions | Why C |
|---|---|---|
| ARC (5) | `spec_alloc`, `retain`, `release`, `assign`, `assign_transfer` | Refcount atomics on the C object header; the foundation Spec runs on |
| ByteBuf struct + ops (9) | `SpecBuf` struct, `buf_new`, `grow`, `destroy`, `append_bytes`, `append_buf`, `to_cstring`, `get_byte`, `push_byte`, `pop_byte` | Direct `->data`/`->capacity`/realloc — THE one container in C |
| Bootstrap intern (2) | `spec_string_intern` + hash-bucket table | Runs before any Spec code exists (every string literal calls it) |
| Closure repr (3) | `SpecClosure` struct, `closure_new`, `call_closure_str`, `noop_closure` | Generated code's function-pointer protocol |
| Panic (3) | `bounds`, `cast`, `byte_range` | abort/exit paths |
| OS syscalls (~16) | `process_execute/sleep/get_pid`, `term_width/height`, `atomic_add/put/get`, `parallel_run/worker`, `file_exists/read/write/remove`, `input_prompt`, `drain_async_tasks` | fork/exec/nanosleep/ioctl/pthread/stat |
| RTTI (2) | `type_name`, `is_subclass_of` | Reads the C object header's `_type_name` |
| Error (1) | `error_line` | stderr write |
| Headers (~5) | `SpecClosure`, `SpecLoopControl` typedefs, ARC header struct | C struct definitions |

### Moves to Spec at self-hosting (~35 — pure computation over buf ops)

| Group | Functions | Spec implementation |
|---|---|---|
| String ops (24) | `from_bytes`, `copy`, `length`, `equals`, `substring`, `index_of`, `index_of_from`, `trim`, `has_prefix`, `has_suffix`, `starts_with`, `ends_with`, `contains`, `char_at`, `from_char_code`, `is_digit`, `is_alpha`, `is_whitespace`, `replace_all`, `split`, `lines`, `join`, `bytes_equal`, `string_from_chars` | Byte loops over `Buf:bufGetByte`/`bufLength` — bodies already in String.spec (Phase A) |
| Conversions (6) | `to_string_int`, `to_string_bool`, `int_to_base`, `parse_base`, `construct_string`, `construct_byte` | Division/character loops over the floor |
| Concat (2) | `spec_string_concat`, `concat_impl` | The `.` operator emission routes to `String.concatWith` (a Spec method over bufAppendBuf) |

The codegen emission changes per function: replace the `spec_string_*` call
with the compiled Spec body's direct-dispatch call (`String_<method>`).
The `String.concatWith` method needs two new sysinternal bindings
(`bufNewString`, `bufAppendBuf`) plus one C wrapper (`spec_buf_new_string`).

### Dies at Phase E (~61 — containers reimplemented in Spec)

| Group | Functions | Replacement |
|---|---|---|
| Array (22) | `spec_array_new/new_object/new_string/add/add_owned/get/set/pop/remove_at/length/clear/each/filter/count/any/map/fold/join/index_of/slice` | Spec class over ByteBuf with element stride |
| Map (16) | `spec_map_new/new_object/set/set_any/set_any_transfer/get/get_string/get_int/get_float/get_bool/has/remove/keys` + hash | Spec hash table over Array |
| Vec (12) | `spec_vec_new/new_object/new_string/push/get/set/length/clear` | Spec class over ByteBuf |
| ByteBuffer (11) | `spec_bytebuffer_new/new_string/push/append_string/get/pop/length/to_string` | Spec class over ByteBuf |

### Debug/trace infrastructure (~25 — not emitted by the new compiler)

`spec_rc_*` (debug ARC tracking), `spec_trace_*`, `_spec_rc_*` statics —
enabled by `SPEC_RC_DEBUG` env var. The new compiler's arena model
(plan §8) replaces the leak-tracking need. These simply don't appear
in the new prelude.

### Direct memory accesses (200 occurrences)

Every `->data`, `->length`, `->capacity`, `->items`, `->elem_size`,
`->elem_kind` targets a C runtime struct. The `SpecBuf` accesses stay
in C (the ByteBuf floor). The `SpecArray`/`SpecMap`/`SpecVec` accesses
die at Phase E when the containers become Spec objects.

## 2. Runtime-managed classes (transitional — die at Phase E)

These live in `lib/` as pure API-surface declarations, but their
*instances* are C-runtime objects (`SpecArray*`, `SpecMap*`, …). The
checker's deleted container branches and the codegen's
`EmissionPolicy.isTransparent` name list exist only for these:

- `Array`, `List`, `Map` — reimplemented as Spec classes over ByteBuf
  (element stride, grow-by-doubling, ARC on elements)
- `File`, `Output`, `Input`, `Process`, `Ansi` — thin Spec classes over
  the fd/process primitives
- `String` — already has real Spec bodies (Phase A); representation stays
  runtime-managed until the ByteBuf wrap lands (plan §7 builder decision)
- `Math` — becomes pure `external` declarations over libm
- `While`/`Loop`/`LoopCallback`/`LoopControl`/`InputHandler` — already
  pure Spec; leave the list only if emission still needs the marker
- `Parallel` — over the thread primitives

**Deletion checklist per class**: (1) Spec implementation lands; (2) name
removed from `EmissionPolicy.isTransparent`; (3) any codegen special
cases for its methods deleted; (4) suite green.

## 3. Old-compiler machinery (transitional — dies with the fossil)

Exists only because the fossil compiler compiles the new tree during
bootstrap. None of it is ported to the new tree:

- `BuiltinCallGenerator` — all 104 interception branches; replaced by
  namespace-driven sysinternal binding + direct dispatch
- `EmissionPolicy.isTransparent` name list — empties per §2
- `bindContainerCallbackParams` — container callback typing; dies when
  containers are real generics over ByteBuf (G6 structural-assignability
  follow-up)
- `isCastable` primitive conversion matrix — dies when Int/Float/Byte are
  Spec classes with declared `castable` entries
- The blanket RETURN retain + claim pool — replaced by clean ownership
  (arenas per plan §8); §7.1 of PLAN-STRING.md documents why it is
  load-bearing until then
- Tolerance pragma (`-Wno-error=incompatible-pointer-types`,
  `Wincompatible-pointer-types` ignore) — generation-gap bridge only
- `/spec-stage*` convergence scratch — bootstrap plumbing, never committed

## 4. Already done (for orientation, not a checklist)

- `String` bodies over the floor (16/16 instance methods; Phase A)
- `Buf`, `Dir`, `Reflection` sysinternal classes
- Namespace-driven floor binding (no interception branches for
  sysinternal calls)
- Package resolution: array-form `using` against scan roots
- Heredocs (`'''` raw / ``` fancy) + `{{expr}}` templating
- New tree G0–G5: chars, tokens, lexer, AST, parser, bidirectional
  checker — all suite-locked under the frozen toolchain

## 5. The invariant to protect

At every step: **the 70-test suite is the spec.** Both compilers must
pass it; a transition step that changes behavior has made a mistake
(or the suite has been deliberately updated — which is a recorded
decision, not an accident).

## 6. Standard library migration (`spec/lib`)

The stdlib now lands in `spec/lib/base/...`, ported idiomatic
(array-form `using`, full docs, duplicates removed), built only on the
distribution's sysinternal floor. The old `lib/` is frozen — no edits.

- **Resolution shadowing**: the Loader's scan roots put input-directory
  ancestors first, and `resolveLibFile` tries `spec/lib/`, then `spec/`
  (where the sysinternal floor lives), then legacy `lib/`. Classes
  present in the new tree win; un-migrated classes fall through. One
  deterministic winner per class name — no double loads.
- **Moved** (19 files): `sysinternal` stays at `spec/base/sysinternal`
  (it is the compiler distribution's floor, not stdlib — and the
  bootstrap loaders cannot resolve it under `lib/` yet);
  `core` (Stringable, Any, String), `iterator` (Loop, LoopControl,
  LoopCallback, While), `struct` (Array, Map), `io` (Output, Input,
  InputHandler, Ansi, File), `sys` (Process, Parallel, StackFrame,
  SourceLocation), `math` (Math).
- **Deliberately not moved** (die with the fossil): `lib/base/reflect`
  (the fossil's reflection AST mirror), `lib/base/meta` (fossil AST),
  `lib/compiler` (the fossil itself).
- **Known sharp edge**: the transparency list in `ast/ClassBindings`
  is name-based; common class names must stay off it (an `Error`
  entry collided with the compiler's own `Error` and silently dropped
  its struct — caught by self-compilation). `error:line` needs no
  class at all: the checker maps the lowercase singleton spelling
  unconditionally and the generator binds it to the floor.
- **Endgame**: when the fossil retires, legacy `lib/` is deleted and
  the loader's `lib/` prefix falls away — one resolver, one stdlib.

- **Package paths are pure package segments** (section 7 follow-up):
  imports say `['base', 'io', Output]` / `['base', 'compiler', 'ast',
  Type]` — the `spec/` and `lib/` directory names are repository
  layout, never package names. The Loader's array-form resolver walks
  layout prefixes per scan root (spec/lib stdlib, spec/ distribution,
  legacy lib, bare direct path). All sources — tree, tests, examples —
  are swept to this spelling; string-form `using` and the legacy
  `lib/` prefix are now removable at the physical-retirement commit.
  The fossil-era phase tests (phase3 lexer / phase4 parser / phase5
  linter / phase6 typechecker) exercised legacy-internal APIs through
  `base:meta`/`base:reflect` and retired with the fossil.

## 7. Sysinternal wrapper discipline (designed; landing next)

The floor is only ever touched by same-name wrappers in `base:sys`:

- `base:sysinternal` keeps the C-bound interface, absolutely minimal.
- `base:sys` carries same-name wrapper classes (`Buf`, `Dir`,
  `Reflection` — drafted in `spec/lib/base/sys/`) with full access to
  the floor by its QUALIFIED chain (`base:sysinternal:Buf:bufLength`),
  and may add methods beyond the floor.
- The checker enforces: any qualified sysinternal call from a class
  whose namespace is not `['base','sys']` is a compile error.
- Class identity becomes namespace-qualified in the Loader's dedupe
  (`namespaceJoined + ':' + name`) so the wrapper and floor coexist;
  bare names resolve to the public wrapper (it registers first — the
  floor loads through the wrapper's imports, never directly).

Landing requires a TWO-GENERATION bootstrap (the generation gap):
existing binaries embed the bare-name-dedupe loader, which silently
drops the second `Buf`. Sequence: (A) revert preloads/consumer imports
to floor-direct, build bin/spec with the fossil — its embedded NEW
loader has qualified dedupe; (B) flip preloads to `base/sys` wrappers
and consumers to wrapper imports; bin/spec-A builds that generation;
then the fixed-point chain as usual. The wrapper drafts, the checker
enforcement patch, the qualified findClass paths, and the consumer
migration are all written (this session) and revertible from git
history of this branch's next commit.

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

# ERRORS-PLAN — Unifying the error story (pre-0.1)

Planning document, not a spec. Order and scope are chosen for **least work to the
end goal**: one error currency, three transports with fixed jurisdictions, the
`Json:hasError()` side channel removed.

## Target model

**Currency.** `SpecError of E` is the only error payload type anywhere. No
transport ever flattens an error to `String` (today: `onError(String)` in
File/Http/Socket, `parseError` in Json).

**Transports — jurisdiction is chosen by failure expectation, not API accident:**

| Transport     | Jurisdiction                                                            |
|---------------|-------------------------------------------------------------------------|
| Result-return | Sync, *expected* failure with no sensible default (parse, compile, TLS handshake) |
| Callback      | Async/scope operations; caller must observe failure at the call site     |
| Unwind        | Fallback: exceptional paths, deep propagation, cross-thread transport, and the default when a caller supplies no handler |

**Derived rules.**
- "Never Null" defaults become sugar over results: a `default:`-parameter API
  unwraps the result and returns the default on failure.
- Absent `onError` on async APIs defaults to **re-raise**, never a no-op.
- The side channel (`Json:hasError()` / `errorMessage()` / `parseFailed`) is
  removed; nothing new may use instance-held error state.

## Ground rules

- Every task closes with the session gate: `./bootstrap.sh` fixed point
  (required for any compiler-touching task) + the specunit wave. Commit per
  task with reasoning, including negative results.
- Sysinternal two-part landing: floor functions land **ahead** of their
  consumers (task 1.3 before task 2.5).
- Phases are dependency-ordered. Tasks inside a phase are independent unless
  noted. One parallel lane exists: 2.2 → 2.3 (currency upgrade) has **no
  compiler dependency** and may start as soon as 2.2 lands.

---

## Phase 1 — Compiler

Goal: the language can *express* the target model. Minimal set; everything
else is library work.

- [x] **1.1 Verify exhaustive `when`.** DONE (a26f0ce). Verdict: enforced —
      plain enums (expression + statement forms), payload-variant enums, and
      the predicate-table form (which requires an `else` when
      value-yielding); the checker also rejects redundant `else` arms on
      exhaustive tables (TypeChecker.spec:1282/:1285). Two gaps locked with
      negative tests: payload-variant non-exhaustiveness and the
      predicate-table else rule (TestNegativeControlFlow.spec). Result-
      safety's keystone holds with no compiler change.
- [x] **1.2 Generic tagged-union enums.** DONE (656d7af, 15d93cc, f093946,
      235f62f). Spelling: post-name params mirroring the class grammar —
      `Enum is Maybe of T { Some(T is value), None }` and
      `Enum is Result of T to E { Ok(T is value), Err(E is error) }` (the
      plan's `Result of T, E` shorthand is spelled `of T to E` in the real
      grammar; pre-name `of` stays the value-enum backing type). Landed in
      four steps: (A) parser+desugar params, (B) grounded match-arm payload
      validation, (C) specializer descends into nested variants + dispatch
      through the subject's spec class, (D) TestGenericEnum.spec suite +
      grounded arm-mismatch negative lock. Bootstrap fixed point re-verified
      byte-identical; full wave identical to the seed baseline (9 failures
      pre-exist on main — flagged separately).
- [x] **1.3 Defer floor (sysinternal).** DONE. Cleanup-stack intrinsics over
      the pending-error machinery; the unwind path runs registered cleanups
      **before** the handler walk. Land ahead of consumers (two-part
      landing). Landed as:
  - [x] **1.3a Floor intrinsics (inert).** DONE (1e900d4) as a mark-based
        API (`frameMark`/`runTo(mark)`) over TLS slots 9/10/11. Superseded
        by the barrier API below — see 1.3b for why.
  - [x] **1.3b Barrier API + unwind/exit wiring.** DONE. Two discoveries
        reshaped the design. (1) The mark-based API breaks under
        helper-mediated pushes: a mark snapshotted at frame entry cannot
        own a registration pushed by a callee. The floor became
        barrier-based — `frameEnter()` pushes a barrier (0) on ONE shared
        thread-local stack, `pushCleanup(action)` retains the closure and
        pushes its address above the innermost barrier, `frameExit()` runs
        everything above the frame's barrier newest-first (releasing each
        registration after its action runs, stashing/restoring the pending
        error per the `recordPendingFrame` precedent) and pops the barrier.
        Ownership is Go-style: a registration belongs to the frame whose
        body performed the push. (2) The floor is named `Cleanup`, NOT
        `Defer`: body-bearing floors must have a bare name unique in the
        program — the checker resolves `findClass` by bare name (a
        same-named wrapper shadows the floor's as-imports and self-calls)
        and emitted `@.typename`/`@.vtable` globals would collide. The
        only same-named floor, Mem, is declaration-only and emits nothing.
        The base:sys `Defer` wrapper (`push`) is the sole floor consumer.
        Wiring: `emitDeferFrameEnter` after pool-enter in method and
        closure prologues (body scan keyed on Defer-facility calls, same
        inline-CF traversal as `collectDeclNamesInExpr`); `Cleanup_frameExit`
        on every exit — via `emitReleaseOwnedLocals` for normal paths, and
        a prefix in `emitUnwindCurrentFrame` (after `recordPendingFrame`,
        BEFORE the handler walk; the `curFnDeferExitRan` flag makes the
        later teardown call a no-op). Defer-less frames emit NOTHING (IR
        verified: 5 enter/exit pairs in the defer suite, 0 in defer-less).
        Gate: fixed point byte-for-byte (two converge runs — one with a
        wrapper `threadCleanup` bridge for the seed's baked prelude
        symbol, one after removing it); wave 189/189 suites, 604/604
        tests; TestDeferCleanup: normal-exit LIFO, nested-frame barrier
        scoping, unwind-runs-cleanup-before-handler, helper-frame push
        ownership.
- [ ] **1.4 (optional — may slip) Typed `SpecErrorHandler` overloads.**
      Checker resolves handler overload sets by error-kind (most-specific
      wins); `IrBuilder` handler walk consults the kind. This is
      catch-clause precision; the unified model works without it. Touches:
      `checker/TypeChecker.spec`, `llvm/IrBuilder.spec` (vtable handler slot
      at the `SpecErrorHandler` walk).

Explicitly **not** in phase 1: `try/guard` lowering (it ships with its
facility wrapper in 2.6, as one gated task), Json changes (pure library).

---

## Phase 2 — Machinery

Goal: the standard building blocks exist and the async transports stop
flattening errors. 2.2 → 2.3 is the parallel lane (no compiler dependency).

- [x] **2.1 `Result of T to E` in `base:core`.** DONE (668f103). The Err
      variant carries the FULL currency (`SpecError of E` — kind,
      description, captured stack trace), so a result converts to an unwind
      without information loss. Generic-in-generic payload needed no
      compiler change beyond 1.2. Suite: TestResultCore.spec (construction
      grounding, destructuring, yield-in-operand, ref payloads across
      coexisting instantiations, identity contract, exhaustiveness).
      Compiler IR never imports Result — stdlib additions don't move the
      seed (verified byte-identical).
- [x] **2.2 Error-kind enums.** DONE (8bb1c8d). FileError, HttpError,
      NetError, ThreadError, JsonError — variant sets surveyed from each
      surface's ACTUAL failure strings. Two-part landing: kinds ahead of
      consumers.
- [ ] **2.3 Currency upgrade on the async transports.** `onError` payloads
      become `SpecError of E`:
      - [x] `base:sys:File` DONE (bd1288f): `emitLastError` builds the
        currency (errno text → description, category → kind); all consumers
        migrated (tests, specunit Assert/SpecUnit, X509, theoedit). NOTE
        DISCOVERED: File's callback params are untyped `Function` and the
        checker does not validate closure-invocation arguments — a stale
        String-declaring caller compiles silently. Enforcement moved to a
        speclint rule (3.5) + the final grep gate.
      - [ ] `base:net:Http` / `Socket`: same; internal thread capture already
        transports `SpecError` objects.
      - [ ] `base:sys:thread:Task` / `ThreadScope`: await/scope-exit re-raise
        path verified to carry kinded errors unchanged.
      Gate per batch: wave identical to baseline; examples still compile.
- [ ] **2.4 No silent swallow.** Remove the no-op default closures
      (`Http:send` currently defaults *both* callbacks to no-ops). New APIs:
      `onError` required. Existing APIs: default = re-raise via
      `raiseError`. Gate: negative test asserting the missing-handler path
      surfaces; `TestOsDispatch`-style suites still pass.
- [ ] **2.5 `Defer` wrapper in `base:sys`.** Same-name public wrapper over
      the 1.3 floor, in the `Conditional`/`Loops` family style. Gate:
      cleanup-order tests (normal exit, unwind exit, nested defers).
- [ ] **2.6 `try`/`guard` construct (spans compiler; skippable for alpha).**
      Facility in the control-flow family; yields the unwrapped value or
      unwinds with the `Err` payload. Skippable: explicit `when` is
      functional, just noisier at call sites. Broken into:
  - [ ] **2.6a Facility + runtime fallback.** The facility spelling surfaces
        and lowers through the generic call machinery (correct-but-slower
        path). Gate: fixed point + value-yield matrix test (extend
        `TestValueYield` shapes).
  - [ ] **2.6b Inline fast path.** `ControlFlowCallLowerer` fast path for
        literal closures (the `Conditional:if` two-tier precedent);
        semantics identical to 2.6a. Gate: fixed point + matrix test + IR
        shape assertion (fast path must not allocate a closure object).
- [ ] **2.7 Never Null sugar pilot.** Re-implement one default-parameter
      getter family over a result-returning core (`Json:getString(obj:,
      key:, default:)` is the pilot) to prove the sugar pattern before the
      phase 3 sweep. Gate: existing `TestJson` passes unchanged.

---

## Phase 3 — Conformance across non-compiler libraries

Goal: nothing outside the compiler violates the model; the side channel is
gone.

- [ ] **3.1 Json result-return + side-channel removal.** Result-returning
      `parse`/typed getters (`Result of Any, JsonError`); migrate internal
      consumers (specbuild, speclsp, weather); remove `parseFailed` /
      `parseError` / `hasError` / `errorMessage`; new speclint rule banning
      facility-held error-state patterns (`UnusedUsingRule` precedent).
      Note: the compiler does not import Json (verified via Driver's using
      table), so the fixed point is untouched. Gate: negative tests assert
      new diagnostics; full specunit wave.
- [ ] **3.2 Stdlib sweep, batched by package.** For each: jurisdiction
      decision per API (result / callback / unwind), kind enum where
      missing, no String-flattened payloads, no instance-held error state:
      - batch A (sync, result-shaped): `Uri`, `Dir`, `Process`, regex
        `Arex` (pattern compile failures), `NumericBases`-style parsers.
      - batch B (async, callback-shaped): `tls/TlsClient` / `TlsVerifier`,
        `Audio` / `AudioDevice`, `Input` / `InputHandler`.
      - batch C (runtime, unwind-shaped): `Mem` (panic boundary),
        `Parallel` (worker errors join through Task), `Lazy`, `Box`.
      - batch D (UI, callback-shaped): `cleo`, `theo` event handlers —
        errors from view callbacks route to the app's `SpecErrorHandler`.
      Gate per batch: suite wave + one example per touched package still
      runs.
- [ ] **3.3 Tooling migration.** `specbuild`, `speclsp`, `specunit`,
      `specinit` consume only result/callback/unwind surfaces. Gate:
      `TestSpecBuild`, `TestSpecLsp`, `TestSpeclint`, `TestSpecUnit*`.
- [ ] **3.4 Examples migration.** weather (showcase: result + kinded
      `SpecError` callbacks + Defer around the UI scope), theoedit,
      theojack, scope_as_demo, random_tune. Gate: each example builds and
      its test suite passes.
- [ ] **3.5 Docs + negative-test sweep.** Update the committed error
      documentation (ERRORS.md referenced by `TestErrors`) to the
      jurisdiction table; add negative tests: side-channel usage rejected
      by lint, String-payload `onError` rejected by checker (if typed
      strictly), missing `when` case rejected by checker.
- [ ] **3.6 Final gate.** Repo-wide grep: no `hasError(` outside history,
      no `onError: local Function(String` signatures, no `local .* is
      .*[Ee]rror.*:''` held state in `spec/lib`. Fixed point re-verified.
      Error-path cost spot-check in the benchmark harness (unwind path only
      pays on raise — confirm no per-call regression appears in mc_pi /
      wildcard-filter runs).

---

## Decisions taken (defaults — revisit before alpha, not during)

1. `Result` is **one generic enum** (`Result of T, E`), not per-domain result
   types. Kind enums carry the domain specificity in `E`.
2. Result-return only where failure is *expected and default-less*.
   Default-able getters stay Never-Null sugar; they do not become Results.
3. Callbacks stay required-to-observe on async APIs; the unwind default
   covers absent handlers instead of a no-op.
4. Side channel is **removed**, not deprecated-and-kept: a lint rule bridges
   the transition, then the fields die (task 3.1).
5. Kind enums are plain variant enums per package; `SpecError` itself gains
   no new fields (stack trace, chaining, cross-thread transport already work).
6. Payload binding in `when` is **blessed as shipped**: typed branch
   closures, payloads bound positionally in declaration order
   (`Result:Err: local Function(Int is c, String is m)` — already tested
   green in `TestNextGenFeatures` Feature 7). Named binders in the key may
   land later as an additive, non-breaking evolution; no migration is
   planned or required. The positional hazard is confined to multi-field
   variants with same-typed fields; `Result of T, E` is single-payload, so
   the error path is unaffected.

## Deferred (not needed for the goal)

- Typed `SpecErrorHandler` overloads (task 1.4) if it slips.
- `try`/`guard` (task 2.6) if alpha ships with explicit `when`.
- Weak references / cycle-breaking for ARC (out of scope here; noted because
  unwind tests will keep exercising ARC behavior).

## Test-failure repairs carried on this branch (pre-existing main drift)

Fixed while the error workstream was in flight (all failed identically under
the pre-branch seed binary; none were error-plan work):

- TestStack — checker required-field validation covered private
  (`local`/`contained`) fields that no caller can ever supply (dedcbcd).
- TestHeldResolver + testEntryBadInit + testByteHeldResolverPanic — tests
  adopting the Stage 3–5 init-override contract (`replace` on subclass
  inits); the latter's compile failure had masked the intended panic
  (6f957f2).
- TestAnyRoot.testDefaultToString — pins the documented `TypeName@hash`
  toString contract (282ddf0).
- TestSpeclint.testTemplateStringNotice — two real bugs: silent kwarg-drop
  (`contains(substring:)` → `needle:`; 17 sites incl. vacuous TestTheoEditor
  assertions and live SyntaxHighlighter checks) and Binary expressions
  carrying line=0 from foldBinary (282ddf0, 4b0ff2a).
- TestLlvmIrAndOpt (2) — cast-to-String unified to type identity (Any vs
  concrete paths disagreed); stale 7-field classMeta expectation → 9
  (d16fe30).
- TestPackageResolution — loader bare-name dedup dropped (namespace-
  qualified identity is the contract) + failed resolution candidates now
  unload (c42054f).
- TestAsCast — assertions updated (f2545fb); the suite's FLAKY SEGV remains
  OPEN: ASan makes it deterministic — SEGV in Slab_allocSlot <-
  Arc_allocObj <- Intern_internCstr <- spec_string_intern <-
  testEnumRender; minimal enum-concat repro is clean under ASan, so the
  corruption is injected by earlier tests in the suite (cross-test
  allocator state). Needs a dedicated bisect session before alpha.

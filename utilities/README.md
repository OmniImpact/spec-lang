# Migration utilities (FUNCTIONS.md Part II — temporary)

Tools for the `if` → `Conditional:branch` statement migration. These are
one-shot scaffolding: they **stay for one more job** — the planned
`While` → control-flow-provider rename (FUNCTIONS.md §II.4 reuses
migrate_if.py's scanner for the `While:condition(` → `while(` sweep) —
and **this folder is removed after that lands** (they stay in the commit
history if we ever need to reference or rerun them).

## migrate_if.py

The migration tool itself: rewrites statement-form `if` blocks into
`Conditional:branch(check: {...}, then: {...}, otherwise: {...});` calls.

- String/comment-aware scanner (backslash escapes, `'''` heredocs, backtick
  templates, `#` comments) — nothing inside literals is touched.
- Paren/brace-matched spans; `else if` chains migrate into nested calls.
- Line-anchored: only statement-position ifs (line starts), so the
  value-yield one-liners and C-in-strings are naturally excluded.
- Idempotent: already-migrated files pass through unchanged.
- Adds `['base', 'sys', as Conditional()]` to every using block that lacks
  it (creating one after the namespace line if the class has none).

```
python3 utilities/migrate_if.py [--check] FILE.spec [FILE.spec ...]
```

`--check` reports what would migrate without writing.

## migrate_step.sh / migrate_test_step.sh

The batch pipelines. **The ratchet**: one big hop breaks the previous
generation's loader (the bootstrap's first emission can't self-host), so
migrate a FEW files at a time, verify, bootstrap, commit, repeat.

- `migrate_step.sh FILE...` (compiler/stdlib files): migrate → emit the
  whole compiler → gcc → self-load pre-check → bootstrap → commit. A
  failing pre-check aborts before the bootstrap, so a bad hop never
  poisons the seed.
- `migrate_test_step.sh FILE...` (tests): migrate → compile+run each file
  (must PASS) → commit.

Both abort on the first failure; `git` state stays at the last verified
batch.

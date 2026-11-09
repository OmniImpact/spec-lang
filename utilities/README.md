# Utilities

`run_tests.sh` / `run_sanitized.sh` — the regression gates (FUNCTIONS.md
"Verification discipline").

The migration tooling (migrate_if.py and the step scripts) served twice
— the if/else flip and the While -> Loops fold (FUNCTIONS.md II.3/II.4)
— and was removed after the latter landed; it stays in the commit
history if it is ever needed again.

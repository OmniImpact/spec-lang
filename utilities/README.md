# Utilities

The regression gate is the specunit runner (`specunit/` — a Spec
program): build it into `bin/` and invoke it directly (see
KNOWLEDGE-SPECDEV.md §4a for the commands and the sanitized wave).
`run_tests.sh` / `run_sanitized.sh` were retired — their shim work is
now the two documented commands.

The migration tooling (migrate_if.py and the step scripts) served twice
— the if/else flip and the While -> Loops fold (II.3/II.4)
— and was removed after the latter landed; it stays in the commit
history if it is ever needed again.

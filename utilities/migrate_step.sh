#!/usr/bin/env bash
# migrate_if step: migrate files -> pre-check -> bootstrap -> commit
set -e
cd /home/daniel/Projects/Spec
echo "=== migrating: $*"
python3 /tmp/migrate_if.py "$@"
echo "=== pre-check (emit + gcc + self-load)"
rm -f /tmp/y.c /tmp/y_bin
bin/spec -i spec/base/compiler/driver/Driver.spec --emit-c /tmp/y.c >/tmp/pre.log 2>&1
if grep -q "errors" /tmp/pre.log && grep -qE "Type errors|Compilation aborted" /tmp/pre.log; then
  echo "PRE-CHECK TYPE FAIL"; grep "^\[" /tmp/pre.log | head -3; exit 1
fi
gcc -O2 /tmp/y.c -o /tmp/y_bin -pthread -lm
n=$(/tmp/y_bin -i spec/base/compiler/driver/Driver.spec --emit-c /tmp/z.c 2>&1 | grep -cE "LoadError" || true)
if [ "$n" != "0" ]; then echo "PRE-CHECK LOAD FAIL ($n errors)"; exit 1; fi
echo "pre-check clean"
echo "=== bootstrap"
./bootstrap.sh 2>&1 | grep -E "Fixed point|Error" | head -3
git add -A
git commit -m "migrate(compiler): statement-ifs to Conditional:branch — $*" >/dev/null
git log --oneline -1

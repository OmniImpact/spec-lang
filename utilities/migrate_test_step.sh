#!/usr/bin/env bash
# migrate test files -> compile+run each -> commit
set -e
cd /home/daniel/Projects/Spec
echo "=== migrating: $*"
python3 /tmp/migrate_if.py "$@"
for f in "$@"; do
  name=$(basename $f .spec)
  if bin/spec -i "$f" --emit-c /tmp/ts_$name.c >/tmp/ts_$name.log 2>&1; then
    gcc -O2 /tmp/ts_$name.c -o /tmp/ts_$name -pthread -lm 2>/dev/null
    if /tmp/ts_$name 2>&1 | grep -q "FAIL"; then echo "RUNTIME-FAIL $name"; /tmp/ts_$name | grep FAIL | head -2; exit 1; fi
  else
    echo "TYPE-FAIL $name"; grep "^\[" /tmp/ts_$name.log | head -2; exit 1
  fi
done
echo "all clean"
git add -A
git commit -m "migrate(tests): statement-ifs to Conditional:branch — $*" >/dev/null
git log --oneline -1

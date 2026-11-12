#!/usr/bin/env bash
# The test gate. The runner is specunit (utilities/specunit/SpecUnit.spec
# — a Spec program, see KNOWLEDGE-SPECDEV.md section 4a): it compiles
# and runs every suite and self-describing negative fixture in parallel
# (cores - 2 workers, one compiler thread per compile), then prints the
# summary. This shim compiles specunit with the compiler under test,
# runs it, and adds the repo-specific smoke the general tool does not
# own: the compiler CLI contract (exit codes, stderr) and the bootstrap
# fixed-point freshness. Override the compiler with SPEC= (e.g.
# SPEC="$ROOT/bin/spec-asan" for the sanitized gate).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPEC="${SPEC:-$ROOT/bin/spec}"
if [ ! -x "$SPEC" ]; then
	echo "FAIL: compiler binary not found at $SPEC (run ./bootstrap.sh first, or set SPEC=)" >&2
	exit 1
fi
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
"$SPEC" --quiet -i "$ROOT/utilities/specunit/SpecUnit.spec" -o "$WORK/specunit" || exit 1
cd "$ROOT"
"$WORK/specunit" -s "$SPEC" -t examples -t tests
rc=$?

# --- repo-specific smoke: the compiler CLI contract ---
SMOKE="$WORK/smoke"
mkdir -p "$SMOKE"
cat > "$SMOKE/valid.spec" <<'EOF'
Class is ExitValidApp{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		Output:line('valid');
	}
}
EOF
cat > "$SMOKE/broken.spec" <<'EOF'
Class is ExitBrokenApp{
	local Int is x: ;
}
EOF
smoke=0
if ! "$SPEC" --quiet -i "$SMOKE/valid.spec" -o "$SMOKE/valid" > /dev/null 2>&1; then
	echo "FAIL exit-code: valid program compiles"
	smoke=1
fi
if "$SPEC" --quiet -i "$SMOKE/broken.spec" -o "$SMOKE/broken" > /dev/null 2>&1; then
	echo "FAIL exit-code: syntax errors exit 1"
	smoke=1
fi
"$SPEC" > /dev/null 2>&1
usage_rc=$?
if [ "$usage_rc" -ne 2 ]; then
	echo "FAIL exit-code: usage errors exit 2 (got $usage_rc)"
	smoke=1
fi
"$SPEC" --quiet -i "$SMOKE/broken.spec" -o "$SMOKE/broken2" 2> "$SMOKE/err" > /dev/null
if ! grep -qE 'ype error|yntax' "$SMOKE/err"; then
	echo "FAIL exit-code: diagnostics on stderr"
	smoke=1
fi

# --- the bootstrap fixed-point freshness ---
"$SPEC" --quiet -i "$ROOT/spec/base/compiler/driver/Driver.spec" --emit-c "$SMOKE/fp.c" > /dev/null 2>&1
if ! cmp -s "$SMOKE/fp.c" "$ROOT/bootstrap/spec.c"; then
	echo "FAIL bootstrap fixed point — re-baseline: cp $SMOKE/fp.c bootstrap/spec.c"
	smoke=1
fi

exit $((rc | smoke))

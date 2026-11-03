#!/usr/bin/env bash
# =============================================================================
# Spec Regression Test Runner
#
# Compiles and runs every example program, asserts the negative-diagnostic
# test files, and verifies compiler exit-code semantics.
#
# Usage:   ./utilities/run_tests.sh
# Exit:    0 all green, 1 any failure
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPEC="$ROOT/spec"

if [ ! -x "$SPEC" ]; then
	echo "FAIL: compiler binary not found at $SPEC (run ./bootstrap.sh first)" >&2
	exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

ok()	{ echo "  [PASS] $1"; pass=$((pass + 1)); }
bad()	{ echo "  [FAIL] $1"; fail=$((fail + 1)); }

# -----------------------------------------------------------------------------
# 1. Positive examples: compile, run, require zero [FAIL] marks
# -----------------------------------------------------------------------------
echo "== Positive examples =="
for src in "$ROOT"/examples/*.spec; do
	name="$(basename "$src" .spec)"
	case "$name" in
		grouping_negative_test|regression_negative_type_safety_test) continue ;;
	esac
	bin="$WORK/$name"
	if ! out="$("$SPEC" -i "$src" -o "$bin" 2>&1)"; then
		bad "$name: compilation failed: $(echo "$out" | head -1)"
		continue
	fi
	run_out="$(timeout 10 "$bin" < /dev/null 2>&1)"
	run_status=$?
	if [ $run_status -ne 0 ]; then
		bad "$name: exited with status $run_status"
	elif echo "$run_out" | grep -q "\[FAIL\]"; then
		bad "$name: $(echo "$run_out" | grep '\[FAIL\]' | head -1)"
	else
		ok "$name"
	fi
done

# -----------------------------------------------------------------------------
# 2. Negative diagnostics: must fail to compile with required messages
# -----------------------------------------------------------------------------
echo "== Negative diagnostics =="
assert_compile_failure() {
	local name="$1" src="$2"
	shift 2
	local required=("$@")
	local out
	out="$("$SPEC" -i "$src" -o "$WORK/$name.bin" 2>&1)"
	local status=$?
	if [ $status -eq 0 ]; then
		bad "$name: compilation succeeded but must fail"
		return
	fi
	local missing=0
	local msg
	for msg in "${required[@]}"; do
		if ! echo "$out" | grep -q "$msg"; then
			bad "$name: missing required diagnostic: $msg"
			missing=1
		fi
	done
	[ $missing -eq 0 ] && ok "$name (compile rejected, all diagnostics present)"
}

assert_compile_failure "negative-type-safety" \
	"$ROOT/examples/regression_negative_type_safety_test.spec" \
	"'Float' to 'Int'" \
	"'Array:String' to 'Array:Int'" \
	"'Map:String:String' to 'Map:String:Int'" \
	"Undefined identifier 'untrackedTotal'" \
	"Condition in 'if' must be Boolean" \
	"is read before being initialized" \
	"Argument 'n' for 'CallArgumentMismatch.double'" \
	"Non-exhaustive 'when'"

assert_compile_failure "grouping-negative" \
	"$ROOT/examples/grouping_negative_test.spec" \
	"Duplicate member 'value' in class 'Merged'"

# -----------------------------------------------------------------------------
# 3. Compiler exit-code semantics
# -----------------------------------------------------------------------------
echo "== Exit codes =="
cat > "$WORK/valid.spec" <<'EOF'
class ValidApp{
	replace local Array of String is using: [base:io:Output];
	replace local Function is init(Map of String to String is args){
		output:line("valid");
	}
}
EOF
printf 'class Broken{\n\tlocal Int is x: ;\n}\n' > "$WORK/broken.spec"

"$SPEC" -i "$WORK/valid.spec" -o "$WORK/valid" >/dev/null 2>&1
[ $? -eq 0 ] && ok "successful compile exits 0" || bad "successful compile did not exit 0"

"$SPEC" -i "$WORK/broken.spec" -o "$WORK/broken" >/dev/null 2>&1
[ $? -eq 1 ] && ok "syntax errors exit 1" || bad "syntax errors did not exit 1"

"$SPEC" >/dev/null 2>&1
[ $? -eq 2 ] && ok "usage errors exit 2" || bad "usage errors did not exit 2"

if "$SPEC" -i "$WORK/broken.spec" -o "$WORK/broken" 2>&1 >/dev/null | grep -q "SyntaxError"; then
	ok "diagnostics routed to stderr"
else
	bad "diagnostics not routed to stderr"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "== Summary: $pass passed, $fail failed =="
if [ $fail -ne 0 ]; then
	exit 1
fi
exit 0

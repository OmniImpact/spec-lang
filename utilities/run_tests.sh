#!/usr/bin/env bash
# =============================================================================
# Spec Regression Test Runner
#
# Compiles and runs every demo (examples/) and test suite (tests/), asserts
# the must-fail suites (tests/negative/), and verifies compiler exit-code
# semantics.
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
# 1. Demos & test suites: compile, run, require zero [FAIL] marks
# -----------------------------------------------------------------------------
run_suite() {
	local label="$1"
	local dir="$2"
	echo "== $label =="
	for src in "$dir"/*.spec; do
		local name
		name="$(basename "$src" .spec)"
		local bin="$WORK/$name"
		local out
		if ! out="$("$SPEC" -i "$src" -o "$bin" 2>&1)"; then
			bad "$name: compilation failed: $(echo "$out" | head -1)"
			continue
		fi
		local run_out run_status
		run_out="$(cd "$ROOT" && timeout 10 "$bin" < /dev/null 2>&1)"
		run_status=$?
		if [ $run_status -ne 0 ]; then
			bad "$name: exited with status $run_status"
		elif echo "$run_out" | grep -q "\[FAIL\]"; then
			bad "$name: $(echo "$run_out" | grep '\[FAIL\]' | head -1)"
		else
			ok "$name"
		fi
	done
}

run_suite "Demos" "$ROOT/examples"
run_suite "Test suites" "$ROOT/tests"

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
	"$ROOT/tests/negative/regression_negative_type_safety_test.spec" \
	"'Float' to 'Int'" \
	"'Array:String' to 'Array:Int'" \
	"'Map:String:String' to 'Map:String:Int'" \
	"Undefined identifier 'untrackedTotal'" \
	"Condition in 'if' must be Boolean" \
	"is read before being initialized" \
	"Argument 'n' for 'CallArgumentMismatch.double'" \
	"Non-exhaustive 'when'"

assert_compile_failure "grouping-negative" \
	"$ROOT/tests/negative/grouping_negative_test.spec" \
	"Duplicate member 'value' in class 'Merged'"

assert_compile_failure "merge-negative" \
	"$ROOT/tests/negative/merge_negative_test.spec" \
	"must contain a forward statement" \
	"'merge' requires an Array field" \
	"no parent declares a method with that name"

assert_compile_failure "visibility-negative" \
	"$ROOT/tests/negative/visibility_negative_test.spec" \
	"Member 'secret' is local to class 'VisBase'" \
	"Member 'helper' is contained in class 'VisBase'" \
	"Member 'secret' is local in ancestor 'VisBase' and cannot be replaced or merged" \
	"Member 'counter' is local in ancestor 'ShadowedLocal' and cannot be replaced or merged" \
	"combines 'replace'/'merge' with a visibility modifier"

assert_compile_failure "as-cast-negative" \
	"$ROOT/tests/negative/as_cast_negative_test.spec" \
	"Cannot cast 'Cat' to unrelated class 'Dog'" \
	"Cannot cast to enum 'Color'" \
	"Cast 'as Hex' requires an Int or String operand" \
	"Unknown cast target 'Hexadecimal'"

assert_compile_failure "as-chained-negative" \
	"$ROOT/tests/negative/as_chained_negative_test.spec" \
	"Chained 'as' casts are not supported"

assert_compile_failure "any-contract-negative" \
	"$ROOT/tests/negative/any_contract_negative_test.spec" \
	"Member 'fetch' is not part of the root contract"

assert_compile_failure "invalid-literal-negative" \
	"$ROOT/tests/negative/invalid_literal_negative_test.spec" \
	"Invalid digit in base-16 number literal"

assert_compile_failure "bitwise-negative" \
	"$ROOT/tests/negative/bitwise_negative_test.spec" \
	"Bitwise operator '&' requires Int operands" \
	"Bitwise complement '~' requires an Int operand"

assert_compile_failure "diamond-conflict-negative" \
	"$ROOT/tests/negative/diamond_conflict_negative_test.spec" \
	"inherits conflicting implementations of 'value' from 'DiamondA' and 'DiamondB'"

assert_compile_failure "merge-function-negative" \
	"$ROOT/tests/negative/merge_function_negative_test.spec" \
	"requires the enclosing method to declare 'merge'" \
	"with abstract method from 'FwdBase'" \
	"Partial forward requires named arguments" \
	"passes 3 arguments but parent 'twoOf' accepts 2" \
	"omits 'b' of 'partial' which has no default value" \
	"cannot assign 'String' to 'Int'"

# -----------------------------------------------------------------------------
# 3. Compiler exit-code semantics
# -----------------------------------------------------------------------------
echo "== Exit codes =="
cat > "$WORK/valid.spec" <<'EOF'
Class is ValidApp{
	replace Array of String is using: [base:io:Output];
	replace Function is init(Map of String to String is args){
		output:line("valid");
	}
}
EOF
printf 'Class is Broken{\n\tlocal Int is x: ;\n}\n' > "$WORK/broken.spec"
printf 'class LegacySyntax{\n}\n' > "$WORK/legacy.spec"

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

legacy_out="$("$SPEC" -i "$WORK/legacy.spec" -o "$WORK/legacy" 2>&1)"
if echo "$legacy_out" | grep -q "no longer valid"; then
	ok "legacy 'class' rejected with pointed diagnostic"
else
	bad "legacy 'class' not rejected with pointed diagnostic"
fi

# -----------------------------------------------------------------------------
# 4. Bootstrap fixed-point freshness: the committed spec.c must equal the
#    compiler's own emitted output, proving the checked-in seed is current.
# -----------------------------------------------------------------------------
echo "== Bootstrap fixed point =="
if [ -f "$ROOT/bootstrap/spec.c" ]; then
	SELF_C="$WORK/self_hosted.c"
	if "$SPEC" -i "$ROOT/lib/compiler/Driver.spec" --emit-c "$SELF_C" >/dev/null 2>&1; then
		if cmp -s "$SELF_C" "$ROOT/bootstrap/spec.c"; then
			ok "bootstrap/spec.c is the current fixed point"
		else
			bad "bootstrap/spec.c is STALE: re-baseline with 'cp <emitted> bootstrap/spec.c && ./bootstrap.sh'"
		fi
	else
		bad "fixed-point check: self-compilation failed"
	fi
else
	bad "bootstrap/spec.c not found"
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

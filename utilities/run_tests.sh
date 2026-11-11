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
# Compiler under test; override to test an alternate binary, e.g.:
#   SPEC="$ROOT/bin/spec-asan" bash utilities/run_tests.sh
SPEC="${SPEC:-$ROOT/bin/spec}"

if [ ! -x "$SPEC" ]; then
	echo "FAIL: compiler binary not found at $SPEC (run ./bootstrap.sh first, or set SPEC=)" >&2
	exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

# Parallelism: compile+run waves over this many workers (16-core host).
JOBS="${JOBS:-12}"

ok()	{ echo "  [PASS] $1"; pass=$((pass + 1)); }
bad()	{ echo "  [FAIL] $1"; fail=$((fail + 1)); }

# -----------------------------------------------------------------------------
# 1. Demos & test suites: compile, run, require zero [FAIL] marks
#
# Tests run JOBS-wide (each is an independent compiler invocation plus a
# binary run); results are collected per test and printed in scan order so
# the output stays deterministic.
# -----------------------------------------------------------------------------
run_one() {
	local src="$1" name="$2" key="$3"
	local bin="$WORK/$key-$name"
	if ! out="$("$SPEC" --quiet -i "$src" -o "$bin" 2>&1)"; then
		echo "F|$name|compilation failed: $(echo "$out" | head -1)" > "$WORK/$key-$name.res"
		return
	fi
	local run_out run_status
	run_out="$(cd "$ROOT" && timeout 10 "$bin" < /dev/null 2>&1)"
	run_status=$?
	if [ $run_status -ne 0 ]; then
		echo "F|$name|exited with status $run_status" > "$WORK/$key-$name.res"
	elif echo "$run_out" | grep -q "\[FAIL\]"; then
		echo "F|$name|$(echo "$run_out" | grep '\[FAIL\]' | head -1)" > "$WORK/$key-$name.res"
	else
		echo "P|$name|" > "$WORK/$key-$name.res"
	fi
}

run_suite() {
	local label="$1" dir="$2" key="$3"
	echo "== $label =="
	local names=()
	for src in "$dir"/*.spec; do
		names+=("$(basename "$src" .spec)")
	done
	for name in "${names[@]}"; do
		while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do
			wait -n
		done
		run_one "$dir/$name.spec" "$name" "$key" &
	done
	wait
	for name in "${names[@]}"; do
		local res="${RES:-}"
		res="$(cat "$WORK/$key-$name.res" 2>/dev/null || echo "F|$name|missing result")"
		local st="${res%%|*}"
		local rest="${res#*|}"
		local nm="${rest%%|*}"
		local detail="${rest#*|}"
		if [ "$st" = "P" ]; then
			ok "$nm"
		else
			bad "$nm: $detail"
		fi
	done
}

run_suite "Demos" "$ROOT/examples" demos
run_suite "Test suites" "$ROOT/tests" tests

# -----------------------------------------------------------------------------
# 2. Negative diagnostics: must fail to compile with required messages
# -----------------------------------------------------------------------------
echo "== Negative diagnostics =="
assert_compile_failure() {
	local name="$1" src="$2"
	shift 2
	local required=("$@")
	local out
	out="$("$SPEC" --quiet -i "$src" -o "$WORK/$name.bin" 2>&1)"
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
	"Method declared return type 'Boolean', but returned 'Int'." \
	"is read before being initialized" \
	"Argument 'n' for 'CallArgumentMismatch.double'" \
	"Non-exhaustive match"

assert_compile_failure "nested-ambiguity-at-reference" \
	"$ROOT/tests/negative/n25_inner_name_collision_negative_test.spec" \
	"Type 'Helper' is provided by LibA:Helper and LibB:Helper; qualify the reference"

assert_compile_failure "field-through-import-wall" \
	"$ROOT/tests/negative/n26_field_through_import_negative_test.spec" \
	"Fields are not reachable through the class-name prefix 'FieldDep'"

assert_compile_failure "inner-import-leak-wall" \
	"$ROOT/tests/negative/n27_inner_import_leak_negative_test.spec" \
	"Undefined function 'floor' on class 'N27InnerImportLeak'"

assert_compile_failure "as-form-construction-wall" \
	"$ROOT/tests/negative/n28_as_form_construction_negative_test.spec" \
	"'Math2' is not imported by 'N28AsFormConstruction'; add it to the using declaration"

assert_compile_failure "as-form-default-wall" \
	"$ROOT/tests/negative/n29_as_form_default_negative_test.spec" \
	"'Math2' is not imported by 'N29AsFormDefault'; add it to the using declaration to construct it"

assert_compile_failure "held-members-walls" \
	"$ROOT/tests/negative/n30_held_members_negative_test.spec" \
	"is read-only: held members are class-scoped single copies" \
	"combines 'held' with 'replace'/'merge'" \
	"'self' is not available" \
	"of the same class; the once-guards would deadlock" \
	"reach it through the class name, not an instance" \
	"is local to class 'N30HeldWalls' and cannot be accessed from 'N30HeldProbe'" \
	"requires an initializer"

assert_compile_failure "held-function-walls" \
	"$ROOT/tests/negative/n31_held_functions_negative_test.spec" \
	"is class-scoped: call it through the class name, not an instance" \
	"must be called; bare references to held functions are not supported" \
	"cannot be a root-contract member" \
	"held functions do not overload" \
	"A held member body has no instance: 'self' is not available" \
	"use self (§2.2)"

assert_compile_failure "held-resolver-walls" \
	"$ROOT/tests/negative/n32_held_resolver_negative_test.spec" \
	"must be declared exactly 'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)'" \
	"The resolution hook cannot resolve through its own class prefix" \
	"only held members are (§2.3)" \
	"is read-only: resolution-hook values are cached single copies"

assert_compile_failure "cases-match-walls" \
	"$ROOT/tests/negative/n33_cases_match_negative_test.spec" \
	"is not a held member of 'N33Sink'" \
	"Duplicate match key 'file'" \
	"Non-exhaustive match: missing arm(s) N33Mode:off" \
	"A value-yielding match requires an else arm" \
	"The match arms mix value-yielding and void closures" \
	"Match arms after else are unreachable" \
	"'Int' cannot be matched"

assert_compile_failure "predicate-table-literal-wall" \
	"$ROOT/tests/negative/n35_predicate_table_literal_negative_test.spec" \
	"predicate match table is compile-time" \

assert_compile_failure "predicate-params-wall" \
	"$ROOT/tests/negative/n36_predicate_params_negative_test.spec" \
	"Predicate match arms take no parameters" \

assert_compile_failure "loop-vars-literals-wall" \
	"$ROOT/tests/negative/n34_loop_vars_literals_negative_test.spec" \
	"requires inline literal closures"

assert_compile_failure "import-local-member-wall" \
	"$ROOT/tests/negative/n24_import_local_member_negative_test.spec" \
	"is local to class 'StatefulCounter' and cannot be accessed from 'WallProbe'"

assert_compile_failure "transitive-import-wall" \
	"$ROOT/tests/transitive/TransitiveUse.spec" \
	"Members of 'Output' are callable only through an instance"

assert_compile_failure "void-in-value-context" \
	"$ROOT/tests/negative/n23_void_in_value_context_negative_test.spec" \
	"'Conditional.if' declares no return value" \
	"'Output.line' declares no return value"

assert_compile_failure "instance-model-n1-own-name" \
	"$ROOT/tests/negative/n1_own_name_negative_test.spec" \
	"through the class name inside 'N1SelfRead' itself; use self"

assert_compile_failure "instance-model-n2-undefined-bare" \
	"$ROOT/tests/negative/n2_undefined_bare_negative_test.spec" \
	"Undefined function 'nope' on class 'N2UndefinedBare'"

assert_compile_failure "instance-model-n3-bare-collision" \
	"$ROOT/tests/negative/n3_bare_collision_negative_test.spec" \
	"provided by the enclosing class and Math; qualify the call"

assert_compile_failure "instance-model-n4-type-import" \
	"$ROOT/tests/negative/n4_type_import_negative_test.spec" \
	"Members of 'Math' are callable only through an instance"

assert_compile_failure "instance-model-n5-duplicate-as" \
	"$ROOT/tests/negative/n5_duplicate_as_negative_test.spec" \
	"instance-imports 'Math' more than once"

assert_compile_failure "instance-model-n6-import-cycle" \
	"$ROOT/tests/negative/instancecycle/cycroot.spec" \
	"Instance import cycle: A -> B -> A"

assert_compile_failure "instance-model-n7-nonliteral-arg" \
	"$ROOT/tests/negative/n7_nonliteral_as_arg_negative_test.spec" \
	"must be direct literal values"

assert_compile_failure "instance-model-n8-enum-import" \
	"$ROOT/tests/negative/n8_enum_as_import_negative_test.spec" \
	"Cannot instance-import enum 'ExpressionKind'"

assert_compile_failure "overloads-n12-identical-signature" \
	"$ROOT/tests/negative/n12_identical_signature_negative_test.spec" \
	"declare identical signatures"

assert_compile_failure "overloads-n13-ambiguous-positional" \
	"$ROOT/tests/negative/n13_ambiguous_positional_negative_test.spec" \
	"the arguments match multiple overloads; use named arguments"

assert_compile_failure "overloads-n14-no-exact-match" \
	"$ROOT/tests/negative/n14_no_exact_match_negative_test.spec" \
	"No exact overload of 'N14NoExact.f' for (Any)"

assert_compile_failure "overloads-n15-mixed-call" \
	"$ROOT/tests/negative/n15_mixed_call_negative_test.spec" \
	"Mixed positional and named arguments are not supported"

assert_compile_failure "as-n19-filled-branch" \
	"$ROOT/tests/negative/n19_as_filled_branch_negative_test.spec" \
	"has no open scope slot"

assert_compile_failure "gating-n18-unimported-type" \
	"$ROOT/tests/negative/n18gate/n18_unimported_type_negative_test.spec" \
	"'GTarget' is not imported by 'N18UnimportedType'"

assert_compile_failure "hardening-n17-string-relational-mixed" \
	"$ROOT/tests/negative/n17_string_relational_mixed_negative_test.spec" \
	"requires two String operands"

assert_compile_failure "overloads-n16-replace-overloaded" \
	"$ROOT/tests/negative/n16_replace_overloaded_negative_test.spec" \
	"Cannot replace or merge an overloaded method"

assert_compile_failure "instance-model-n11-prefix-field" \
	"$ROOT/tests/negative/n11_prefix_field_negative_test.spec" \
	"Fields are not reachable through the class-name prefix"

assert_compile_failure "instance-model-n10-init-on-instance" \
	"$ROOT/tests/negative/n10_init_on_instance_negative_test.spec" \
	"'init' is construct-only"

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
	"Cannot cast 'Dog' to unrelated class 'Color'" \
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

assert_compile_failure "byte-negative" \
	"$ROOT/tests/negative/byte_negative_test.spec" \
	"cannot assign 'Int' to 'Byte'" \
	"Cannot cast 'String' to 'Byte'"

assert_compile_failure "list-guard-negative" \
	"$ROOT/tests/negative/list_guard_negative_test.spec" \
	"Bare List type requires" \
	"requires a 'default:' argument"

assert_compile_failure "entry-init-signature-wall" \
	"$ROOT/tests/negative/n37_entry_init_params_negative_test.spec" \
	"init must take no parameters or a single 'Map of String to String'"

assert_compile_failure "entry-enum-only-wall" \
	"$ROOT/tests/negative/n38_entry_enum_only_negative_test.spec" \
	"No entry class found in"

# -----------------------------------------------------------------------------
# 2b. Runtime panics: must compile, must exit non-zero with required diagnostics
# -----------------------------------------------------------------------------
echo "== Runtime panics =="
assert_runtime_panic() {
	local name="$1" src="$2"
	shift 2
	local required=("$@")
	local out
	if ! out="$("$SPEC" --quiet -i "$src" -o "$WORK/$name.bin" 2>&1)"; then
		bad "$name: compilation failed: $(echo "$out" | head -1)"
		return
	fi
	local run_out run_status
	run_out="$(cd "$ROOT" && timeout 10 "$WORK/$name.bin" < /dev/null 2>&1)"
	run_status=$?
	if [ $run_status -eq 0 ]; then
		bad "$name: exited 0 but must panic at runtime"
		return
	fi
	local missing=0
	local msg
	for msg in "${required[@]}"; do
		if ! echo "$run_out" | grep -q "$msg"; then
			bad "$name: missing panic diagnostic: $msg"
			missing=1
		fi
	done
	[ $missing -eq 0 ] && ok "$name (runtime panic, all diagnostics present)"
}

assert_runtime_panic "byte-range-panic" \
	"$ROOT/tests/negative/byte_range_panic_test.spec" \
	"[Spec Runtime Panic]" \
	"Byte cast out of range: 300"

assert_runtime_panic "held-resolver-missing-branch" \
	"$ROOT/tests/negative/byte_held_resolver_panic_test.spec" \
	"No held member 'phantom' on HeldPanicRegistry"

# -----------------------------------------------------------------------------
# 3. Compiler exit-code semantics
# -----------------------------------------------------------------------------
echo "== Exit codes =="
cat > "$WORK/valid.spec" <<'EOF'
Class is ValidApp{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		Output:line("valid");
	}
}
EOF
printf 'Class is Broken{\n\tlocal Int is x: ;\n}\n' > "$WORK/broken.spec"
printf 'class LegacySyntax{\n}\n' > "$WORK/legacy.spec"

"$SPEC" --quiet -i "$WORK/valid.spec" -o "$WORK/valid" >/dev/null 2>&1
[ $? -eq 0 ] && ok "successful compile exits 0" || bad "successful compile did not exit 0"

"$SPEC" -i "$WORK/broken.spec" -o "$WORK/broken" >/dev/null 2>&1
[ $? -eq 1 ] && ok "syntax errors exit 1" || bad "syntax errors did not exit 1"

"$SPEC" >/dev/null 2>&1
[ $? -eq 2 ] && ok "usage errors exit 2" || bad "usage errors did not exit 2"

if "$SPEC" --quiet -i "$WORK/broken.spec" -o "$WORK/broken" 2>&1 >/dev/null | grep -q "SyntaxError"; then
	ok "diagnostics routed to stderr"
else
	bad "diagnostics not routed to stderr"
fi

legacy_out="$("$SPEC" --quiet -i "$WORK/legacy.spec" -o "$WORK/legacy" 2>&1)"
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
	if "$SPEC" -i "$ROOT/spec/base/compiler/driver/Driver.spec" --emit-c "$SELF_C" >/dev/null 2>&1; then
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

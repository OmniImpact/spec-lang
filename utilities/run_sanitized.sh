#!/usr/bin/env bash
# =============================================================================
# Spec Sanitized Regression Runner
#
# Builds an AddressSanitizer + UBSan instrumented compiler from the canonical
# bootstrap source (bootstrap/spec.c) and runs the full regression suite
# against it via SPEC=.
#
# Scope: validates crash-freedom of the compiler process itself (use-after-free,
# out-of-bounds access, undefined behavior). Generated test binaries are
# compiled normally through the instrumented compiler's internal gcc call.
#
# Usage:   ./utilities/run_sanitized.sh
# Exit:    0 all green, 1 any failure
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$ROOT/bootstrap/spec.c" ]; then
	echo "FAIL: bootstrap/spec.c not found (run ./bootstrap.sh first)" >&2
	exit 1
fi

CC_BIN="${CC:-gcc}"

echo "== Building ASan/UBSan-instrumented compiler =="
"$CC_BIN" -O1 -g \
	-fsanitize=address,undefined \
	-fno-sanitize-recover=undefined \
	-fno-omit-frame-pointer \
	"$ROOT/bootstrap/spec.c" -o "$ROOT/spec-asan" -pthread -lm

# Leak detection is OFF by default. The ARC engine fully reclaims the compiler's
# object graph (AST, tokens, class tree — zero spec_alloc leaks), and an atexit
# shutdown reclaims the string ring buffer. What remains is string-lifetime
# churn (~0.5 MB for a self-compile): strings are not refcounted, so locals,
# temporaries, and clone chains are unreachable-but-never-freed at process exit.
# Flipping this on requires string-lifetime ownership (planned follow-up).
# The gate below covers the dangerous classes: use-after-free, out-of-bounds,
# double-free, and fatal undefined behavior.
# Opt back in for leak accounting with: ASAN_OPTIONS=detect_leaks=1 ./utilities/run_sanitized.sh
export ASAN_OPTIONS="${ASAN_OPTIONS:-detect_leaks=0}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-print_stacktrace=1:halt_on_error=1}"

echo "== Regression suite under sanitizer =="
if SPEC="$ROOT/spec-asan" bash "$ROOT/utilities/run_tests.sh"; then
	echo ""
	echo "== Sanitized suite: PASS =="
else
	echo ""
	echo "== Sanitized suite: FAIL (see sanitizer reports above) ==" >&2
	exit 1
fi

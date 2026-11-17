#!/usr/bin/env bash
# Spec Programming Language - Bootstrap Script
#
# Builds the compiler from the canonical LLVM IR seed (bootstrap/spec.ll)
# and runtime shim (bootstrap/spec_runtime.c), and verifies the self-hosting
# fixed point: the freshly built compiler must recompile its own sources to
# byte-identical LLVM IR. Converges over up to three cycles.
set -euo pipefail

echo "=================================================="
echo " Bootstrapping Spec Compiler"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "bootstrap/spec.ll" ] || [ ! -f "bootstrap/spec_runtime.c" ]; then
	echo "Error: Canonical bootstrap seed 'bootstrap/spec.ll' or 'bootstrap/spec_runtime.c' not found." >&2
	exit 1
fi

CLANG_BIN="${CLANG:-clang}"
DRIVER="spec/base/compiler/driver/Driver.spec"

EXTRA_LIBS=""
case "$(uname -s)" in
	MINGW*|MSYS*|CYGWIN*)
		CUR_DRIVE="$(pwd | cut -d/ -f2)"
		mkdir -p "/${CUR_DRIVE}/tmp" /tmp /c/tmp /d/tmp 2>/dev/null || true
		if command -v mount >/dev/null 2>&1; then
			mount -f "/${CUR_DRIVE}/tmp" /tmp 2>/dev/null || true
		fi
		EXTRA_LIBS="-lws2_32 -lwinmm -lpsapi"
		;;
	Darwin*)
		EXTRA_LIBS="-framework AudioToolbox"
		;;
	Linux*)
		EXTRA_LIBS="-ldl -no-pie"
		;;
esac

file_cmp() {
	if command -v cmp >/dev/null 2>&1; then
		cmp -s "$1" "$2"
	elif command -v diff >/dev/null 2>&1; then
		diff -q "$1" "$2" >/dev/null 2>&1
	else
		[ "$(wc -c < "$1")" -eq "$(wc -c < "$2")" ] && [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$(sha256sum "$2" | cut -d' ' -f1)" ]
	fi
}

echo "Compiling bootstrap/spec_runtime.c -> /tmp/spec_bootstrap_runtime.o via ${CLANG_BIN}..."
"${CLANG_BIN}" -O2 -c bootstrap/spec_runtime.c -o /tmp/spec_bootstrap_runtime.o -pthread

for cycle in 1 2 3; do
	echo "Compiling bootstrap/spec.ll -> bin/spec via ${CLANG_BIN}..."
	"${CLANG_BIN}" -O2 -Wno-override-module bootstrap/spec.ll /tmp/spec_bootstrap_runtime.o -o bin/spec -pthread -lm ${EXTRA_LIBS}

	echo "Verifying the self-hosting fixed point (cycle ${cycle})..."
	bin/spec -i "$DRIVER" --emit-llvm /tmp/spec_fixedpoint_verify.ll --emit-runtime /tmp/spec_runtime_verify.c --quiet
	if file_cmp /tmp/spec_fixedpoint_verify.ll bootstrap/spec.ll && file_cmp /tmp/spec_runtime_verify.c bootstrap/spec_runtime.c; then
		echo "Fixed point verified: the compiler reproduces its own seed byte-for-byte."
		rm -f /tmp/spec_fixedpoint_verify.ll /tmp/spec_runtime_verify.c /tmp/spec_bootstrap_runtime.o
		echo "Spec compiler bootstrapped successfully!"
		bin/spec --help || true
		exit 0
	fi
	if [ "$cycle" -lt 3 ]; then
		echo "Seed drifted (compiler sources changed) — converging..."
		cp /tmp/spec_fixedpoint_verify.ll bootstrap/spec.ll
		if ! file_cmp /tmp/spec_runtime_verify.c bootstrap/spec_runtime.c; then
			cp /tmp/spec_runtime_verify.c bootstrap/spec_runtime.c
			"${CLANG_BIN}" -O2 -c bootstrap/spec_runtime.c -o /tmp/spec_bootstrap_runtime.o -pthread
		fi
	else
		rm -f /tmp/spec_fixedpoint_verify.ll /tmp/spec_runtime_verify.c /tmp/spec_bootstrap_runtime.o
		echo "Error: the fixed point did not converge in 3 cycles (nondeterministic emission?)" >&2
		exit 1
	fi
done

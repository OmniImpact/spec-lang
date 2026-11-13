#!/usr/bin/env bash
# Spec Programming Language - Bootstrap Script
#
# Builds the compiler from the canonical C11 seed (bootstrap/spec.c) and
# verifies the self-hosting fixed point: the freshly built compiler must
# recompile its own sources to byte-identical C. Converges over up to
# three cycles — needed after compiler-source changes shift the slot map.
set -euo pipefail

echo "=================================================="
echo " Bootstrapping Spec Compiler"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "bootstrap/spec.c" ]; then
	echo "Error: Canonical bootstrap source 'bootstrap/spec.c' not found." >&2
	exit 1
fi

CC_BIN="${CC:-gcc}"
DRIVER="spec/base/compiler/driver/Driver.spec"

EXTRA_LIBS=""
case "$(uname -s)" in
	MINGW*|MSYS*|CYGWIN*)
		EXTRA_LIBS="-lws2_32 -lwinmm"
		;;
	Darwin*)
		EXTRA_LIBS="-framework AudioToolbox"
		;;
	Linux*)
		EXTRA_LIBS="-ldl"
		;;
esac

for cycle in 1 2 3; do
	echo "Compiling bootstrap/spec.c -> bin/spec via ${CC_BIN}..."
	"${CC_BIN}" -O2 bootstrap/spec.c -o bin/spec -pthread -lm ${EXTRA_LIBS}

	echo "Verifying the self-hosting fixed point (cycle ${cycle})..."
	bin/spec -i "$DRIVER" --emit-c /tmp/spec_fixedpoint_verify.c --quiet
	if cmp -s /tmp/spec_fixedpoint_verify.c bootstrap/spec.c; then
		echo "Fixed point verified: the compiler reproduces its own seed byte-for-byte."
		rm -f /tmp/spec_fixedpoint_verify.c
		echo "Spec compiler bootstrapped successfully!"
		bin/spec --help || true
		exit 0
	fi
	if [ "$cycle" -lt 3 ]; then
		echo "Seed drifted (compiler sources changed) — converging..."
		cp /tmp/spec_fixedpoint_verify.c bootstrap/spec.c
	else
		echo "Error: the fixed point did not converge in 3 cycles (nondeterministic emission?)" >&2
		exit 1
	fi
done

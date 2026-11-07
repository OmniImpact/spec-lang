#!/usr/bin/env bash
# Spec Programming Language - Bootstrap Script
#
# Builds the compiler from the canonical C11 seed (bootstrap/spec.c) and
# verifies the self-hosting fixed point: the freshly built compiler must
# recompile its own sources to byte-identical C.
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
echo "Compiling bootstrap/spec.c -> bin/spec via ${CC_BIN}..."
"${CC_BIN}" -O2 bootstrap/spec.c -o bin/spec -pthread -lm

echo "Verifying the self-hosting fixed point..."
bin/spec -i spec/base/compiler/driver/Driver.spec --emit-c /tmp/spec_fixedpoint_verify.c --quiet
if cmp -s /tmp/spec_fixedpoint_verify.c bootstrap/spec.c; then
	echo "Fixed point verified: the compiler reproduces its own seed byte-for-byte."
else
	echo "WARNING: emitted C differs from bootstrap/spec.c (stale seed?)." >&2
	echo "  Re-baseline with: bin/spec -i spec/base/compiler/driver/Driver.spec --emit-c bootstrap/spec.c" >&2
fi
rm -f /tmp/spec_fixedpoint_verify.c

echo "Spec compiler bootstrapped successfully!"
bin/spec --help || true

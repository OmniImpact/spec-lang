#!/usr/bin/env bash
# Spec Programming Language - Self-Hosting Bootstrap Script
# Builds the official pure-Spec compiler executable directly from canonical C11 source.
set -euo pipefail

echo "=================================================="
echo " Bootstrapping Spec Compiler (Pure-Spec Bootstrap)"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "bootstrap/spec.c" ]; then
	echo "Error: Canonical bootstrap source 'bootstrap/spec.c' not found." >&2
	exit 1
fi

echo "Compiling bootstrap/spec.c -> ./spec via gcc..."
gcc -O2 bootstrap/spec.c -o spec -pthread -lm

echo "Spec compiler bootstrapped successfully!"
./spec --help || true

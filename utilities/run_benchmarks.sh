#!/usr/bin/env bash
# =============================================================================
# Spec Cross-Language Performance Benchmark Runner
#
# Runs the identical Monte Carlo pi benchmark (mc_pi.* in this directory) in
# every available language, measuring both COMPILE and EXECUTION:
#
#   compile — wall seconds, CPU seconds, peak RSS of each build step
#   run     — wall seconds, CPU seconds, peak RSS, and the program-reported
#             sampling rate (points/sec) per configuration
#
# Methodology notes live in README-PERFORMANCE.md. Defaults: 3 measured runs
# per configuration (median reported), 200M points for compiled languages,
# 20M for the GIL/GVL-interpreted lane (Python/Ruby), 8-thread parallel
# fan-out. Results land in $SPEC_BENCH_OUT (default /tmp/spec-bench).
#
# Missing toolchains are skipped with a notice, not fatal.
#
# Usage:  utilities/run_benchmarks.sh
# Env:    RUNS=3 PAR=8 SPEC_BENCH_OUT=/tmp/spec-bench GO=<path> KOTLINC=<path>
#         JAVAC=<path>
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCH="$SCRIPT_DIR/benchmarks"
OUT="${SPEC_BENCH_OUT:-/tmp/spec-bench}"
RUNS="${RUNS:-3}"
PAR="${PAR:-8}"
P_COMP=200000000
P_INT=20000000
mkdir -p "$OUT"
RESULTS="$OUT/results.csv"
BUILDS="$OUT/builds.csv"
: > "$RESULTS"
: > "$BUILDS"

have() { command -v "$1" >/dev/null 2>&1; }

# Toolchain discovery: PATH first, env overrides for out-of-tree installs.
GO_BIN="${GO:-go}"
KOTLINC_BIN="${KOTLINC:-kotlinc}"
JAVAC="${JAVAC:-}"
if [ -z "$JAVAC" ] && have java; then
	JH="$(java -XshowSettings:properties -version 2>&1 | awk '/java.home/ {print $3}')"
	[ -n "$JH" ] && [ -x "$JH/bin/javac" ] && JAVAC="$JH/bin/javac"
fi

# measure_step LABEL -- cmd... : one measured build step.
# Parses measure.py's __MEASURE__ line into $W / $C / $R / $RC and emits a
# builds.csv row — unless the command failed, in which case nothing is
# recorded (a failed build must not masquerade as a datapoint).
measure_step() {
	local label="$1"; shift
	local out w c r rc
	out="$(python3 "$BENCH/measure.py" "$@")"
	w="$(awk '/__MEASURE__/ {split($2,a,"="); print a[2]}' <<< "$out")"
	c="$(awk '/__MEASURE__/ {split($3,a,"="); print a[2]}' <<< "$out")"
	r="$(awk '/__MEASURE__/ {split($4,a,"="); print a[2]}' <<< "$out")"
	rc="$(awk '/__MEASURE__/ {split($5,a,"="); print a[2]}' <<< "$out")"
	if [ "$rc" != "0" ]; then
		echo "  [FAIL] $label: build command exited $rc — no datapoint recorded"
		[ -n "$out" ] && printf '%s\n' "$out" | grep -v '__MEASURE__' | tail -5 | sed 's/^/      /'
		return 1
	fi
	printf '%s,%s,%s,%s\n' "$label" "$w" "$c" "$r"
}

# run_matrix LANG THREADS POINTS WARMUPS -- cmd...
# One warm-up pass (unmeasured) then RUNS measured passes into $RESULTS.
# A failing run is recorded as failed, never as a zero-rate datapoint.
run_matrix() {
	local lang="$1" threads="$2" points="$3" warmups="$4"; shift 4
	local w r out rate wall cpu rss rc
	for ((w = 0; w < warmups; w++)); do "$@" >/dev/null 2>&1; done
	for ((r = 1; r <= RUNS; r++)); do
		out="$(python3 "$BENCH/measure.py" "$@")"
		rate="$(grep -o 'rate=[0-9.e+-]*' <<< "$out" | head -1 | cut -d= -f2)"
		# The Spec benchmark reports its own Throughput line instead of rate=.
		if [ -z "$rate" ]; then
			rate="$(grep -oE 'Throughput: [0-9]+' <<< "$out" | head -1 | awk '{print $2}')"
		fi
		wall="$(awk '/__MEASURE__/ {split($2,a,"="); print a[2]}' <<< "$out")"
		cpu="$(awk '/__MEASURE__/ {split($3,a,"="); print a[2]}' <<< "$out")"
		rss="$(awk '/__MEASURE__/ {split($4,a,"="); print a[2]}' <<< "$out")"
		rc="$(awk '/__MEASURE__/ {split($5,a,"="); print a[2]}' <<< "$out")"
		if [ "$rc" != "0" ] || [ -z "$rate" ]; then
			echo "  [run $r] FAIL (exit=$rc rate=${rate:-none}) — recorded as failed"
			echo "$lang,$threads,$points,$r,FAIL,,," >> "$RESULTS"
			continue
		fi
		echo "$lang,$threads,$points,$r,$wall,$cpu,$rss,$rate" >> "$RESULTS"
		echo "  [run $r] rate=${rate:-?} pts/s  wall=${wall}s  cpu=${cpu}s  rss=${rss}KB"
	done
}

echo "== Spec cross-language benchmark runner =="
echo "   runs per config: $RUNS   parallel fan-out: $PAR threads"
echo "   output: $OUT"
echo ""

# -----------------------------------------------------------------------------
# 1. Build phase — every compile step is itself measured.
# -----------------------------------------------------------------------------
echo "== Build phase (wall / cpu / peak RSS per compile) =="

if have gcc; then
	measure_step c gcc -O2 "$BENCH/mc_pi.c" -o "$OUT/mc_pi_c" -pthread -lm | tee -a "$BUILDS"
	measure_step c32 gcc -O2 "$BENCH/mc_pi32.c" -o "$OUT/mc_pi_c32" -pthread -lm | tee -a "$BUILDS"
else
	echo "   [SKIP] gcc not found"
fi
if have g++; then
	measure_step cpp g++ -O2 -std=c++17 "$BENCH/mc_pi.cpp" -o "$OUT/mc_pi_cpp" -pthread | tee -a "$BUILDS"
else
	echo "   [SKIP] g++ not found"
fi
if have rustc; then
	measure_step rust rustc -O "$BENCH/mc_pi.rs" -o "$OUT/mc_pi_rs" | tee -a "$BUILDS"
else
	echo "   [SKIP] rustc not found"
fi
if [ -x "$GO_BIN" ] || have go; then
	(cd "$BENCH" && GOTOOLCHAIN=local measure_step go "$GO_BIN" build -o "$OUT/mc_pi_go" mc_pi.go) | tee -a "$BUILDS"
else
	echo "   [SKIP] go not found"
fi
if have java; then
	if [ -n "$JAVAC" ]; then
		mkdir -p "$OUT/classes"
		measure_step java "$JAVAC" -d "$OUT/classes" "$BENCH/mc_pi.java" | tee -a "$BUILDS"
	else
		echo "   java: no javac on this JDK — compilation is embedded in the first run (single-file launch)"
		echo "java,embedded,,, " | sed 's/,$//' >> "$BUILDS"
	fi
else
	echo "   [SKIP] java not found"
fi
if [ -e "$KOTLINC_BIN" ] || have kotlinc; then
	measure_step kotlin "$KOTLINC_BIN" "$BENCH/mc_pi.kt" -include-runtime -d "$OUT/mc_pi_kt.jar" | tee -a "$BUILDS"
else
	echo "   [SKIP] kotlinc not found"
fi
if [ -x "$ROOT/bin/spec" ]; then
	measure_step spec "$ROOT/bin/spec" --quiet -i "$ROOT/examples/pi_benchmark.spec" -o "$OUT/spec_pi" | tee -a "$BUILDS"
else
	echo "   [SKIP] bin/spec not found (run ./bootstrap.sh first)"
fi
echo "   (node / python / ruby: interpreted — no separate build step)"
echo ""

# -----------------------------------------------------------------------------
# 2. Execution phase — the matrix.
# -----------------------------------------------------------------------------
echo "== Execution phase (3 medians reported at the end) =="

if [ -x "$OUT/mc_pi_c" ]; then
	echo "-- C (xorshift64 anchor) --"
	run_matrix c 1 "$P_COMP" 0 "$OUT/mc_pi_c" 1 "$P_COMP"
	run_matrix c "$PAR" "$P_COMP" 0 "$OUT/mc_pi_c" "$PAR" "$P_COMP"
fi
if [ -x "$OUT/mc_pi_c32" ]; then
	echo "-- C 32-bit RNG (RNG-width quantifier) --"
	run_matrix c32 1 "$P_COMP" 0 "$OUT/mc_pi_c32" 1 "$P_COMP"
fi
if [ -x "$OUT/mc_pi_cpp" ]; then
	echo "-- C++ --"
	run_matrix cpp 1 "$P_COMP" 0 "$OUT/mc_pi_cpp" 1 "$P_COMP"
	run_matrix cpp "$PAR" "$P_COMP" 0 "$OUT/mc_pi_cpp" "$PAR" "$P_COMP"
fi
if [ -x "$OUT/mc_pi_rs" ]; then
	echo "-- Rust --"
	run_matrix rust 1 "$P_COMP" 0 "$OUT/mc_pi_rs" 1 "$P_COMP"
	run_matrix rust "$PAR" "$P_COMP" 0 "$OUT/mc_pi_rs" "$PAR" "$P_COMP"
fi
if [ -x "$OUT/mc_pi_go" ]; then
	echo "-- Go --"
	run_matrix go 1 "$P_COMP" 0 "$OUT/mc_pi_go" 1 "$P_COMP"
	run_matrix go "$PAR" "$P_COMP" 0 "$OUT/mc_pi_go" "$PAR" "$P_COMP"
fi
if have java && { [ -n "$JAVAC" ] || true; }; then
	echo "-- Java (JIT warmed in-process) --"
	if [ -n "$JAVAC" ]; then
		run_matrix java 1 "$P_COMP" 0 java -cp "$OUT/classes" McPi 1 "$P_COMP"
		run_matrix java "$PAR" "$P_COMP" 0 java -cp "$OUT/classes" McPi "$PAR" "$P_COMP"
	else
		run_matrix java 1 "$P_COMP" 0 java "$BENCH/mc_pi.java" 1 "$P_COMP"
		run_matrix java "$PAR" "$P_COMP" 0 java "$BENCH/mc_pi.java" "$PAR" "$P_COMP"
	fi
fi
if [ -f "$OUT/mc_pi_kt.jar" ]; then
	echo "-- Kotlin (JIT warmed in-process) --"
	run_matrix kotlin 1 "$P_COMP" 0 java -jar "$OUT/mc_pi_kt.jar" 1 "$P_COMP"
	run_matrix kotlin "$PAR" "$P_COMP" 0 java -jar "$OUT/mc_pi_kt.jar" "$PAR" "$P_COMP"
fi
if have node; then
	echo "-- JavaScript / Node (workers for >1 thread) --"
	run_matrix node 1 "$P_COMP" 0 node "$BENCH/mc_pi.js" 1 "$P_COMP"
	run_matrix node "$PAR" "$P_COMP" 0 node "$BENCH/mc_pi.js" "$PAR" "$P_COMP"
fi
if have python3; then
	echo "-- Python (GIL: single thread; 20M points) --"
	run_matrix python 1 "$P_INT" 0 python3 "$BENCH/mc_pi.py" 1 "$P_INT"
	echo "-- Python experimental JIT (PYTHON_JIT=1) --"
	run_matrix python-jit 1 "$P_INT" 1 env PYTHON_JIT=1 python3 "$BENCH/mc_pi.py" 1 "$P_INT"
fi
if have ruby; then
	echo "-- Ruby (GVL: single thread; 20M points) --"
	run_matrix ruby 1 "$P_INT" 0 ruby "$BENCH/mc_pi.rb" 1 "$P_INT"
fi
if [ -x "$OUT/spec_pi" ]; then
	echo "-- Spec --"
	run_matrix spec 1 "$P_COMP" 0 "$OUT/spec_pi" --threads=1 --points="$P_COMP" --refresh=999999
	run_matrix spec "$PAR" "$P_COMP" 0 "$OUT/spec_pi" "--threads=$PAR" --points="$P_COMP" --refresh=999999
fi

# -----------------------------------------------------------------------------
# 3. Aggregation — medians per (language, threads) with ratios to the C anchor.
# -----------------------------------------------------------------------------
echo ""
echo "== Medians (rate pts/s | wall s | cpu% | peak RSS KB) =="
python3 - "$RESULTS" "$PAR" <<'PYEOF'
import statistics, sys

results, par = sys.argv[1], int(sys.argv[2])
groups = {}
for line in open(results):
    lang, threads, points, run, wall, cpu, rss, rate = line.strip().split(',')
    try:
        groups.setdefault((lang, int(threads)), []).append(
            (float(wall), float(cpu), float(rss), float(rate)))
    except ValueError:
        continue

def med(lang, threads):
    rows = groups.get((lang, threads))
    if not rows:
        return None
    w = statistics.median(r[0] for r in rows)
    c = statistics.median(r[1] for r in rows)
    r_ = statistics.median(r[2] for r in rows)
    rate = statistics.median(r[3] for r in rows)
    return w, c, r_, rate

order = ['c', 'c32', 'cpp', 'rust', 'go', 'java', 'kotlin', 'node',
         'python', 'python-jit', 'ruby', 'spec']
print(f"{'language':<12} {'thr':>3} {'rate pts/s':>14} {'x C':>6} {'x Spec':>7} "
      f"{'wall_s':>8} {'cpu%':>6} {'rss_kb':>8}")
for lang in order:
    for threads in ([1, par] if lang not in ('c32', 'python', 'python-jit', 'ruby') else [1]):
        m = med(lang, threads)
        if not m:
            continue
        w, c, rss, rate = m
        anchor = med('c', threads)
        specref = med('spec', threads)
        xc = rate / anchor[3] if anchor else 0.0
        xs = rate / specref[3] if specref else 0.0
        cpupct = 100.0 * c / w if w else 0.0
        print(f"{lang:<12} {threads:>3} {rate:>14.4e} {xc:>6.2f} {xs:>7.2f} "
              f"{w:>8.3f} {cpupct:>5.0f}% {rss:>8.0f}")
PYEOF

echo ""
echo "== Build medians (wall s | cpu s | peak RSS KB) =="
if [ -s "$BUILDS" ]; then
	awk -F, 'NF >= 4 && $2 != "" { printf "  %-8s wall=%-8s cpu=%-8s rss=%s KB\n", $1, $2, $3, $4 }' "$BUILDS"
fi
echo ""
echo "Raw per-run data: $RESULTS (runs) and $BUILDS (compiles)"

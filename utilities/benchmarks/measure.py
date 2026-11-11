#!/usr/bin/env python3
# =============================================================================
# Single-run measurement wrapper for the Spec cross-language benchmarks.
#
# Runs one command as an isolated child and reports the three metrics the
# performance comparison tracks:
#   wall_s  — monotonic wall-clock seconds (spawn to exit)
#   cpu_s   — user+system CPU seconds across ALL of the child's threads
#             (getrusage RUSAGE_CHILDREN; JVM/GC and worker threads included)
#   rss_kb  — peak resident set size of the child process tree, KiB
#
# The child's stdout passes through verbatim, then a single __MEASURE__ line
# is appended for run_benchmarks.sh to parse. One wrapper invocation per run:
# RUSAGE_CHILDREN is a cumulative max over reaped children, so isolated
# processes are the only way to attribute maxrss to a single run.
# =============================================================================
import resource
import subprocess
import sys
import time

cmd = sys.argv[1:]
t0 = time.monotonic()
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
wall = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
cpu = ru.ru_utime + ru.ru_stime
print(proc.stdout, end='')
sys.stdout.flush()
print(f"__MEASURE__ wall_s={wall:.3f} cpu_s={cpu:.3f} rss_kb={ru.ru_maxrss} exit={proc.returncode}")

#!/usr/bin/env ruby
# =============================================================================
# Monte Carlo pi benchmark — Ruby (CRuby 3.3). Same per-point work shape as
# mc_pi.c but with an xorshift32 (no fast native 64-bit integer loop; the
# 32-bit variant's cost is quantified separately against mc_pi32.c).
#
# Single thread only: the GVL prevents CPU-parallel threading. This build of
# CRuby is compiled without YJIT, so the number is plain interpreter speed.
#
# Usage: ruby mc_pi.rb <ignored-threads> <points>
# =============================================================================
n = (ARGV[1] || 20_000_000).to_i
m = 0xFFFFFFFF
d = 1.0 / 4294967296.0
st = (0x9E3779B9 ^ 1) & m
h = 0
t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
i = 0
while i < n
  st = (st ^ (st << 13)) & m
  st ^= (st >> 17)
  st = (st ^ (st << 5)) & m
  x = st * d
  st = (st ^ (st << 13)) & m
  st ^= (st >> 17)
  st = (st ^ (st << 5)) & m
  y = st * d
  h += 1 if x * x + y * y <= 1.0
  i += 1
end
ms = (Process.clock_gettime(Process::CLOCK_MONOTONIC) - t0) * 1000.0
puts format("pi=%.5f threads=1 points=%d ms=%.0f rate=%.4e", 4.0 * h / n, n, ms, n / (ms / 1000.0))

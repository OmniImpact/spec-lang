# =============================================================================
# Word/log-line frequency benchmark — Ruby (Hash + split).
# Usage: ruby wf.rb [count]
# =============================================================================

count = (ARGV[0] || "200000").to_i
count = 1 if count < 1

services = %w[
  auth api billing cache
  db edge feed gateway
  ingest jobs kv logs
  metrics notify proxy search
].freeze
levels = %w[INFO WARN ERR].freeze

st = 0x9E3779B9
3.times do
  st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
  st = (st ^ (st >> 17)) & 0xFFFFFFFF
  st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
end

counts = Hash.new(0)
t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)

count.times do
  st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
  st = (st ^ (st >> 17)) & 0xFFFFFFFF
  st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
  r1 = st & 15

  st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
  st = (st ^ (st >> 17)) & 0xFFFFFFFF
  st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
  r2 = (st & 0x7FFFFFFF) % 3

  st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
  st = (st ^ (st >> 17)) & 0xFFFFFFFF
  st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
  r3 = (st & 0x7FFFFFFF) % 500

  line = "#{services[r1]}:#{levels[r2]}:#{r3}"
  parts = line.split(":")
  code = parts[2].to_i
  bucket = code & 63
  key = "#{parts[0]}:#{parts[1]}:#{bucket}"
  counts[key] += 1
end

total = 0
max_count = 0
counts.each_value do |v|
  total += v
  max_count = v if v > max_count
end

ms = (Process.clock_gettime(Process::CLOCK_MONOTONIC) - t0) * 1000.0
ms = 1.0 if ms < 1.0
rate = count / (ms / 1000.0)
puts format("unique=%d total=%d max=%d count=%d ms=%.0f rate=%.4e", counts.size, total, max_count, count, ms, rate)

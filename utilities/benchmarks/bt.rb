# =============================================================================
# Binary-trees benchmark — Ruby (single-threaded).
# Usage: ruby bt.rb [threads] [max_depth]
# =============================================================================

Node = Struct.new(:left, :right)

def make_tree(depth)
  return Node.new(nil, nil) if depth <= 0
  Node.new(make_tree(depth - 1), make_tree(depth - 1))
end

def check_tree(n)
  return 1 if n.left.nil?
  1 + check_tree(n.left) + check_tree(n.right)
end

t = (ARGV[0] || "1").to_i
max_depth = (ARGV[1] || "14").to_i
min_depth = 4
max_depth = min_depth + 2 if max_depth < min_depth + 2

t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
total_checks = 0

stretch = make_tree(max_depth + 1)
total_checks += check_tree(stretch)
stretch = nil

long_lived = make_tree(max_depth)

d = min_depth
while d <= max_depth
  iterations = 1 << (max_depth - d + min_depth)
  iterations.times do
    total_checks += check_tree(make_tree(d))
  end
  d += 2
end

total_checks += check_tree(long_lived)

ms = (Process.clock_gettime(Process::CLOCK_MONOTONIC) - t0) * 1000.0
ms = 1.0 if ms < 1.0
rate = total_checks / (ms / 1000.0)
puts format("checksum=%d threads=%d depth=%d ms=%.0f rate=%.4e", total_checks, t, max_depth, ms, rate)

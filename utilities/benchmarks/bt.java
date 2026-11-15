// =============================================================================
// Binary-trees benchmark — Java (C2 JIT warmed with two depth-12 rounds).
// Usage: javac bt.java && java BinaryTrees <threads> <max_depth>
// =============================================================================
class BinaryTrees {

    private static final class Node {
        final Node left;
        final Node right;
        Node(Node l, Node r) {
            this.left = l;
            this.right = r;
        }
    }

    private static Node makeTree(int depth) {
        if (depth <= 0) return new Node(null, null);
        return new Node(makeTree(depth - 1), makeTree(depth - 1));
    }

    private static long checkTree(Node n) {
        if (n.left == null) return 1L;
        return 1L + checkTree(n.left) + checkTree(n.right);
    }

    private static void runOnce(int t, int maxDepth, boolean report) throws Exception {
        final int minDepth = 4;
        if (maxDepth < minDepth + 2) maxDepth = minDepth + 2;

        long t0 = System.nanoTime();
        long totalChecks = 0;

        Node stretch = makeTree(maxDepth + 1);
        totalChecks += checkTree(stretch);
        stretch = null;

        Node longLived = makeTree(maxDepth);

        for (int d = minDepth; d <= maxDepth; d += 2) {
            final int depth = d;
            long iterations = 1L << (maxDepth - d + minDepth);
            if (t <= 1) {
                for (long i = 0; i < iterations; i++) {
                    totalChecks += checkTree(makeTree(depth));
                }
            } else {
                final long[] sums = new long[t];
                Thread[] th = new Thread[t];
                long base = iterations / t, rem = iterations % t;
                for (int i = 0; i < t; i++) {
                    final int idx = i;
                    final long cnt = base + (i < rem ? 1 : 0);
                    th[i] = new Thread(() -> {
                        long s = 0;
                        for (long k = 0; k < cnt; k++) {
                            s += checkTree(makeTree(depth));
                        }
                        sums[idx] = s;
                    });
                    th[i].start();
                }
                for (int i = 0; i < t; i++) {
                    th[i].join();
                    totalChecks += sums[i];
                }
            }
        }

        totalChecks += checkTree(longLived);

        long ms = (System.nanoTime() - t0) / 1_000_000L;
        if (ms < 1) ms = 1;
        if (report) {
            System.out.printf("checksum=%d threads=%d depth=%d ms=%d rate=%.4e%n",
                totalChecks, t, maxDepth, ms, (double) totalChecks / (ms / 1000.0));
        }
    }

    public static void main(String[] args) throws Exception {
        int t = args.length > 0 ? Integer.parseInt(args[0]) : 1;
        int maxDepth = args.length > 1 ? Integer.parseInt(args[1]) : 18;
        if (t < 1) t = 1;
        for (int w = 0; w < 2; w++) runOnce(t, 12, false);
        runOnce(t, maxDepth, true);
    }
}

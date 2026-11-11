// =============================================================================
// Monte Carlo pi benchmark — Java, same algorithm as mc_pi.c (xorshift64,
// identical constants, identical per-point work). Plain threads + join keep
// the fan-out shape; the JIT is warmed with three throwaway rounds before the
// measured round, so the number is steady-state C2, not interpreter start-up.
// Package-private class so javac accepts any source file name (and the
// single-file source launcher still works).
//
// Usage: java mc_pi.java <threads> <points>   (single-file source launch)
//        javac mc_pi.java && java McPi <threads> <points>
// =============================================================================
class McPi {

    private static long nx(long s) {
        s ^= s << 13;
        s ^= s >>> 7;
        s ^= s << 17;
        return s;
    }

    private static long slice(int idx, long n, int t) {
        long st = 0x9E3779B97F4A7C15L
                ^ ((long) idx * 0xBF58476D1CE4E5B9L + 0x94D049BB133111EBL);
        if (st == 0) st = 1;
        st = nx(st); st = nx(st); st = nx(st);
        long h = 0;
        long per = n / t + (idx < n % t ? 1 : 0);
        final double scale = 1.0 / 9007199254740992.0;
        for (long k = 0; k < per; k++) {
            st = nx(st);
            double x = (double) (st >>> 11) * scale;
            st = nx(st);
            double y = (double) (st >>> 11) * scale;
            if (x * x + y * y <= 1.0) h++;
        }
        return h;
    }

    private static long runOnce(int t, long n, boolean report) throws Exception {
        final long[] hits = new long[t];
        Thread[] th = new Thread[t];
        long t0 = System.nanoTime();
        for (int i = 0; i < t; i++) {
            final int idx = i;
            th[i] = new Thread(() -> hits[idx] = slice(idx, n, t));
            th[i].start();
        }
        long h = 0;
        for (int i = 0; i < t; i++) {
            th[i].join();
            h += hits[i];
        }
        long ms = (System.nanoTime() - t0) / 1_000_000L;
        if (report) {
            System.out.printf("pi=%.5f threads=%d points=%d ms=%d rate=%.4e%n",
                    4.0 * h / (double) n, t, n, ms, n / (ms / 1000.0));
        }
        return ms;
    }

    public static void main(String[] args) throws Exception {
        int t = args.length > 0 ? Integer.parseInt(args[0]) : 8;
        long n = args.length > 1 ? Long.parseLong(args[1]) : 200_000_000L;
        if (t < 1) t = 1;
        for (int w = 0; w < 3; w++) runOnce(t, n / 4, false); // JIT warm-up
        runOnce(t, n, true);
    }
}

// =============================================================================
// Word/log-line frequency benchmark — Java (C2 JIT warmed with 50k lines).
// Usage: javac wf.java && java WordFreq [count]
// =============================================================================
import java.util.HashMap;

class WordFreq {

    private static long nx(long s) {
        s ^= s << 13;
        s ^= s >>> 7;
        s ^= s << 17;
        return s;
    }

    private static void runOnce(long count, boolean report) {
        final String[] services = {
            "auth", "api", "billing", "cache",
            "db", "edge", "feed", "gateway",
            "ingest", "jobs", "kv", "logs",
            "metrics", "notify", "proxy", "search"
        };
        final String[] levels = { "INFO", "WARN", "ERR" };

        long st = 0x9E3779B97F4A7C15L;
        st = nx(st); st = nx(st); st = nx(st);

        HashMap<String, Long> counts = new HashMap<>();
        long t0 = System.nanoTime();

        for (long i = 0; i < count; i++) {
            st = nx(st);
            int r1 = (int) (st & 15L);
            st = nx(st);
            int r2 = (int) ((st & 0x7FFFFFFFL) % 3L);
            st = nx(st);
            long r3 = (st & 0x7FFFFFFFL) % 500L;

            String line = services[r1] + ":" + levels[r2] + ":" + r3;
            String[] parts = line.split(":");
            long code = Long.parseLong(parts[2]);
            long bucket = code & 63L;
            String key = parts[0] + ":" + parts[1] + ":" + bucket;
            counts.merge(key, 1L, Long::sum);
        }

        long total = 0, maxCount = 0;
        for (long v : counts.values()) {
            total += v;
            if (v > maxCount) maxCount = v;
        }

        long ms = (System.nanoTime() - t0) / 1_000_000L;
        if (ms < 1) ms = 1;
        if (report) {
            System.out.printf("unique=%d total=%d max=%d count=%d ms=%d rate=%.4e%n",
                counts.size(), total, maxCount, count, ms, (double) count / (ms / 1000.0));
        }
    }

    public static void main(String[] args) {
        long count = args.length > 0 ? Long.parseLong(args[0]) : 1_000_000L;
        if (count < 1) count = 1;
        runOnce(50_000L, false);
        runOnce(count, true);
    }
}
